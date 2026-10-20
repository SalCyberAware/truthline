import csv
import importlib.util
from pathlib import Path

import pytest
from PIL import Image

_spec = importlib.util.spec_from_file_location("add_sample", Path(__file__).resolve().parents[1] / "benchmark" / "add_sample.py")
add_sample_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(add_sample_mod)


def _img(tmp_path, name="a.png", color=(255, 255, 255)):
    p = tmp_path / name
    Image.new("RGB", (100, 200), color).save(p)
    return p


def _bench(tmp_path):
    d = tmp_path / "benchmark"
    d.mkdir()
    return d


def _add(tmp_path, bench, f, **kw):
    args = dict(category="real", source="iPhone 15, Messages", consent_ref="CR-001", confirm_rules=True, benchmark_dir=bench)
    args.update(kw)
    return add_sample_mod.add_sample(f, **args)


def test_adds_copy_and_manifest_row_with_hash(tmp_path):
    bench = _bench(tmp_path)
    dest = _add(tmp_path, bench, _img(tmp_path))
    assert dest.name == "real-001.png" and dest.exists()
    rows = list(csv.DictReader((bench / "manifest.csv").open(encoding="utf-8")))
    assert rows[0]["path"] == "samples/real/real-001.png"
    assert len(rows[0]["sha256"]) == 64
    assert rows[0]["consent_ref"] == "CR-001"


def test_numbers_continue_per_category(tmp_path):
    bench = _bench(tmp_path)
    _add(tmp_path, bench, _img(tmp_path, "a.png", (1, 1, 1)))
    d2 = _add(tmp_path, bench, _img(tmp_path, "b.png", (2, 2, 2)))
    d3 = _add(tmp_path, bench, _img(tmp_path, "c.png", (3, 3, 3)), category="fabricated")
    assert d2.name == "real-002.png"
    assert d3.name == "fabricated-001.png"


def test_refuses_without_confirmation(tmp_path):
    with pytest.raises(add_sample_mod.SampleError, match="confirm-rules"):
        _add(tmp_path, _bench(tmp_path), _img(tmp_path), confirm_rules=False)


def test_refuses_bad_consent_reference_and_duplicates_and_non_images(tmp_path):
    bench = _bench(tmp_path)
    f = _img(tmp_path)
    with pytest.raises(add_sample_mod.SampleError, match="CR-001"):
        _add(tmp_path, bench, f, consent_ref="yes")
    _add(tmp_path, bench, f)
    with pytest.raises(add_sample_mod.SampleError, match="already in the manifest"):
        _add(tmp_path, bench, f)
    doc = tmp_path / "x.pdf"
    doc.write_bytes(b"%PDF")
    with pytest.raises(add_sample_mod.SampleError, match="only images"):
        _add(tmp_path, bench, doc)


def test_cli_benchmark_dir_flag_and_env_var(tmp_path, monkeypatch):
    f = _img(tmp_path, "cli.png", (9, 9, 9))
    elsewhere = tmp_path / "data"
    rc = add_sample_mod.main([str(f), "--category", "fabricated", "--source", "test tool", "--consent-ref", "CR-001",
                              "--confirm-rules", "--benchmark-dir", str(elsewhere)])
    assert rc == 0
    assert (elsewhere / "samples" / "fabricated" / "fabricated-001.png").exists()
    assert (elsewhere / "manifest.csv").exists()

    other = tmp_path / "envdata"
    monkeypatch.setenv("TRUTHLINE_BENCHMARK_DIR", str(other))
    f2 = _img(tmp_path, "cli2.png", (8, 8, 8))
    rc = add_sample_mod.main([str(f2), "--category", "real", "--source", "test", "--consent-ref", "CR-002", "--confirm-rules"])
    assert rc == 0
    assert (other / "samples" / "real" / "real-001.png").exists()
