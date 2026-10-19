import json

import pytest
from PIL import Image

from truthline.cli import main
from truthline.contract import Submission
from truthline.pipeline import run
from truthline.reports import Reporter, draft, to_dict
from truthline.reports.templates import AGENCIES


def _case(tmp_path, claimed="a screenshot of a text message", context="", name="a.png"):
    p = tmp_path / name
    Image.new("RGB", (1170, 2532), (255, 255, 255)).save(p)
    return to_dict(run(Submission.from_path(p, claimed_type=claimed, context=context)))


REPORTER = Reporter("Pat Lee", "Lincoln Middle School", "Assistant Principal", "813-555-0100", "pat@example.org", "Tampa, FL")


@pytest.mark.parametrize("agency_id", sorted(AGENCIES))
def test_every_draft_renders_with_hash_and_no_unresolved_fields(tmp_path, agency_id):
    case = _case(tmp_path, context="says he will bring a gun to school")
    d = draft(case, agency_id, REPORTER)
    assert case["file"]["sha256"] in d.text
    assert "{" not in d.text and "}" not in d.text      # every {field} was filled
    assert "Truthline wrote this draft; it has not sent anything" in d.text
    assert "Pat Lee" in d.text


def test_unknown_agency_is_a_clear_error(tmp_path):
    with pytest.raises(KeyError, match="unknown agency"):
        draft(_case(tmp_path), "nsa", REPORTER)


def test_blank_reporter_leaves_fill_in_markers_and_lists_them(tmp_path):
    d = draft(_case(tmp_path), "ic3")
    assert "[FILL IN: your name]" in d.text
    assert "[FILL IN: your name]" in d.unfilled


def test_draft_never_calls_it_a_crime_or_a_bare_fake(tmp_path):
    d = draft(_case(tmp_path), "fbi", REPORTER)
    assert "not a finding that a crime occurred" in d.text
    assert "is fake" not in d.text.lower()


def test_threat_case_shows_911_instruction_in_fbi_and_school_drafts(tmp_path):
    case = _case(tmp_path, context="says he will bring a gun to school tomorrow")
    for agency_id in ("fbi", "school"):
        assert "911" in draft(case, agency_id, REPORTER).text


def test_minor_sexual_content_withholds_submitter_text_in_all_drafts(tmp_path):
    secret = "NSFWDETAIL-should-not-appear"
    case = _case(tmp_path, claimed="nude photo of a middle school student", context=secret)
    for agency_id in AGENCIES:
        d = draft(case, agency_id, REPORTER)
        assert secret not in d.text
        assert d.warnings
        assert "withheld" in d.text


def test_ncmec_draft_is_hash_only_and_says_do_not_attach(tmp_path):
    d = draft(_case(tmp_path, claimed="intimate image of a student"), "ncmec", REPORTER)
    assert "Do NOT view, save, copy, forward or attach" in d.text
    assert "Do not attach the file to this report." in d.text
    assert "What an analysis tool found" not in d.text     # no evidence narrative; identifiers only
    assert d.agency.attach_file is False


def test_preservation_letter_is_for_governmental_entities_only(tmp_path):
    d = draft(_case(tmp_path), "preservation", Reporter("Ofc. Ray", "Tampa PD", "Officer"))
    assert "GOVERNMENTAL ENTITY" in d.text
    assert "2703(f)" in d.text
    assert "90 days" in d.text
    assert "court order" in d.text


def test_cli_agencies_and_draft_roundtrip(tmp_path, capsys):
    img = tmp_path / "s.png"
    Image.new("RGB", (1170, 2532), (255, 255, 255)).save(img)
    case_path = tmp_path / "case.json"
    assert main(["check", str(img), "--as", "a screenshot of a text", "--json", "--out", str(case_path)]) == 0
    assert main(["agencies"]) == 0
    out = tmp_path / "draft.md"
    assert main(["draft", str(case_path), "--to", "ic3", "--name", "Pat", "--out", str(out)]) == 0
    assert "Draft report" in out.read_text(encoding="utf-8")
    err = capsys.readouterr().err
    assert "still marked [FILL IN]" in err


def test_cli_draft_rejects_non_case_files(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"hello": 1}), encoding="utf-8")
    assert main(["draft", str(bad), "--to", "fbi"]) == 2
    assert main(["draft", str(tmp_path / "missing.json"), "--to", "fbi"]) == 2
