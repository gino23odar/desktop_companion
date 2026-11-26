
#include "Mood.h"

#include <cstring>
#include <cstdio>

namespace {

    const char* const EYE_NAMES[] = {
        "open",
        "happy",
        "sleepy",
        "excited",
        "glasses"
    };

    const char* const MOUTH_NAMES[] = {
        "none",
        "smile",
        "neutral",
        "open"
    };

    const char* const ACCESSORY_NAMES[] = {
        "none",
        "heart",
        "star",
        "zzz"
    };


    // --------------------------------------------------
    // String validation
    // --------------------------------------------------

    bool readText(
        JsonVariantConst value,
        char* output,
        size_t capacity
    ) {

        if (!value.is<const char*>()) {
            return false;
        }

        JsonString text = value.as<JsonString>();

        size_t length = text.size();

        if (length >= capacity) {
            return false;
        }

        const char* data = text.c_str();

        if (data == nullptr) {
            return false;
        }

        // Only printable ASCII characters are supported
        for (size_t i = 0; i < length; ++i) {

            unsigned char character = data[i];

            if (
                character < 32 ||
                character > 126
            ) {
                return false;
            }
        }

        memcpy(output, data, length);
        output[length] = '\0';

        return true;
    }


    bool isValidId(const char* id) {

        if (id[0] == '\0') {
            return false;
        }

        for (size_t i = 0; id[i] != '\0'; ++i) {

            char c = id[i];

            bool valid =
                (c >= 'a' && c <= 'z') ||
                (c >= '0' && c <= '9') ||
                c == '_' ||
                c == '-';

            if (!valid) {
                return false;
            }
        }

        return true;
    }


    // --------------------------------------------------
    // Color parsing
    // --------------------------------------------------

    int hexDigit(char character) {

        if (
            character >= '0' &&
            character <= '9'
        ) {
            return character - '0';
        }

        if (
            character >= 'a' &&
            character <= 'f'
        ) {
            return character - 'a' + 10;
        }

        if (
            character >= 'A' &&
            character <= 'F'
        ) {
            return character - 'A' + 10;
        }

        return -1;
    }


    bool readColor(
        JsonVariantConst value,
        uint32_t& output
    ) {

        char text[8];

        if (!readText(value, text, sizeof(text))) {
            return false;
        }

        if (
            strlen(text) != 7 ||
            text[0] != '#'
        ) {
            return false;
        }

        uint32_t result = 0;

        for (size_t i = 1; i < 7; ++i) {

            int digit = hexDigit(text[i]);

            if (digit < 0) {
                return false;
            }

            result =
                (result << 4) |
                static_cast<uint32_t>(digit);
        }

        output = result;

        return true;
    }


    // --------------------------------------------------
    // Enum parsing
    // --------------------------------------------------

    template <typename Enum, size_t N>
    bool readOption(
        JsonVariantConst value,
        const char* const (&names)[N],
        Enum& output
    ) {

        char text[16];

        if (!readText(value, text, sizeof(text))) {
            return false;
        }

        for (size_t i = 0; i < N; ++i) {

            if (strcmp(text, names[i]) == 0) {

                output = static_cast<Enum>(i);

                return true;
            }
        }

        return false;
    }


    const char* readAnimation(
        JsonVariantConst source,
        AnimationSettings& output
    ) {

        if (!source.is<JsonObjectConst>()) {
            return "animation";
        }

        JsonVariantConst blink =
            source["blink_ms"];

        if (!blink.is<uint32_t>()) {
            return "animation.blink_ms";
        }

        uint32_t blinkMs =
            blink.as<uint32_t>();

        if (
            blinkMs != 0 &&
            (
                blinkMs < AnimationLimits::MIN_BLINK_MS ||
                blinkMs > AnimationLimits::MAX_BLINK_MS
            )
        ) {
            return "animation.blink_ms";
        }

        if (!source["ear_wiggle"].is<bool>()) {
            return "animation.ear_wiggle";
        }

        if (!source["accessory_motion"].is<bool>()) {
            return "animation.accessory_motion";
        }

        if (source.size() != 3) {
            return "animation.unknown_field";
        }

        output = AnimationSettings{
            blinkMs,
            source["ear_wiggle"].as<bool>(),
            source["accessory_motion"].as<bool>()
        };

        return nullptr;
    }
}


// --------------------------------------------------
// Public mood functions
// --------------------------------------------------

namespace MoodModel {

Mood defaultMood() {

    return Mood {
        "idle",
        0xFFD1DE,
        EyeStyle::Open,
        MouthStyle::None,
        false,
        Accessory::None,
        "Hello Svinka!",
        defaultAnimationSettings()
    };
}


Mood boopMood(const Mood& activeMood) {

    Mood reaction = activeMood;

    reaction.eyes = EyeStyle::Happy;
    reaction.mouth = MouthStyle::Smile;
    reaction.blush = true;
    reaction.accessory = Accessory::Heart;

    strcpy(reaction.message, "BOOP!");

    return reaction;
}


const char* parse(
    JsonVariantConst source,
    Mood& output
) {

    if (!source.is<JsonObjectConst>()) {
        return "mood";
    }

    // Do not modify the active mood until every
    // field has been validated successfully
    Mood candidate = {};
    candidate.animation = defaultAnimationSettings();

    if (
        !readText(
            source["id"],
            candidate.id,
            sizeof(candidate.id)
        ) ||
        !isValidId(candidate.id)
    ) {
        return "id";
    }

    if (
        !readColor(
            source["background"],
            candidate.background
        )
    ) {
        return "background";
    }

    if (
        !readOption(
            source["eyes"],
            EYE_NAMES,
            candidate.eyes
        )
    ) {
        return "eyes";
    }

    if (
        !readOption(
            source["mouth"],
            MOUTH_NAMES,
            candidate.mouth
        )
    ) {
        return "mouth";
    }

    if (!source["blush"].is<bool>()) {
        return "blush";
    }

    candidate.blush = source["blush"].as<bool>();

    if (
        !readOption(
            source["accessory"],
            ACCESSORY_NAMES,
            candidate.accessory
        )
    ) {
        return "accessory";
    }

    if (
        !readText(
            source["message"],
            candidate.message,
            sizeof(candidate.message)
        )
    ) {
        return "message";
    }

    
    bool hasAnimation = false;

    for (
        JsonPairConst pair :
        source.as<JsonObjectConst>()
    ) {

        JsonString key = pair.key();

        if (
            key.size() == 9 &&
            memcmp(
                key.c_str(),
                "animation",
                9
            ) == 0
        ) {
            hasAnimation = true;
            break;
        }
    }

    if (hasAnimation) {

        const char* error = readAnimation(
            source["animation"],
            candidate.animation
        );

        if (error != nullptr) {
            return error;
        }
    }

    const size_t expectedFields =
        hasAnimation ? 8 : 7;

    if (source.size() != expectedFields) {
        return "unknown_field";
    }


    // Commit only a completely valid mood
    output = candidate;

    return nullptr;
}


void writeJson(
    JsonObject destination,
    const Mood& mood
) {

    char color[8];

    snprintf(
        color,
        sizeof(color),
        "#%06lX",
        static_cast<unsigned long>(
            mood.background & 0xFFFFFFUL
        )
    );

    destination["id"] = mood.id;

    // Ensure the JSON document owns the temporary color
    destination["background"] = static_cast<char*>(color);

    destination["eyes"] =
        EYE_NAMES[
            static_cast<uint8_t>(mood.eyes)
        ];

    destination["mouth"] =
        MOUTH_NAMES[
            static_cast<uint8_t>(mood.mouth)
        ];

    destination["blush"] = mood.blush;

    destination["accessory"] =
        ACCESSORY_NAMES[
            static_cast<uint8_t>(mood.accessory)
        ];

    destination["message"] = mood.message;
    
    JsonObject animation = destination["animation"].to<JsonObject>();

    animation["blink_ms"] = mood.animation.blinkMs;

    animation["ear_wiggle"] = mood.animation.earWiggle;

    animation["accessory_motion"] = mood.animation.accessoryMotion;
}

}
