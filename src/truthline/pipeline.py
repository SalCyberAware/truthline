"""The pipeline: safety gate -> analyzers in parallel -> assessment -> case.

Design rules enforced here:
- Analyzers that cannot run are reported as unavailable, never silently skipped.
- One failing analyzer does not stop the others.
- The result always says which layers were missing.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import __version__
from .analyzers import REGISTRY
from .assessment import Assessment, assess
from .contract import Analyzer, AnalyzerResult, Submission

EMERGENCY_WORDS = (
    "shoot", "shooting", "gun", "bomb", "kill", "stab", "attack", "hurt myself", "suicide",
    "kill myself", "tomorrow at school", "bring a weapon",
)


@dataclass
class SafetyGate:
    """Runs before analysis. It never blocks analysis; it only makes sure the
    emergency instruction is shown first when the context describes imminent harm."""

    triggered: bool = False
    instruction: str = ""


@dataclass
class Case:
    submission: Submission
    created_at: str
    truthline_version: str
    safety: SafetyGate
    results: list[AnalyzerResult] = field(default_factory=list)
    assessment: Assessment | None = None
    duration_ms: int = 0

    @property
    def unavailable(self) -> list[AnalyzerResult]:
        return [r for r in self.results if not r.available]


def safety_gate(submission: Submission) -> SafetyGate:
    text = f"{submission.claimed_type} {submission.context}".lower()
    if any(w in text for w in EMERGENCY_WORDS):
        return SafetyGate(
            triggered=True,
            instruction=(
                "If anyone may be in immediate danger, call 911 (or your local emergency number) now "
                "and start your organization's threat protocol. Do not wait for this analysis. "
                "Whether this file is real or fabricated, the safety question must be closed by people."
            ),
        )
    return SafetyGate()


def run(submission: Submission, analyzers: list[Analyzer] | None = None, timeout_s: float = 60.0) -> Case:
    t0 = time.perf_counter()
    analyzers = REGISTRY if analyzers is None else analyzers
    case = Case(
        submission=submission,
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        truthline_version=__version__,
        safety=safety_gate(submission),
    )

    applicable = [a for a in analyzers if submission.media_type in a.media_types]
    skipped = [a for a in analyzers if submission.media_type not in a.media_types]
    for a in skipped:
        case.results.append(AnalyzerResult(a.name, available=False, note=f"does not handle {submission.media_type.value} files"))

    with ThreadPoolExecutor(max_workers=max(1, len(applicable))) as pool:
        futures = {pool.submit(a.analyze, submission): a for a in applicable}
        for fut in as_completed(futures, timeout=timeout_s):
            a = futures[fut]
            try:
                case.results.append(fut.result())
            except Exception as exc:  # an analyzer crashed; say so, keep going
                case.results.append(AnalyzerResult(a.name, available=False, note=f"analyzer error: {exc}"))

    case.results.sort(key=lambda r: r.analyzer)
    case.assessment = assess(case.results, submission)
    case.duration_ms = int((time.perf_counter() - t0) * 1000)
    return case
