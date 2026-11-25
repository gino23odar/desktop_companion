
# Hardware regression tests

## Test 01: Firmware compilation

Compile the Buddy sketch using the ESP32 Dev Module
board configuration.

Expected: Compilation succeeds.

## Test 02: Startup

Upload the firmware and open Serial Monitor at
115200 baud.

Expected:

- BUDDY v0.1.0
- Display initialized.
- Touch initialized.
- Ready for boops!

## Test 03: Default rendering

Power on the device.

Expected:

- Pink background.
- Two ears.
- Two open eyes.
- Pink snout.
- Hello Buddy! caption.

## Test 04: Touch interaction

Tap the touchscreen.

Expected:

- Happy eye expression.
- BOOP! caption.
- BOOP! message in Serial Monitor.

## Test 05: Reaction expiration

Tap the screen and release it.

Expected:

The default expression returns after approximately
one second.

## Test 06: Continuous touch

Press and hold the screen for three seconds.

Expected:

Only one BOOP! event is emitted during the
continuous touch.

## Test 07: Repeated interaction

Tap, release and tap again.

Expected:

Each separate touch produces a BOOP! event.

## Test 08: Power cycle

Disconnect USB power and reconnect it.

Expected:

The device boots normally and displays the
default character.

## Test 09: Stability

Leave the device powered for five minutes.
Interact with the touchscreen periodically.

Expected:

- No unexpected restarts.
- No frozen touchscreen.
- No corrupted graphics.
