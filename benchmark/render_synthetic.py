"""Render synthetic chat screenshots with known, planted flaws.

Why this exists
---------------
No public labeled dataset of real/fake chat screenshots exists. Real samples must
come from consenting adults (see SAMPLE-COLLECTION-GUIDE.md). Fakes, though, we can
make ourselves, and the most useful fakes are ones where we know exactly which flaw
was planted. This script draws phone-sized chat screenshots in a generic "iPhone-like"
or "Android-like" style, light or dark, and optionally plants one or more flaws:

    seam          a hard color strip pasted over the status bar
    misaligned    outgoing bubbles that do not share a right edge
    nostatus      a full-size image with an empty status bar
    editor        a PNG "Software" tag naming an image editor

Everything it makes is labeled `synthetic` in the manifest, never `fabricated`:
these are unit-test fodder for the analyzers, not evidence of how well Truthline
catches real-world fakes. Keep the two numbers separate.

Usage
-----
    python benchmark/render_synthetic.py --out benchmark/samples/synthetic --count 12
    python benchmark/render_synthetic.py --out /tmp/x --style android --dark --flaws seam,misaligned

Writes PNGs plus `<out>/synthetic-manifest.csv` with one row per file, including the
exact recipe (style, theme, flaws, seed) so anyone can reproduce the set.

No real app's fonts, icons or assets are used. Bubble colors and layout are approximations
chosen for testing; they are not the real apps' designs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

SCREENS = {"iphone": (1170, 2532), "android": (1080, 2400)}
FLAWS = ("seam", "misaligned", "nostatus", "editor")

LINES_A = [
    "Are we still on for lunch Thursday?", "Yes! See you at noon.", "Can you send the address again?",
    "Sure, it's the place on Main Street.", "Running 5 min late, sorry", "No problem, I'll grab a table",
    "Did you finish the report?", "Almost, sending it tonight", "Thanks for the ride yesterday!",
    "Anytime. How was the game?", "We lost, but it was fun", "Ha, next time", "Happy birthday!!",
    "Thank you so much", "Movie Friday?", "Sounds good, 7pm?", "Perfect", "See you then",
]


@dataclass
class Recipe:
    style: str = "iphone"
    dark: bool = False
    flaws: list[str] = field(default_factory=list)
    seed: int = 0
    n_messages: int = 8

    def label(self) -> str:
        flaws = "+".join(self.flaws) if self.flaws else "clean"
        return f"{self.style}-{'dark' if self.dark else 'light'}-{flaws}-s{self.seed}"


def _font(size: int) -> ImageFont.FreeTypeFont:
    for name in ("DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()  # type: ignore[return-value]


def _palette(style: str, dark: bool) -> dict[str, tuple[int, int, int]]:
    if style == "iphone":
        return {
            "bg": (0, 0, 0) if dark else (255, 255, 255),
            "out": (10, 132, 255), "out_text": (255, 255, 255),
            "in": (38, 38, 40) if dark else (229, 229, 234), "in_text": (255, 255, 255) if dark else (0, 0, 0),
            "fg": (255, 255, 255) if dark else (0, 0, 0), "muted": (142, 142, 147),
            "bar": (0, 0, 0) if dark else (255, 255, 255),
        }
    return {
        "bg": (18, 18, 18) if dark else (255, 255, 255),
        "out": (168, 199, 250) if dark else (12, 87, 208), "out_text": (0, 0, 0) if dark else (255, 255, 255),
        "in": (48, 48, 48) if dark else (233, 238, 246), "in_text": (255, 255, 255) if dark else (0, 0, 0),
        "fg": (255, 255, 255) if dark else (0, 0, 0), "muted": (150, 150, 150),
        "bar": (18, 18, 18) if dark else (255, 255, 255),
    }


def render(recipe: Recipe) -> Image.Image:
    rng = random.Random(recipe.seed)
    w, h = SCREENS[recipe.style]
    p = _palette(recipe.style, recipe.dark)
    im = Image.new("RGB", (w, h), p["bg"])
    d = ImageDraw.Draw(im)
    f_bar, f_msg, f_hdr, f_small = _font(44), _font(46), _font(40), _font(34)

    # status bar
    if "nostatus" not in recipe.flaws:
        clock = f"{rng.randint(1, 12)}:{rng.randint(0, 59):02d}"
        d.text((int(w * 0.075), 60), clock, fill=p["fg"], font=f_bar)
        for i in range(4):  # signal bars
            x = int(w * 0.76) + i * 22
            d.rectangle([x, 96 - (i + 1) * 9, x + 14, 96], fill=p["fg"])
        d.rounded_rectangle([int(w * 0.87), 62, int(w * 0.87) + 72, 98], radius=8, outline=p["fg"], width=4)
        d.rectangle([int(w * 0.87) + 6, 68, int(w * 0.87) + 6 + rng.randint(20, 58), 92], fill=p["fg"])
    if "seam" in recipe.flaws:
        d.rectangle([0, 0, w, 150], fill=(70, 70, 70) if recipe.dark else (200, 200, 200))

    # header
    name = rng.choice(["Alex", "Jordan", "Sam", "Taylor", "Casey", "Morgan"])
    d.line([(0, 250), (w, 250)], fill=p["muted"], width=2)
    d.text((w // 2 - len(name) * 11, 170), name, fill=p["fg"], font=f_hdr)
    d.text((w // 2 - 120, 290), f"Today {rng.randint(8, 11)}:{rng.randint(10, 59)} AM", fill=p["muted"], font=f_small)

    # bubbles
    margin = int(w * 0.04)
    max_w = int(w * 0.72)
    y = 380
    outgoing = rng.random() < 0.5
    for i in range(recipe.n_messages):
        text = LINES_A[(recipe.seed * 3 + i) % len(LINES_A)]
        tw = int(d.textlength(text, font=f_msg))
        bw = min(max_w, tw + 60)
        bh = 110
        if outgoing:
            right = w - margin
            if "misaligned" in recipe.flaws and i % 2 == 1:
                right -= rng.randint(40, 120)
            box = [right - bw, y, right, y + bh]
            fill, tc = p["out"], p["out_text"]
        else:
            box = [margin, y, margin + bw, y + bh]
            fill, tc = p["in"], p["in_text"]
        d.rounded_rectangle(box, radius=44, fill=fill)
        d.text((box[0] + 30, y + 28), text, fill=tc, font=f_msg)
        y += bh + 36
        outgoing = not outgoing if rng.random() < 0.6 else outgoing

    # input bar
    d.rounded_rectangle([margin, h - 260, w - margin, h - 160], radius=50, outline=p["muted"], width=3)
    d.text((margin + 40, h - 232), "Message", fill=p["muted"], font=f_small)
    d.rounded_rectangle([w // 2 - 180, h - 60, w // 2 + 180, h - 44], radius=8, fill=p["fg"])
    return im


def save(im: Image.Image, path: Path, recipe: Recipe) -> None:
    info = PngImagePlugin.PngInfo()
    if "editor" in recipe.flaws:
        info.add_text("Software", "Adobe Photoshop 25.0 (synthetic test tag)")
    info.add_text("Comment", "Truthline synthetic test image; not a real screenshot")
    im.save(path, pnginfo=info)


def generate(out: Path, count: int, style: str | None, dark: bool | None, flaws: list[str] | None, seed0: int) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    rng = random.Random(seed0)
    for i in range(count):
        r = Recipe(
            style=style or rng.choice(list(SCREENS)),
            dark=dark if dark is not None else rng.random() < 0.5,
            flaws=flaws if flaws is not None else rng.sample(FLAWS, k=rng.choice([0, 0, 1, 1, 2])),
            seed=seed0 + i,
        )
        im = render(r)
        path = out / f"synthetic-{i + 1:03d}-{r.label()}.png"
        save(im, path, r)
        rows.append({
            "path": path.name, "category": "synthetic", "claimed_type": "a screenshot of a text message",
            "source": f"benchmark/render_synthetic.py style={r.style} theme={'dark' if r.dark else 'light'}",
            "consent_ref": "N/A-synthetic", "notes": "flaws=" + ("+".join(r.flaws) or "none") + f" seed={r.seed}",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    with (out / "synthetic-manifest.csv").open("w", encoding="utf-8", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wtr.writeheader()
        wtr.writerows(rows)
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render synthetic chat screenshots with planted flaws.")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--count", type=int, default=12)
    p.add_argument("--style", choices=sorted(SCREENS))
    p.add_argument("--dark", action="store_true", default=None)
    p.add_argument("--flaws", help="comma-separated: " + ",".join(FLAWS) + " (or 'none')")
    p.add_argument("--seed", type=int, default=1)
    a = p.parse_args(argv)
    flaws = None
    if a.flaws is not None:
        flaws = [] if a.flaws == "none" else a.flaws.split(",")
        bad = [x for x in flaws if x not in FLAWS]
        if bad:
            print(f"unknown flaw(s): {', '.join(bad)}", file=sys.stderr)
            return 2
    rows = generate(a.out, a.count, a.style, a.dark, flaws, a.seed)
    print(f"wrote {len(rows)} files and synthetic-manifest.csv to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
