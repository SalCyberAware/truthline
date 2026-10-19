"""Metadata analyzer: what the file says about itself.

Reliability note: metadata is easy to strip and easy to forge, so most of these
signals are WEAK or MODERATE. Their value is in combination: a "screenshot" with
no screenshot or device metadata, last written by an image editor, is a pattern
investigators recognize. Absence of metadata on its own is NEUTRAL, because
social platforms strip it from real files too.
"""

from __future__ import annotations

import time

from PIL import ExifTags, Image

from ..contract import (
    AnalyzerResult,
    Direction,
    MediaType,
    Signal,
    Strength,
    Submission,
)

EDITOR_HINTS = ("photoshop", "gimp", "canva", "pixlr", "lightroom", "affinity", "paint.net", "picsart")
SCREENSHOT_HINTS = ("screenshot", "screen shot", "screencapture")


class MetadataAnalyzer:
    name = "metadata"
    media_types = frozenset({MediaType.IMAGE})

    def analyze(self, submission: Submission) -> AnalyzerResult:
        t0 = time.perf_counter()
        if submission.media_type != MediaType.IMAGE:
            return AnalyzerResult(self.name, available=False, note="image files only")

        signals: list[Signal] = []
        details: dict = {}
        try:
            with Image.open(submission.path) as im:
                details["format"] = im.format
                details["size"] = list(im.size)
                details["mode"] = im.mode
                info = dict(im.info)
                exif = {}
                raw_exif = im.getexif()
                for tag_id, value in raw_exif.items():
                    tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                    if isinstance(value, bytes):
                        value = value[:64].hex()
                    exif[tag] = str(value)[:200]
                details["exif"] = exif
                # PNG text chunks and XMP often carry software / creator hints
                text_chunks = {k: str(v)[:200] for k, v in info.items() if isinstance(v, (str, bytes)) and k not in ("exif", "icc_profile")}
                details["text_chunks"] = text_chunks
        except Exception as exc:  # unreadable image
            return AnalyzerResult(self.name, available=False, note=f"could not read image: {exc}")

        software_name = exif.get("Software") or text_chunks.get("Software") or ""
        software = (software_name + " " + " ".join(text_chunks.values())).lower()
        has_camera = any(k in exif for k in ("Make", "Model", "LensModel"))
        has_datetime = any(k in exif for k in ("DateTimeOriginal", "DateTime"))

        if any(h in software for h in EDITOR_HINTS):
            signals.append(Signal(
                analyzer=self.name, key="metadata.editor_software",
                direction=Direction.FABRICATED, strength=Strength.MODERATE,
                summary=f"The file was last saved by an image editor ({software_name or 'editor tag found'}).",
                why_it_matters="Real screenshots and camera photos are not normally saved from an editor; this means the image was opened and re-saved, which is how edits are made.",
                details={"software": software_name, "hints": [h for h in EDITOR_HINTS if h in software]},
            ))

        # Only the Software tag counts here. Free-text chunks (Comment, Description) are
        # too easy to plant: a word like "screenshot" in a comment proves nothing.
        if any(h in software_name.lower() for h in SCREENSHOT_HINTS):
            signals.append(Signal(
                analyzer=self.name, key="metadata.screenshot_tag",
                direction=Direction.AUTHENTIC, strength=Strength.WEAK,
                summary="The file's Software tag names a screenshot tool.",
                why_it_matters="Weak evidence it was captured as a screenshot on a device, though such tags can be copied.",
                details={"software": software_name},
            ))

        if has_camera:
            signals.append(Signal(
                analyzer=self.name, key="metadata.camera_present",
                direction=Direction.AUTHENTIC, strength=Strength.WEAK,
                summary=f"Camera metadata is present ({exif.get('Make', '')} {exif.get('Model', '')}).".replace("  ", " "),
                why_it_matters="Consistent with a photo taken on a device, but camera tags can be forged or copied from another file.",
                details={"make": exif.get("Make", ""), "model": exif.get("Model", "")},
            ))

        if not exif and not text_chunks:
            signals.append(Signal(
                analyzer=self.name, key="metadata.none",
                direction=Direction.NEUTRAL, strength=Strength.WEAK,
                summary="The file has no metadata at all.",
                why_it_matters="Proves nothing by itself: messaging apps and social platforms strip metadata from real files too. Ask the submitter for the original from the device it was captured on.",
                details={},
            ))

        if not has_datetime and submission.claimed_type and "screenshot" not in submission.claimed_type.lower():
            signals.append(Signal(
                analyzer=self.name, key="metadata.no_timestamp",
                direction=Direction.NEUTRAL, strength=Strength.WEAK,
                summary="No capture timestamp in the file.",
                why_it_matters="A timestamp would let you compare the file's own clock to the time shown in the image; without it, request the original.",
                details={},
            ))

        return AnalyzerResult(
            self.name, available=True, signals=signals,
            note="Metadata is easy to strip or forge; treat these as supporting signals.",
            duration_ms=int((time.perf_counter() - t0) * 1000),
        )
