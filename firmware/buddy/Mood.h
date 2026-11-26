
#pragma once

#include <stdint.h>
#include <stddef.h>
#include <ArduinoJson.h>
#include "AnimationEngine.h"

enum class EyeStyle : uint8_t {
    Open,
    Happy,
    Sleepy,
    Excited,
    Glasses
};

enum class MouthStyle : uint8_t {
    None,
    Smile,
    Neutral,
    Open
};

enum class Accessory : uint8_t {
    None,
    Heart,
    Star,
    Zzz
};

struct Mood {

    char id[25];

    uint32_t background;

    EyeStyle eyes;
    MouthStyle mouth;

    bool blush;

    Accessory accessory;

    char message[25];

    AnimationSettings animation;
};

namespace MoodModel {

    // Create the original default expression
    Mood defaultMood();

    // Create a temporary reaction from an active mood
    Mood boopMood(const Mood& activeMood);

    // Returns nullptr on success, or the invalid field name
    const char* parse(
        JsonVariantConst source,
        Mood& output
    );

    // Convert a mood back into its JSON representation
    void writeJson(
        JsonObject destination,
        const Mood& mood
    );
}
