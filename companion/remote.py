"""Read-only authenticated HTTP transport. No redirects or implicit proxies."""
import json
from http.client import HTTPException
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (HTTPRedirectHandler, ProxyHandler, Request, build_opener)

from .sync_models import validate_publication

MAX_HTTP_BYTES = 8192


class RemoteError(Exception):
    """Remote state unavailable; retain the last known valid publication."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_url(value):
    if not value or any(ord(c) <= 32 or ord(c) == 127 for c in value):
        raise ValueError("Set BUDDY_API_URL to an HTTPS origin or loopback HTTP origin")
    try:
        u = urlsplit(value)
        port = u.port
    except ValueError:
        raise ValueError("Invalid API origin") from None
    if (u.scheme not in ("http", "https") or not u.hostname or u.username is not None
            or u.password is not None or u.path not in ("", "/") or u.query or u.fragment
            or port == 0 or "\\" in value or "?" in value or "#" in value):
        raise ValueError("API URL must be an origin without credentials, path, query or fragment")
    if u.scheme == "http" and u.hostname not in ("127.0.0.1", "::1"):
        raise ValueError("Plain HTTP is allowed only on numeric loopback addresses; use HTTPS otherwise")
    return value.rstrip("/")


@dataclass(frozen=True)
class RemoteSettings:
    url: str
    token: str = field(repr=False)
    cache_path: Path

    @classmethod
    def from_env(cls):
        url = validate_url(os.environ.get("BUDDY_API_URL", ""))
        token = os.environ.get("BUDDY_DEVICE_TOKEN", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", token):
            raise ValueError("Set BUDDY_DEVICE_TOKEN to a valid device credential")
        path = Path(os.environ.get("BUDDY_SYNC_CACHE", "data/sync-cache.json"))
        return cls(url, token, path)


class RemoteClient:
    endpoint = "/api/v1/active"
    max_bytes = MAX_HTTP_BYTES
    validator = staticmethod(validate_publication)

    def __init__(self, settings, *, timeout=3.0, opener=None):
        self.url = validate_url(settings.url)
        self.token = settings.token
        self.timeout = timeout
        self.opener = opener if opener is not None else build_opener(ProxyHandler({}), NoRedirect())

    def fetch(self):
        request = Request(self.url + self.endpoint, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json", "Cache-Control": "no-cache",
        }, method="GET")
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                if response.status != 200 or response.headers.get_content_type() != "application/json":
                    raise RemoteError("Unexpected API response")
                raw = response.read(self.max_bytes + 1)
            if len(raw) > self.max_bytes:
                raise RemoteError("API response exceeds size limit")
            return self.validator(json.loads(raw))
        except HTTPError as exc:
            exc.close()
            raise RemoteError(f"API HTTP {exc.code}") from None
        except (URLError, OSError, HTTPException, ValueError, RecursionError):
            # Do not log request URLs, body or credentials from exceptions.
            raise RemoteError("API connection or validation failed") from None


from .artwork import validate_v2

class ArtworkRemote(RemoteClient):
    endpoint = "/api/v2/active"
    max_bytes = 64 * 1024
    validator = staticmethod(validate_v2)
