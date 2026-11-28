import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.config import Settings
from backend.database import Database
from backend.models import Mood

ADMIN = "a" * 40
DEVICE = "d" * 40
A = {"Authorization": f"Bearer {ADMIN}"}
D = {"Authorization": f"Bearer {DEVICE}"}
BASE = {"id": "sleepy", "background": "#24243D", "eyes": "sleepy",
        "mouth": "none", "blush": False, "accessory": "zzz",
        "message": "Buenas noches", "animation": {"blink_ms": 0,
        "ear_wiggle": False, "accessory_motion": True}}
API = "/api/v1"


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.settings = Settings(Path(self.tmp.name) / "db.sqlite3", ADMIN, DEVICE)
        self.client = TestClient(create_app(self.settings))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def create(self, mood=None):
        response = self.client.post(API + "/moods", json=BASE if mood is None else mood, headers=A)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def activate(self, mood_id="sleepy"):
        response = self.client.put(API + "/active", json={"mood_id": mood_id}, headers=A)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def active(self):
        response = self.client.get(API + "/active", headers=D)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_health(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})

    def test_initial_state(self):
        state = self.active()
        self.assertEqual(state["revision"], 1)
        self.assertEqual(state["mood"]["id"], "idle")
        self.assertEqual(state["mood"]["animation"]["blink_ms"], 4500)
        self.assertEqual(self.client.get(API + "/moods", headers=A).json(), [state["mood"]])

    def test_missing_token(self):
        self.assertEqual(self.client.get(API + "/active").status_code, 401)

    def test_wrong_token(self):
        response = self.client.get(API + "/active", headers={"Authorization": "Bearer wrong"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_wrong_scheme(self):
        self.assertEqual(self.client.get(API + "/active", headers={"Authorization": "Basic abc"}).status_code, 401)

    def test_device_scope(self):
        for method, path, body in [("GET", "/moods", None), ("GET", "/moods/idle", None),
            ("POST", "/moods", BASE), ("PUT", "/moods/sleepy", BASE),
            ("DELETE", "/moods/idle", None), ("PUT", "/active", {"mood_id": "idle"})]:
            with self.subTest(method=method, path=path):
                self.assertEqual(self.client.request(method, API + path, headers=D, json=body).status_code, 403)

    def test_admin_can_read_active(self):
        self.assertEqual(self.client.get(API + "/active", headers=A).json(), self.active())

    def test_create_get_list(self):
        self.assertEqual(self.create(), BASE)
        self.assertEqual(self.client.get(API + "/moods/sleepy", headers=A).json(), BASE)
        self.assertEqual([m["id"] for m in self.client.get(API + "/moods", headers=A).json()], ["idle", "sleepy"])
        self.assertEqual(self.active()["revision"], 1)

    def test_duplicate_id(self):
        self.create()
        self.assertEqual(self.client.post(API + "/moods", headers=A, json=BASE).status_code, 409)

    def test_missing_mood(self):
        for method in ("GET", "PUT", "DELETE"):
            with self.subTest(method=method):
                self.assertEqual(self.client.request(method, API + "/moods/sleepy", headers=A,
                    json=BASE if method == "PUT" else None).status_code, 404)
        self.assertEqual(self.client.put(API + "/active", headers=A, json={"mood_id": "sleepy"}).status_code, 404)

    def test_path_id_mismatch(self):
        self.create()
        self.assertEqual(self.client.put(API + "/moods/sleepy", headers=A, json=dict(BASE, id="other")).status_code, 422)

    def test_legacy_defaults_and_color_normalization(self):
        legacy = dict(BASE, background="#abcdef")
        del legacy["animation"]
        result = self.create(legacy)
        self.assertEqual(result["background"], "#ABCDEF")
        self.assertEqual(result["animation"], {"blink_ms": 4500, "ear_wiggle": True, "accessory_motion": True})

    def test_invalid_appearance(self):
        cases = [("id", "UPPER"), ("id", ""), ("id", "a" * 25), ("id", "abc\n"),
            ("background", "#GG0000"), ("background", "#123"), ("eyes", "laser"),
            ("mouth", "wide"), ("blush", 1), ("blush", "true"), ("accessory", "moon"),
            ("message", "ñ"), ("message", "x" * 25), ("message", "a\n"), ("message", "a\x00")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                self.assertEqual(self.client.post(API + "/moods", headers=A, json=dict(BASE, **{field: value})).status_code, 422)

    def test_missing_and_extra_fields(self):
        for field in ("id", "background", "eyes", "mouth", "blush", "accessory", "message"):
            bad = dict(BASE)
            del bad[field]
            self.assertEqual(self.client.post(API + "/moods", headers=A, json=bad).status_code, 422)
        self.assertEqual(self.client.post(API + "/moods", headers=A, json=dict(BASE, extra=True)).status_code, 422)

    def test_invalid_animation(self):
        anim = BASE["animation"]
        cases = [None, "animated", {}, dict(anim, extra=True), dict(anim, blink_ms=999),
                 dict(anim, blink_ms=15001), dict(anim, blink_ms=-1), dict(anim, blink_ms=1000.0),
                 dict(anim, blink_ms=True), dict(anim, blink_ms="1000"), dict(anim, ear_wiggle=1),
                 dict(anim, accessory_motion="false")]
        for value in cases:
            with self.subTest(value=value):
                self.assertEqual(self.client.post(API + "/moods", headers=A, json=dict(BASE, animation=value)).status_code, 422)

    def test_valid_boundaries_and_wire_size(self):
        for value in (0, 1000, 15000):
            mood = dict(BASE, id="a" * 24, message='\\"' * 12, eyes="excited", mouth="neutral",
                        animation=dict(BASE["animation"], blink_ms=value))
            data = Mood.model_validate(mood).model_dump()
            wire = json.dumps({"type": "set_mood", "request_id": 4294967295, "mood": data},
                              ensure_ascii=True, separators=(",", ":")).encode("ascii")
            self.assertLessEqual(len(wire), 511)

    def test_activation_and_duplicate(self):
        self.create()
        first = self.activate()
        self.assertEqual(first["revision"], 2)
        self.assertEqual(first["mood"], BASE)
        self.assertEqual(self.activate(), first)
        self.assertEqual(self.active(), first)

    def test_edit_does_not_publish(self):
        self.create()
        first = self.activate()
        replacement = dict(BASE, message="Dulces suenos")
        response = self.client.put(API + "/moods/sleepy", headers=A, json=replacement)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.active(), first)
        next_state = self.activate()
        self.assertEqual(next_state["revision"], 3)
        self.assertEqual(next_state["mood"], replacement)

    def test_delete_active_conflict_and_delete_inactive(self):
        self.create()
        self.activate()
        self.assertEqual(self.client.delete(API + "/moods/sleepy", headers=A).status_code, 409)
        self.activate("idle")
        self.assertEqual(self.client.delete(API + "/moods/sleepy", headers=A).status_code, 204)
        self.assertEqual(self.client.get(API + "/moods/sleepy", headers=A).status_code, 404)

    def test_invalid_update_preserves_state(self):
        self.create()
        original = self.activate()
        self.assertEqual(self.client.put(API + "/moods/sleepy", headers=A, json=dict(BASE, eyes="laser")).status_code, 422)
        self.assertEqual(self.active(), original)
        self.assertEqual(self.client.get(API + "/moods/sleepy", headers=A).json(), BASE)

    def test_restart_persists_catalog_and_revision(self):
        self.create()
        original = self.activate()
        with TestClient(create_app(self.settings)) as restarted:
            self.assertEqual(restarted.get(API + "/active", headers=D).json(), original)
            self.assertEqual(restarted.get(API + "/moods/sleepy", headers=A).json(), BASE)

    def test_concurrent_publication(self):
        self.create()
        self.create(dict(BASE, id="other"))
        def activate(mood_id):
            return Database(self.settings.db_path).activate(mood_id).revision
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(activate, ["sleepy", "other"]))
        self.assertEqual(sorted(results), [2, 3])
        self.assertEqual(self.active()["revision"], 3)

    def test_sql_like_message_roundtrip(self):
        mood = dict(BASE, message="'; DROP TABLE moods; --")
        self.assertEqual(self.create(mood), mood)
        self.assertEqual(self.activate()["mood"], mood)

    def test_no_cache(self):
        self.assertEqual(self.client.get(API + "/active", headers=D).headers["cache-control"], "no-store")

    def test_invalid_activation(self):
        for payload in ({}, {"mood_id": "UPPER"}, {"mood_id": "idle", "extra": True}):
            self.assertEqual(self.client.put(API + "/active", headers=A, json=payload).status_code, 422)
        self.assertEqual(self.active()["revision"], 1)

    def test_unsupported_db_schema(self):
        path = Path(self.tmp.name) / "unsupported.sqlite3"
        with closing(sqlite3.connect(path)) as conn:
            conn.execute("PRAGMA user_version = 99")
            conn.commit()
        with self.assertRaisesRegex(RuntimeError, "Unsupported database schema"):
            Database(path).initialize()

    def test_invalid_credentials_config(self):
        for a, d in [("", DEVICE), (ADMIN, "short"), (ADMIN, ADMIN), (ADMIN, "ñ" * 40)]:
            with self.assertRaises(ValueError):
                Settings(self.settings.db_path, a, d)
        self.assertNotIn(ADMIN, repr(self.settings))
        self.assertNotIn(DEVICE, repr(self.settings))


if __name__ == "__main__":
    unittest.main()
