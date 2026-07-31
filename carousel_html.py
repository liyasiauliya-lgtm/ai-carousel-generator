#!/usr/bin/env python3
"""
Carousel HTML Renderer v3 — dua mode:

  Mode script (default): BAHAN/script.txt → HTML carousel (v2 legacy, tetap jalan)
  Mode json  (--json):   slides.json     → HTML carousel 1080x1350, position:absolute per element (v3)

Export PNG 1080x1350 (4:5) built-in via SVG foreignObject. Browser-only, zero dependency.
"""

import re, base64, json, argparse, urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BAHAN = SCRIPT_DIR / "BAHAN"
RESULT = SCRIPT_DIR / "RESULT"

FONTS = ["Inter, sans-serif", "system-ui, -apple-system, sans-serif"]

SLIDE_STYLES = {
    "cover": {
        "bg": "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
        "title_color": "#ffffff",
        "sub_color": "#c4b5fd",
        "accent": "#a78bfa",
    },
    "content": {
        "bg": "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
        "title_color": "#ffffff",
        "sub_color": "#93c5fd",
        "accent": "#60a5fa",
    },
    "cta": {
        "bg": "linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%)",
        "title_color": "#fef08a",
        "sub_color": "#e0e7ff",
        "accent": "#facc15",
    },
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ─── Card template (Judul.html / content.html) ─────────────

CARD_FRAME = "https://cdn.imgchest.com/files/cc266281c3a3.png"
CARD_TEMPLATES = {
    # Judul.html — cover
    "cover": {"front": "https://cdn.imgchest.com/files/b5688eeb235e.png",
              "judul_color": "#ffffff", "judul_size": 42},
    # content.html — content & cta
    "content": {"front": "https://cdn.imgchest.com/files/366e233fdee2.png",
                "judul_color": "#000000", "judul_size": 54},
    "cta": {"front": "https://cdn.imgchest.com/files/366e233fdee2.png",
            "judul_color": "#000000", "judul_size": 54},
}

_img_cache = {}


def fetch_b64(url):
    """Fetch gambar → data URI base64. Cache per URL. Embedded = export PNG aman (ga kena CORS)."""
    if url in _img_cache:
        return _img_cache[url]
    if not url.startswith("data:"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            url = "data:image/png;base64," + base64.b64encode(data).decode()
            print(f"  ✓ embed {url.split(',')[1][:8]}… ({len(data)//1024} KB)")
        except Exception as e:
            print(f"  ⚠️ gagal fetch {url[:60]} — {e} (pake URL langsung; preview online OK, export PNG bisa gagal)")
    _img_cache[url] = url
    return url


# ─── Parsers ────────────────────────────────────────────────

def parse_script(path):
    slides = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            m = re.match(r"^(\d+)\s+(COVER|CONTENT|CTA)_(.+)$", line, re.IGNORECASE)
            if not m:
                print(f"  ⚠️  Baris {i}: format salah — {line[:60]}")
                continue
            num = int(m.group(1))
            tipe = m.group(2).upper()
            rest = m.group(3).strip()
            judul = subjudul = ""
            jm = re.search(r"JUDUL:\s*(.+?)(?:_SUBJUDUL:|$)", rest, re.IGNORECASE)
            sm = re.search(r"SUBJUDUL:\s*(.+?)$", rest, re.IGNORECASE)
            if jm: judul = jm.group(1).strip()
            if sm: subjudul = sm.group(1).strip()
            if not judul and not subjudul: judul = rest
            slides.append({"num": num, "type": tipe, "judul": judul, "subjudul": subjudul})
    return slides


def parse_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    slides = data["slides"] if isinstance(data, dict) and "slides" in data else data
    for i, s in enumerate(slides):
        s.setdefault("num", i + 1)
        s.setdefault("type", (s.get("class") or "content").upper())
    return slides


def embed_bg_images():
    embedded = {}
    for tipe in ("cover", "content", "cta"):
        p = BAHAN / f"{tipe}.png"
        if p.exists():
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                embedded[tipe] = f"data:image/png;base64,{b64}"
            print(f"  ✓ BG {tipe}.png embedded")
        else:
            print(f"  ~ BG {tipe}.png not found — pake CSS gradient")
    return embedded


# ─── v3 render engine ───────────────────────────────────────

def _pct(v, default=0):
    if isinstance(v, (int, float)):
        return f"{v}%"
    return str(v) if v is not None else f"{default}%"


def render_slide(slide: dict, index: int, mode: str = "script") -> str:
    """Satu slide dict → HTML string. Canvas 1080x1350, element position:absolute dalam %."""
    n = slide.get("num", index + 1)
    bg = slide.get("bg") or slide.get("background") or "#1a1a2e"
    cls = slide.get("class", "")
    active = " active" if index == 0 else ""
    tipe = (slide.get("type") or cls or "content").lower()

    # Card template mode — Judul.html (cover) / content.html (content, cta)
    if tipe in CARD_TEMPLATES:
        tpl = CARD_TEMPLATES[tipe]
        frame = slide.get("frame", CARD_FRAME)
        front = slide.get("front", tpl["front"])
        judul_color = slide.get("judul_color", tpl["judul_color"])
        judul_size = slide.get("judul_size", tpl["judul_size"])
        sub_color = slide.get("sub_color", "#1f2430")
        sub_size = slide.get("sub_size", 30)
        judul = esc(slide.get("judul", "")).replace("\n", "<br>")
        subjudul = esc(slide.get("subjudul", "")).replace("\n", "<br>")
        judul_lines = str(slide.get("judul", "")).count("\n") + 1
        # Aturan jarak (dari Liya 2026-07-31): judul 1 baris → subjudul 700px; 2 baris → 768px
        sub_top = slide.get("sub_top") or (700 if judul_lines <= 1 else 768)
        return f"""
    <div class="slide v3-slide card-slide {cls}{active}" id="slide-{n}">
      <img class="layer-frame" src="{fetch_b64(frame)}" alt="frame" crossorigin="anonymous" referrerpolicy="no-referrer">
      <img class="layer-front" src="{fetch_b64(front)}" alt="front" crossorigin="anonymous" referrerpolicy="no-referrer">
      <div class="judul-wrap"><div class="judul" style="color:{judul_color};font-size:{judul_size}px;">{judul}</div></div>
      <div class="subjudul" style="color:{sub_color};font-size:{sub_size}px;top:{sub_top}px;">{subjudul}</div>
    </div>"""

    elems = []
    for el in slide.get("elements", []):
        t = el.get("type", "text")
        style = (f"position:absolute;left:{_pct(el.get('x'), 5)};"
                 f"top:{_pct(el.get('y'), 8)};width:{_pct(el.get('width'), 90)};")
        if t == "text":
            style += (f"font-size:{el.get('font_size', el.get('size', 48))}px;"
                      f"color:{el.get('color', '#fff')};"
                      f"font-weight:{el.get('font_weight', el.get('weight', 400))};"
                      f"text-align:{el.get('text_align', el.get('align', 'left'))};"
                      f"line-height:1.35;")
            if el.get("font"):
                style += f"font-family:{el['font']};"
            if "letter_spacing" in el:
                style += f"letter-spacing:{el['letter_spacing']}em;"
            if "opacity" in el:
                style += f"opacity:{el['opacity']};"
            elems.append(f'<div style="{style}">{esc(el.get("content", ""))}</div>')
        elif t == "image":
            style += "max-width:100%;height:auto;"
            elems.append(f'<img src="{el.get("src", "")}" style="{style}" alt="">')
        elif t in ("shape", "accent"):
            h = el.get("height", 4)
            color = el.get("color", "#fff")
            if el.get("shape") == "circle":
                style += f"width:{h}px;height:{h}px;background:{color};border-radius:50%;"
            elif el.get("shape") == "line":
                style += f"height:{h}px;background:{color};border-radius:2px;"
            else:
                style += f"height:{h}px;background:{color};border-radius:{el.get('radius', 0)}px;"
            if "opacity" in el:
                style += f"opacity:{el['opacity']};"
            elems.append(f'<div style="{style}"></div>')
    return (f'<div class="slide v3-slide {cls}{active}" id="slide-{n}" '
            f'style="background:{bg};background-size:cover;background-position:center;">'
            f'{"".join(elems)}</div>')


# ─── HTML generator ─────────────────────────────────────────

def generate_html(slides, embedded_bg, mode="script"):
    slides_html = ""
    for i, s in enumerate(slides):
        if s.get("elements") or (mode == "json" and (s.get("judul") is not None or s.get("subjudul") is not None)):
            slides_html += render_slide(s, i, mode) + "\n"
            continue
        tipe = s["type"].lower()
        style = SLIDE_STYLES.get(tipe, SLIDE_STYLES["content"])
        bg = embedded_bg.get(tipe, style["bg"])
        is_first = "active" if i == 0 else ""
        slide_id = f"slide-{i+1}"
        slides_html += f"""
    <div class="slide {tipe} {is_first}" id="{slide_id}" style="background: {bg};">
      <div class="slide-number">0{i+1}/{len(slides):02d}</div>
      <div class="slide-content">
"""
        if s["judul"]:
            slides_html += f'        <div class="title">{esc(s["judul"])}</div>\n'
        if s["subjudul"]:
            slides_html += f'        <div class="subtitle">{esc(s["subjudul"])}</div>\n'
        slides_html += f"""        <div class="type-badge">{s['type']}</div>
      </div>
    </div>
"""

    dots_html = "\n".join(
        f'      <span class="dot {"active" if i==0 else ""}" data-slide="{i+1}"></span>'
        for i in range(len(slides))
    )

    font_family = ", ".join(FONTS)
    c = {k: SLIDE_STYLES[k] for k in ("cover", "content", "cta")}
    n_slides = len(slides)
    title = f"Carousel V3 — {n_slides} Slides" if mode == "json" else f"Carousel — {n_slides} Slides"

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
  *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: {font_family};
    background: #0a0a0f;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 20px;
  }}
  .carousel-container {{
    position: relative;
    width: 100%;
    max-width: 540px;
    aspect-ratio: 4 / 5;
    border-radius: 24px;
    overflow: hidden;
    box-shadow: 0 25px 60px rgba(0,0,0,0.5);
  }}
  .slides {{ width: 100%; height: 100%; position: relative; }}
  .slide {{
    position: absolute; top: 0; left: 0;
    width: 1080px; height: 1350px;
    transform: scale(0.5); transform-origin: 0 0;
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    padding: 10%;
    opacity: 0; visibility: hidden;
    transition: opacity 0.5s ease, visibility 0.5s ease;
    background-size: cover !important; background-position: center !important;
  }}
  .slide.active {{ opacity: 1; visibility: visible; }}
  .v3-slide {{ padding: 0; display: block; }}
  .card-slide .layer-frame,
  .card-slide .layer-front {{
    position: absolute; top: 0; left: 0;
    width: 1080px; height: 1350px;
  }}
  .card-slide .layer-frame {{ z-index: 1; }}
  .card-slide .layer-front {{ z-index: 2; }}
  .card-slide .judul-wrap {{
    position: absolute; top: 538px; left: 180px; width: 720px;
    z-index: 3; display: flex; justify-content: center;
  }}
  .card-slide .judul {{
    color: #000000; font-weight: 800; font-size: 54px;
    line-height: 1.25; text-align: center; padding: 36px 40px;
  }}
  .card-slide .subjudul {{
    position: absolute; top: 700px; left: 150px; width: 780px;
    z-index: 3; text-align: center; color: #1f2430;
    font-size: 30px; line-height: 1.5; font-weight: 400;
  }}
  .slide-content {{ text-align: center; max-width: 90%; }}
  .title {{
    font-size: clamp(1.4rem, 5vw, 2.8rem);
    font-weight: 800; line-height: 1.3;
    margin-bottom: 0.35em; letter-spacing: -0.01em;
  }}
  .subtitle {{
    font-size: clamp(0.85rem, 2.5vw, 1.3rem);
    font-weight: 400; line-height: 1.6; opacity: 0.9;
  }}
  .type-badge {{
    display: inline-block; margin-top: 12%;
    padding: 6px 18px; border-radius: 100px;
    font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.6;
  }}
  .slide-number {{
    position: absolute; top: 6%; right: 8%;
    font-size: 0.75rem; font-weight: 500; opacity: 0.5; letter-spacing: 0.05em;
  }}
  .controls {{
    position: absolute; bottom: 6%;
    left: 50%; transform: translateX(-50%);
    display: flex; align-items: center; gap: 16px; z-index: 10;
  }}
  .nav-btn {{
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.15); color: #fff;
    width: 40px; height: 40px; border-radius: 50%;
    cursor: pointer; font-size: 1.2rem;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.2s; backdrop-filter: blur(4px);
  }}
  .nav-btn:hover {{ background: rgba(255,255,255,0.25); }}
  .nav-btn:active {{ transform: scale(0.92); }}
  .dots {{ display: flex; gap: 6px; }}
  .dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: rgba(255,255,255,0.3); cursor: pointer; transition: all 0.3s;
  }}
  .dot.active {{ width: 24px; border-radius: 4px; background: rgba(255,255,255,0.85); }}

  .cover .title {{ color: {c['cover']['title_color']}; }}
  .cover .subtitle {{ color: {c['cover']['sub_color']}; }}
  .cover .type-badge {{ background: {c['cover']['accent']}22; color: {c['cover']['accent']}; }}
  .cover .slide-number {{ color: {c['cover']['title_color']}; }}
  .content .title {{ color: {c['content']['title_color']}; }}
  .content .subtitle {{ color: {c['content']['sub_color']}; }}
  .content .type-badge {{ background: {c['content']['accent']}22; color: {c['content']['accent']}; }}
  .content .slide-number {{ color: {c['content']['title_color']}; }}
  .cta .title {{ color: {c['cta']['title_color']}; }}
  .cta .subtitle {{ color: {c['cta']['sub_color']}; }}
  .cta .type-badge {{ background: {c['cta']['accent']}22; color: {c['cta']['accent']}; }}
  .cta .slide-number {{ color: {c['cta']['title_color']}; }}

  @media (max-width: 480px) {{
    .carousel-container {{ border-radius: 16px; }}
    .nav-btn {{ width: 32px; height: 32px; font-size: 1rem; }}
  }}

  /* ─── Tombol download ─── */
  .toolbar {{
    display: flex; gap: 8px;
    margin-top: 24px; flex-wrap: wrap; justify-content: center;
  }}
  .toolbar button {{
    font-family: {font_family};
    padding: 10px 20px; border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.08);
    color: #fff; font-size: 0.9rem; cursor: pointer;
    transition: background 0.2s; backdrop-filter: blur(4px);
    display: inline-flex; align-items: center; gap: 6px;
  }}
  .toolbar button:hover {{ background: rgba(255,255,255,0.18); }}
  .toolbar button:active {{ transform: scale(0.96); }}
  .toolbar .progress {{ font-size: 0.8rem; opacity: 0.6; align-self: center; margin-left: 8px; }}
  #exportStatus {{
    margin-top: 8px; font-size: 0.8rem; opacity: 0.6;
    font-family: {font_family};
  }}
</style>
</head>
<body>

<div class="carousel-container">
  <div class="slides">
{slides_html}  </div>
  <div class="controls">
    <button class="nav-btn" id="prevBtn" aria-label="Previous">&larr;</button>
    <div class="dots">
{dots_html}
    </div>
    <button class="nav-btn" id="nextBtn" aria-label="Next">&rarr;</button>
  </div>
</div>

<div class="toolbar">
  <button id="downloadBtn">&darr; Download All PNG</button>
  <span class="progress" id="progress"></span>
</div>
<div id="exportStatus"></div>

<script>
(function() {{
  window.addEventListener('error', function(e) {{
    var st = document.getElementById('exportStatus');
    if (st && e.message) st.textContent = 'Error: ' + e.message;
  }});

  const slides = document.querySelectorAll('.slide');
  const dots = document.querySelectorAll('.dot');
  let current = 0;

  function goTo(idx) {{
    if (idx < 0 || idx >= slides.length) return;
    slides.forEach(s => s.classList.remove('active'));
    dots.forEach(d => d.classList.remove('active'));
    slides[idx].classList.add('active');
    dots[idx].classList.add('active');
    current = idx;
  }}
  document.getElementById('prevBtn').addEventListener('click', () => goTo(current - 1 >= 0 ? current - 1 : slides.length - 1));
  document.getElementById('nextBtn').addEventListener('click', () => goTo(current + 1 < slides.length ? current + 1 : 0));
  dots.forEach((dot, i) => dot.addEventListener('click', () => goTo(i)));
  document.addEventListener('keydown', e => {{
    if (e.key === 'ArrowLeft') goTo(current - 1 >= 0 ? current - 1 : slides.length - 1);
    if (e.key === 'ArrowRight') goTo(current + 1 < slides.length ? current + 1 : 0);
  }});

  /* Slide dirender 1080x1350, di-scale biar muat preview */
  function fitSlides() {{
    const frame = document.querySelector('.carousel-container');
    const s = frame.clientWidth / 1080;
    document.querySelectorAll('.slide').forEach(sl => sl.style.transform = 'scale(' + s + ')');
  }}
  window.addEventListener('resize', fitSlides);
  fitSlides();

  /* Aturan jarak (Liya 2026-07-31): judul 1 baris → subjudul 700px; 2 baris → 768px.
     Fallback buat judul yang wrap otomatis jadi 2 baris di layar (judul asli 1 baris tapi panjang). */
  function fixSubPositions() {{
    document.querySelectorAll('.card-slide').forEach(sl => {{
      const j = sl.querySelector('.judul');
      const sub = sl.querySelector('.subjudul');
      if (!j || !sub) return;
      const jh = j.getBoundingClientRect().height;
      const lines = Math.round(jh / (parseFloat(getComputedStyle(j).fontSize) * 1.25));
      if (lines >= 2 && !sub.style.top) sub.style.top = '768px';
    }});
  }}
  window.addEventListener('load', fixSubPositions);
  setTimeout(fixSubPositions, 300);

  /* ─── Export PNG 1080x1350 (html2canvas, stabil lintas-browser) ─── */
  const prog = document.getElementById('progress');
  const status = document.getElementById('exportStatus');
  const downloadBtn = document.getElementById('downloadBtn');

  function sleep(ms) {{ return new Promise(r => setTimeout(r, ms)); }}

  downloadBtn.addEventListener('click', async () => {{
    if (typeof html2canvas === 'undefined') {{
      status.textContent = 'Gagal load library html2canvas (cek koneksi internet), coba refresh halaman.';
      return;
    }}

    const total = slides.length;
    prog.textContent = '0/' + total;
    status.textContent = '';
    downloadBtn.disabled = true;

    const originalActiveIndex = current;
    // Matikan transisi opacity supaya slide langsung kelihatan penuh saat difoto
    slides.forEach(s => {{ s.style.transition = 'none'; }});

    for (let i = 0; i < total; i++) {{
      const slide = slides[i];
      prog.textContent = (i + 1) + '/' + total;

      // Tampilkan slide ke-i secara penuh (tanpa scale preview) supaya html2canvas
      // menangkap ukuran asli 1080x1350
      slides.forEach(s => s.classList.remove('active'));
      slide.classList.add('active');
      const prevTransform = slide.style.transform;
      slide.style.transform = 'none';

      // Kasih waktu 1 frame biar browser selesai layout/paint sebelum di-screenshot
      await sleep(60);

      try {{
        const canvas = await html2canvas(slide, {{
          width: 1080,
          height: 1350,
          windowWidth: 1080,
          windowHeight: 1350,
          scale: 1,
          backgroundColor: null,
          useCORS: true,
          allowTaint: true,
          logging: false
        }});

        const link = document.createElement('a');
        link.download = 'slide_' + String(i + 1).padStart(2, '0') + '.png';
        link.href = canvas.toDataURL('image/png');
        document.body.appendChild(link);
        link.click();
        link.remove();

        // jeda kecil antar-download biar browser ga nge-block popup/download beruntun
        await sleep(250);
      }} catch (e) {{
        status.textContent = 'Error slide ' + (i + 1) + ': ' + e.message;
        console.error(e);
      }} finally {{
        slide.style.transform = prevTransform;
      }}
    }}

    // kembalikan tampilan seperti semula
    slides.forEach(s => {{ s.style.transition = ''; }});
    goTo(originalActiveIndex);
    fitSlides();

    downloadBtn.disabled = false;
    prog.textContent = 'Done!';
    status.textContent = total + ' PNG berhasil didownload (1080x1350).';
  }});
}})();
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Carousel HTML Renderer v3")
    parser.add_argument("--json", metavar="slides.json", nargs="?",
                        const="slides.json", default=None,
                        help="v3 mode: render dari JSON slide model (default: slides.json di cwd)")
    parser.add_argument("--online", action="store_true",
                        help="fetch arg --json sebagai URL (mis. pastebin raw)")
    args = parser.parse_args()

    print("=" * 48)
    print("  Carousel HTML Renderer + Export PNG")
    print("=" * 48)

    if not BAHAN.exists():
        print(f"\n❌ Folder BAHAN/ ga ditemukan")
        return 1
    RESULT.mkdir(exist_ok=True)

    if args.json:
        json_path = Path(args.json)
        if args.online:
            try:
                print(f"  ↓ fetch {json_path} …")
                req = urllib.request.Request(str(json_path), headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    raw = r.read().decode("utf-8")
                slides = json.loads(raw)
                mode = "json"
                print(f"  ✓ {len(slides['slides'] if isinstance(slides, dict) else slides)} slide (JSON online)")
            except Exception as e:
                print(f"\n❌ gagal fetch URL: {e}")
                return 1
        elif json_path.exists():
            slides = parse_json(json_path)
            mode = "json"
            print(f"  ✓ {len(slides)} slide terparsing (JSON v3)")
        else:
            print(f"\n❌ {json_path} ga ditemukan")
            return 1
        embedded = {}
    else:
        script_path = BAHAN / "script.txt"
        if not script_path.exists():
            print(f"\n❌ script.txt ga ditemukan")
            return 1
        slides = parse_script(script_path)
        mode = "script"
        print(f"  ✓ {len(slides)} slide terparsing (script.txt)")
        embedded = embed_bg_images()

    if not slides:
        print(f"\n❌ Gagal parse input")
        return 1

    html = generate_html(slides, embedded, mode)

    out_name = f"carousel_v3_{len(slides)}slides.html" if mode == "json" else f"carousel_{len(slides)}slides.html"
    out_path = RESULT / out_name
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  ✅ {out_name}")
    print(f"  📁 {RESULT.resolve()}/")

    return 0


if __name__ == "__main__":
    exit(main())
