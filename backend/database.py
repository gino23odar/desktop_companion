"""SQLite catalog and transactional publication of immutable snapshots."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .models import ActiveMood, Mood, default_mood

SCHEMA_VERSION = 2


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


def canonical(mood: Mood) -> str:
    return json.dumps(mood.model_dump(), ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Database:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connection(self, *, write=False):
        conn = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            if write:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            if write:
                conn.commit()
        except BaseException:
            if write:
                conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection(write=True) as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version == SCHEMA_VERSION:
                # Fail rather than silently reseed an inconsistent database.
                self._read_active(conn)
                return
            if version == 1:
                self._migrate_artwork(conn)
                self._read_active(conn)
                return
            if version != 0:
                raise RuntimeError(f"Unsupported database schema: {version}")
            conn.execute("""CREATE TABLE moods (
                id TEXT PRIMARY KEY NOT NULL,
                definition TEXT NOT NULL
            )""")
            conn.execute("""CREATE TABLE active_state (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                revision INTEGER NOT NULL CHECK (revision >= 1),
                definition TEXT NOT NULL,
                published_at TEXT NOT NULL
            )""")
            mood = default_mood()
            definition = canonical(mood)
            conn.execute("INSERT INTO moods VALUES (?, ?)", (mood.id, definition))
            conn.execute("INSERT INTO active_state VALUES (1, 1, ?, ?)",
                         (definition, utc_now()))
            self._migrate_artwork(conn)

    @staticmethod
    def _migrate_artwork(conn):
        conn.execute("CREATE TABLE artworks (id TEXT PRIMARY KEY NOT NULL, pack TEXT NOT NULL)")
        conn.execute("ALTER TABLE active_state ADD COLUMN artwork_id TEXT")
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    @staticmethod
    def _read_active(conn):
        row = conn.execute("SELECT revision, definition, published_at FROM active_state WHERE singleton = 1").fetchone()
        if row is None:
            raise RuntimeError("Missing active state")
        return ActiveMood(revision=row["revision"],
                          mood=Mood.model_validate_json(row["definition"]),
                          published_at=row["published_at"])

    def active(self):
        with self.connection() as conn:
            return self._read_active(conn)

    def list_moods(self):
        with self.connection() as conn:
            rows = conn.execute("SELECT definition FROM moods ORDER BY id").fetchall()
            return [Mood.model_validate_json(row["definition"]) for row in rows]

    @staticmethod
    def _get(conn, mood_id):
        row = conn.execute("SELECT definition FROM moods WHERE id = ?", (mood_id,)).fetchone()
        if row is None:
            raise NotFound("Mood not found")
        return Mood.model_validate_json(row["definition"])

    def get(self, mood_id):
        with self.connection() as conn:
            return self._get(conn, mood_id)

    def create(self, mood):
        with self.connection(write=True) as conn:
            if conn.execute("SELECT 1 FROM moods WHERE id = ?", (mood.id,)).fetchone():
                raise Conflict("Mood ID already exists")
            conn.execute("INSERT INTO moods VALUES (?, ?)", (mood.id, canonical(mood)))
        return mood

    def replace(self, mood_id, mood):
        with self.connection(write=True) as conn:
            self._get(conn, mood_id)
            conn.execute("UPDATE moods SET definition = ? WHERE id = ?", (canonical(mood), mood_id))
        return mood

    def delete(self, mood_id):
        with self.connection(write=True) as conn:
            self._get(conn, mood_id)
            if self._read_active(conn).mood.id == mood_id:
                raise Conflict("Cannot delete the published mood; activate another mood first")
            conn.execute("DELETE FROM moods WHERE id = ?", (mood_id,))

    def activate(self, mood_id):
        # Serialize concurrent writers so two distinct publications cannot
        # read the same old revision and overwrite each other's increment.
        with self.connection(write=True) as conn:
            mood = self._get(conn, mood_id)
            active = self._read_active(conn)
            if canonical(mood) == canonical(active.mood) and self._artwork_id(conn) is None:
                return active
            conn.execute("UPDATE active_state SET revision = revision + 1, definition = ?, published_at = ?, artwork_id = NULL WHERE singleton = 1",
                         (canonical(mood), utc_now()))
            return self._read_active(conn)

    @staticmethod
    def _artwork_id(conn):
        return conn.execute("SELECT artwork_id FROM active_state WHERE singleton = 1").fetchone()[0]

    @staticmethod
    def _artwork(conn, artwork_id):
        row = conn.execute("SELECT id, pack FROM artworks WHERE id = ?", (artwork_id,)).fetchone()
        if row is None:
            raise NotFound("Artwork not found")
        return dict(row)

    def list_artworks(self):
        with self.connection() as conn:
            return [row[0] for row in conn.execute("SELECT id FROM artworks ORDER BY id")]

    def get_artwork(self, artwork_id):
        with self.connection() as conn:
            return self._artwork(conn, artwork_id)

    def create_artwork(self, artwork):
        with self.connection(write=True) as conn:
            if conn.execute("SELECT 1 FROM artworks WHERE id = ?", (artwork['id'],)).fetchone():
                raise Conflict("Artwork ID already exists; use a new ID for revisions")
            if conn.execute("SELECT count(*) FROM artworks").fetchone()[0] >= 128:
                raise Conflict("Artwork catalog full (128 packs)")
            conn.execute("INSERT INTO artworks VALUES (?, ?)", (artwork['id'], artwork['pack']))
        return artwork

    def delete_artwork(self, artwork_id):
        with self.connection(write=True) as conn:
            self._artwork(conn, artwork_id)
            if self._artwork_id(conn) == artwork_id:
                raise Conflict("Cannot delete published artwork")
            conn.execute("DELETE FROM artworks WHERE id = ?", (artwork_id,))

    def _active_v2(self, conn):
        # Single SELECT gives one consistent snapshot even with concurrent publishers.
        row = conn.execute("""SELECT a.revision, a.definition, a.published_at,
                             a.artwork_id, p.pack FROM active_state a
                             LEFT JOIN artworks p ON p.id = a.artwork_id
                             WHERE a.singleton = 1""").fetchone()
        if row is None or (row['artwork_id'] is not None and row['pack'] is None):
            raise RuntimeError("Invalid active artwork state")
        return {'revision': row['revision'], 'mood': Mood.model_validate_json(row['definition']).model_dump(),
                'published_at': row['published_at'], 'artwork': None if row['artwork_id'] is None
                else {'id': row['artwork_id'], 'pack': row['pack']}}

    def active_v2(self):
        with self.connection() as conn:
            return self._active_v2(conn)

    def activate_artwork(self, artwork_id):
        with self.connection(write=True) as conn:
            self._artwork(conn, artwork_id)
            if self._artwork_id(conn) != artwork_id:
                conn.execute("UPDATE active_state SET revision = revision + 1, artwork_id = ?, published_at = ? WHERE singleton = 1",
                             (artwork_id, utc_now()))
            return self._active_v2(conn)
