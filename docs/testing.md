
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


## USB protocol regression tests

### Test 10 - Device identification

Send:

    {"type":"hello"}

Expected:

A hello response containing device name,
firmware version and protocol version.

### Test 11 - Heartbeat

Send:

    {"type":"ping","request_id":42}

Expected:

    {"type":"pong","request_id":42}

### Test 12 - Remote interaction

Send:

    {"type":"boop"}

Expected:

- Boop animation activates.
- An acknowledgment is returned.
- The default face returns after one second.
- No physical-touch event is emitted.

### Test 13 - Physical interaction

Tap the touchscreen.

Expected:

    {"type":"event","event":"boop","source":"touch"}

### Test 14 - Command validation

Send missing, malformed and unsupported commands.

Expected:

- An appropriate structured error response.
- No unexpected display changes.
- No firmware crashes.

### Test 15 - Message size limit

Send a line containing more than 511 bytes.

Expected:

    {"type":"error","code":"message_too_large"}

### Test 16 - Error recovery

After sending an oversized or malformed message,
send a valid ping command.

Expected:

    {"type":"pong"}

### Test 17 - Incomplete message handling

Set Serial Monitor to No line ending.

Send:

    {"type":

Verify that the device remains responsive to touch.

Switch Serial Monitor back to Newline and send:

    "ping"}

Expected:

    {"type":"pong"}

### Test 18 - Trailing data rejection

Send:

    {"type":"boop"}garbage

Expected:

    {"type":"error","code":"invalid_json"}

The boop animation must not activate.

### Test 19 - Mixed interaction stability

For five minutes, alternate between touchscreen
interactions, valid commands and invalid commands.

Expected:

- No crashes.
- No unexpected resets.
- No frozen display.
- No persistent loss of communication.
