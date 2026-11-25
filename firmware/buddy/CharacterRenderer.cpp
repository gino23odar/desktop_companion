
#include "CharacterRenderer.h"


CharacterRenderer::CharacterRenderer(
    Adafruit_ILI9341& display
) : display(display) {
}


// --------------------------------------------------
// Colors
// --------------------------------------------------

uint16_t CharacterRenderer::toColor565(
    uint32_t rgb
) {

    uint8_t red = (rgb >> 16) & 0xFF;
    uint8_t green = (rgb >> 8) & 0xFF;
    uint8_t blue = rgb & 0xFF;

    return display.color565(
        red,
        green,
        blue
    );
}


uint16_t CharacterRenderer::contrastingColor(
    uint32_t rgb
) {

    uint32_t red = (rgb >> 16) & 0xFF;
    uint32_t green = (rgb >> 8) & 0xFF;
    uint32_t blue = rgb & 0xFF;

    uint32_t brightness =
        (red * 299 +
         green * 587 +
         blue * 114) / 1000;

    return brightness < 128
        ? ILI9341_WHITE
        : ILI9341_BLACK;
}


// --------------------------------------------------
// Character rendering
// --------------------------------------------------

void CharacterRenderer::render(
    const Mood& mood
) {

    uint16_t background =
        toColor565(mood.background);

    uint16_t ink =
        contrastingColor(mood.background);

    uint16_t nose =
        display.color565(244, 145, 170);

    display.fillScreen(background);

    drawEars(nose);

    drawEyes(mood.eyes, ink);

    if (mood.blush) {
        drawBlush();
    }

    drawSnout(nose);

    drawMouth(mood.mouth, ink);

    drawAccessory(
        mood.accessory,
        ink
    );

    drawCaption(
        mood.message,
        ink
    );
}


void CharacterRenderer::drawEars(
    uint16_t color
) {

    display.fillTriangle(
        60, 90,
        90, 45,
        120, 90,
        color
    );

    display.fillTriangle(
        200, 90,
        230, 45,
        260, 90,
        color
    );
}


void CharacterRenderer::drawEyes(
    EyeStyle style,
    uint16_t ink
) {

    const int16_t positions[] = {
        110,
        210
    };

    for (int16_t x : positions) {

        switch (style) {

            case EyeStyle::Open:

                display.fillCircle(
                    x, 115, 10, ink
                );

                break;

            case EyeStyle::Happy:

                for (int16_t offset = 0;
                     offset < 3;
                     ++offset) {

                    display.drawLine(
                        x - 12,
                        115 + offset,
                        x,
                        103 + offset,
                        ink
                    );

                    display.drawLine(
                        x,
                        103 + offset,
                        x + 12,
                        115 + offset,
                        ink
                    );
                }

                break;

            case EyeStyle::Sleepy:

                for (int16_t offset = 0;
                     offset < 3;
                     ++offset) {

                    display.drawLine(
                        x - 12,
                        115 + offset,
                        x,
                        121 + offset,
                        ink
                    );

                    display.drawLine(
                        x,
                        121 + offset,
                        x + 12,
                        115 + offset,
                        ink
                    );
                }

                break;

            case EyeStyle::Excited:

                display.fillCircle(
                    x, 112, 14, ink
                );

                display.fillCircle(
                    x - 4,
                    107,
                    4,
                    ink == ILI9341_WHITE
                        ? ILI9341_BLACK
                        : ILI9341_WHITE
                );

                break;

            case EyeStyle::Glasses:

                display.fillCircle(
                    x, 115, 9, ink
                );

                display.drawRoundRect(
                    x - 23,
                    96,
                    46,
                    37,
                    7,
                    ink
                );

                display.drawRoundRect(
                    x - 22,
                    97,
                    44,
                    35,
                    6,
                    ink
                );

                break;
        }
    }

    if (style == EyeStyle::Glasses) {

        display.drawFastHLine(
            133, 113, 54, ink
        );

        display.drawFastHLine(
            133, 114, 54, ink
        );
    }
}


void CharacterRenderer::drawBlush() {

    uint16_t blush =
        display.color565(247, 140, 167);

    display.fillRoundRect(
        66, 139,
        40, 16,
        8,
        blush
    );

    display.fillRoundRect(
        214, 139,
        40, 16,
        8,
        blush
    );
}


void CharacterRenderer::drawSnout(
    uint16_t color
) {

    display.fillRoundRect(
        125, 140,
        70, 45,
        20,
        color
    );

    display.fillCircle(
        145, 162,
        6,
        ILI9341_BLACK
    );

    display.fillCircle(
        175, 162,
        6,
        ILI9341_BLACK
    );
}


void CharacterRenderer::drawMouth(
    MouthStyle style,
    uint16_t ink
) {

    switch (style) {

        case MouthStyle::None:

            break;

        case MouthStyle::Smile:

            display.drawLine(
                150, 193,
                160, 199,
                ink
            );

            display.drawLine(
                160, 199,
                170, 193,
                ink
            );

            break;

        case MouthStyle::Neutral:

            display.drawFastHLine(
                152, 195, 17, ink
            );

            display.drawFastHLine(
                152, 196, 17, ink
            );

            break;

        case MouthStyle::Open:

            display.fillRoundRect(
                153, 190,
                14, 10,
                5,
                ink
            );

            break;
    }
}


// --------------------------------------------------
// Accessories
// --------------------------------------------------

void CharacterRenderer::drawAccessory(
    Accessory accessory,
    uint16_t ink
) {

    switch (accessory) {

        case Accessory::None:

            break;

        case Accessory::Heart: {

            uint16_t color =
                display.color565(223, 66, 107);

            display.fillCircle(
                272, 42, 9, color
            );

            display.fillCircle(
                288, 42, 9, color
            );

            display.fillTriangle(
                263, 45,
                297, 45,
                280, 64,
                color
            );

            break;
        }

        case Accessory::Star: {

            uint16_t color =
                display.color565(231, 182, 58);

            display.fillTriangle(
                280, 29,
                268, 65,
                297, 43,
                color
            );

            display.fillTriangle(
                280, 29,
                292, 65,
                263, 43,
                color
            );

            display.fillTriangle(
                263, 43,
                297, 43,
                280, 57,
                color
            );

            break;
        }

        case Accessory::Zzz:

            display.setTextSize(2);

            display.setTextColor(ink);

            display.setCursor(263, 40);

            display.print("Zzz");

            break;
    }
}


// --------------------------------------------------
// Caption
// --------------------------------------------------

void CharacterRenderer::drawCaption(
    const char* message,
    uint16_t ink
) {

    display.setFont(nullptr);
    display.setTextSize(2);
    display.setTextColor(ink);
    display.setTextWrap(false);

    int16_t x;
    int16_t y;

    uint16_t width;
    uint16_t height;

    display.getTextBounds(
        message,
        0,
        0,
        &x,
        &y,
        &width,
        &height
    );

    int16_t centeredX =
        (display.width() -
         static_cast<int16_t>(width)) / 2;

    if (centeredX < 0) {
        centeredX = 0;
    }

    display.setCursor(
        centeredX,
        210
    );

    display.print(message);
}
