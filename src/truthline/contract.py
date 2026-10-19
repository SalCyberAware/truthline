"""The analyzer contract.

This file is the whole interface between the Truthline core and any analyzer.
It is deliberately small so that a university lab, a vendor or a volunteer can
write an analyzer without reading the rest of the project.

An analyzer receives a Submission and returns a list of Signals. It never
returns a verdict. The assessment engine (assessment.py) combines signals into
a Grade using public rules.

This file is offered under Apache-2.0 in addition to the project's AGPL-3.0,
so that it can be embedded freely.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable


class MediaType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class Direction(str, Enum):
    """Which way a signal points."""

    AUTHENTIC = "authentic"      # evidence the file is what it claims to be
    FABRICATED = "fabricated"    # evidence of alteration or fabrication (any method)
    AI_GENERATED = "ai_generated"  # evidence of synthetic generation specifically
    NEUTRAL = "neutral"          # informative, points nowhere on its own


class Strength(str, Enum):
    """How much weight a signal carries on its own.

    STRONG: on its own, enough to change the grade (e.g. a valid C2PA manifest
            naming an AI generator; a status bar that matches no shipped OS).
    MODERATE: meaningful but needs company (e.g. file last written by an editor).
    WEAK: suggestive only (e.g. error-level analysis hot spots).
    """

    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


@dataclass(frozen=True)
class Submission:
    """What the user handed us, plus what they said it was."""

    path: Path
    claimed_type: str = ""        # free text: "a screenshot of a text message"
    context: str = ""             # free text: who sent it, when, why it matters
    sha256: str = field(default="", compare=False)
    media_type: MediaType = MediaType.UNKNOWN
    size_bytes: int = 0

    @classmethod
    def from_path(cls, path: str | Path, claimed_type: str = "", context: str = "") -> Submission:
        p = Path(path)
        data = p.read_bytes()
        return cls(
            path=p,
            claimed_type=claimed_type,
            context=context,
            sha256=hashlib.sha256(data).hexdigest(),
            media_type=guess_media_type(p),
            size_bytes=len(data),
        )


@dataclass(frozen=True)
class Signal:
    """One finding from one analyzer.

    Every field is shown to the user. Write `summary` and `why_it_matters`
    for a school secretary, not for a forensic examiner.
    """

    analyzer: str                 # e.g. "metadata", "c2pa"
    key: str                      # stable machine key, e.g. "c2pa.manifest_valid"
    direction: Direction
    strength: Strength
    summary: str                  # one sentence: what was found
    why_it_matters: str           # one sentence: what that means
    details: dict = field(default_factory=dict)  # raw evidence for the case file


@dataclass
class AnalyzerResult:
    """What an analyzer returns. `available=False` means the analyzer could not
    run (missing dependency, unsupported media); the pipeline reports that
    honestly instead of silently lowering confidence."""

    analyzer: str
    available: bool
    signals: list[Signal] = field(default_factory=list)
    note: str = ""                # why unavailable, or a caveat
    duration_ms: int = 0


@runtime_checkable
class Analyzer(Protocol):
    """Implement this and register it in truthline.analyzers.REGISTRY."""

    name: str
    media_types: frozenset[MediaType]

    def analyze(self, submission: Submission) -> AnalyzerResult: ...


IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".heic", ".gif", ".bmp", ".tif", ".tiff"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".opus"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
DOC_EXT = {".pdf", ".docx", ".doc", ".txt", ".rtf"}


def guess_media_type(path: Path) -> MediaType:
    ext = path.suffix.lower()
    if ext in IMAGE_EXT:
        return MediaType.IMAGE
    if ext in AUDIO_EXT:
        return MediaType.AUDIO
    if ext in VIDEO_EXT:
        return MediaType.VIDEO
    if ext in DOC_EXT:
        return MediaType.DOCUMENT
    return MediaType.UNKNOWN
