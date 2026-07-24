# AI Carousel Generator

Agentic pipeline: **topik → LM Studio (local) → outline JSON → Pillow render → carousel_final.png**

## Cara Pakai

```bash
# 1. Install
pip install -r requirements.txt

# 2. Siapin template Canva di folder templates/
#    - templates/cover.png    (1080x1080)
#    - templates/content.png  (1080x1080)
#    - templates/cta.png      (1080x1080)
#
#    Kalo belum ada script auto bikin placeholder.

# 3. Jalanin
python carousel_generator.py "5 Tips Public Speaking"

# 4. Output di output/carousel_final.png
```

## Argumen

| Arg | Default | Fungsi |
|-----|---------|--------|
| `topic` | (required) | Topik carousel |
| `--model` | `gemma-2-9b-it` | Nama model di LM Studio |
| `--url` | `http://127.0.0.1:1234/v1/chat/completions` | LM Studio API URL |

## Struktur

```
├── carousel_generator.py   # Main
├── requirements.txt
├── templates/              # Template Canva (bikin sendiri)
│   ├── cover.png
│   ├── content.png
│   └── cta.png
└── output/                 # Hasil generate
    └── carousel_final.png
```

## Tech

- **LLM**: LM Studio (local, OpenAI-compatible API)
- **Render**: Python Pillow
- **Output**: PNG 1080x1080 per slide, digabung vertikal
