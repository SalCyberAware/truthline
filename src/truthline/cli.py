"""Command line.

    truthline check <file> [--as "a screenshot of a text"] [--context "..."] [--json] [--out FILE]
    truthline agencies
    truthline draft <case.json> --to ic3 [--name ... --org ... --role ... --phone ... --email ... --location ...]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .contract import Submission
from .pipeline import run
from .reports import Reporter, draft, to_json, to_markdown
from .reports.templates import AGENCIES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="truthline", description="Verify whether a file is real, altered or AI-generated. Evidence, not verdicts.")
    parser.add_argument("--version", action="version", version=f"truthline {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    chk = sub.add_parser("check", help="analyze one file and print a case file")
    chk.add_argument("file", type=Path)
    chk.add_argument("--as", dest="claimed_type", default="", help='what the file claims to be, e.g. "a screenshot of a text message"')
    chk.add_argument("--context", default="", help="who sent it, when, why it matters")
    chk.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    chk.add_argument("--out", type=Path, help="write the case file here instead of stdout")

    sub.add_parser("analyzers", help="list analyzers and whether they can run")
    sub.add_parser("agencies", help="list the report drafts Truthline can write")

    drf = sub.add_parser("draft", help="write a draft report for an agency from a saved case file (JSON)")
    drf.add_argument("case", type=Path, help="case file made with: truthline check <file> --json --out case.json")
    drf.add_argument("--to", required=True, choices=sorted(AGENCIES), help="which agency the draft is for")
    drf.add_argument("--name", default="")
    drf.add_argument("--org", default="")
    drf.add_argument("--role", default="")
    drf.add_argument("--phone", default="")
    drf.add_argument("--email", default="")
    drf.add_argument("--location", default="")
    drf.add_argument("--out", type=Path, help="write the draft here instead of stdout")

    args = parser.parse_args(argv)

    if args.cmd == "analyzers":
        from .analyzers import REGISTRY
        for a in REGISTRY:
            print(f"{a.name:12s} handles: {', '.join(sorted(m.value for m in a.media_types))}")
        return 0

    if args.cmd == "agencies":
        for a in AGENCIES.values():
            print(f"{a.id:13s} {a.name}\n{'':13s} send at: {a.submit_at}")
        return 0

    if args.cmd == "draft":
        if not args.case.exists():
            print(f"error: {args.case} does not exist", file=sys.stderr)
            return 2
        try:
            case = json.loads(args.case.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"error: {args.case} is not a Truthline case file ({exc})", file=sys.stderr)
            return 2
        if "file" not in case or "assessment" not in case:
            print(f"error: {args.case} is not a Truthline case file (missing 'file' or 'assessment')", file=sys.stderr)
            return 2
        reporter = Reporter(args.name, args.org, args.role, args.phone, args.email, args.location)
        d = draft(case, args.to, reporter)
        if args.out:
            args.out.write_text(d.text, encoding="utf-8")
            print(f"wrote {args.out}")
        else:
            print(d.text)
        for w in d.warnings:
            print(f"SAFETY: {w}", file=sys.stderr)
        print(f"{len(d.unfilled)} item(s) still marked [FILL IN]; a person must complete them before sending.", file=sys.stderr)
        return 0

    if not args.file.exists():
        print(f"error: {args.file} does not exist", file=sys.stderr)
        return 2

    submission = Submission.from_path(args.file, claimed_type=args.claimed_type, context=args.context)
    case = run(submission)
    text = to_json(case) if args.json else to_markdown(case)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
