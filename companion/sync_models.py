"""Validate the v1 publication contract without server-side dependencies."""
import re
from datetime import datetime

from .protocol import encode_request


def normalize_mood(value):
    required = {"id", "background", "eyes", "mouth", "blush", "accessory", "message"}
    if type(value) is not dict or not required <= value.keys() or value.keys() - required - {"animation"}:
        raise ValueError("Invalid mood fields")
    for field, pattern in (("id", r"[a-z0-9_-]{1,24}"), ("background", r"#[0-9a-fA-F]{6}"), ("message", r"[\x20-\x7e]{0,24}")):
        if type(value[field]) is not str or not re.fullmatch(pattern, value[field]):
            raise ValueError(f"Invalid mood {field}")
    for field, options in (("eyes", ("open", "happy", "sleepy", "excited", "glasses")), ("mouth", ("none", "smile", "neutral", "open")), ("accessory", ("none", "heart", "star", "zzz"))):
        if type(value[field]) is not str or value[field] not in options:
            raise ValueError(f"Invalid mood {field}")
    if type(value["blush"]) is not bool:
        raise ValueError("Invalid mood blush")
    anim = value.get("animation", {"blink_ms": 4500, "ear_wiggle": True, "accessory_motion": True})
    if type(anim) is not dict or set(anim) != {"blink_ms", "ear_wiggle", "accessory_motion"}:
        raise ValueError("Invalid animation fields")
    blink = anim["blink_ms"]
    if type(blink) is not int or (blink != 0 and not 1000 <= blink <= 15000):
        raise ValueError("Invalid blink_ms")
    if any(type(anim[k]) is not bool for k in ("ear_wiggle", "accessory_motion")):
        raise ValueError("Invalid animation boolean")
    mood = {**value, "background": value["background"].upper(), "animation": dict(anim)}
    encode_request({"type": "set_mood", "request_id": 0xFFFFFFFF, "mood": mood})
    return mood


def validate_publication(value):
    if type(value) is not dict or set(value) != {"revision", "mood", "published_at"}:
        raise ValueError("Invalid publication fields")
    rev, stamp = value["revision"], value["published_at"]
    if type(rev) is not int or not 1 <= rev <= 0x7FFFFFFFFFFFFFFF:
        raise ValueError("Invalid revision")
    if type(stamp) is not str or len(stamp) > 64:
        raise ValueError("Invalid publication timestamp")
    try:
        parsed = datetime.fromisoformat(stamp)
        if parsed.utcoffset() is None:
            raise ValueError
    except (ValueError, OverflowError):
        raise ValueError("Invalid publication timestamp") from None
    return {"revision": rev, "mood": normalize_mood(value["mood"]), "published_at": stamp}
