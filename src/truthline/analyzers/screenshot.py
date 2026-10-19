"""Chat-screenshot forensics analyzer (v0.1, first pass).

This is the analyzer no public tool offers, and the one the school case needs.
This first version runs three simple, explainable checks that need no template
library and no machine learning:

1. Dimensions: does the image match a real phone screen size?
2. Status bar: is there a hard color seam in the status-bar area, and does a
   full-size capture show any clock or battery icons at all?
3. Bubble alignment: do the outgoing message bubbles line up on the same
   right edge, as real chat apps draw them?

Honesty rules for this file
---------------------------
* Every signal here is WEAK. Fake-text generators output phone-sized images and
  can draw tidy bubbles, so none of these checks can prove a screenshot real,
  and none can prove it fake. Under assessment rule R7 weak signals never decide
  a grade; they are shown to the human reviewer as context.
* This analyzer therefore never emits an AUTHENTIC signal.
* The strong signals (status bar geometry per OS version, bubble corner radius
  and font metrics per app version, clock vs. file timestamp) need a maintained
  template library. That is the next milestone; see docs/roadmap in the README.

Pure Pillow, no extra dependencies.
"""

from __future__ import annotations

import time

from PIL import Image

from ..contract import (
    AnalyzerResult,
    Direction,
    MediaType,
    Signal,
    Strength,
    Submission,
)

COMMON_SCREEN_SIZES = {
    # width x height in pixels for common portrait phone captures
    (1170, 2532), (1179, 2556), (1290, 2796), (1080, 2400), (1080, 2340), (1440, 3120),
    (1125, 2436), (750, 1334), (1284, 2778), (1206, 2622), (1320, 2868),
}

WORK_WIDTH = 400            # analysis is done on a copy scaled to this width
SEAM_DISTANCE = 60          # RGB distance between neighbouring uniform rows that counts as a hard seam
SATURATED = 90              # max(R,G,B) - min(R,G,B) at or above this counts as "colored bubble" pixel
ALIGN_TOLERANCE = 0.03      # outgoing bubble right edges may differ by this fraction of width (tails, rounding)
MIN_BUBBLES = 3             # need at least this many outgoing bubbles to judge alignment


def _is_screenshot_claim(submission: Submission) -> bool:
    text = f"{submission.claimed_type} {submission.context}".lower()
    return any(w in text for w in ("screenshot", "screen shot", "screen capture", "text message", "chat", "dm ", "imessage"))


def _prepare(path) -> tuple[Image.Image, tuple[int, int]]:
    with Image.open(path) as im:
        original = im.size
        rgb = im.convert("RGB")
    w, h = rgb.size
    if w > WORK_WIDTH:
        rgb = rgb.resize((WORK_WIDTH, max(1, round(h * WORK_WIDTH / w))), Image.BILINEAR)
    return rgb, original


def _median_color(px, y: int, w: int) -> tuple[int, int, int]:
    row = [px[x, y] for x in range(w)]
    return tuple(sorted(c[i] for c in row)[w // 2] for i in range(3))  # type: ignore[return-value]


def _row_uniformity(px, y: int, w: int, med, tol: int = 12) -> float:
    near = sum(1 for x in range(w) if max(abs(px[x, y][i] - med[i]) for i in range(3)) <= tol)
    return near / w


def _distance(a, b) -> float:
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


def find_status_bar_seam(im: Image.Image) -> tuple[int, float] | None:
    """Largest hard color jump between two uniform rows in the top 8% of the image."""
    w, h = im.size
    if h < 300:
        return None
    px = im.load()
    limit = int(h * 0.08)
    meds = [_median_color(px, y, w) for y in range(limit + 1)]
    uni = [_row_uniformity(px, y, w, meds[y]) for y in range(limit + 1)]
    best: tuple[int, float] | None = None
    for y in range(1, limit + 1):
        if uni[y] >= 0.6 and uni[y - 1] >= 0.6:
            d = _distance(meds[y], meds[y - 1])
            if d >= SEAM_DISTANCE and (best is None or d > best[1]):
                best = (y, d)
    return best


def status_bar_has_content(im: Image.Image) -> bool | None:
    """True if the top ~3.5% holds anything besides background (clock, icons, camera cutout)."""
    w, h = im.size
    band = int(h * 0.035)
    if band < 8:
        return None
    px = im.load()
    med = tuple(sorted(px[x, y][i] for y in range(band) for x in range(w))[(band * w) // 2] for i in range(3))
    different = sum(
        1 for y in range(band) for x in range(w)
        if max(abs(px[x, y][i] - med[i]) for i in range(3)) > 60
    )
    return different / (band * w) >= 0.005


def outgoing_bubble_edges(im: Image.Image) -> list[int]:
    """Right edge (x) of each right-aligned, saturated-color bubble band in the chat area."""
    w, h = im.size
    px = im.load()
    top, bottom = int(h * 0.10), int(h * 0.92)
    bands: list[tuple[int, int, int]] = []  # (start_row, end_row, right_edge)
    start = None
    right = 0
    for y in range(top, bottom + 1):
        xs = [x for x in range(w) if (max(px[x, y]) - min(px[x, y])) >= SATURATED]
        solid = False
        if len(xs) >= 0.08 * w:
            span = xs[-1] - xs[0] + 1
            solid = len(xs) >= 0.6 * span
        if solid and y <= bottom:
            if start is None:
                start, right = y, xs[-1]
            right = max(right, xs[-1])
        elif start is not None:
            bands.append((start, y - 1, right))
            start = None
    if start is not None:
        bands.append((start, bottom, right))
    min_height = max(4, int(h * 0.012))
    return [r for s, e, r in bands if (e - s + 1) >= min_height and r >= 0.75 * w]


class ScreenshotAnalyzer:
    name = "screenshot"
    media_types = frozenset({MediaType.IMAGE})

    def analyze(self, submission: Submission) -> AnalyzerResult:
        if submission.media_type != MediaType.IMAGE:
            return AnalyzerResult(self.name, available=False, note="image files only")
        if not _is_screenshot_claim(submission):
            return AnalyzerResult(
                self.name, available=False,
                note="Not applicable: the submission was not described as a screenshot or chat capture.",
            )

        t0 = time.perf_counter()
        try:
            im, original = _prepare(submission.path)
        except Exception as exc:  # unreadable image
            return AnalyzerResult(self.name, available=False, note=f"could not read image: {exc}")

        signals: list[Signal] = []
        w0, h0 = original
        full_phone = (w0, h0) in COMMON_SCREEN_SIZES

        # 1. Dimensions. NEUTRAL by design: fake-text generators output phone-sized images too.
        if full_phone:
            signals.append(Signal(
                analyzer=self.name, key="screenshot.dimensions",
                direction=Direction.NEUTRAL, strength=Strength.WEAK,
                summary=f"The image is {w0} x {h0} pixels, a real phone screen size.",
                why_it_matters="Consistent with a full-screen capture, but fake-message generators often produce images of exactly this size, so it does not help either way.",
                details={"width": w0, "height": h0, "matches_known_screen": True},
            ))
        else:
            signals.append(Signal(
                analyzer=self.name, key="screenshot.dimensions",
                direction=Direction.NEUTRAL, strength=Strength.WEAK,
                summary=f"The image is {w0} x {h0} pixels, which is not a known full phone screen size.",
                why_it_matters="Common for a screenshot that was cropped, resized or re-saved by a messaging app, so it proves little. Ask for the original capture.",
                details={"width": w0, "height": h0, "matches_known_screen": False},
            ))

        # 2a. Hard color seam in the status-bar area.
        seam = find_status_bar_seam(im)
        if seam:
            y, dist = seam
            signals.append(Signal(
                analyzer=self.name, key="screenshot.status_bar_seam",
                direction=Direction.FABRICATED, strength=Strength.WEAK,
                summary="There is a hard color boundary across the top of the image where the status bar would be.",
                why_it_matters="On most phones the status bar blends into the app header. A sharp seam can mean a strip was pasted on, but some Android phones draw it this way, so treat it as a lead, not proof.",
                details={"row_in_scaled_image": y, "color_distance": round(dist, 1), "scaled_width": im.size[0]},
            ))

        # 2b. Full-size capture with nothing in the status bar.
        if full_phone:
            content = status_bar_has_content(im)
            if content is False:
                signals.append(Signal(
                    analyzer=self.name, key="screenshot.status_bar_empty",
                    direction=Direction.NEUTRAL, strength=Strength.WEAK,
                    summary="No clock, battery or signal icons are visible at the top of this full-size image.",
                    why_it_matters="Real full-screen captures normally show them. People also hide them on purpose for privacy, and message generators sometimes leave them out. The original device would settle it.",
                    details={},
                ))

        # 3. Outgoing bubble alignment.
        edges = outgoing_bubble_edges(im)
        if len(edges) >= MIN_BUBBLES:
            spread = max(edges) - min(edges)
            limit = ALIGN_TOLERANCE * im.size[0]
            details = {"bubbles_measured": len(edges), "right_edges_scaled": edges, "spread_px_scaled": spread,
                       "allowed_px_scaled": round(limit, 1), "scaled_width": im.size[0]}
            if spread > limit:
                signals.append(Signal(
                    analyzer=self.name, key="screenshot.bubble_alignment_off",
                    direction=Direction.FABRICATED, strength=Strength.WEAK,
                    summary=f"The right edges of {len(edges)} outgoing message bubbles do not line up.",
                    why_it_matters="Chat apps right-align a sender's bubbles on one fixed margin. Uneven edges can come from hand-edited or generated messages, but attachments and reactions can also cause it.",
                    details=details,
                ))
            else:
                signals.append(Signal(
                    analyzer=self.name, key="screenshot.bubble_alignment_ok",
                    direction=Direction.NEUTRAL, strength=Strength.WEAK,
                    summary=f"The right edges of {len(edges)} outgoing message bubbles line up.",
                    why_it_matters="This is what a real chat looks like, and also what a careful fake looks like, so it does not help either way.",
                    details=details,
                ))

        return AnalyzerResult(
            self.name, available=True, signals=signals,
            note="First-pass checks only (dimensions, status bar, bubble alignment). All are weak evidence; "
                 "template-based checks per OS and app version are not built yet.",
            duration_ms=int((time.perf_counter() - t0) * 1000),
        )
