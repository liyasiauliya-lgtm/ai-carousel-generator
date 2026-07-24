# Carousel Renderer

Template-based carousel generator. Baca BAHAN/script.txt → render teks di template → output ke RESULT/

## Cara Pakai

### 1. Siapin folder BAHAN/

```
BAHAN/
├── cover.png        ← template background 1080x1080
├── content.png      ← template background 1080x1080
├── cta.png          ← template background 1080x1080
├── font.ttf         ← font yg dipake (opsional, kalo ga ada fallback ke Arial)
└── script.txt       ← isi konten
```

### 2. Format script.txt

```
1 COVER_5 Tips Public Speaking
2 CONTENT_Tips pertama: kontak mata dengan audiens
3 CONTENT_Tips kedua: suara jelas dan intonasi
4 CTA_Simpan postingan ini buat latihan!
```

- `NUMBER` — urutan slide
- `TYPE` — `COVER` / `CONTENT` / `CTA`
- `_` — separator
- `text` — isi konten, auto-word-wrap, auto-scale font biar muat

Template untuk slide CONTENT dipake terus kalo ada lebih dari 1.

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

## Catatan

- Font **auto-scale** — panjang teks → font mengecil biar selalu muat di area
- Posisi teks **center** horizontal & vertikal di dalam bounding box tiap tipe
- Teks pake **stroke hitam + fill putih** biar kebaca di background apapun
- Ga perlu koneksi internet, ga perlu LLM, murni Python lokal
