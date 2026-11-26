
#pragma once

#include <stdint.h>

namespace AnimationLimits {

    constexpr uint32_t MIN_BLINK_MS = 1000;

    constexpr uint32_t MAX_BLINK_MS = 15000;

    constexpr uint32_t BLINK_DURATION_MS = 120;

    constexpr uint32_t EAR_CYCLE_MS = 5000;

    constexpr uint32_t ACCESSORY_CYCLE_MS = 1600;
}


struct AnimationSettings {

    uint32_t blinkMs;

    bool earWiggle;

    bool accessoryMotion;
};


constexpr AnimationSettings defaultAnimationSettings() {

    return {4500, true, true};
}


struct AnimationFrame {

    bool eyesClosed;

    int8_t earOffset;

    int8_t accessoryOffset;
};


class AnimationEngine {

public:

    void reset(
        const AnimationSettings& settings,
        uint32_t now
    );

    AnimationFrame tick(uint32_t now);

private:

    AnimationSettings settings_ =
        defaultAnimationSettings();

    uint32_t lastTick_ = 0;

    uint32_t blinkPhase_ = 0;

    uint32_t earPhase_ = 0;

    uint32_t accessoryPhase_ = 0;
};
