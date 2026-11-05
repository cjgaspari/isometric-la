# Landmark snapshots (print flow)

Generate **high-resolution isometric artworks of individual Los Angeles landmarks** for print — not a seamless city-wide map.

Pipeline:

1. **Render** — orthographic Google Photorealistic 3D Tiles capture (`render.png`)
2. **Stylize** — isometric pixel-art generation at native **1K / 2K / 4K** (no upscaler)
3. **Export** — `generation.png` ready for print shop / further grade

## Quick start

```bash
# Deps
uv sync
cd src/web_render && bun install && cd ../..
uv run playwright install chromium

# Env (minimum for render + Gemini stylize)
cp .env.example .env
# set GOOGLE_TILES_API_KEY and GEMINI_API_KEY
```

```bash
# Hollywood Bowl @ 2K via Gemini
uv run landmark-snapshot landmarks/hollywoodwood_bowl.json --backend gemini

# Native 4K print
uv run landmark-snapshot landmarks/hollywoodwood_bowl.json --backend gemini --resolution 4k

# On-device stylize (Apple Silicon + mflux)
uv tool install mflux
uv run landmark-snapshot landmarks/hollywoodwood_bowl.json --backend local --resolution 2k

# Render only / re-stylize
uv run landmark-snapshot landmarks/hollywoodwood_bowl.json --render-only
uv run landmark-snapshot --job-dir exports/landmarks/hollywoodwood-bowl --skip-render --backend gemini
```

Outputs land in `exports/landmarks/<id>/`:

```text
view.json
landmark.json
render.png
generation.png
```

## Landmark JSON

See `landmarks/*.json`. Important fields:

| Field | Meaning |
| --- | --- |
| `lat` / `lon` | Landmark center |
| `size_meters` / `view_height_meters` | Framing |
| `print.resolution` | `1k` \| `2k` \| `4k` (native model size) |
| `print.aspect_ratio` | e.g. `1:1`, `16:9` |
| `style_reference` | Palette / style guide image |
| `prompt_extra` | Landmark-specific notes |

## Backends

| Backend | Where | Needs | Best for |
| --- | --- | --- | --- |
| **`local`** | On-device (Mac / MLX via **mflux**) | `mflux` on PATH | Privacy, no per-image API cost |
| **`gemini`** (default) | Cloud | `GEMINI_API_KEY` | Highest quality teacher/print today; native **4K** |
| **`grok`** | Cloud | `XAI_API_KEY` | Alternative cloud stylize; native up to **2K** |

### Recommended default

- **Mac laptop + Gemini** for the first print set (simplest, 2K/4K).
- Switch **`--backend local`** once mflux edit works well on your machine.
- Use **Grok** as an A/B cloud alternative, not as the only path.

You do **not** need a Mac Studio Ultra for this flow. Any recent Apple Silicon Mac is enough for local 1K–2K; cloud handles heavy stylize if preferred.

## Print sizing (300 DPI)

| `resolution` | ~square px | Approx. print @ 300 DPI |
| --- | --- | --- |
| `1k` | 1024 | ~3.4″ |
| `2k` | 2048 | ~6.8″ |
| `4k` | 4096 | ~13.6″ |

For larger physical prints, prefer **native 4K (Gemini)** over AI upscaling.

## vs city-wide map

This flow intentionally skips MultiDiffusion, LoRAs, and joint sampling. Each landmark is an independent artwork. For a seamless Los Angeles map, see `docs/generation_approaches.md` and `docs/local_mac_setup.md` on the investigation branches.
