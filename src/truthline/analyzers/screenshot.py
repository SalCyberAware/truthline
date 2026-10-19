"""Chat-screenshot forensics analyzer (v0.0.1: scaffold).

This is the analyzer no public tool offers, and the one the school case needs.
In v0.1 it will check, against a maintained template library:

- status bar geometry (clock, battery, signal placement) per OS version
- message-bubble color, corner radius and tail shape per app version
- font metrics (system font vs the fonts used by fake-text generator sites)
- date and time formats, carrier capitalization, "Delivered"/"Read" markers
- consistency between the on-screen clock and the file's own timestamps
- image dimensions vs real device screen sizes

For now it reports itself unavailable, so the pipeline is honest about what
it cannot yet see. Template library lives in `src/truthline/analyzers/templates/`
(to be added).
"""

from __future__ import annotations

from ..contract import AnalyzerResult, MediaType, Submission

COMMON_SCREEN_SIZES = {
    # width x height in pixels for common phones; used in v0.1 for a WEAK signal
    (1170, 2532), (1179, 2556), (1290, 2796), (1080, 2400), (1080, 2340), (1440, 3120),
    (1125, 2436), (750, 1334), (1284, 2778), (1206, 2622), (1320, 2868),
}


class ScreenshotAnalyzer:
    name = "screenshot"
    media_types = frozenset({MediaType.IMAGE})

    def analyze(self, submission: Submission) -> AnalyzerResult:
        return AnalyzerResult(
            self.name, available=False,
            note="Chat-screenshot forensics is not implemented yet (planned for v0.1). "
                 "Until then: ask the submitter for the original on the device it was captured on, "
                 "and request platform records through law enforcement.",
        )
