#!/usr/bin/env python3
"""
AI Carousel Generator — Agentic Pipeline
Input: topik → LM Studio (local) outline JSON → Pillow render → carousel_final.png

Usage:
  python carousel_generator.py "Topik Carousel"
  python carousel_generator.py "topik" --model "gemma-2-9b-it"
"""

import json, sys, os, argparse
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont

# ─── Config ───────────────────────────────────────────────────────────
LMSTUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "gemma-2-9b-it"   # ganti sesuai nama model di LM Studio
TEMPLATES_DIR = Path("templates")
OUTPUT_DIR = Path("output")

SYSTEM_PROMPT = """KAMU ADALAH AI CONTENT WRITER UNTUK CAROUSEL INSTAGRAM.

### ATURAN KARAKTER
- Judul: MAKSIMAL 5 KATA
- Subjudul/penjelasan: MAKSIMAL 30 KATA (sekitar 200 karakter dengan spasi)
- Tiap judul harus bisa berdiri sendiri, tetap nyambung ke topik

### STRUKTUR
1. Cover — judul besar narik perhatian + subjudul pengantar
2. Content slide (2-5 slide) — judul point + penjelasan singkat
3. CTA — ajakan action + subjudul penutup

### FORMAT OUTPUT
Kembalikan JSON array saja, tanpa teks lain:
[{"slide":1, "type":"cover", "title":"...", "subtitle":"..."}, ...]"""


def call_llm(prompt, system_prompt=None):
    """Call LM Studio API (OpenAI-compatible)."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        LMSTUDIO_URL,
        json={"model": MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 2048},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def clean_json(raw):
    """Extract JSON array from LLM response (handle markdown fences)."""
    raw = raw.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    # cari [ pertama dan ] terakhir
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"Ga nemu JSON array di response:\n{raw[:500]}")
    return json.loads(raw[start : end + 1])


def find_font():
    """Cari font bold & regular di berbagai OS."""
    candidates = [
        # Linux
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        # Windows
        ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"),
        ("C:/Windows/Fonts/Calibri-Bold.ttf", "C:/Windows/Fonts/Calibri.ttf"),
        ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf"),
        # Mac
        ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Helvetica.ttc"),
    ]
    for bold_path, regular_path in candidates:
        if os.path.exists(bold_path):
            return bold_path, regular_path
    return None, None


def render_slide(slide, font_title, font_sub, output_path):
    """Render teks di template PNG."""
    template_file = TEMPLATES_DIR / f"{slide['type']}.png"
    if not template_file.exists():
        raise FileNotFoundError(f"Template ga ditemukan: {template_file}\nBikin dulu template Canva 1080x1080: cover.png, content.png, cta.png")

    img = Image.open(template_file).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    title = slide.get("title", "")
    subtitle = slide.get("subtitle", "")

    # — Title — centered horizontal, 1/3 dari atas
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (w - tw) // 2
    ty = h // 3
    # stroke biar kebaca di background terang
    draw.text((tx, ty), title, font=font_title, fill="white", stroke_width=2, stroke_color="black")

    # — Subtitle — di bawah title
    bbox2 = draw.textbbox((0, 0), subtitle, font=font_sub)
    sw, sh = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
    sx = (w - sw) // 2
    sy = ty + th + 30
    draw.text((sx, sy), subtitle, font=font_sub, fill="white", stroke_width=1, stroke_color="black")

    img.save(output_path)
    print(f"  ✓ Slide {slide['slide']} ({slide['type']})")


def make_placeholder_templates():
    """Bikin template placeholder kalo belum ada, biar langsung test."""
    TEMPLATES_DIR.mkdir(exist_ok=True)
    colors = {"cover": "#1a1a2e", "content": "#16213e", "cta": "#0f3460"}
    label = {"cover": "COVER\nGanti dengan template Canva", "content": "CONTENT\nGanti dengan template Canva", "cta": "CTA\nGanti dengan template Canva"}

    for t, color in colors.items():
        path = TEMPLATES_DIR / f"{t}.png"
        if not path.exists():
            img = Image.new("RGB", (1080, 1080), color)
            draw = ImageDraw.Draw(img)
            # garis panduan area teks
            draw.rectangle([100, 300, 980, 800], outline="white", width=2)
            draw.text((540, 540), label[t], font=ImageFont.load_default(), fill="white", anchor="mm")
            img.save(path)
            print(f"  📦 Template placeholder: {path}")


def combine_slides(slide_paths, output_path):
    """Gabung vertikal semua slide jadi 1 gambar."""
    images = [Image.open(p).convert("RGB") for p in slide_paths]
    total_h = sum(img.height for img in images)
    w = images[0].width
    combined = Image.new("RGB", (w, total_h))
    y = 0
    for img in images:
        combined.paste(img, (0, y))
        y += img.height
    combined.save(output_path)
    print(f"\n✅ Carousel final: {output_path}")
    print(f"   {len(images)} slide, {w}x{total_h}px")


def main():
    parser = argparse.ArgumentParser(description="AI Carousel Generator — Agentic Pipeline")
    parser.add_argument("topic", help="Topik carousel (e.g. '5 Tips public speaking')")
    parser.add_argument("--model", default=MODEL, help=f"Nama model di LM Studio (default: {MODEL})")
    parser.add_argument("--url", default=LMSTUDIO_URL, help="LM Studio API URL")
    args = parser.parse_args()

    global MODEL, LMSTUDIO_URL
    MODEL = args.model
    LMSTUDIO_URL = args.url

    OUTPUT_DIR.mkdir(exist_ok=True)
    make_placeholder_templates()

    # Cari font
    font_bold_path, font_reg_path = find_font()
    if not font_bold_path:
        print("⚠️ Ga nemu font, pake default")
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    else:
        font_title = ImageFont.truetype(font_bold_path, 56)  # title 56pt
        font_sub = ImageFont.truetype(font_reg_path, 32)    # subtitle 32pt

    print(f"\n▶ Generate carousel: \"{args.topic}\"")
    print(f"  Model: {MODEL} @ {LMSTUDIO_URL}")

    # Step 1: Outline dari LM Studio
    print("\n  Step 1/3: Call LM Studio → outline...")
    try:
        raw = call_llm(f"Buat carousel Instagram tentang: {args.topic}", SYSTEM_PROMPT)
        outline = clean_json(raw)
    except Exception as e:
        print(f"  ❌ Gagal: {e}")
        sys.exit(1)
    print(f"  → {len(outline)} slide generated")

    # Step 2: Render tiap slide
    print("\n  Step 2/3: Render slides ke template...")
    slides = []
    for slide in outline:
        out = OUTPUT_DIR / f"slide{slide['slide']}.png"
        render_slide(slide, font_title, font_sub, out)
        slides.append(out)

    # Step 3: Gabung
    print("\n  Step 3/3: Combine vertical...")
    combine_slides(slides, OUTPUT_DIR / "carousel_final.png")

    print("\n🎉 Done!")


if __name__ == "__main__":
    main()
