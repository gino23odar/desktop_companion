
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

All seven fields are required.

Unknown additional mood fields are rejected.

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

The active mood is currently stored in RAM.

Power cycling the device restores the default
idle mood.

Persistent storage will be introduced in a
subsequent release.

## Limitations

The current mood schema supports a fixed set
of rendering primitives.

Custom artwork, animation timelines and
downloadable assets are not yet supported.
