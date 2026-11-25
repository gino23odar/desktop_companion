#pragma once

#include <Arduino.h>

namespace Hardware {

    // USB serial communication
    constexpr uint32_t SERIAL_BAUD = 115200;
    // Maximum incoming serial line length in bytes
    constexpr size_t SERIAL_BUFFER_SIZE = 512;
    // Maximum serial bytes processed per loop iteration
    constexpr size_t SERIAL_BYTES_PER_LOOP = 128;

    // Shared SPI bus
    constexpr uint8_t SPI_SCK = 18;
    constexpr uint8_t SPI_MISO = 19;
    constexpr uint8_t SPI_MOSI = 23;

    // ILI9341 display
    constexpr uint8_t TFT_CS = 26;
    constexpr uint8_t TFT_DC = 27;
    constexpr uint8_t TFT_RST = 33;

    // XPT2046 touchscreen
    constexpr uint8_t TOUCH_CS = 25;

    // Display settings
    constexpr uint32_t TFT_SPI_FREQUENCY = 10000000;

    constexpr uint8_t DISPLAY_ROTATION = 1;
    constexpr uint8_t TOUCH_ROTATION = 1;

    constexpr uint16_t SCREEN_WIDTH = 320;
    constexpr uint16_t SCREEN_HEIGHT = 240;

}