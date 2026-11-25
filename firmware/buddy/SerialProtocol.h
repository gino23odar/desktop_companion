
#pragma once

#include <Arduino.h>

namespace SerialProtocol {

    constexpr uint8_t PROTOCOL_VERSION = 1;

    constexpr char DEVICE_NAME[] = "svinka";

    constexpr char FIRMWARE_VERSION[] = "0.2.0";

    // Callback invoked when a remote boop is requested
    using BoopHandler = void (*)();

    // Process pending incoming serial data
    void poll(BoopHandler onBoop);

    // Report that the firmware has started
    void emitReady();

    // Report a physical touchscreen interaction
    void emitBoopEvent();

}
