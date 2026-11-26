
#include "AnimationEngine.h"

namespace {


// --------------------------------------------------
// Phase calculation
// --------------------------------------------------

uint32_t advancePhase(
    uint32_t phase,
    uint32_t elapsed,
    uint32_t period
) {

    if (period == 0) {
        return 0;
    }

    return (phase + elapsed % period) % period;
}


// --------------------------------------------------
// Ear animation
// --------------------------------------------------

int8_t earPosition(uint32_t phase) {

    if (phase >= 4200 && phase < 4350) {
        return 4;
    }

    if (phase >= 4350 && phase < 4500) {
        return -4;
    }

    if (phase >= 4500 && phase < 4650) {
        return 3;
    }

    return 0;
}


// --------------------------------------------------
// Accessory animation
// --------------------------------------------------

int8_t accessoryPosition(uint32_t phase) {

    uint32_t step = phase / 200;

    uint32_t height =
        step <= 4
            ? step
            : 8 - step;

    return static_cast<int8_t>(
        -2 * static_cast<int>(height)
    );
}

}


// --------------------------------------------------
// Reset animation state
// --------------------------------------------------

void AnimationEngine::reset(
    const AnimationSettings& settings,
    uint32_t now
) {

    settings_ = settings;

    // Defensive protection against invalid timing.
    if (
        settings_.blinkMs <
            AnimationLimits::MIN_BLINK_MS ||
        settings_.blinkMs >
            AnimationLimits::MAX_BLINK_MS
    ) {
        settings_.blinkMs = 0;
    }

    lastTick_ = now;

    blinkPhase_ = 0;
    earPhase_ = 0;
    accessoryPhase_ = 0;
}


// --------------------------------------------------
// Calculate the current animation frame
// --------------------------------------------------

AnimationFrame AnimationEngine::tick(
    uint32_t now
) {

    const uint32_t elapsed =
        now - lastTick_;

    lastTick_ = now;

    blinkPhase_ = advancePhase(
        blinkPhase_,
        elapsed,
        settings_.blinkMs
    );

    earPhase_ = advancePhase(
        earPhase_,
        elapsed,
        AnimationLimits::EAR_CYCLE_MS
    );

    accessoryPhase_ = advancePhase(
        accessoryPhase_,
        elapsed,
        AnimationLimits::ACCESSORY_CYCLE_MS
    );

    AnimationFrame frame{};

    if (settings_.blinkMs != 0) {

        frame.eyesClosed =
            blinkPhase_ >=
            settings_.blinkMs -
            AnimationLimits::BLINK_DURATION_MS;
    }

    if (settings_.earWiggle) {

        frame.earOffset =
            earPosition(earPhase_);
    }

    if (settings_.accessoryMotion) {

        frame.accessoryOffset =
            accessoryPosition(accessoryPhase_);
    }

    return frame;
}
