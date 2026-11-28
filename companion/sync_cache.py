"""Atomic local cache of the last validated publication, scoped to an API origin."""
import json
import logging
import os
import tempfile

from .remote import MAX_HTTP_BYTES
from .sync_models import validate_publication

LOG = logging.getLogger(__name__)


class MoodCache:
    schema = 1
    max_bytes = MAX_HTTP_BYTES
    validator = staticmethod(validate_publication)

    def __init__(self, path, url):
        self.path = path
        self.url = url

    def decode(self, data):
        if (type(data) is not dict or set(data) != {"schema", "origin", "publication"}
                or type(data["schema"]) is not int or data["schema"] != self.schema or data["origin"] != self.url):
            raise ValueError("Unsupported cache or different API origin")
        return self.validator(data["publication"])

    def load(self):
        try:
            with self.path.open("rb") as handle:
                raw = handle.read(self.max_bytes + 1)
            if len(raw) > self.max_bytes:
                raise ValueError("Oversized cache")
            data = json.loads(raw)
            return self.decode(data)
        except FileNotFoundError:
            return None
        except (OSError, ValueError, RecursionError):
            LOG.warning("Ignoring invalid or unreadable sync cache")
            return None

    def save(self, publication):
        data = {"schema": self.schema, "origin": self.url, "publication": self.validator(publication)}
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


from .artwork import validate_v2

class ArtworkCache(MoodCache):
    schema = 2
    max_bytes = 66 * 1024
    validator = staticmethod(validate_v2)

    def decode(self, data):
        if (type(data) is dict and set(data) == {"schema", "origin", "publication"}
                and type(data["schema"]) is int and data["schema"] == 1 and data["origin"] == self.url):
            return {**validate_publication(data["publication"]), 'artwork': None}
        return super().decode(data)
