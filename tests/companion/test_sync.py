import copy
import json
import os
from pathlib import Path
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from unittest.mock import Mock, patch

from companion.__main__ import main
from companion.protocol import RequestTimeout, LinkError
from companion.remote import RemoteClient, RemoteSettings, RemoteError, validate_url
from companion.sync import Synchronizer
from companion.sync_cache import MoodCache
from companion.sync_models import normalize_mood, validate_publication

URL = "http://127.0.0.1:8000"
TOKEN = "a" * 43


def mood(message="Hello Svinka!"):
    return {"id": "idle", "background": "#FFD1DE", "eyes": "open", "mouth": "none", "blush": False,
            "accessory": "none", "message": message,
            "animation": {"blink_ms": 4500, "ear_wiggle": True, "accessory_motion": True}}


def publication(revision=1, message="Hello Svinka!"):
    return {"revision": revision, "mood": mood(message), "published_at": "2026-11-28T00:00:00+00:00"}


class ModelTests(unittest.TestCase):
    def test_normalization_and_legacy_defaults(self):
        m = mood(); m.pop("animation"); m["background"] = "#ffd1de"
        self.assertEqual(normalize_mood(m), mood())

    def test_invalid_mood_fields(self):
        for key, value in [("id", "BAD"), ("eyes", "bogus"), ("mouth", []), ("accessory", {}),
                           ("blush", 1), ("background", "pink"), ("message", "ñ"),
                           ("message", "x" * 25), ("extra", 1), ("animation", None)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                normalize_mood({**mood(), key: value})

    def test_invalid_animations(self):
        for change in ({"blink_ms": True}, {"blink_ms": 500}, {"blink_ms": 15001}, {"ear_wiggle": 1}, {"extra": 1}):
            m = mood(); m["animation"].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                normalize_mood(m)

    def test_invalid_publications(self):
        for change in ({"revision": True}, {"revision": 0}, {"revision": 1.0}, {"published_at": "bad"},
                       {"published_at": "2026-11-28T00:00:00"}, {"extra": 1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_publication({**publication(), **change})

    def test_maximum_escaped_mood(self):
        m = mood('\\"' * 12); m["id"] = "x" * 24
        self.assertEqual(normalize_mood(m), m)


class ConfigTests(unittest.TestCase):
    def test_reject_insecure_or_ambiguous_origins(self):
        for url in ("http://example.org", "http://localhost:8000", "https://u:p@example.org", "https://example.org/path", "https://example.org?x=y", "https://example.org#", "https://example.org:0", "https://example.org/\n"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_url(url)
        self.assertEqual(validate_url(URL + "/"), URL)
        self.assertEqual(validate_url("https://example.org"), "https://example.org")

    def test_env_and_secret_repr(self):
        with patch.dict(os.environ, {"BUDDY_API_URL": URL, "BUDDY_DEVICE_TOKEN": TOKEN}, clear=True):
            settings = RemoteSettings.from_env()
            self.assertNotIn(TOKEN, repr(settings))
        with patch.dict(os.environ, {"BUDDY_API_URL": URL}, clear=True), self.assertRaises(ValueError):
            RemoteSettings.from_env()

    def test_cli_sync_dispatch(self):
        with patch.dict(os.environ, {"BUDDY_API_URL": URL, "BUDDY_DEVICE_TOKEN": TOKEN}, clear=True), patch("companion.__main__.run_sync") as run:
            self.assertEqual(main(["--port", "COM4", "sync"]), 0)
            self.assertEqual(run.call_args.kwargs["explicit"], "COM4")


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.status, self.body, self.kind = 200, json.dumps(publication()).encode(), "application/json"
        outer = self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                outer.requests.append((self.path, self.headers.get("Authorization")))
                self.send_response(outer.status)
                self.send_header("Content-Type", outer.kind)
                if outer.status == 302:
                    self.send_header("Location", "/redirected")
                self.send_header("Content-Length", str(len(outer.body)))
                self.end_headers()
                self.wfile.write(outer.body)
            def log_message(self, *args):
                pass
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.thread.join, 3)
        self.addCleanup(self.server.shutdown)
        self.client = RemoteClient(RemoteSettings(f"http://127.0.0.1:{self.server.server_port}", TOKEN, Path("unused")))

    def test_actual_http_and_bearer(self):
        self.assertEqual(self.client.fetch(), publication())
        self.assertEqual(self.requests, [("/api/v1/active", "Bearer " + TOKEN)])

    def test_redirect_is_not_followed(self):
        self.status = 302
        with self.assertRaises(RemoteError):
            self.client.fetch()
        self.assertEqual(len(self.requests), 1)

    def test_http_errors(self):
        for status in (401, 403, 503):
            self.status = status
            with self.subTest(status=status), self.assertRaisesRegex(RemoteError, str(status)):
                self.client.fetch()

    def test_invalid_or_oversized_body(self):
        for body in (b"not json", b"x" * 8193, b'{"revision":true}'):
            self.body = body
            with self.subTest(length=len(body)), self.assertRaises(RemoteError):
                self.client.fetch()

    def test_unexpected_content_type(self):
        self.kind = "text/html"
        with self.assertRaises(RemoteError):
            self.client.fetch()


class CacheTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "nested" / "cache.json"
        self.cache = MoodCache(self.path, URL)

    def test_round_trip_and_origin_isolation(self):
        self.assertIsNone(self.cache.load())
        self.cache.save(publication())
        self.assertEqual(self.cache.load(), publication())
        self.assertNotIn(TOKEN, self.path.read_text())
        self.assertIsNone(MoodCache(self.path, "https://other.example").load())

    def test_corrupt_cache(self):
        self.cache.save(publication()); self.path.write_text("broken")
        self.assertIsNone(self.cache.load())

    def test_failed_replace_preserves_previous_cache(self):
        self.cache.save(publication())
        with patch("companion.sync_cache.os.replace", side_effect=OSError), self.assertRaises(OSError):
            self.cache.save(publication(2, "new"))
        self.assertEqual(self.cache.load(), publication())
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])


class Device:
    def __init__(self, initial=None):
        self.mood = initial or mood(); self.requests = []; self.fail_write = False
        self.fail_poll = False; self.closed = False; self.ignore_write = False

    def request(self, command, **payload):
        self.requests.append(command)
        if command == "get_mood":
            return {"type": "mood", "mood": copy.deepcopy(self.mood)}
        if command == "set_mood":
            if not self.ignore_write:
                self.mood = copy.deepcopy(payload["mood"])
            if self.fail_write:
                self.fail_write = False
                raise RequestTimeout("lost ack")
            return {"type": "ack", "command": command}
        return {"type": "pong"}

    def poll(self, **kwargs):
        if self.fail_poll:
            raise LinkError("USB gone")

    def close(self):
        self.closed = True


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.remote = Mock(); self.remote.fetch.return_value = publication(2, "new")
        self.cache = Mock(); self.cache.load.return_value = None
        self.device = Device(); self.connect = Mock(return_value=self.device)
        self.sync = Synchronizer(self.remote, self.cache, connector=self.connect, clock=lambda: self.now)

    def advance(self, seconds):
        self.now += seconds; self.sync.step()

    def test_initial_delivery_and_readback(self):
        self.sync.step()
        self.assertEqual(self.device.requests, ["get_mood", "set_mood", "get_mood"])
        self.assertEqual(self.device.mood, publication(2, "new")["mood"])
        self.cache.save.assert_called_once()

    def test_unchanged_no_duplicate_writes_or_cache(self):
        self.sync.step(); self.advance(5); self.advance(15)
        self.assertEqual(self.device.requests.count("set_mood"), 1)
        self.cache.save.assert_called_once()

    def test_same_revision_different_content(self):
        self.sync.step(); self.remote.fetch.return_value = publication(2, "other")
        self.advance(5)
        self.assertEqual(self.device.mood["message"], "other")

    def test_server_reset_lower_revision(self):
        self.sync.step(); self.remote.fetch.return_value = publication(1)
        self.advance(5)
        self.assertEqual(self.device.mood, mood())

    def test_offline_without_cache_leaves_device_untouched(self):
        self.remote.fetch.side_effect = RemoteError("offline")
        self.sync.step(); self.advance(3)
        self.assertEqual(self.device.requests, ["ping"])

    def test_cached_startup_offline(self):
        self.sync.desired = self.sync.cached = publication(4, "cached")
        self.remote.fetch.side_effect = RemoteError("offline")
        self.sync.step()
        self.assertEqual(self.device.mood["message"], "cached")
        self.cache.save.assert_not_called()

    def test_server_backoff_and_recovery(self):
        self.remote.fetch.side_effect = [RemoteError("offline"), RemoteError("offline"), publication(3, "back")]
        self.sync.step(); self.advance(4)
        self.assertEqual(self.remote.fetch.call_count, 1)
        self.advance(1); self.advance(9)
        self.assertEqual(self.remote.fetch.call_count, 2)
        self.advance(1)
        self.assertEqual(self.device.mood["message"], "back")
        self.assertEqual(self.sync.http_delay, 5)

    def test_usb_unplug_polls_and_caches_latest(self):
        self.connect.side_effect = LinkError("missing")
        self.sync.step(); self.remote.fetch.return_value = publication(3, "latest")
        self.advance(5)
        self.cache.save.assert_called_with(publication(3, "latest"))
        self.connect.side_effect = None
        self.advance(2)
        self.assertEqual(self.device.mood["message"], "latest")

    def test_ack_loss_reconciles_before_retry(self):
        self.device.fail_write = True
        self.sync.step(); self.assertTrue(self.device.closed)
        self.advance(2)
        self.assertEqual(self.device.requests.count("set_mood"), 1)
        self.assertEqual(self.device.requests[-1], "get_mood")

    def test_mismatching_readback_reconnects(self):
        self.device.ignore_write = True
        self.sync.step(); self.assertIsNone(self.sync.client)
        self.device.ignore_write = False; self.advance(2)
        self.assertEqual(self.device.mood["message"], "new")

    def test_ready_and_periodic_reconciliation(self):
        self.sync.step(); self.device.mood = mood(); self.sync.event({"type": "ready"})
        self.advance(1); self.assertEqual(self.device.mood["message"], "new")
        self.device.mood = mood(); self.advance(15)
        self.assertEqual(self.device.mood["message"], "new")

    def test_cache_failure_does_not_block_delivery_and_retries(self):
        self.cache.save.side_effect = OSError("disk")
        self.sync.step(); self.assertEqual(self.device.mood["message"], "new")
        self.cache.save.side_effect = None; self.advance(5)
        self.assertEqual(self.cache.save.call_count, 2)

    def test_disconnect_closes_and_reconnects(self):
        self.sync.step(); self.device.fail_poll = True; self.advance(1)
        self.assertTrue(self.device.closed); self.assertIsNone(self.sync.client)
        self.device.fail_poll = False; self.advance(2)
        self.assertEqual(self.connect.call_count, 2)

    def test_interrupt_closes_port(self):
        self.sync.step()
        self.sync.sleep = Mock(side_effect=KeyboardInterrupt)
        with self.assertRaises(KeyboardInterrupt):
            self.sync.run()
        self.assertTrue(self.device.closed)


if __name__ == "__main__":
    unittest.main()
