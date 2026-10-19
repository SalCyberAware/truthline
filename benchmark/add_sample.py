"""Add one consented sample to the benchmark: copy it in, hash it, record it.

Usage:
  python benchmark/add_sample.py my-screenshot.png --category real \
      --source "iPhone 15, iOS 19, Messages, light mode" --consent-ref CR-001 --confirm-rules

What it does, so you can check it:
  1. refuses unless you pass --confirm-rules (consent form signed; nothing from the never-list)
  2. refuses if the file is not an image, or its SHA-256 is already in the manifest
  3. copies the file to benchmark/samples/<category>/<category>-NNN.<ext>
  4. appends one row to benchmark/manifest.csv (including the SHA-256)

The samples folder is git-ignored: the files stay on your computer. Only manifest.csv is committed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import sys
from pathlib import Path

CATEGORIES = ("real", "fabricated", "ai_generated")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".heic"}
COLUMNS = ["path", "category", "claimed_type", "source", "consent_ref", "notes", "sha256"]
DEFAULT_CLAIM = "a screenshot of a text message"


class SampleError(ValueError):
    """The sample was refused; the message says why in plain words."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_manifest(manifest: Path) -> list[dict[str, str]]:
    if not manifest.exists():
        return []
    with manifest.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def add_sample(
    file: Path,
    category: str,
    source: str,
    consent_ref: str,
    confirm_rules: bool,
    benchmark_dir: Path,
    claimed_type: str = DEFAULT_CLAIM,
    notes: str = "",
) -> Path:
    if not confirm_rules:
        raise SampleError(
            "Add --confirm-rules to confirm that the consent form is signed and the file contains nothing "
            "from the never-list (sexual content involving a minor, real threats, other people's private messages "
            "without permission, material from a live case)."
        )
    if category not in CATEGORIES:
        raise SampleError(f"category must be one of: {', '.join(CATEGORIES)}")
    if not re.fullmatch(r"CR-\d{3,}", consent_ref):
        raise SampleError("consent reference must look like CR-001 (assigned when the consent form is signed)")
    if not source.strip():
        raise SampleError("say where the file came from, e.g. 'iPhone 15, Messages, dark mode' or 'fake-text website, iPhone style'")
    if not file.is_file():
        raise SampleError(f"{file} does not exist")
    if file.suffix.lower() not in IMAGE_EXT:
        raise SampleError(f"only images for now ({', '.join(sorted(IMAGE_EXT))})")

    manifest = benchmark_dir / "manifest.csv"
    rows = _read_manifest(manifest)
    digest = _sha256(file)
    if any(r.get("sha256") == digest for r in rows):
        raise SampleError("this exact file is already in the manifest")

    folder = benchmark_dir / "samples" / category
    folder.mkdir(parents=True, exist_ok=True)
    n = sum(1 for r in rows if r.get("category") == category) + 1
    dest = folder / f"{category}-{n:03d}{file.suffix.lower()}"
    shutil.copyfile(file, dest)

    new_file = not manifest.exists() or manifest.stat().st_size == 0
    with manifest.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new_file:
            w.writeheader()
        w.writerow({
            "path": dest.relative_to(benchmark_dir).as_posix(),
            "category": category, "claimed_type": claimed_type, "source": source,
            "consent_ref": consent_ref, "notes": notes, "sha256": digest,
        })
    return dest


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Add one consented sample to the Truthline benchmark.")
    p.add_argument("file", type=Path)
    p.add_argument("--category", required=True, choices=CATEGORIES)
    p.add_argument("--source", required=True, help="device/app, or the tool and version that made it")
    p.add_argument("--consent-ref", required=True, help="e.g. CR-001")
    p.add_argument("--claimed-type", default=DEFAULT_CLAIM)
    p.add_argument("--notes", default="", help="method used, e.g. 'edited the time in an image editor'")
    p.add_argument("--confirm-rules", action="store_true")
    args = p.parse_args(argv)
    try:
        dest = add_sample(args.file, args.category, args.source, args.consent_ref, args.confirm_rules,
                          Path(__file__).resolve().parent, args.claimed_type, args.notes)
    except SampleError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"added {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
