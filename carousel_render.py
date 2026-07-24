#!/usr/bin/env python3
"""
Carousel Renderer v2 — Template-based carousel generator.
Baca BAHAN/script.txt → render JUDUL (bold/gede) + SUBJUDUL (normal/kecil) → RESULT/
"""

import os, re, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ─── Bounding box per tipe slide ──────────────────────────────────────
# Semua teks (judul + subjudul) dipusatkan di area ini
TEXT_AREAS = {
    "cover":   {"x": 60, "y": 300, "w": 960, "h": 480},
    "content": {"x": 60, "y": 250, "w": 960, "h": 580},
    "cta":     {"x": 60, "y": 350, "w": 960, "h": 380},
}

SCRIPT_DIR = Path(__file__).parent
BAHAN = SCRIPT_DIR / "BAHAN"
RESULT = SCRIPT_DIR / "RESULT"

MIN_SIZE = 12
MAX_TITLE_SIZE = 100
MAX_SUB_SIZE = 60
TITLE_RATIO = 1.6  # title 1.6x lebih gede dari subtitle


# ─── Parsing ──────────────────────────────────────────────────────────

def parse_script(path):
    """Parse script.txt.
    Format:
      1 COVER_JUDUL:Judul Besar_SUBJUDUL:Subjudul kecil
      2 CONTENT_JUDUL:Judul_SUBJUDUL:...dst
    """
    slides = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            # Ambil nomor + tipe
            m = re.match(r"^(\d+)\s+(COVER|CONTENT|CTA)_(.+)$", line, re.IGNORECASE)
            if not m:
                print(f"  ⚠️  Baris {i}: format salah — {line[:60]}")
                continue

            num = int(m.group(1))
            tipe = m.group(2).upper()
            rest = m.group(3).strip()

            # Ekstrak JUDUL:... dan SUBJUDUL:...
            judul = ""
            subjudul = ""
            # Cari JUDUL:..._SUBJUDUL:... atau JUDUL:... atau SUBJUDUL:...
            jm = re.search(r"JUDUL:\s*(.+?)(?:_SUBJUDUL:|$)", rest, re.IGNORECASE)
            sm = re.search(r"SUBJUDUL:\s*(.+?)$", rest, re.IGNORECASE)
            if jm:
                judul = jm.group(1).strip()
            if sm:
                subjudul = sm.group(1).strip()
            # Fallback: kalo ga ada JUDUL/SUBJUDUL, seluruh teks jadi judul
            if not judul and not subjudul:
                judul = rest

            slides.append({"num": num, "type": tipe, "judul": judul, "subjudul": subjudul})
    return slides


# ─── Font ─────────────────────────────────────────────────────────────

def find_font():
    """Cari font di BAHAN/, fallback ke Arial Windows."""
    for f in sorted(BAHAN.iterdir()):
        if f.suffix.lower() in (".ttf", ".otf"):
            return str(f)
    # Fallback Windows
    for p in [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Calibri.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]:
        if os.path.exists(p):
            return p
    return None


def load_font_pair(font_path):
    """Load font pair: bold untuk judul, regular untuk subjudul.
    Fallback: kalo ga dapet bold, pake regular buat dua2nya.
    """
    p = Path(font_path)
    bold_path = None
    # Coba cari file bold di folder yg sama
    stem = p.stem
    parent = p.parent
    for candidate in [
        parent / f"{stem}b.ttf",
        parent / f"{stem}-bold.ttf",
        parent / f"{stem}-Bold.ttf",
        parent / f"{stem}Bold.ttf",
        parent / f"{stem}_bold.ttf",
    ]:
        if candidate.exists():
            bold_path = str(candidate)
            break

    # Fallback: font yg sama dipake buat dua2nya
    if not bold_path:
        bold_path = font_path
    return bold_path, font_path


# ─── Render helpers ───────────────────────────────────────────────────

def wrap_text(draw, text, font, max_w):
    """Word wrap, handle empty string."""
    if not text:
        return []
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


def fit_text_block(draw, text, font_path, area_w, area_h, max_size):
    """Cari font size terbesar biar wrapped text muat di area."""
    if not text:
        return None, []
    for size in range(max_size, MIN_SIZE - 1, -2):
        font = ImageFont.truetype(font_path, size)
        lines = wrap_text(draw, text, font, area_w)
        if not lines:
            continue
        lh = draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]
        gap = lh // 3
        total_h = len(lines) * (lh + gap) - gap
        if total_h <= area_h:
            return font, lines
    font = ImageFont.truetype(font_path, MIN_SIZE)
    return font, wrap_text(draw, text, font, area_w)


def render_block(draw, lines, font, area_x, area_w, y_start, line_gap, fill="black", stroke_width=0, stroke_color="white"):
    """Render multiline text centered horizontally."""
    lh = draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]
    gap = max(lh // line_gap, 2)
    y = y_start
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        tx = area_x + (area_w - tw) // 2
        draw.text((tx, y), line, font=font, fill=fill, stroke_width=stroke_width, stroke_color=stroke_color)
        y += lh + gap


# ─── Render slide ─────────────────────────────────────────────────────

def render_slide(slide, templates, font_bold_path, font_reg_path, out_path):
    """Render 1 slide: judul bold gede di atas, subjudul normal kecil di bawah."""
    tipe = slide["type"].lower()
    img = templates[tipe].copy()
    draw = ImageDraw.Draw(img)
    area = TEXT_AREAS.get(tipe, TEXT_AREAS["content"])
    aw, ah = area["w"], area["h"]

    judul = slide.get("judul", "")
    subjudul = slide.get("subjudul", "")

    # Kalkulasi area: judul ambil ~55%, subjudul ~45%
    title_area_h = ah
    sub_area_h = ah

    if judul and subjudul:
        title_area_h = int(ah * 0.55)
        sub_area_h = ah - title_area_h
    elif judul:
        title_area_h = ah
        sub_area_h = 0

    # Fit judul
    title_font, title_lines = fit_text_block(draw, judul, font_bold_path, aw, title_area_h, MAX_TITLE_SIZE)
    # Fit subjudul — max size dibatasi biar ga overscale
    sub_font, sub_lines = fit_text_block(draw, subjudul, font_reg_path, aw, sub_area_h, MAX_SUB_SIZE)

    # Hitung total tinggi kedua blok
    total_h = 0
    if title_lines:
        lh = draw.textbbox((0, 0), "Ay", font=title_font)[3] - draw.textbbox((0, 0), "Ay", font=title_font)[1]
        gap = max(lh // 3, 2)
        total_h += len(title_lines) * (lh + gap) - gap
    if sub_lines:
        lh2 = draw.textbbox((0, 0), "Ay", font=sub_font)[3] - draw.textbbox((0, 0), "Ay", font=sub_font)[1]
        gap2 = max(lh2 // 3, 2)
        total_h += len(sub_lines) * (lh2 + gap2) - gap2 + 15  # 15px gap antar blok

    # Mulai dari center vertical
    y_start = area["y"] + (ah - total_h) // 2

    # Render judul
    if title_lines:
        lh = draw.textbbox((0, 0), "Ay", font=title_font)[3] - draw.textbbox((0, 0), "Ay", font=title_font)[1]
        gap = max(lh // 3, 2)
        render_block(draw, title_lines, title_font, area["x"], area["w"], y_start, 3,
                     fill="black", stroke_width=0, stroke_color="white")
        y_start += len(title_lines) * (lh + gap) - gap + 15

    # Render subjudul
    if sub_lines:
        render_block(draw, sub_lines, sub_font, area["x"], area["w"], y_start, 3,
                     fill="black", stroke_width=0, stroke_color="white")

    img.save(out_path)
    parts = [f"J:{judul[:30]}" if judul else ""]
    if subjudul:
        parts.append(f"S:{subjudul[:30]}")
    print(f"  ✓ Slide {slide['num']:02d} — {tipe} | {' | '.join(parts)}")


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    print("=" * 48)
    print("  Carousel Renderer v2")
    print("=" * 48)

    if not BAHAN.exists():
        print(f"\n❌ Folder BAHAN/ ga ditemukan")
        print("   Taruh: cover.png, content.png, cta.png, font.ttf, script.txt")
        input("\n   Enter untuk exit...")
        return 1
    RESULT.mkdir(exist_ok=True)

    # 1. Load templates
    templates = {}
    for tipe in ("cover", "content", "cta"):
        path = BAHAN / f"{tipe}.png"
        if not path.exists():
            print(f"\n❌ Template {tipe}.png ga ditemukan")
            input("   Enter untuk exit...")
            return 1
        templates[tipe] = Image.open(path).convert("RGB")
        print(f"  ✓ Template: {tipe}.png ({templates[tipe].size})")

    # 2. Font
    font_path = find_font()
    if not font_path:
        print("\n❌ Ga nemu font di BAHAN/ atau system")
        input("   Enter untuk exit...")
        return 1
    bold_path, reg_path = load_font_pair(font_path)
    print(f"  ✓ Font bold: {Path(bold_path).name}")
    print(f"  ✓ Font reg:  {Path(reg_path).name}" if bold_path != reg_path else f"  ✓ Font: {Path(font_path).name}")

    # 3. Parse script
    script_path = BAHAN / "script.txt"
    if not script_path.exists():
        print(f"\n❌ script.txt ga ditemukan")
        input("   Enter untuk exit...")
        return 1
    slides = parse_script(script_path)
    if not slides:
        print(f"\n❌ Gagal parse script.txt")
        print("   Format: 1 TYPE_JUDUL:Judul_SUBJUDUL:Subjudul")
        input("   Enter untuk exit...")
        return 1
    print(f"  ✓ Script: {len(slides)} slide")

    # 4. Render
    print(f"\n{'─' * 48}")
    print("  Rendering...")
    print(f"{'─' * 48}")
    rendered = []
    for s in slides:
        fname = f"{s['num']:02d}_{s['type'].lower()}.png"
        out = RESULT / fname
        render_slide(s, templates, bold_path, reg_path, out)
        rendered.append(out)

    print(f"\n{'─' * 48}")
    print(f"  ✅ {len(rendered)} slide selesai!")
    print(f"  📁 {RESULT}/")
    for p in rendered:
        print(f"     {p.name}")
    return 0


if __name__ == "__main__":
    ec = main()
    input("\n  Enter untuk tutup...")
    sys.exit(ec)
