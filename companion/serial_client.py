"""Single-owner, synchronous request/reply client with unsolicited events."""
from collections import deque
import logging
import time

from .config import (DEVICE_NAME, PROTOCOL_VERSION, REQUEST_TIMEOUT,
                     HELLO_ATTEMPTS)
from .protocol import (LineDecoder, encode_request, LinkError,
                       RequestTimeout, ProtocolError, DeviceError)

LOG = logging.getLogger(__name__)


class SerialClient:
    def __init__(self, port, on_event=None):
        self.port = port
        self._on_event = on_event or (lambda event: None)
        self._decoder = LineDecoder()
        self._pending = deque()
        self._next_id = 1
        self.identity = None

    def close(self):
        self.port.close()

    def _read_message(self, deadline):
        while True:
            if self._pending:
                return self._pending.popleft()
            if time.monotonic() >= deadline:
                return None
            try:
                chunk = self.port.read(256)
            except OSError as exc:
                raise LinkError(f"USB read failed: {exc}") from exc
            if chunk:
                self._pending.extend(self._decoder.feed(chunk))

    def _dispatch_event(self, msg):
        if msg.get("type") in ("event", "ready"):
            self._on_event(msg)
            return True
        return False

    def request(self, command, *, timeout=REQUEST_TIMEOUT, **payload):
        if "type" in payload or "request_id" in payload:
            raise ValueError("Reserved request field")
        request_id = self._next_id
        self._next_id = request_id % 0xFFFFFFFF + 1
        wire = encode_request({"type": command, "request_id": request_id,
                               **payload})
        try:
            if self.port.write(wire) != len(wire):
                raise LinkError("Incomplete USB write")
        except OSError as exc:
            raise LinkError(f"USB write failed: {exc}") from exc

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            reply = self._read_message(deadline)
            if reply is None:
                break
            if self._dispatch_event(reply):
                continue
            # bool and float compare equal to ints in Python; reject them.
            reply_id = reply.get("request_id")
            if type(reply_id) is not int or reply_id != request_id:
                continue
            if reply.get("type") == "error":
                raise DeviceError(reply)
            expected = {"hello": "hello", "ping": "pong",
                        "get_info": "info", "get_mood": "mood"}.get(command, "ack")
            if reply.get("type") != expected:
                raise ProtocolError(f"Expected {expected} for {command}")
            if expected == "ack" and reply.get("command") != command:
                raise ProtocolError("Acknowledgment names the wrong command")
            return reply
        raise RequestTimeout(f"No reply to {command} (request {request_id}); outcome unknown")

    def handshake(self, *, attempts=HELLO_ATTEMPTS, timeout=REQUEST_TIMEOUT):
        self.identity = None
        for _ in range(attempts):
            try:
                reply = self.request("hello", timeout=timeout)
            except RequestTimeout:
                continue  # Opening the port may have reset the ESP32.
            if (reply.get("device") != DEVICE_NAME or
                    type(reply.get("protocol")) is not int or
                    reply["protocol"] != PROTOCOL_VERSION):
                raise ProtocolError("Not a compatible Svinka device")
            self.identity = reply
            return reply
        raise RequestTimeout("Svinka handshake timed out")

    def poll(self, timeout=0.25):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = self._read_message(deadline)
            if msg is None:
                return
            if not self._dispatch_event(msg):
                LOG.debug("Ignoring unsolicited response")
