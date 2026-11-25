
#include <Arduino.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <XPT2046_Touchscreen.h>

#include "HardwareConfig.h"
#include "SerialProtocol.h"

// Hardware instances
Adafruit_ILI9341 tft(
    Hardware::TFT_CS,
    Hardware::TFT_DC,
    Hardware::TFT_RST
);

XPT2046_Touchscreen touch(
    Hardware::TOUCH_CS
);

// Interaction configuration
constexpr uint32_t BOOP_DURATION_MS = 1000;
constexpr uint32_t LOOP_DELAY_MS = 20;

// Interaction state
bool wasTouched = false;
bool booping = false;

uint32_t boopStartedAt = 0;


// --------------------------------------------------
// Hardware initialization
// --------------------------------------------------

void initializeHardware() {

    Serial.begin(Hardware::SERIAL_BAUD);

    pinMode(Hardware::TFT_CS, OUTPUT);
    pinMode(Hardware::TOUCH_CS, OUTPUT);

    digitalWrite(Hardware::TFT_CS, HIGH);
    digitalWrite(Hardware::TOUCH_CS, HIGH);

    SPI.begin(
        Hardware::SPI_SCK,
        Hardware::SPI_MISO,
        Hardware::SPI_MOSI
    );

    tft.begin(Hardware::TFT_SPI_FREQUENCY);

    tft.setRotation(
        Hardware::DISPLAY_ROTATION
    );

    touch.begin(SPI);

    touch.setRotation(
        Hardware::TOUCH_ROTATION
    );
}


// --------------------------------------------------
// Character rendering - Piggy "Svinka"
// --------------------------------------------------

void drawEyes(bool happy) {

    if (happy) {

        // Left happy eye
        tft.drawLine(
            100, 115, 110, 105,
            ILI9341_BLACK
        );

        tft.drawLine(
            110, 105, 120, 115,
            ILI9341_BLACK
        );

        // Right happy eye
        tft.drawLine(
            200, 115, 210, 105,
            ILI9341_BLACK
        );

        tft.drawLine(
            210, 105, 220, 115,
            ILI9341_BLACK
        );

    } else {

        // Normal eyes
        tft.fillCircle(
            110, 115, 10,
            ILI9341_BLACK
        );

        tft.fillCircle(
            210, 115, 10,
            ILI9341_BLACK
        );
    }
}


void drawCaption(const char* caption) {

    tft.setTextSize(2);
    tft.setTextColor(ILI9341_BLACK);
    tft.setTextWrap(false);

    int16_t x;
    int16_t y;

    uint16_t width;
    uint16_t height;

    tft.getTextBounds(
        caption,
        0,
        0,
        &x,
        &y,
        &width,
        &height
    );

    int16_t centeredX =
        (Hardware::SCREEN_WIDTH - width) / 2;

    tft.setCursor(centeredX, 210);
    tft.print(caption);
}


void drawSvinka(bool happy) {

    const uint16_t background =
        tft.color565(255, 209, 222);

    const uint16_t nose =
        tft.color565(244, 145, 170);

    // Background
    tft.fillScreen(background);

    // Left ear
    tft.fillTriangle(
        60, 90,
        90, 45,
        120, 90,
        nose
    );

    // Right ear
    tft.fillTriangle(
        200, 90,
        230, 45,
        260, 90,
        nose
    );

    drawEyes(happy);

    // Snout
    tft.fillRoundRect(
        125, 140,
        70, 45,
        20,
        nose
    );

    // Nostrils
    tft.fillCircle(
        145, 162, 6,
        ILI9341_BLACK
    );

    tft.fillCircle(
        175, 162, 6,
        ILI9341_BLACK
    );

    drawCaption(
        happy ? "BOOP!" : "Hello Svinka!"
    );
}


// --------------------------------------------------
// Interaction handling
// --------------------------------------------------

void startBoop() {

    booping = true;

    drawSvinka(true);

    boopStartedAt = millis();

}


void updateTouch() {

    bool isTouched = touch.touched();

    // Trigger only when a new touch begins
    if (isTouched && !wasTouched) {
        startBoop();
        SerialProtocol::emitBoopEvent();
    }

    wasTouched = isTouched;
}


void updateInteraction() {

    if (!booping) {
        return;
    }

    uint32_t elapsed =
        millis() - boopStartedAt;

    if (elapsed >= BOOP_DURATION_MS) {

        booping = false;

        drawSvinka(false);
    }
}


// --------------------------------------------------
// Arduino lifecycle
// --------------------------------------------------

void setup() {

    initializeHardware();

    drawSvinka(false);

    SerialProtocol::emitReady();
}


void loop() {

    SerialProtocol::poll(startBoop);

    updateTouch();

    updateInteraction();

    delay(LOOP_DELAY_MS);
}
