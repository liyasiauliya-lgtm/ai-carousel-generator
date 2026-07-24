#!/usr/bin/env python3
"""
Carousel Renderer — Template-based carousel generator.
Baca BAHAN/script.txt → render teks di template → output ke RESULT/
"""

import os, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ─── Bounding box teks per tipe slide ─────────────────────────────────
# (x, y) = pojok kiri atas, w = lebar, h = tinggi
# Text akan di-scale & center otomatis di dalam area ini.
TEXT_AREAS = {
    "cover":   {"x": 140, "y": 350, "w": 800, "h": 400},
    "content": {"x": 140, "y": 300, "w": 800, "h": 480},
    "cta":     {"x": 140, "y": 400, "w": 800, "h": 300},
}

SCRIPT_DIR = Path(__file__).parent
BAHAN = SCRIPT_DIR / "BAHAN"
RESULT = SCRIPT_DIR / "RESULT"
FONT_MIN = 14
FONT_MAX = 100


# ─── Helpers ──────────────────────────────────────────────────────────

def parse_script(path):
    """Parse script.txt. Format: [NUMBER] [TYPE]_[text]"""
    slides = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = re.match(r"^(\d+)\s+(COVER|CONTENT|CTA)_(.+)$", line, re.IGNORECASE)
            if not m:
                print(f"  ⚠️  Skip (format salah): {line[:70]}")
                continue
            slides.append({
                "num":  int(m.group(1)),
                "type": m.group(2).upper(),
                "text": m.group(3).strip(),
            })
    return slides


def find_font():
    """Cari font .ttf/.otf di BAHAN/, fallback ke Arial Windows."""
    for f in sorted(BAHAN.iterdir()):
        if f.suffix.lower() in (".ttf", ".otf"):
            return str(f)
    # Fallback Windows
    win_fonts = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Calibri.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for p in win_fonts:
        if os.path.exists(p):
            return p
    return None


def wrap_text(draw, text, font, max_w):
    """Word-wrap biar muat di max_w pixel."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = cur + " " + w if cur else w
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text(draw, text, font_path, area_w, area_h):
    """Cari font size terbesar biar wrapped text muat di area."""
    for size in range(FONT_MAX, FONT_MIN - 1, -2):
        font = ImageFont.truetype(font_path, size)
        lines = wrap_text(draw, text, font, area_w)
        if not lines:
            continue
        lh = draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]
        gap = lh // 4
        total_h = len(lines) * (lh + gap) - gap
        if total_h <= area_h:
            return font, lines
    font = ImageFont.truetype(font_path, FONT_MIN)
    return font, wrap_text(draw, text, font, area_w)


def render_slide(slide, templates, font_path, out_path):
    """Render 1 slide ke file PNG."""
    tipe = slide["type"].lower()
    img = templates[tipe].copy()
    draw = ImageDraw.Draw(img)
    area = TEXT_AREAS.get(tipe, TEXT_AREAS["content"])
    iw, ih = img.size

    font, lines = fit_text(draw, slide["text"], font_path, area["w"], area["h"])
    lh = draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]
    gap = max(lh // 4, 4)
    total_h = len(lines) * (lh + gap) - gap
    sy = area["y"] + (area["h"] - total_h) // 2

    for i, line in enumerate(lines):
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        tx = area["x"] + (area["w"] - tw) // 2
        ty = sy + i * (lh + gap)
        draw.text((tx, ty), line, font=font, fill="white",
                  stroke_width=2, stroke_color="black")

    img.save(out_path)
    print(f"  ✓ Slide {slide['num']:02d} — {tipe}")


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    print("=" * 48)
    print("  Carousel Renderer")
    print("=" * 48)

    # Validate folders
    if not BAHAN.exists():
        print(f"\n❌ Folder BAHAN/ ga ditemukan di {BAHAN}")
        print("   Bikin folder BAHAN/ dan taruh: cover.png, content.png, cta.png, font.ttf, script.txt")
        input("\n   Enter untuk exit...")
        return 1
    RESULT.mkdir(exist_ok=True)

    # 1. Load templates
    templates = {}
    for tipe in ("cover", "content", "cta"):
        path = BAHAN / f"{tipe}.png"
        if not path.exists():
            print(f"\n❌ Template {tipe}.png ga ditemukan di BAHAN/")
            input("\n   Enter untuk exit...")
            return 1
        templates[tipe] = Image.open(path).convert("RGB")
        print(f"  ✓ Template: {tipe}.png ({templates[tipe].size[0]}x{templates[tipe].size[1]})")

    # 2. Load font
    font_path = find_font()
    if not font_path:
        print("\n❌ Ga nemu font (.ttf/.otf) di BAHAN/ atau system")
        input("\n   Enter untuk exit...")
        return 1
    print(f"  ✓ Font: {Path(font_path).name}")

    # 3. Parse script
    script_path = BAHAN / "script.txt"
    if not script_path.exists():
        print(f"\n❌ script.txt ga ditemukan di BAHAN/")
        input("\n   Enter untuk exit...")
        return 1
    slides = parse_script(script_path)
    if not slides:
        print(f"\n❌ script.txt kosong atau format salah")
        print("   Format: [NUMBER] [TYPE]_[text]")
        print("   Contoh: 1 COVER_5 Tips Public Speaking")
        input("\n   Enter untuk exit...")
        return 1
    print(f"  ✓ Script: {len(slides)} slide")

    # 4. Render each slide
    print(f"\n{'─' * 40}")
    print("  Rendering...")
    print(f"{'─' * 40}")
    rendered = []
    for s in slides:
        fname = f"{s['num']:02d}_{s['type'].lower()}.png"
        out = RESULT / fname
        render_slide(s, templates, font_path, out)
        rendered.append(out)

    # 5. Done
    print(f"\n{'─' * 40}")
    print(f"  ✅ {len(rendered)} slide selesai!")
    print(f"  📁 Output: {RESULT}")
    for p in rendered:
        print(f"     {p.name}")
    return 0


if __name__ == "__main__":
    ec = main()
    input("\n  Enter untuk tutup...")
    sys.exit(ec)
