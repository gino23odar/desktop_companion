"""Wire format and bounded incremental NDJSON decoding"""
import json
from .config import MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES


class LinkError(Exception):
    """Connection or protocol failure"""


class RequestTimeout(LinkError):
    """No correlated reply before the deadline"""


class DeviceError(Exception):
    """Firmware explicitly rejected a request"""

    def __init__(self, reply: dict):
        self.reply = reply
        super().__init__(str(reply.get("code", "unknown_error")))


class ProtocolError(LinkError):
    """A reply did not match the expected protocol"""


def encode_request(message: dict) -> bytes:
    data = json.dumps(message, ensure_ascii=True, separators=(",", ":"),
                      allow_nan=False).encode("ascii")
    if len(data) > MAX_REQUEST_BYTES:
        raise ValueError("Request exceeds the firmware's 511-byte line limit")
    return data + b"\n"


class LineDecoder:
    """Retain partial lines between reads; drop bad/oversized lines"""

    def __init__(self):
        self._buffer = bytearray()
        self._discard = False

    def feed(self, chunk: bytes) -> list[dict]:
        messages = []
        for byte in chunk:
            if byte == 10:  # LF, including the end of a discarded line
                if not self._discard and self._buffer:
                    try:
                        msg = json.loads(self._buffer.decode("utf-8"))
                        if isinstance(msg, dict):
                            messages.append(msg)
                    except (UnicodeError, ValueError, RecursionError):
                        pass  # ESP32 boot logs or malformed lines
                self._buffer.clear()
                self._discard = False
            elif not self._discard:
                if byte == 0 or len(self._buffer) >= MAX_RESPONSE_BYTES:
                    self._buffer.clear()
                    self._discard = True
                else:
                    self._buffer.append(byte)
        return messages
