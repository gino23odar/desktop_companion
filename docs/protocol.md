
# Buddy USB communication protocol

## Version

Protocol version: 1

Introduced in firmware version 0.4.0.

## Transport

- USB serial
- Baud rate: 115200
- Data bits: 8
- Parity: None
- Stop bits: 1
- Encoding: UTF-8
- Message format: newline-delimited JSON
- Supported line endings: LF and CRLF

Each message must contain one JSON object.

The terminating newline is required.

## Message limits

The receive buffer is 512 bytes, including space
for the terminating null character.

The maximum received line length is therefore
511 bytes, excluding LF but including an optional CR.

Oversized messages are discarded until the next LF.

JSON nesting is limited to four levels.

Empty lines are ignored.

Clients should send one request at a time and wait
for a response before sending the next request.

Bulk data transfer is not supported in protocol v1.

## Request format

Every request must contain a string field named type.

An optional request_id may be supplied.

Request identifiers must be unsigned 32-bit integers.
A null identifier is treated as omitted.

When supplied and valid, the request identifier is
included in the corresponding response.

Unknown additional fields are currently ignored.

## Commands

### hello

Identifies the device and returns the firmware
and protocol versions.

Request:

    {"type":"hello"}

Response:

    {"type":"hello","device":"svinka","protocol":1,"firmware":"0.2.0"} // here buddy will be called svinka

### ping

Checks whether the device is responsive.

Request:

    {"type":"ping","request_id":1}

Response:

    {"type":"pong","request_id":1}

### get_info

Returns information about the device.

Request:

    {"type":"get_info"}

Response:

    {"type":"info","device":"svinka","firmware":"0.2.0","protocol":1,"width":320,"height":240}

### boop

Triggers the temporary boop reaction.

Request:

    {"type":"boop","request_id":2}

Response:

    {"type":"ack","command":"boop","request_id":2}

Remote boops do not generate physical-touch events.

## Device events

Events may arrive without a corresponding request.

### Startup

    {"type":"ready","device":"svinka","firmware":"0.2.0","protocol":1}

### Physical touch

    {"type":"event","event":"boop","source":"touch"}

## Error responses

Errors use the following format:

    {"type":"error","code":"unknown_command"}

Supported error codes:

| Code | Description |
|------|-------------|
| invalid_json | Malformed or incorrectly framed JSON |
| invalid_request | Root value is not a JSON object |
| invalid_request_id | Invalid request identifier |
| invalid_command | Missing or invalid command type |
| unknown_command | Command is not supported |
| message_too_large | Incoming line exceeds buffer capacity |
| invalid_frame | Incoming line contains a raw null byte |
| handler_unavailable | Required command handler is unavailable |

Malformed and oversized requests may not include a
request identifier in their error response.

## Client responsibilities

- Ignore non-JSON startup logs from the ESP32.
- Distinguish command responses from device events.
- Use request identifiers for response correlation.
- Implement response timeouts.
- Repeat the hello handshake after reconnecting.
- Do not assume that a USB port is always Buddy.

## Security

This protocol is intended for local USB communication.

It does not provide authentication or encryption.

The future desktop companion will be responsible
for authenticating remote backend requests.

The firmware must independently validate all
commands and supported content.


## set_mood

Introduced in firmware version 0.3.0.

Validates and activates a complete mood definition.

Request:

    {"type":"set_mood","request_id":1,"mood":{"id":"sleepy","background":"#DCD5F3","eyes":"sleepy","mouth":"none","blush":false,"accessory":"zzz","message":"Buenas noches"}}

Successful response:

    {"type":"ack","command":"set_mood","request_id":1}

An acknowledgment indicates that the mood was
accepted as the active mood.

If a temporary reaction is running, the new
mood is displayed when that reaction expires.

Invalid response:

    {"type":"error","code":"invalid_mood","field":"eyes","request_id":1}

An invalid update does not replace the existing
active mood.

See moods.md for the complete mood schema.

## get_mood

Returns the current active mood.

Request:

    {"type":"get_mood","request_id":2}

Response:

    {"type":"mood","mood":{"id":"sleepy","background":"#DCD5F3","eyes":"sleepy","mouth":"none","blush":false,"accessory":"zzz","message":"Buenas noches"},"request_id":2}

This command returns the base mood rather than
temporary visual reactions.

## Additional error codes

| Code | Description |
|------|-------------|
| invalid_mood | Invalid or unsupported mood definition |

Mood validation errors contain a field property
identifying the invalid field.

The special field values mood and unknown_field
indicate an invalid root value or unsupported
additional fields, respectively.

## Animation configuration

Firmware version 0.4.0 extends mood definitions
with an optional animation object.

Existing set_mood requests remain supported.

get_mood responses now include the complete
animation configuration.

Invalid animation settings use the existing
invalid_mood error format.

Example:

    {"type":"error","code":"invalid_mood","field":"animation.blink_ms"}

The protocol version remains 1.

See animations.md for the supported settings.


## Persistent mood behavior

Starting with firmware version 0.5.0,
set_mood persists a valid mood before
activating it.

An acknowledgment indicates that the mood
was successfully saved or was identical
to an already saved record.

If persistence fails, the existing active
mood remains unchanged.

## reset_mood

Restores and persists the default mood.

Request:

    {"type":"reset_mood","request_id":1}

Response:

    {"type":"ack","command":"reset_mood","request_id":1}

If a temporary boop reaction is active,
the default mood appears when it expires.

## Storage errors

    {"type":"error","code":"storage_error","request_id":1}

The requested mood could not be persisted.

## Storage event

Emitted after the startup ready message.

    {"type":"event","event":"storage","status":"restored"}

Possible status values:

- restored
- empty
- invalid
- unsupported_version
- unavailable

See storage.md for additional details.

The USB protocol version remains 1.
