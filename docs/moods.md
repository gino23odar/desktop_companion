
# Mood definitions

Introduced in firmware version 0.3.0.

## Overview

A mood is a complete data-driven description of
the character's current appearance.

Moods are independent of the USB transport and
the character renderer.

## Schema

| Field | Type | Description |
|-------|------|-------------|
| id | String | Unique mood identifier |
| background | String | RGB hexadecimal color |
| eyes | String | Eye expression |
| mouth | String | Mouth expression |
| blush | Boolean | Enable cheek blush |
| accessory | String | Decorative symbol |
| message | String | Display caption |

The original seven appearance fields are required.

An optional animation object may also be supplied.

Unknown additional fields are rejected.

## Animation configuration

| Field | Type | Default |
|-------|------|---------|
| blink_ms | Integer | 4500 |
| ear_wiggle | Boolean | true |
| accessory_motion | Boolean | true |

blink_ms must be zero or between 1000 and
15000 milliseconds.

Zero disables blinking.

If animation is supplied, all three settings
are required.

If animation is omitted, default settings apply.

See [Animation engine](animations.md) for details.

## Supported values

### Identifier

Between 1 and 24 characters.

Allowed characters:

- Lowercase ASCII letters
- Digits
- Underscores
- Hyphens

### Background

RGB hexadecimal color in #RRGGBB format.

Uppercase and lowercase hexadecimal digits
are accepted.

Colors are returned in uppercase.

### Eyes

- open
- happy
- sleepy
- excited
- glasses

### Mouth

- none
- smile
- neutral
- open

### Accessory

- none
- heart
- star
- zzz

### Message

Between 0 and 24 printable ASCII characters.

Non-ASCII characters and control characters
are not currently supported.

## Example

    {
      "id": "sleepy",
      "background": "#DCD5F3",
      "eyes": "sleepy",
      "mouth": "none",
      "blush": false,
      "accessory": "zzz",
      "message": "Buenas noches"
    }

## Validation

The firmware validates all fields before
replacing the active mood.

Invalid definitions do not modify existing
application state.

## Temporary interactions

A boop creates a temporary visual reaction
derived from the active mood.

The active mood remains unchanged.

When the reaction expires, the renderer
displays the current active mood.

Updates received during a boop are accepted
but rendered after the reaction finishes.

## Persistence

Starting with firmware version 0.5.0,
accepted moods are saved to nonvolatile storage.

The selected mood and its animation settings
are restored when the device restarts.

Temporary reactions and animation frames
are not persisted.

The default mood is used when no valid
saved record is available.

See [Persistent storage](storage.md).

## Limitations

The current mood schema supports a fixed set
of rendering primitives.

Custom artwork, animation timelines and
downloadable assets are not yet supported.
