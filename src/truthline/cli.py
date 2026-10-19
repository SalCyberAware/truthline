"""Command line: `truthline check <file> [--as "a screenshot of a text"] [--context "..."] [--json]`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .contract import Submission
from .pipeline import run
from .reports import to_json, to_markdown


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

    args = parser.parse_args(argv)

    if args.cmd == "analyzers":
        from .analyzers import REGISTRY
        for a in REGISTRY:
            print(f"{a.name:12s} handles: {', '.join(sorted(m.value for m in a.media_types))}")
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
