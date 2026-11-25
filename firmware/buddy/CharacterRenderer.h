
#pragma once

#include <Adafruit_ILI9341.h>
#include "Mood.h"

class CharacterRenderer {

public:

    explicit CharacterRenderer(
        Adafruit_ILI9341& display
    );

    void render(const Mood& mood);

private:

    Adafruit_ILI9341& display;

    uint16_t toColor565(uint32_t rgb);

    uint16_t contrastingColor(uint32_t rgb);

    void drawEars(uint16_t color);

    void drawEyes(
        EyeStyle style,
        uint16_t ink
    );

    void drawMouth(
        MouthStyle style,
        uint16_t ink
    );

    void drawBlush();

    void drawSnout(uint16_t color);

    void drawAccessory(
        Accessory accessory,
        uint16_t ink
    );

    void drawCaption(
        const char* message,
        uint16_t ink
    );
};
