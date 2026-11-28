"""Real PR-07 HTTP API -> PR-08 synchronization -> PR-06 serial client.

The physical ESP32 is replaced by an in-memory serial transport.
"""
import json
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest

import httpx
import uvicorn

from backend.app import create_app
from backend.config import Settings
from backend.models import default_mood
from companion.remote import RemoteClient, RemoteSettings
from companion.serial_client import SerialClient
from companion.sync import Synchronizer
from companion.sync_cache import MoodCache


class SimulatedPort:
    def __init__(self):
        self.mood = default_mood().model_dump()
        self.pending = bytearray()
        self.writes = 0
        self.closed = False

    def write(self, data):
        req = json.loads(data)
        kind = req["type"]
        if kind == "hello":
            reply = {"type": "hello", "device": "svinka", "protocol": 1, "firmware": "0.5.1"}
        elif kind == "get_mood":
            reply = {"type": "mood", "mood": self.mood}
        elif kind == "set_mood":
            self.writes += 1
            self.mood = req["mood"]
            reply = {"type": "ack", "command": "set_mood"}
        elif kind == "ping":
            reply = {"type": "pong"}
        else:
            raise AssertionError(kind)
        reply["request_id"] = req["request_id"]
        self.pending.extend(json.dumps(reply).encode() + b"\n")
        return len(data)

    def read(self, size):
        if not self.pending:
            time.sleep(0.002)
        result = bytes(self.pending[:size]); del self.pending[:size]
        return result

    def close(self):
        self.closed = True


class EndToEndTests(unittest.TestCase):
    def test_publish_and_sync_over_live_http(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            admin, device = "a" * 43, "b" * 43
            app = create_app(Settings(root / "db.sqlite3", admin, device))
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", 0))
                url = f"http://127.0.0.1:{sock.getsockname()[1]}"
                server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="on", ws="none"))
                worker = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
                worker.start()
                try:
                    deadline = time.monotonic() + 10
                    while not server.started and worker.is_alive() and time.monotonic() < deadline:
                        time.sleep(0.02)
                    self.assertTrue(server.started, "Uvicorn did not start")
                    remote = RemoteClient(RemoteSettings(url, device, root / "cache.json"))
                    cache = MoodCache(root / "cache.json", url)
                    port = SimulatedPort()
                    def connector(**kwargs):
                        client = SerialClient(port, kwargs["on_event"])
                        client.handshake()
                        return client
                    now = [0.0]
                    sync = Synchronizer(remote, cache, connector=connector, clock=lambda: now[0])
                    try:
                        sync.step()
                        self.assertEqual(port.writes, 0)
                        new = {**default_mood().model_dump(), "id": "remote_test", "message": "Te quiero!"}
                        with httpx.Client(base_url=url, headers={"Authorization": "Bearer " + admin}, trust_env=False, timeout=5) as api:
                            self.assertEqual(api.post("/api/v1/moods", json=new).status_code, 201)
                            self.assertEqual(api.put("/api/v1/active", json={"mood_id": "remote_test"}).json()["revision"], 2)
                        now[0] += 5; sync.step()
                        self.assertEqual(port.mood, new)
                        self.assertEqual(cache.load()["revision"], 2)
                        now[0] += 15; sync.step()
                        self.assertEqual(port.writes, 1)
                    finally:
                        sync.close()
                    self.assertTrue(port.closed)
                finally:
                    server.should_exit = True
                    worker.join(10)
                    self.assertFalse(worker.is_alive(), "Uvicorn did not stop")


if __name__ == "__main__":
    unittest.main()
