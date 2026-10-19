"""Render agency report drafts from a case file.

Rules this module enforces
--------------------------
* Truthline never submits anything. It writes text a person reviews and sends.
* Anything it cannot know is marked [FILL IN: ...]; `Draft.unfilled` lists them.
* If the case may involve sexual content about a minor, the submitter's free text
  is withheld from every draft (it may describe the content) and no draft ever
  includes the file itself. NCMEC drafts carry the hash only.
* A draft states what the file's evidence showed. It never says a crime occurred
  or who did it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .casefile import DIRECTION_WORD, STRENGTH_WORD
from .templates import AGENCIES, Agency

FILL = "[FILL IN: {}]"
FILL_PATTERN = re.compile(r"\[FILL IN: [^\]]*\]")

INTIMATE_WORDS = ("nude", "naked", "intimate", "sextortion", "explicit", "sexual", "porn", "undress")
MINOR_WORDS = ("minor", "child", "kid", "underage", "under 18", "teen", "student", "year-old", "year old",
               "girl", "boy", "school", "classmate", "middle school", "high school")
WITHHELD = "[withheld: this case may involve sexual content about a minor; use the agency's own form to describe it]"


@dataclass
class Reporter:
    """Who is sending the report. Any blank field becomes a [FILL IN] marker."""

    name: str = ""
    organization: str = ""
    role: str = ""
    phone: str = ""
    email: str = ""
    location: str = ""


@dataclass
class Draft:
    agency: Agency
    text: str
    unfilled: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def involves_possible_minor_sexual_content(case: dict[str, Any]) -> bool:
    said = case.get("submitter_said", {})
    text = f"{said.get('claimed_type', '')} {said.get('context', '')}".lower()
    return any(w in text for w in INTIMATE_WORDS) and any(w in text for w in MINOR_WORDS)


def _or_fill(value: str, label: str) -> str:
    return value.strip() if value and value.strip() else FILL.format(label)


def _evidence_lines(case: dict[str, Any]) -> str:
    signals = case.get("signals", [])
    if not signals:
        return "- No signals were found by the checks that ran."
    return "\n".join(
        f"- {s['summary']} ({STRENGTH_WORD[s['strength']]}; {DIRECTION_WORD[s['direction']]})" for s in signals
    )


def _not_checked(case: dict[str, Any]) -> str:
    missing = [a for a in case.get("analyzers", []) if not a["available"]]
    if not missing:
        return "All checks that apply to this file type ran."
    return "; ".join(f"{a['name']}: {a['note']}" for a in missing)


def _found_block(case: dict[str, Any], ctx: dict[str, str]) -> str:
    a = case.get("assessment") or {}
    return (
        f"An open-source tool (Truthline {ctx['version']}) examined the file \"{ctx['file_name']}\" on {ctx['analyzed_at']}. "
        f"Its assessment was: {ctx['grade_label']}. {ctx['reasoning']}\n\n"
        "This is a technical assessment of the file's evidence. It is not a finding that a crime occurred or of who is responsible.\n\n"
        f"Evidence the tool reported:\n{ctx['evidence']}\n\n"
        f"What it could not check: {ctx['not_checked']}\n\n"
        f"File fingerprint (SHA-256): {ctx['sha256']}\n"
        "The fingerprint lets a recipient confirm that the file they receive is identical to the one analyzed."
        + (f"\n\n{a.get('human_decision_line', '')}" if a.get("human_decision_line") else "")
    )


def build_context(case: dict[str, Any], reporter: Reporter) -> tuple[dict[str, str], list[str]]:
    warnings: list[str] = []
    said = case.get("submitter_said", {})
    a = case.get("assessment") or {}
    minor_risk = involves_possible_minor_sexual_content(case)
    if minor_risk:
        warnings.append(
            "This case may involve sexual content about a minor. The submitter's description was withheld from the draft. "
            "Do not view, save or forward the file; report to NCMEC (report.cybertip.org) and contact law enforcement."
        )

    safety = case.get("safety_gate", {})
    safety_line = (
        safety["instruction"] if safety.get("triggered")
        else "No emergency wording was detected by this tool. If anyone may be in danger, call 911 first."
    )
    claim = said.get("claimed_type", "").strip()
    context_text = said.get("context", "").strip()
    ctx = {
        "reporter_name": _or_fill(reporter.name, "your name"),
        "reporter_org": _or_fill(reporter.organization, "your organization"),
        "reporter_role": _or_fill(reporter.role, "your role"),
        "reporter_phone": _or_fill(reporter.phone, "phone"),
        "reporter_email": _or_fill(reporter.email, "email"),
        "reporter_location": _or_fill(reporter.location, "city and state"),
        "file_name": case["file"]["name"],
        "sha256": case["file"]["sha256"],
        "analyzed_at": case["created_at"],
        "version": case["truthline_version"],
        "grade_label": a.get("label", "not assessed"),
        "reasoning": a.get("reasoning", ""),
        "evidence": _evidence_lines(case),
        "not_checked": _not_checked(case),
        "submitter_claim": claim or FILL.format("what the file was said to be"),
        "submitter_context": WITHHELD if minor_risk else (context_text or FILL.format("what you were told about it")),
        "safety_line": safety_line,
    }
    ctx["what_truthline_found"] = _found_block(case, ctx)
    return ctx, warnings


def draft(case: dict[str, Any], agency_id: str, reporter: Reporter | None = None) -> Draft:
    if agency_id not in AGENCIES:
        raise KeyError(f"unknown agency '{agency_id}'; choose from: {', '.join(AGENCIES)}")
    agency = AGENCIES[agency_id]
    ctx, warnings = build_context(case, reporter or Reporter())

    lines = [f"# Draft report: {agency.name}", ""]
    lines.append(f"**Where to send it:** {agency.submit_at}  ")
    lines.append(f"**Use this for:** {agency.use_for}")
    lines.append("")
    lines.append("> **Truthline wrote this draft; it has not sent anything.** A person must read it, complete the "
                 "[FILL IN] items and submit it. Delete this box and the checklist below before sending.")
    lines.append("")
    if warnings:
        for w in warnings:
            lines.append(f"> **Safety:** {w}")
        lines.append("")
    lines.append("## Before you send (not part of the report)")
    lines.append("")
    for item in agency.before_you_send:
        lines.append(f"- {item}")
    if not agency.attach_file:
        lines.append("- Do not attach the file to this report.")
    lines.append("")
    lines.append("---")
    lines.append("")
    for section in agency.sections:
        lines.append(f"## {section.heading}")
        lines.append("")
        lines.append(section.body.format_map(ctx))
        lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    unfilled = sorted(set(FILL_PATTERN.findall(text)))
    return Draft(agency=agency, text=text, unfilled=unfilled, warnings=warnings)
