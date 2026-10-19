import csv
import importlib.util
import sys
from pathlib import Path

from truthline.analyzers.screenshot import ScreenshotAnalyzer
from truthline.contract import Submission

_spec = importlib.util.spec_from_file_location("render_synthetic", Path(__file__).resolve().parents[1] / "benchmark" / "render_synthetic.py")
rs = importlib.util.module_from_spec(_spec)
sys.modules["render_synthetic"] = rs
_spec.loader.exec_module(rs)


def _keys(path, claimed="a screenshot of a text message"):
    r = ScreenshotAnalyzer().analyze(Submission.from_path(path, claimed_type=claimed))
    return {s.key for s in r.signals}


def test_generates_files_and_manifest_labeled_synthetic(tmp_path):
    rows = rs.generate(tmp_path, 4, None, None, None, 1)
    assert len(rows) == 4
    assert all(r["category"] == "synthetic" for r in rows)
    m = list(csv.DictReader((tmp_path / "synthetic-manifest.csv").open(encoding="utf-8")))
    assert len(m) == 4 and len(m[0]["sha256"]) == 64


def test_same_seed_same_image(tmp_path):
    a = rs.render(rs.Recipe(seed=5))
    b = rs.render(rs.Recipe(seed=5))
    assert a.tobytes() == b.tobytes()


def test_each_planted_flaw_is_seen_by_the_screenshot_analyzer(tmp_path):
    for style in ("iphone", "android"):
        for dark in (False, True):
            clean = tmp_path / f"clean-{style}-{dark}.png"
            rs.save(rs.render(rs.Recipe(style=style, dark=dark, flaws=[], seed=3)), clean, rs.Recipe())
            k = _keys(clean)
            assert "screenshot.status_bar_seam" not in k
            assert "screenshot.bubble_alignment_off" not in k
            assert "screenshot.status_bar_empty" not in k

            flawed = tmp_path / f"flawed-{style}-{dark}.png"
            rec = rs.Recipe(style=style, dark=dark, flaws=["seam", "misaligned"], seed=3)
            rs.save(rs.render(rec), flawed, rec)
            k = _keys(flawed)
            assert "screenshot.status_bar_seam" in k
            assert "screenshot.bubble_alignment_off" in k

    empty = tmp_path / "nostatus.png"
    rec = rs.Recipe(flaws=["nostatus"], seed=3)
    rs.save(rs.render(rec), empty, rec)
    assert "screenshot.status_bar_empty" in _keys(empty)
