
# Persistent mood storage

Introduced in firmware version 0.5.0.

## Overview

The device stores its most recently accepted mood
in the ESP32 nonvolatile storage partition.

The saved mood survives normal power cycles
and USB disconnection.

## Backend

- Library: ESP32 Preferences
- Storage type: NVS binary record
- Namespace: desk_buddy
- Key: active_mood
- Maximum record size: 511 bytes
- Storage schema version: 1

## Record format

The record contains a storage schema version
and a complete mood definition.

Example:

    {
      "schema": 1,
      "mood": {
        "id": "idle",
        "background": "#FFD1DE",
        "eyes": "open",
        "mouth": "none",
        "blush": false,
        "accessory": "none",
        "message": "Hello Svinka!",
        "animation": {
          "blink_ms": 4500,
          "ear_wiggle": true,
          "accessory_motion": true
        }
      }
    }

Records are stored as compact JSON in a
canonical serialization format.

## Saving behavior

Valid incoming moods are persisted before
being activated and acknowledged.

Identical saved records are not written again.

The storage cache is updated only after a
successful write or restoration.

Failed writes return a storage_error response.

The current active mood remains unchanged
when a save fails.

## Startup behavior

The firmware attempts to restore the saved mood.

If the record is missing, invalid, incompatible,
or unavailable, the default mood is used.

The firmware does not automatically erase
invalid or incompatible records.

## Storage status

The firmware emits a storage event after
the startup ready message.

Supported status values:

- restored
- empty
- invalid
- unsupported_version
- unavailable

## Temporary reactions

Boop reactions and animation frames are
never persisted.

Only the underlying selected mood is saved.

Animation timelines restart after power cycling.

## Resetting

Send:

    {"type":"reset_mood"}

The default mood replaces the saved mood.

This command does not erase the NVS partition.

## Testing

Native C++ tests use a fake storage backend.

These tests verify:

- Empty storage
- Serialization round trip
- Duplicate write prevention
- Duplicate prevention after restart
- Changed mood content
- Malformed data
- Invalid saved moods
- Unsupported schema versions
- Oversized records
- Trailing data
- Write failures and retries
- Reset behavior
- Unavailable storage

GitHub Actions runs these tests automatically.

Physical power-cycle tests must also be
performed on the ESP32.

## Limitations

Only one selected mood is persisted.

The device does not store a complete mood catalog.

Flash writes are synchronous.

Storage records are not encrypted by this module.

Interrupted writes rely on NVS recovery behavior.

Future schema changes may require migration logic.
