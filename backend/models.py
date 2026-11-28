"""Strict models matching MoodModel::parse in firmware protocol v1"""
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class AnimationSettings(StrictModel):
    blink_ms: int
    ear_wiggle: bool
    accessory_motion: bool

    @field_validator("blink_ms")
    @classmethod
    def validate_blink(cls, value):
        if value != 0 and not 1000 <= value <= 15000:
            raise ValueError("blink_ms must be zero or 1000–15000")
        return value


def default_animation():
    return AnimationSettings(blink_ms=4500, ear_wiggle=True, accessory_motion=True)


class Mood(StrictModel):
    id: str = Field(min_length=1, max_length=24)
    background: str = Field(min_length=7, max_length=7)
    eyes: Literal["open", "happy", "sleepy", "excited", "glasses"]
    mouth: Literal["none", "smile", "neutral", "open"]
    blush: bool
    accessory: Literal["none", "heart", "star", "zzz"]
    message: str = Field(max_length=24)
    animation: AnimationSettings = Field(default_factory=default_animation)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value):
        if not re.fullmatch(r"[a-z0-9_-]{1,24}", value):
            raise ValueError("Invalid mood ID")
        return value

    @field_validator("background")
    @classmethod
    def validate_color(cls, value):
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("Expected #RRGGBB")
        return value.upper()

    @field_validator("message")
    @classmethod
    def validate_message(cls, value):
        if not re.fullmatch(r"[\x20-\x7e]{0,24}", value):
            raise ValueError("Expected at most 24 printable ASCII characters")
        return value


class Activation(StrictModel):
    mood_id: str = Field(min_length=1, max_length=24)

    @field_validator("mood_id")
    @classmethod
    def validate_id(cls, value):
        return Mood.validate_id(value)


class ActiveMood(StrictModel):
    revision: int = Field(ge=1)
    mood: Mood
    published_at: str


def default_mood():
    return Mood(id="idle", background="#FFD1DE", eyes="open", mouth="none",
                blush=False, accessory="none", message="Hello Svinka!")
