
#include <Arduino.h>
#include <SPI.h>

#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <XPT2046_Touchscreen.h>

#include "HardwareConfig.h"
#include "SerialProtocol.h"
#include "Mood.h"
#include "CharacterRenderer.h"


// --------------------------------------------------
// Hardware instances
// --------------------------------------------------

Adafruit_ILI9341 tft(
    Hardware::TFT_CS,
    Hardware::TFT_DC,
    Hardware::TFT_RST
);

XPT2046_Touchscreen touch(
    Hardware::TOUCH_CS
);

CharacterRenderer renderer(tft);


// --------------------------------------------------
// Configuration and application state
// --------------------------------------------------

constexpr uint32_t BOOP_DURATION_MS = 1000;

constexpr uint32_t LOOP_DELAY_MS = 20;

Mood activeMood = MoodModel::defaultMood();

bool wasTouched = false;

bool booping = false;

uint32_t boopStartedAt = 0;


// --------------------------------------------------
// Hardware initialization
// --------------------------------------------------

void initializeHardware() {

    Serial.begin(Hardware::SERIAL_BAUD);

    pinMode(
        Hardware::TFT_CS,
        OUTPUT
    );

    pinMode(
        Hardware::TOUCH_CS,
        OUTPUT
    );

    digitalWrite(
        Hardware::TFT_CS,
        HIGH
    );

    digitalWrite(
        Hardware::TOUCH_CS,
        HIGH
    );

    SPI.begin(
        Hardware::SPI_SCK,
        Hardware::SPI_MISO,
        Hardware::SPI_MOSI
    );

    tft.begin(
        Hardware::TFT_SPI_FREQUENCY
    );

    tft.setRotation(
        Hardware::DISPLAY_ROTATION
    );

    touch.begin(SPI);

    touch.setRotation(
        Hardware::TOUCH_ROTATION
    );
}


// --------------------------------------------------
// Mood management
// --------------------------------------------------

const Mood& getActiveMood() {

    return activeMood;
}


void renderCurrentMood() {

    if (booping) {

        Mood reaction =
            MoodModel::boopMood(activeMood);

        renderer.render(reaction);

    } else {

        renderer.render(activeMood);
    }
}


void applyMood(const Mood& mood) {

    activeMood = mood;

    // If a temporary reaction is active display the new base mood when it expires
    if (!booping) {

        renderCurrentMood();
    }
}


// --------------------------------------------------
// Interaction handling
// --------------------------------------------------

void startBoop() {

    booping = true;

    renderCurrentMood();

    boopStartedAt = millis();
}


void updateTouch() {

    bool isTouched = touch.touched();

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

        renderCurrentMood();
    }
}


// --------------------------------------------------
// Protocol handlers
// --------------------------------------------------

const SerialProtocol::Handlers handlers = {

    startBoop,

    applyMood,

    getActiveMood
};


// --------------------------------------------------
// Arduino lifecycle
// --------------------------------------------------

void setup() {

    initializeHardware();

    renderCurrentMood();

    SerialProtocol::emitReady();
}


void loop() {

    SerialProtocol::poll(handlers);

    updateTouch();

    updateInteraction();

    delay(LOOP_DELAY_MS);
}
