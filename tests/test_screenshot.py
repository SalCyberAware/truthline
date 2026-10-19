from PIL import Image, ImageDraw

from truthline.analyzers.screenshot import ScreenshotAnalyzer
from truthline.contract import Direction, Strength, Submission

W, H = 1170, 2532
BLUE = (10, 132, 255)


def _chat(tmp_path, right_edges=(1100, 1100, 1100, 1100), status_bar=True, seam=False, name="chat.png"):
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    if status_bar:
        d.rectangle([90, 40, 210, 80], fill=(0, 0, 0))        # clock
        d.rectangle([950, 40, 1080, 80], fill=(0, 0, 0))      # battery
    if seam:
        d.rectangle([0, 0, W, 150], fill=(0, 0, 0))
    y = 500
    for edge in right_edges:
        d.rounded_rectangle([edge - 500, y, edge, y + 140], radius=60, fill=BLUE)
        y += 260
    p = tmp_path / name
    im.save(p)
    return p


def _run(path, claimed="a screenshot of a text message"):
    sub = Submission.from_path(path, claimed_type=claimed)
    return ScreenshotAnalyzer().analyze(sub)


def _keys(result):
    return {s.key: s for s in result.signals}


def test_not_applicable_when_not_a_screenshot(tmp_path):
    r = _run(_chat(tmp_path), claimed="a photo of my dog")
    assert not r.available
    assert "Not applicable" in r.note


def test_tidy_chat_has_no_fabrication_signals(tmp_path):
    r = _run(_chat(tmp_path))
    assert r.available
    keys = _keys(r)
    assert keys["screenshot.dimensions"].direction == Direction.NEUTRAL
    assert "screenshot.bubble_alignment_ok" in keys
    assert "screenshot.status_bar_empty" not in keys
    assert not [s for s in r.signals if s.direction == Direction.FABRICATED]


def test_misaligned_bubbles_flagged_weak(tmp_path):
    r = _run(_chat(tmp_path, right_edges=(1100, 1000, 1090, 1040)))
    s = _keys(r)["screenshot.bubble_alignment_off"]
    assert s.direction == Direction.FABRICATED
    assert s.strength == Strength.WEAK


def test_small_tail_sized_difference_is_tolerated(tmp_path):
    r = _run(_chat(tmp_path, right_edges=(1100, 1100, 1100, 1110)))
    assert "screenshot.bubble_alignment_off" not in _keys(r)


def test_status_bar_seam_flagged(tmp_path):
    r = _run(_chat(tmp_path, seam=True))
    assert "screenshot.status_bar_seam" in _keys(r)


def test_empty_status_bar_is_neutral(tmp_path):
    r = _run(_chat(tmp_path, status_bar=False))
    s = _keys(r)["screenshot.status_bar_empty"]
    assert s.direction == Direction.NEUTRAL


def test_cropped_image_is_not_judged_on_status_bar(tmp_path):
    im = Image.new("RGB", (900, 1200), (255, 255, 255))
    p = tmp_path / "crop.png"
    im.save(p)
    keys = _keys(_run(p))
    assert keys["screenshot.dimensions"].details["matches_known_screen"] is False
    assert "screenshot.status_bar_empty" not in keys


def test_analyzer_never_emits_authentic_or_non_weak_signals(tmp_path):
    for p in (_chat(tmp_path), _chat(tmp_path, right_edges=(1100, 900, 1000, 1100), seam=True, name="b.png")):
        for s in _run(p).signals:
            assert s.direction != Direction.AUTHENTIC
            assert s.strength == Strength.WEAK


def test_screenshot_word_in_comment_is_not_a_screenshot_tag(tmp_path):
    from PIL import PngImagePlugin

    from truthline.analyzers.metadata import MetadataAnalyzer
    p = tmp_path / "c.png"
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "this is a screenshot, honest")
    Image.new("RGB", (W, H), (255, 255, 255)).save(p, pnginfo=info)
    r = MetadataAnalyzer().analyze(Submission.from_path(p, claimed_type="screenshot"))
    assert "metadata.screenshot_tag" not in {s.key for s in r.signals}
    info2 = PngImagePlugin.PngInfo()
    info2.add_text("Software", "Android Screenshot")
    Image.new("RGB", (W, H), (255, 255, 255)).save(p, pnginfo=info2)
    r2 = MetadataAnalyzer().analyze(Submission.from_path(p, claimed_type="screenshot"))
    assert "metadata.screenshot_tag" in {s.key for s in r2.signals}
