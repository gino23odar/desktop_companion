
#include <Arduino.h>
#include <SPI.h>

#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <XPT2046_Touchscreen.h>

#include "HardwareConfig.h"
#include "SerialProtocol.h"
#include "Mood.h"
#include "CharacterRenderer.h"
#include "AnimationEngine.h"


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

AnimationEngine animationEngine;


// --------------------------------------------------
// Configuration and application state
// --------------------------------------------------

constexpr uint32_t BOOP_DURATION_MS = 1000;

constexpr uint32_t LOOP_DELAY_MS = 5;

Mood activeMood = MoodModel::defaultMood();

AnimationFrame displayedFrame{};

bool wasTouched = false;

bool booping = false;

uint32_t boopStartedAt = 0;


// --------------------------------------------------
// Hardware initialization
// --------------------------------------------------

void initializeHardware() {

    Serial.setRxBufferSize(
        Hardware::SERIAL_RX_BUFFER_SIZE
    );

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


void showActiveMood() {

    displayedFrame = AnimationFrame{};

    renderer.render(
        activeMood,
        displayedFrame
    );

    animationEngine.reset(
        activeMood.animation,
        millis()
    );
}


void applyMood(const Mood& mood) {

    activeMood = mood;

    // Allow temporary reactions to finish.
    if (!booping) {

        showActiveMood();
    }
}


// --------------------------------------------------
// Animation management
// --------------------------------------------------

void updateAnimation() {

    // Normal animations are suspended during boops.
    if (booping) {
        return;
    }

    AnimationFrame nextFrame =
        animationEngine.tick(millis());

    renderer.renderAnimation(
        activeMood,
        displayedFrame,
        nextFrame
    );

    displayedFrame = nextFrame;
}


// --------------------------------------------------
// Interaction handling
// --------------------------------------------------

void startBoop() {

    booping = true;

    Mood reaction =
        MoodModel::boopMood(activeMood);

    // Display a fixed temporary reaction.
    renderer.render(
        reaction,
        AnimationFrame{}
    );

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

        showActiveMood();
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

    showActiveMood();

    SerialProtocol::emitReady();
}


void loop() {

    SerialProtocol::poll(handlers);

    updateTouch();

    updateInteraction();

    updateAnimation();

    delay(LOOP_DELAY_MS);
}
