"""The case file: everything a human or an agency needs, in JSON and Markdown.

The JSON is the machine-readable record (hash, signals, rules, timestamps).
The Markdown is what a person reads and attaches to a report.
Agency-specific drafts (FBI, IC3, NCMEC, Safe2Tell, FTC) are v0.1 work and
will render from templates in `templates/` using this same data.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from ..pipeline import Case

STRENGTH_WORD = {"strong": "strong", "moderate": "moderate", "weak": "weak"}
DIRECTION_WORD = {
    "authentic": "points to authentic",
    "fabricated": "points to altered or fabricated",
    "ai_generated": "points to AI-generated",
    "neutral": "neutral",
}


def to_dict(case: Case) -> dict[str, Any]:
    sub = case.submission
    return {
        "truthline_version": case.truthline_version,
        "created_at": case.created_at,
        "duration_ms": case.duration_ms,
        "file": {
            "name": sub.path.name,
            "sha256": sub.sha256,
            "size_bytes": sub.size_bytes,
            "media_type": sub.media_type.value,
        },
        "submitter_said": {"claimed_type": sub.claimed_type, "context": sub.context},
        "safety_gate": asdict(case.safety),
        "assessment": {
            "grade": case.assessment.grade.value,
            "label": case.assessment.label,
            "reasoning": case.assessment.reasoning,
            "rules_applied": case.assessment.rules_applied,
            "capped": case.assessment.capped,
            "human_decision_line": case.assessment.human_decision_line,
            "next_steps": case.assessment.next_steps,
        } if case.assessment else None,
        "signals": [asdict(s) for s in (case.assessment.signals if case.assessment else [])],
        "analyzers": [
            {"name": r.analyzer, "available": r.available, "note": r.note, "duration_ms": r.duration_ms, "signal_count": len(r.signals)}
            for r in case.results
        ],
    }


def to_json(case: Case, indent: int = 2) -> str:
    return json.dumps(to_dict(case), indent=indent, default=str)


def to_markdown(case: Case) -> str:
    d = to_dict(case)
    a = d["assessment"]
    lines: list[str] = []
    lines.append("# Truthline case file")
    lines.append("")
    lines.append(f"**File:** `{d['file']['name']}`  ")
    lines.append(f"**SHA-256:** `{d['file']['sha256']}`  ")
    lines.append(f"**Analyzed:** {d['created_at']} (Truthline {d['truthline_version']})  ")
    if d["submitter_said"]["claimed_type"]:
        lines.append(f"**Submitted as:** {d['submitter_said']['claimed_type']}  ")
    if d["submitter_said"]["context"]:
        lines.append(f"**Context given:** {d['submitter_said']['context']}  ")
    lines.append("")

    if d["safety_gate"]["triggered"]:
        lines.append(f"> **Safety first.** {d['safety_gate']['instruction']}")
        lines.append("")

    lines.append(f"## {a['label']}")
    lines.append("")
    lines.append(a["reasoning"])
    lines.append("")
    lines.append(f"*{a['human_decision_line']}*")
    lines.append("")

    lines.append("## What the evidence shows")
    lines.append("")
    if not d["signals"]:
        lines.append("No signals were found by the analyzers that ran.")
    for s in d["signals"]:
        lines.append(f"- **{s['summary']}** ({STRENGTH_WORD[s['strength']]}, {DIRECTION_WORD[s['direction']]}; from `{s['analyzer']}`)  ")
        lines.append(f"  {s['why_it_matters']}")
    lines.append("")

    unavailable = [r for r in d["analyzers"] if not r["available"]]
    if unavailable:
        lines.append("## What could not be checked")
        lines.append("")
        for r in unavailable:
            lines.append(f"- `{r['name']}`: {r['note']}")
        lines.append("")

    lines.append("## What to do next")
    lines.append("")
    for i, step in enumerate(a["next_steps"], 1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append(f"<sub>Rules applied: {', '.join(a['rules_applied'])}. Truthline is open source; the rules are public at src/truthline/assessment.py.</sub>")
    return "\n".join(lines)
