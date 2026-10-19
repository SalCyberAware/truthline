from pathlib import Path

from PIL import Image

from truthline.assessment import Grade, assess
from truthline.contract import AnalyzerResult, Direction, Signal, Strength, Submission
from truthline.pipeline import run
from truthline.reports import to_dict, to_markdown


def _png(tmp_path: Path, name: str = "a.png", software: str | None = None) -> Path:
    p = tmp_path / name
    im = Image.new("RGB", (1170, 2532), (255, 255, 255))
    if software:
        from PIL import PngImagePlugin
        meta = PngImagePlugin.PngInfo()
        meta.add_text("Software", software)
        im.save(p, pnginfo=meta)
    else:
        im.save(p)
    return p


def test_empty_pipeline_is_inconclusive(tmp_path):
    sub = Submission.from_path(_png(tmp_path), claimed_type="a screenshot of a text message")
    case = run(sub)
    assert case.assessment.grade == Grade.INCONCLUSIVE
    assert len(sub.sha256) == 64
    # the screenshot analyzer must say it could not run, not pretend it did
    assert any(r.analyzer == "screenshot" and not r.available for r in case.results)


def test_editor_software_is_a_moderate_signal(tmp_path):
    sub = Submission.from_path(_png(tmp_path, software="Adobe Photoshop 25.0"), claimed_type="a screenshot")
    case = run(sub)
    keys = {s.key for s in case.assessment.signals}
    assert "metadata.editor_software" in keys
    # one moderate signal alone does not change the grade (R4 needs two analyzers)
    assert case.assessment.grade == Grade.INCONCLUSIVE


def test_safety_gate_triggers_on_threat_context(tmp_path):
    sub = Submission.from_path(_png(tmp_path), claimed_type="screenshot", context="says he will bring a gun to school tomorrow")
    case = run(sub)
    assert case.safety.triggered
    md = to_markdown(case)
    assert "911" in md
    assert "threat-assessment protocol" in md


def _sig(analyzer, direction, strength, key="k"):
    return Signal(analyzer, key, direction, strength, "s", "w")


def _sub(tmp_path, claimed=""):
    return Submission.from_path(_png(tmp_path), claimed_type=claimed)


def test_rule_r1_ai_provenance(tmp_path):
    results = [AnalyzerResult("c2pa", True, [_sig("c2pa", Direction.AI_GENERATED, Strength.STRONG)])]
    assert assess(results, _sub(tmp_path)).grade == Grade.VERY_LIKELY_FABRICATED


def test_rule_r2_valid_provenance(tmp_path):
    results = [AnalyzerResult("c2pa", True, [_sig("c2pa", Direction.AUTHENTIC, Strength.STRONG)])]
    assert assess(results, _sub(tmp_path)).grade == Grade.VERIFIED_AUTHENTIC


def test_rule_r3_strong_plus_corroboration(tmp_path):
    results = [
        AnalyzerResult("screenshot", True, [_sig("screenshot", Direction.FABRICATED, Strength.STRONG)]),
        AnalyzerResult("metadata", True, [_sig("metadata", Direction.FABRICATED, Strength.MODERATE)]),
    ]
    assert assess(results, _sub(tmp_path)).grade == Grade.VERY_LIKELY_FABRICATED


def test_rule_r4_two_moderate_different_analyzers(tmp_path):
    results = [
        AnalyzerResult("a", True, [_sig("a", Direction.FABRICATED, Strength.MODERATE)]),
        AnalyzerResult("b", True, [_sig("b", Direction.FABRICATED, Strength.MODERATE)]),
    ]
    assert assess(results, _sub(tmp_path)).grade == Grade.LIKELY_FABRICATED


def test_rule_r7_weak_signals_never_decide(tmp_path):
    results = [AnalyzerResult("a", True, [_sig("a", Direction.FABRICATED, Strength.WEAK), _sig("a", Direction.FABRICATED, Strength.WEAK, "k2")])]
    assert assess(results, _sub(tmp_path)).grade == Grade.INCONCLUSIVE


def test_case_file_has_hash_and_rules(tmp_path):
    case = run(Submission.from_path(_png(tmp_path)))
    d = to_dict(case)
    assert d["file"]["sha256"] == case.submission.sha256
    assert d["assessment"]["rules_applied"]
    assert "human_decision_line" in d["assessment"]
