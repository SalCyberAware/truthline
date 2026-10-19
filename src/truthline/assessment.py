"""Assessment: public rules that turn signals into a grade and next steps.

Read this file as the policy it is. Every rule is written so a non-engineer can
argue with it. Changing a rule is a pull request with a reason, not a config flip.

Grades
------
VERIFIED_AUTHENTIC   a valid provenance chain says the file is what it claims
LIKELY_AUTHENTIC     several authentic signals, no fabrication signals
INCONCLUSIVE         the default: not enough evidence either way
LIKELY_FABRICATED    one strong or two moderate fabrication signals
VERY_LIKELY_FABRICATED  a strong provenance statement of AI generation, or
                     one strong plus one moderate independent fabrication signal

Rules
-----
R1  A STRONG AI_GENERATED signal from provenance alone yields VERY_LIKELY_FABRICATED
    (with the wording "AI-generated or AI-edited").
R2  A STRONG AUTHENTIC provenance signal with no FABRICATED signals yields VERIFIED_AUTHENTIC.
R3  One STRONG FABRICATED signal yields LIKELY_FABRICATED; with any additional MODERATE
    or STRONG fabrication signal from a *different analyzer*, VERY_LIKELY_FABRICATED.
R4  Two MODERATE FABRICATED signals from different analyzers yield LIKELY_FABRICATED.
R5  Two or more AUTHENTIC signals (any strength) and zero FABRICATED/AI signals yield
    LIKELY_AUTHENTIC.
R6  Anything else is INCONCLUSIVE.
R7  WEAK signals never change a grade on their own; they are shown as context.
R8  If the analyzers that matter most for the claimed type were unavailable
    (e.g. the screenshot analyzer for a claimed screenshot), the grade is capped
    at INCONCLUSIVE unless provenance decided it, and the case says why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .contract import AnalyzerResult, Direction, Signal, Strength, Submission


class Grade(str, Enum):
    VERIFIED_AUTHENTIC = "verified_authentic"
    LIKELY_AUTHENTIC = "likely_authentic"
    INCONCLUSIVE = "inconclusive"
    LIKELY_FABRICATED = "likely_fabricated"
    VERY_LIKELY_FABRICATED = "very_likely_fabricated"


GRADE_LABEL = {
    Grade.VERIFIED_AUTHENTIC: "Verified authentic",
    Grade.LIKELY_AUTHENTIC: "Likely authentic",
    Grade.INCONCLUSIVE: "Inconclusive",
    Grade.LIKELY_FABRICATED: "Likely altered or fabricated",
    Grade.VERY_LIKELY_FABRICATED: "Very likely AI-generated or fabricated",
}

HUMAN_DECISION_LINE = (
    "This assessment does not tell you whether a threat, a scam or a wrong exists. "
    "It tells you what the file's evidence shows. Follow your organization's protocol regardless of the grade."
)


@dataclass
class Assessment:
    grade: Grade
    label: str
    rules_applied: list[str]
    reasoning: str
    signals: list[Signal]
    unavailable: list[str]
    next_steps: list[str]
    human_decision_line: str = HUMAN_DECISION_LINE
    capped: bool = False
    details: dict = field(default_factory=dict)


def _by(signals: list[Signal], direction: Direction, strength: Strength | None = None) -> list[Signal]:
    return [s for s in signals if s.direction == direction and (strength is None or s.strength == strength)]


def assess(results: list[AnalyzerResult], submission: Submission) -> Assessment:
    signals = [s for r in results if r.available for s in r.signals]
    unavailable = [f"{r.analyzer}: {r.note}" for r in results if not r.available]
    rules: list[str] = []

    ai_strong = _by(signals, Direction.AI_GENERATED, Strength.STRONG)
    auth_strong = _by(signals, Direction.AUTHENTIC, Strength.STRONG)
    fab_strong = _by(signals, Direction.FABRICATED, Strength.STRONG)
    fab_mod = _by(signals, Direction.FABRICATED, Strength.MODERATE)
    fab_any_nonweak = [s for s in signals if s.direction in (Direction.FABRICATED, Direction.AI_GENERATED) and s.strength != Strength.WEAK]
    auth_all = _by(signals, Direction.AUTHENTIC)
    fab_or_ai_all = [s for s in signals if s.direction in (Direction.FABRICATED, Direction.AI_GENERATED)]

    grade = Grade.INCONCLUSIVE
    reasoning = "Not enough evidence either way."
    decided_by_provenance = False

    if ai_strong:
        grade, decided_by_provenance = Grade.VERY_LIKELY_FABRICATED, True
        rules.append("R1")
        reasoning = "Signed provenance data states the file was created or edited with an AI tool."
    elif auth_strong and not fab_or_ai_all:
        grade, decided_by_provenance = Grade.VERIFIED_AUTHENTIC, True
        rules.append("R2")
        reasoning = "A valid provenance chain is present and nothing contradicts it."
    elif fab_strong:
        others = [s for s in fab_any_nonweak if s.analyzer != fab_strong[0].analyzer]
        if others:
            grade = Grade.VERY_LIKELY_FABRICATED
            rules.append("R3b")
            reasoning = "A strong fabrication signal is corroborated by an independent analyzer."
        else:
            grade = Grade.LIKELY_FABRICATED
            rules.append("R3a")
            reasoning = "One strong fabrication signal, not yet corroborated."
    elif len({s.analyzer for s in fab_mod}) >= 2:
        grade = Grade.LIKELY_FABRICATED
        rules.append("R4")
        reasoning = "Two independent moderate fabrication signals."
    elif len(auth_all) >= 2 and not fab_or_ai_all:
        grade = Grade.LIKELY_AUTHENTIC
        rules.append("R5")
        reasoning = "Multiple authenticity signals and no contradicting evidence."
    else:
        rules.append("R6")

    capped = False
    claimed = submission.claimed_type.lower()
    if "screenshot" in claimed and any(r.analyzer == "screenshot" and not r.available for r in results) and not decided_by_provenance:
        if grade != Grade.INCONCLUSIVE:
            capped = True
            rules.append("R8")
            reasoning += " Capped at inconclusive because the screenshot analyzer could not run."
        grade = Grade.INCONCLUSIVE if grade in (Grade.LIKELY_AUTHENTIC,) else grade

    next_steps = _next_steps(grade, submission, unavailable)
    return Assessment(
        grade=grade, label=GRADE_LABEL[grade], rules_applied=rules, reasoning=reasoning,
        signals=signals, unavailable=unavailable, next_steps=next_steps, capped=capped,
    )


def _next_steps(grade: Grade, submission: Submission, unavailable: list[str]) -> list[str]:
    steps: list[str] = []
    claimed = submission.claimed_type.lower()
    ctx = f"{claimed} {submission.context}".lower()

    if any(w in ctx for w in ("threat", "shoot", "gun", "bomb", "school")):
        steps.append("Run your threat-assessment protocol now, regardless of this grade.")
        steps.append("Preserve the original file exactly as received; do not forward edited copies.")
        steps.append("Ask the submitter for the device the screenshot was taken on and the account it came from.")
        steps.append("Give your school resource officer or local police the case file; ask them to send a preservation request (18 U.S.C. 2703(f)) to the platform named in the image.")
    elif any(w in ctx for w in ("voicemail", "voice", "call", "payment", "wire", "invoice", "ceo", "boss")):
        steps.append("Do not act on the request. Call the person back on a number you already have, not one from the message.")
        steps.append("Require a second approver for any payment or account change.")
        steps.append("Report to IC3 (ic3.gov) and, for business impersonation, to the FTC (reportfraud.ftc.gov).")
    elif any(w in ctx for w in ("nude", "intimate", "sextortion", "explicit")):
        steps.append("If the person depicted is under 18, do not view, save or forward the file. Report to the NCMEC CyberTipline (report.cybertip.org) and contact law enforcement.")
        steps.append("Use Take It Down (takeitdown.ncmec.org) or StopNCII.org to have copies removed from participating platforms.")
        steps.append("Do not pay or negotiate with anyone demanding money.")
    else:
        steps.append("Ask the submitter for the original file from the device it was created or captured on.")
        steps.append("Try a reverse image search to find earlier copies of the image.")

    if unavailable:
        steps.append("Some analyzers could not run (listed in the case file); the grade may change when they are available.")
    steps.append("Keep this case file with the original; its SHA-256 hash lets anyone confirm the file was not changed afterwards.")
    return steps
