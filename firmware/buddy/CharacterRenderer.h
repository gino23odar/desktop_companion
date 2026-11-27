
#pragma once

#include <Adafruit_ILI9341.h>

#include "Mood.h"
#include "AnimationEngine.h"

class CharacterRenderer {

public:

    explicit CharacterRenderer(
        Adafruit_ILI9341& display
    );

    // Draw a complete mood.
    void render(
        const Mood& mood,
        const AnimationFrame& frame
    );

    // Draw only the changed animation regions.
    void renderAnimation(
        const Mood& mood,
        const AnimationFrame& previous,
        const AnimationFrame& current
    );

private:

    Adafruit_ILI9341& display;

    uint16_t toColor565(uint32_t rgb);

    uint16_t contrastingColor(uint32_t rgb);

    void drawEars(
        uint16_t color,
        int8_t offset
    );

    void drawEyes(
        EyeStyle style,
        uint16_t ink,
        bool closed
    );

    void drawMouth(
        MouthStyle style,
        uint16_t ink
    );

    void drawBlush();

    void drawSnout(uint16_t color);

    void drawAccessory(
        Adafruit_GFX& target,
        Accessory accessory,
        uint16_t ink,
        int8_t offset,
        int16_t originX = 0,
        int16_t originY = 0
    );

    void drawCaption(
        const char* message,
        uint16_t ink
    );
};
