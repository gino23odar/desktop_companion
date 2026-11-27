
# Animation engine

Introduced in firmware version 0.4.0.

## Overview

The animation engine calculates time-dependent
character appearance independently of display
hardware and USB communication.

## Supported animations

### Blinking

- Default cycle: 4500 milliseconds.
- Closed-eye duration: 120 milliseconds.
- Configurable cycle: 1000 to 15000 milliseconds.
- A value of zero disables blinking.

Open, excited and glasses expressions support
visible blinking. Happy and sleepy expressions
already represent closed eyes.

### Ear wiggle

- Cycle duration: 5000 milliseconds.
- Ear tips move through three displaced positions.
- Enabled by default.

### Accessory movement

- Cycle duration: 1600 milliseconds.
- Maximum upward displacement: eight pixels.
- Position changes every 200 milliseconds.
- Supports hearts, stars and Zzz.
- Enabled by default.

## Configuration

Moods may include an optional animation object:

    {
      "blink_ms": 4500,
      "ear_wiggle": true,
      "accessory_motion": true
    }

All three fields are required when the object
is supplied.

Legacy mood definitions use default settings.

## Timing

The engine receives timestamps from the caller.

Animation timing does not use blocking delays.

Unsigned elapsed-time calculations support
32-bit timestamp rollover when the engine
continues to be updated regularly.

## Rendering

Full-screen rendering is used when:

- The device starts.
- The active mood changes.
- A temporary reaction begins.
- A temporary reaction expires.

Ordinary animations use partial screen updates.

Only changed ear, eye and accessory regions
are erased and redrawn.

## Temporary reactions

Normal animation updates are suspended while
a boop reaction is active.

After the reaction expires, the active mood
is restored and its animation timeline restarts.

## Testing

The animation engine has no Arduino dependencies.

Native C++ tests verify blinking, ear movements,
accessory movements, disabled animations,
state resets, timestamp rollover and long gaps.

Run from the repository root:

    mkdir -p build/tests

    g++ -std=c++11 -Wall -Wextra -Werror -pedantic \
      -Ifirmware/buddy \
      firmware/buddy/AnimationEngine.cpp \
      tests/firmware/test_animation_engine.cpp \
      -o build/tests/animation_tests

    ./build/tests/animation_tests

GitHub Actions executes these tests automatically.

## Limitations

The current engine uses predefined animation
cycles and rendering primitives.

Custom keyframes, downloadable graphics and
buffered sprite rendering are not implemented.

Display operations remain synchronous.

## Buffered rendering

Firmware version 0.5.1 introduces reusable RGB565
canvas buffers for ear and accessory animations.

Animated regions are composed in RAM before being
transferred to the physical display.

This minimizes visible intermediate drawing stages
and reduces the display update area.

Eye rendering remains unchanged.

If buffer allocation fails, the renderer falls
back to direct drawing.