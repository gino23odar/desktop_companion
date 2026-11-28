
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


## Dynamic mood engine regression tests

### Test 20 - Default mood

Power on the device and send get_mood.

Expected:

- Mood ID is idle.
- Default pig expression is visible.
- Firmware version is 0.3.0.

### Test 21 - Valid mood updates

Send valid definitions covering all supported
eye, mouth and accessory values.

Expected:

- Each valid definition is acknowledged.
- The rendered appearance matches its definition.
- Background and caption update correctly.

### Test 22 - Mood round trip

Send a valid set_mood command.

Send get_mood afterward.

Expected:

The returned definition matches the accepted
definition, with hexadecimal colors normalized
to uppercase.

### Test 23 - Validation

Test:

- Missing required fields
- Unsupported expressions
- Invalid colors
- Invalid identifiers
- Incorrect boolean types
- Oversized messages
- Unsupported characters
- Unknown additional fields
- Incorrect mood object types

Expected:

- Structured invalid_mood error.
- Invalid field is identified.
- Previous mood remains unchanged.

### Test 24 - Physical boop

Select a non-default mood.

Physically tap the touchscreen.

Expected:

- Temporary happy reaction.
- Physical boop event.
- Selected mood restored after expiration.

### Test 25 - Remote boop

Select a non-default mood.

Send a remote boop command.

Expected:

- Temporary happy reaction.
- Command acknowledgment.
- No physical-touch event.
- Selected mood restored after expiration.

### Test 26 - Mood update during reaction

Trigger a boop and send a new mood before
the reaction expires.

Expected:

The newly selected mood is displayed when
the reaction expires.

### Test 27 - Dark backgrounds

Send a mood with a dark background color.

Expected:

White foreground text and facial details
remain visible.

### Test 28 - Message boundaries

Test an empty message, a 24-character message
and a 25-character message.

Expected:

- Empty message accepted.
- 24-character message accepted and fits.
- 25-character message rejected.

### Test 29 - Power cycle

Select a non-default mood.

Disconnect and reconnect USB power.

Expected:

The previously selected mood is restored,
including its animation configuration.

### Test 30 - Mixed interaction stability

Alternate between valid mood updates, invalid
updates, physical touches, remote boops and
get_mood commands for five minutes.

Expected:

- No unexpected restarts.
- No frozen display.
- No corrupted application state.
- Existing USB commands remain responsive.


## Animation engine regression tests

### Test 31 - Native C++ tests

Execute the animation test binary.

Expected: All seven tests pass.

### Test 32 - Default animations

Power on the device.

Expected:

- Default pig character appears.
- Automatic blinking occurs.
- Periodic ear movement occurs.

### Test 33 - Configurable blinking

Test blink cycles of 1000, 4500 and 15000 ms.

Expected:

Blink timing follows the selected configuration.

### Test 34 - Glasses blinking

Select the glasses eye style.

Expected:

Pupils blink while the glasses remain visible.

### Test 35 - Accessory movement

Test hearts, stars and Zzz.

Expected:

Accessories move without leaving visual trails.

### Test 36 - Ear movement

Observe multiple ear movement cycles.

Expected:

Both ears move and return to their original
positions without leaving visual artifacts.

### Test 37 - Disabled animations

Set blink_ms to zero and both flags to false.

Expected:

No automatic character movement.

### Test 38 - Legacy mood compatibility

Send a mood without an animation object.

Expected:

The mood is accepted with default settings.

### Test 39 - Invalid animation settings

Test incorrect values, missing fields and
unsupported additional fields.

Expected:

An invalid_mood error is returned.

The current active mood remains unchanged.

### Test 40 - Physical boop during animation

Tap the display while animations are running.

Expected:

The reaction appears, a touch event is emitted,
and the original mood is restored afterward.

### Test 41 - USB communication during animation

Send commands while animations are active.

Expected:

Serial responses remain available.

### Test 42 - Partial redraw quality

Observe blinking, moving ears and accessories.

Expected:

No persistent trails or corruption in adjacent
screen regions.

### Test 43 - Stability

Leave the device running for ten minutes while
periodically sending commands and tapping it.

Expected:

No unexpected resets, freezes or corrupted
application state.


## Persistent storage regression tests

### Test 44 - Native storage tests

Run the mood storage test binary.

Expected: All thirteen tests pass.

### Test 45 - First startup

Start the device with an empty storage record
namespace.

Expected:

- Default mood is displayed.
- Ready message is emitted.
- Storage status is empty.

### Test 46 - Persistent mood

Send a valid custom mood and wait for its
acknowledgment.

Disconnect and reconnect USB power.

Expected:

The custom mood is restored.

### Test 47 - Animation persistence

Configure non-default animation settings.

Power cycle the device.

Expected:

All animation settings remain unchanged.

### Test 48 - Invalid updates

Send an invalid mood definition.

Expected:

The update is rejected.

The last accepted mood is restored after
a subsequent power cycle.

### Test 49 - Boop persistence isolation

Select a custom mood.

Trigger a boop and disconnect USB during
the temporary reaction.

Expected:

The original custom mood is restored.

### Test 50 - Reset mood

Send reset_mood.

Power cycle the device.

Expected:

The default mood remains selected.

### Test 51 - Legacy mood support

Send a mood without animation settings.

Power cycle the device.

Expected:

The mood is restored with default animation
settings.

### Test 52 - Stability

Run the device for ten minutes while
alternating mood updates, physical touches,
remote boops and USB commands.

Expected:

- No unexpected resets.
- No corrupted graphics.
- No persistent communication failures.

## Desktop companion regression tests

### Test 53 - Python unit tests

Execute the companion test suite.

Expected: All 25 tests pass.

### Test 54 - Device discovery

Connect the desk buddy through USB.

Execute ports and hello.

Expected: The correct device is identified.

### Test 55 - Mood updates

Apply both supplied JSON mood files.

Expected: Each mood is displayed and persisted.

### Test 56 - Device events

Run watch mode and physically touch the screen.

Expected: Structured touch events are received.

### Test 57 - Reconnection

Disconnect and reconnect the device.

Expected: Watch mode automatically reconnects.

### Test 58 - Invalid commands

Send an invalid mood.

Expected: The firmware error is reported and
the previous mood remains unchanged.

### Test 59 - Cross-platform compatibility

Verify Windows and Linux CI.

Perform physical USB testing on Windows.

### Test 60 - Stability

Run watch mode for ten minutes.

Periodically tap the touchscreen.

Expected: No unexpected crashes or persistent
communication failures.

## Backend regression tests

### Test 61 - Automated backend tests

Execute the backend test suite.

Expected: All 27 tests pass.

### Test 62 - Server initialization

Start the backend with a new database.

Expected:

- Database tables are created.
- Default idle mood is available.
- Initial publication revision is 1.

### Test 63 - Mood catalog management

Create, retrieve, update and delete moods.

Expected:

All supported operations behave correctly.

### Test 64 - Authentication

Test administrative, device and invalid credentials.

Expected:

Only administrative credentials can modify
the catalog or publish moods.

### Test 65 - Mood publication

Publish a mood, edit its catalog definition,
and publish it again.

Expected:

Catalog editing does not modify the published
snapshot until explicit activation.

Duplicate publication does not increment
the revision.

### Test 66 - Backend persistence

Stop and restart the server.

Expected:

The mood catalog, published snapshot and
revision remain unchanged.

### Test 67 - Firmware compatibility

Validate mood definitions and serial payload size.

Expected:

Valid backend moods conform to the existing
firmware protocol requirements.

## Remote synchronization regression tests

### Test 68 - Automated synchronization tests

Execute the companion and backend test suites.

Expected: All 83 Python tests pass.

### Test 69 - Automatic mood delivery

Publish a mood using the backend API.

Expected: The physical device displays the new mood
without requiring a manual serial command.

### Test 70 - Duplicate delivery prevention

Publish an identical mood repeatedly.

Expected: No unnecessary set_mood commands or
full-screen redraws occur.

### Test 71 - USB disconnection and recovery

Disconnect the ESP32, publish additional moods,
and reconnect the device.

Expected: The latest publication is applied.

### Test 72 - Backend interruption and recovery

Stop and restart the backend while synchronization
is active.

Expected: The cached mood is retained and polling
recovers automatically.

### Test 73 - Offline startup

Restart the companion with the backend offline.

Expected: The last valid cached publication is used.

### Test 74 - Device reset recovery

Reset the ESP32 while synchronization is active.

Expected: The intended published mood is retained
or restored.

### Test 75 - Physical interaction regression

Trigger boop reactions during synchronization.

Expected: Temporary interactions remain functional
and do not modify the published base mood.

### Test 76 - Authentication regression

Configure an invalid device credential.

Expected: Remote responses are rejected and the last
valid state is retained.

### Test 77 - Extended synchronization stability

Run synchronization for at least ten minutes.

Expected: No unexpected crashes, persistent rendering
artifacts or unrecoverable communication failures.

## Studio regression tests

### Test 78 - JavaScript model and API tests
Run `node --test tests/studio/model.test.mjs tests/studio/api.test.mjs`.
Expected: 15 passing tests.

### Test 79 - Static hosting and backend regression
Run `python -m unittest discover -s tests/backend -v`.
Expected: 32 passing tests, including 4 Studio hosting/security tests.

### Test 80 - Browser integration
Install Playwright and Chromium per docs/studio.md; run
`python -m unittest discover -s tests/studio -p test_browser.py -v`.
Expected: the real browser workflow passes against a temporary database.

### Test 81 - Studio authentication
Open /studio/, reject a device token, connect with an admin token.
Reload; Studio requires authentication again.

### Test 82 - Draft isolation and publication
Create or edit a mood, save, and verify the published snapshot is unchanged.
Publish explicitly; revision and physical display update after sync.

### Test 83 - Preview and validation
Check supported appearance fields, animation timing, boop preview,
ASCII and 24-character limits. Invalid or unsaved moods cannot publish.

### Test 84 - Catalog management
Duplicate a mood, save, delete; cannot delete the active mood.

### Test 85 - Responsive UI and regression
Check desktop and mobile viewport widths. Verify existing Swagger and sync
continue working. Do not confuse publication with delivery confirmation.