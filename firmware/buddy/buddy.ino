
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
#include "MoodStorage.h"
#include "PreferencesBackend.h"
#include "ArtworkPlayer.h"


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

PreferencesBackend storageBackend;

MoodStorage moodStorage(storageBackend);


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
    
    if (ArtworkPlayer::show()) {
        return;
    }

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

void redrawArtworkIfIdle() {
    if (!booping) {
        showActiveMood();
    }
}


bool applyMood(const Mood& mood) {

    // Persist before modifying application state
    if (!moodStorage.save(mood)) {

        return false;
    }

    activeMood = mood;

    // Allow temporary reactions to finish
    if (!booping) {

        showActiveMood();
    }

    return true;
}



// --------------------------------------------------
// Animation management
// --------------------------------------------------

void updateAnimation() {

    // Normal animations are suspended during boops.
    if (booping) {
        return;
    }

    if (ArtworkPlayer::active()) {
        ArtworkPlayer::tick();
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

    Mood reaction = MoodModel::boopMood(activeMood);

    // Display a fixed temporary reaction.
    if (!ArtworkPlayer::showBoop()) {
        renderer.render(
            reaction,
            AnimationFrame{}
        );
    }

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

    // Open nonvolatile storage
    storageBackend.begin();

    // Restore the saved mood or use the default
    const auto restoreResult = moodStorage.restore(activeMood);

    ArtworkPlayer::begin(tft, redrawArtworkIfIdle);

    // Render the restored appearance
    showActiveMood();

    // Preserve the existing startup handshake
    SerialProtocol::emitReady();

    // Report the storage restoration outcome
    SerialProtocol::emitStorageStatus(
        MoodStorage::statusName(
            restoreResult
        )
    );
}



void loop() {

    SerialProtocol::poll(handlers);

    updateTouch();

    updateInteraction();

    updateAnimation();

    delay(LOOP_DELAY_MS);
}
