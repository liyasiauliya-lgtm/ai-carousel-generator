# Carousel Renderer v2

Template-based carousel generator. **Judul bold gede** + **Subjudul normal kecil** — auto-center, auto-scale.

## Cara Pakai

### 1. Isi folder BAHAN/

```
BAHAN/
├── cover.png        ← template background 1080x1080
├── content.png      ← template background 1080x1080
├── cta.png          ← template background 1080x1080
├── font.ttf         ← font (opsional, fallback Arial)
└── script.txt       ← isi konten
```

### 2. Format script.txt

```
1 COVER_JUDUL:5 Tips Public Speaking_SUBJUDUL:Pemula pun pasti bisa!
2 CONTENT_JUDUL:Kontak Mata_SUBJUDUL:Tatap audiens bergantian biar feel connected
3 CONTENT_JUDUL:Intonasi Suara_SUBJUDUL:Jangan monoton, naik-turunin kayak ngobrol
4 CTA_JUDUL:Follow for more!_SUBJUDUL:Simpan buat latihan tiap hari
```

- `TYPE` → `COVER` / `CONTENT` / `CTA`
- `JUDUL:` → teks bold, lebih gede, auto-scale
- `SUBJUDUL:` → teks normal, lebih kecil
- Kalo cuma `JUDUL:` doang (ga ada `SUBJUDUL`), judul aja
- Kalo ga pake format `JUDUL:`/`SUBJUDUL:` sama sekali, seluruh teks jadi judul

### 3. Jalankan

**Windows:** double-click `render.bat`  
**Terminal:** `python carousel_render.py`

### 4. Hasil

```
RESULT/
├── 01_cover.png
├── 02_content.png
├── 03_content.png
└── 04_cta.png
```

## Bounding box teks (bisa lo tweak di script)

| Tipe | Area (x, y, w, h) |
|------|-------------------|
| cover | 60, 300, 960, 480 |
| content | 60, 250, 960, 580 |
| cta | 60, 350, 960, 380 |

## Style teks

Edit 3 baris di bagian atas `carousel_render.py`:

```python
TEXT_FILL = "black"       # warna teks: white / black / #FF5733 / dll
STROKE_WIDTH = 0          # 0=tanpa stroke, 2=stroke tipis, 4=stroke tebel
STROKE_FILL = "white"     # warna stroke (kalo STROKE_WIDTH > 0)
```

| Background | `TEXT_FILL` | `STROKE_WIDTH` | `STROKE_FILL` |
|------------|-------------|----------------|---------------|
| Terang (putih/pastel) | `"black"` | 0 | `"white"` |
| Gelap (item/pekat) | `"white"` | 2 | `"black"` |
| Ramai/penuh warna | `"white"` | 4 | `"black"` |
| Custom color | `"#FF5733"` | 0 | `"white"` |

**Font auto-scale** — ukuran ngecil otomatis kalo teks panjang, biar selalu muat di bounding box.
**Pixel-perfect** — tiap jalan hasilnya persis sama.
