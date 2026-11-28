"""Configuration from environment; no built-in credentials"""
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path
    admin_token: str = field(repr=False)
    device_token: str = field(repr=False)

    def __post_init__(self):
        for name, value in (("admin", self.admin_token), ("device", self.device_token)):
            if not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", value):
                raise ValueError(f"{name} token must be 32–256 URL-safe ASCII characters")
        if self.admin_token == self.device_token:
            raise ValueError("Admin and device tokens must differ")

    @classmethod
    def from_env(cls):
        return cls(
            db_path=Path(os.environ.get("BUDDY_DB_PATH", "data/desk_buddy.sqlite3")),
            admin_token=os.environ.get("BUDDY_ADMIN_TOKEN", ""),
            device_token=os.environ.get("BUDDY_DEVICE_TOKEN", ""),
        )
