"""Atomic local cache of the last validated publication, scoped to an API origin."""
import json
import logging
import os
import tempfile

from .remote import MAX_HTTP_BYTES
from .sync_models import validate_publication

LOG = logging.getLogger(__name__)


class MoodCache:
    def __init__(self, path, url):
        self.path = path
        self.url = url

    def load(self):
        try:
            with self.path.open("rb") as handle:
                raw = handle.read(MAX_HTTP_BYTES + 1)
            if len(raw) > MAX_HTTP_BYTES:
                raise ValueError("Oversized cache")
            data = json.loads(raw)
            if (type(data) is not dict or set(data) != {"schema", "origin", "publication"}
                    or type(data["schema"]) is not int or data["schema"] != 1 or data["origin"] != self.url):
                raise ValueError("Unsupported cache or different API origin")
            return validate_publication(data["publication"])
        except FileNotFoundError:
            return None
        except (OSError, ValueError, RecursionError):
            LOG.warning("Ignoring invalid or unreadable sync cache")
            return None

    def save(self, publication):
        data = {"schema": 1, "origin": self.url, "publication": validate_publication(publication)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as handle:
                temporary = handle.name
                json.dump(data, handle, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            temporary = None
        finally:
            if temporary is not None:
                try:
                    os.unlink(temporary)
                except OSError:
                    LOG.warning("Could not remove temporary cache file")
