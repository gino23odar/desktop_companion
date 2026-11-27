"""Shared protocol and connection settings"""
BAUD_RATE = 115200
PROTOCOL_VERSION = 1
DEVICE_NAME = "svinka"
MAX_REQUEST_BYTES = 511  # Excludes LF; firmware has a 512-byte buffer
MAX_RESPONSE_BYTES = 4096
READ_TIMEOUT = 0.1
WRITE_TIMEOUT = 1.0
REQUEST_TIMEOUT = 2.0
HELLO_ATTEMPTS = 3
RECONNECT_DELAY = 2.0
HEARTBEAT_INTERVAL = 3.0
# Default discovery targets the CP210x bridge on the reference DevKitC
USB_BRIDGES = {(0x10C4, 0xEA60)}
