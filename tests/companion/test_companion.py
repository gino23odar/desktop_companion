import json
from collections import deque
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from companion.config import MAX_RESPONSE_BYTES
from companion.connection import connect, watch
from companion.discovery import select_port
from companion.protocol import (LineDecoder, encode_request, LinkError,
                                RequestTimeout, DeviceError, ProtocolError)
from companion.serial_client import SerialClient
from companion.__main__ import main


def wire(msg):
    return json.dumps(msg).encode() + b"\n"


def hello(req):
    return {"type": "hello", "device": "svinka", "firmware": "0.5.0",
            "protocol": 1, "request_id": req["request_id"]}


def port_info(name, serial="123", vid=0x10C4, pid=0xEA60):
    return SimpleNamespace(device=name, serial_number=serial, vid=vid, pid=pid)


class FakeSerial:
    def __init__(self, respond=lambda req: []):
        self.respond = respond
        self.chunks = deque()
        self.requests = []
        self.closed = False

    def write(self, data):
        request = json.loads(data)
        self.requests.append(request)
        self.chunks.extend(self.respond(request))
        return len(data)

    def read(self, size):
        if not self.chunks:
            return b""
        chunk = self.chunks.popleft()
        if isinstance(chunk, Exception):
            raise chunk
        if len(chunk) > size:
            self.chunks.appendleft(chunk[size:])
        return chunk[:size]

    def close(self):
        self.closed = True


class ProtocolTests(unittest.TestCase):
    def test_encode_bound(self):
        request = {"type": "ping", "pad": "x" * 480}
        self.assertTrue(encode_request(request).endswith(b"\n"))
        with self.assertRaises(ValueError):
            encode_request({"type": "ping", "pad": "x" * 600})

    def test_fragmented_and_multiple_lines(self):
        decoder = LineDecoder()
        self.assertEqual(decoder.feed(b'{"type":"po'), [])
        self.assertEqual(decoder.feed(b'ng"}\r\n{"type":"ready"}\n'),
                         [{"type": "pong"}, {"type": "ready"}])

    def test_noise_and_oversized_recovery(self):
        decoder = LineDecoder()
        self.assertEqual(decoder.feed(b'boot logs\n[]\n\xff\n'), [])
        self.assertEqual(decoder.feed(b'x' * (MAX_RESPONSE_BYTES + 1)), [])
        self.assertEqual(decoder.feed(b'{"type":"bad"}\n{"type":"pong"}\n'),
                         [{"type": "pong"}])

    def test_null_byte_recovery(self):
        decoder = LineDecoder()
        self.assertEqual(decoder.feed(b'{"type":"bad"}\x00\n{"type":"pong"}\n'),
                         [{"type": "pong"}])


class DiscoveryTests(unittest.TestCase):
    def test_single_matching_port(self):
        ports = [port_info("COM1", vid=1), port_info("COM3")]
        self.assertEqual(select_port(ports), "COM3")

    def test_ambiguous_ports(self):
        with self.assertRaises(LinkError):
            select_port([port_info("COM3"), port_info("COM4")])

    def test_serial_selector(self):
        self.assertEqual(select_port([port_info("COM3", "a"), port_info("COM4", "b")],
                                     usb_serial="b"), "COM4")

    def test_explicit_override_and_no_match(self):
        self.assertEqual(select_port([], explicit="/dev/ttyUSB9"), "/dev/ttyUSB9")
        with self.assertRaises(LinkError):
            select_port([])


class ClientTests(unittest.TestCase):
    def test_handshake(self):
        port = FakeSerial(lambda req: [b'booting\n', wire(hello(req))])
        self.assertEqual(SerialClient(port).handshake()["device"], "svinka")

    def test_handshake_retries(self):
        count = 0
        def respond(req):
            nonlocal count
            count += 1
            return [] if count == 1 else [wire(hello(req))]
        self.assertEqual(SerialClient(FakeSerial(respond)).handshake(timeout=0.005)["protocol"], 1)
        self.assertEqual(count, 2)

    def test_wrong_device_closes_port(self):
        port = FakeSerial(lambda req: [wire({**hello(req), "device": "other"})])
        with self.assertRaises(ProtocolError):
            connect(explicit="COM3", opener=lambda _: port)
        self.assertTrue(port.closed)

    def test_wrong_protocol(self):
        port = FakeSerial(lambda req: [wire({**hello(req), "protocol": 2})])
        with self.assertRaises(ProtocolError):
            SerialClient(port).handshake()

    def test_correlation_and_events(self):
        event = {"type": "event", "event": "boop", "source": "touch"}
        def respond(req):
            reply = wire({"type": "pong", "request_id": req["request_id"]})
            return [wire({"type": "pong", "request_id": 999}) + wire(event) + reply[:5],
                    reply[5:]]
        events = []
        client = SerialClient(FakeSerial(respond), events.append)
        self.assertEqual(client.request("ping")["request_id"], 1)
        self.assertEqual(events, [event])

    def test_set_mood_and_request_ids(self):
        port = FakeSerial(lambda req: [wire({"type": "ack", "command": req["type"],
                                             "request_id": req["request_id"]})])
        client = SerialClient(port)
        mood = {"id": "sleepy"}
        client.request("set_mood", mood=mood)
        client.request("reset_mood")
        self.assertEqual(port.requests[0]["mood"], mood)
        self.assertEqual([r["request_id"] for r in port.requests], [1, 2])

    def test_device_error(self):
        port = FakeSerial(lambda req: [wire({"type": "error", "code": "storage_error",
                                             "request_id": req["request_id"]})])
        with self.assertRaises(DeviceError) as ctx:
            SerialClient(port).request("set_mood", mood={})
        self.assertEqual(ctx.exception.reply["code"], "storage_error")

    def test_wrong_ack(self):
        port = FakeSerial(lambda req: [wire({"type": "ack", "command": "reset_mood",
                                             "request_id": req["request_id"]})])
        with self.assertRaises(ProtocolError):
            SerialClient(port).request("boop")

    def test_timeout_does_not_replay(self):
        port = FakeSerial()
        with self.assertRaises(RequestTimeout):
            SerialClient(port).request("boop", timeout=0.005)
        self.assertEqual(len(port.requests), 1)

    def test_disconnect(self):
        port = FakeSerial(lambda req: [OSError("unplugged")])
        with self.assertRaises(LinkError):
            SerialClient(port).request("ping")

    def test_poll_event(self):
        port = FakeSerial()
        event = {"type": "event", "event": "storage", "status": "restored"}
        port.chunks.append(wire(event))
        events = []
        SerialClient(port, events.append).poll(timeout=0.005)
        self.assertEqual(events, [event])

    def test_partial_write(self):
        port = FakeSerial()
        port.write = lambda data: len(data) - 1
        with self.assertRaises(LinkError):
            SerialClient(port).request("ping")


class WatchTests(unittest.TestCase):
    def test_reconnect_after_disconnect(self):
        first = Mock()
        first.poll.side_effect = LinkError("unplugged")
        second = Mock()
        stopped = False
        def stop_after_poll(**kwargs):
            nonlocal stopped
            stopped = True
        second.poll.side_effect = stop_after_poll
        connector = Mock(side_effect=[first, second])
        sleep = Mock()
        watch(connector=connector, sleep=sleep, should_stop=lambda: stopped)
        self.assertEqual(connector.call_count, 2)
        first.close.assert_called_once()
        second.close.assert_called_once()
        sleep.assert_called_once_with(2.0)

    def test_reconnect_if_initially_missing(self):
        stopped = False
        client = Mock()
        def stop_after_poll(**kwargs):
            nonlocal stopped
            stopped = True
        client.poll.side_effect = stop_after_poll
        connector = Mock(side_effect=[LinkError("missing"), client])
        watch(connector=connector, sleep=lambda _: None, should_stop=lambda: stopped)
        self.assertEqual(connector.call_count, 2)

    def test_heartbeat(self):
        client = Mock()
        stopped = False
        now = 0
        def poll(**kwargs):
            nonlocal now, stopped
            now += 4
            stopped = True
        client.poll.side_effect = poll
        watch(connector=lambda **kw: client, clock=lambda: now,
              should_stop=lambda: stopped)
        client.request.assert_called_once_with("ping")


class CliTests(unittest.TestCase):
    @patch("companion.__main__.connect")
    def test_info(self, connector):
        connector.return_value.request.return_value = {"type": "info"}
        with patch("sys.stdout"):
            self.assertEqual(main(["--port", "COM3", "info"]), 0)
        connector.return_value.request.assert_called_once_with("get_info")
        connector.return_value.close.assert_called_once()

    @patch("companion.__main__.connect")
    def test_device_error_exit_status(self, connector):
        connector.return_value.request.side_effect = DeviceError({"type": "error", "code": "storage_error"})
        with patch("sys.stderr"):
            self.assertEqual(main(["reset-mood"]), 2)
        connector.return_value.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
