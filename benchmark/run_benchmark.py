"""Run the Truthline pipeline over a benchmark manifest and report results.

Usage: python benchmark/run_benchmark.py benchmark/manifest.csv
Manifest columns: path, category (real|fabricated|ai_generated), claimed_type, source, consent_ref, notes
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

from truthline.assessment import Grade
from truthline.contract import Submission
from truthline.pipeline import run

FAB_GRADES = {Grade.LIKELY_FABRICATED, Grade.VERY_LIKELY_FABRICATED}


def main(manifest: Path) -> int:
    rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    if not rows:
        print("manifest is empty; add consented samples first (see benchmark/README.md)")
        return 1
    by_cat: dict[str, Counter] = defaultdict(Counter)
    missing = 0
    for row in rows:
        p = manifest.parent / row["path"]
        if not p.exists():
            missing += 1
            continue
        if not row.get("consent_ref"):
            print(f"skipping {p.name}: no consent_ref")
            continue
        case = run(Submission.from_path(p, claimed_type=row.get("claimed_type", "")))
        by_cat[row["category"]][case.assessment.grade] += 1

    print(f"samples: {len(rows)}  missing files: {missing}\n")
    for cat, counts in by_cat.items():
        total = sum(counts.values())
        print(f"[{cat}] n={total}")
        for g in Grade:
            if counts[g]:
                print(f"  {g.value:24s} {counts[g]:4d}  {counts[g]/total:6.1%}")
    real = by_cat.get("real", Counter())
    if real:
        wrongful = sum(real[g] for g in FAB_GRADES) / sum(real.values())
        print(f"\nWrongful fabricated rate (real graded fabricated): {wrongful:.1%}  (target 0%)")
    for cat in ("fabricated", "ai_generated"):
        c = by_cat.get(cat, Counter())
        if c:
            catch = sum(c[g] for g in FAB_GRADES) / sum(c.values())
            print(f"Catch rate [{cat}]: {catch:.1%}")
    if by_cat.get("synthetic"):
        print("\n(synthetic samples are shown above for information only; they are not part of any catch rate)")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "benchmark/manifest.csv")))
