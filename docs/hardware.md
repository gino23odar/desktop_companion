
# Hardware configuration

## Components

- ESP32 DevKitC V4
- ESP-WROOM-32U module
- 2.8-inch ILI9341 SPI TFT LCD
- XPT2046 resistive touchscreen
- Micro-USB data cable
- Breadboard
- Dupont jumper wires

## Display configuration

- Resolution: 320 x 240
- Orientation: Landscape
- SPI frequency: 10 MHz
- Serial baud rate: 115200

## GPIO assignments

| Signal | ESP32 GPIO |
|--------|------------|
| TFT CS | 26 |
| TFT DC | 27 |
| TFT RESET | 33 |
| Touch CS | 25 |
| SPI SCK | 18 |
| SPI MISO | 19 |
| SPI MOSI | 23 |

## Shared SPI connections

| ESP32 | Display | Touch |
|-------|---------|-------|
| GPIO18 | SCK | T_CLK |
| GPIO19 | SDO | T_DO |
| GPIO23 | SDI | T_DIN |

The display and touchscreen use separate chip-select
pins while sharing the SPI bus.

The touchscreen interrupt pin is not required.

## Power

The device is powered through the ESP32 micro-USB port.

Retain the verified display VCC, GND and LED wiring.
The exact display PCB variant must be identified before
changing its power configuration.

## Connectivity

The ESP32 does not use Wi-Fi or Bluetooth.

An internet-connected computer will provide network
connectivity through a companion application and
communicate with the device using USB serial.

## Prototype

The breadboard is intended for development only.
The final enclosure will contain compact insulated
connections instead of the breadboard.

Disconnect USB power before modifying the wiring.
