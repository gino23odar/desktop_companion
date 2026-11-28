
#pragma once

#include <Arduino.h>

#include "Mood.h"

namespace SerialProtocol {

    constexpr uint8_t PROTOCOL_VERSION = 1;

    constexpr char DEVICE_NAME[] = "svinka";

    constexpr char FIRMWARE_VERSION[] = "0.6.0";


    using BoopHandler = void (*)();

    using SetMoodHandler =
        bool (*)(const Mood& mood);

    using GetMoodHandler =
        const Mood& (*)();


    struct Handlers {

        BoopHandler onBoop;

        SetMoodHandler onSetMood;

        GetMoodHandler onGetMood;
    };


    void poll(const Handlers& handlers);

    void emitReady();

    void emitBoopEvent();

    void emitStorageStatus(
        const char* status
    );
}
