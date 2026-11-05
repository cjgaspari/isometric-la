# Generation Approaches for Isometric Los Angeles

Investigation of how **Isometric NYC**, **Tiny London**, and **Isometric Toronto** produce city-scale isometric maps, what we should reuse from this repo, and what newer options look like — including Cursor/Grok-centered paths and alternatives beyond the London/Toronto stack.

Sources:

- [How he built isometric.nyc](https://cannoneyed.com/projects/isometric-nyc) (Andy Coenen)
- [Drawing all of London as one image](https://tiny.london/how/) (Boris Starkov)
- [How Isometric Toronto was made](https://iso.sloptoronto.ca/how) (John Fewell)
- [tiny-london-lora on Hugging Face](https://huggingface.co/ktoyame/tiny-london-lora)
- xAI [Grok Imagine](https://docs.x.ai/developers/model-capabilities/images/generation) docs; fal FLUX LoRA trainers

---

## Executive takeaway

| Approach | Best for | Seam risk | Approx. paid cost (published) | Fits Cursor/Grok-only? |
| --- | --- | --- | --- | --- |
| **NYC-style tiled infill** (this repo) | Prototyping Hollywood Bowl / small districts | High without heavy repair | Gemini API only | Partial — coding yes; image model is Gemini/Oxen today |
| **London/Toronto pipeline** (teacher → LoRA → joint MultiDiffusion) | City-scale seamless map | Near-zero by construction | Toronto ~$92; London ~70 H100-hrs experiments | Coding/orchestration yes; sampling needs local/cloud GPU |
| **Grok Imagine as teacher or tile artist** | Cheap style pilots; maybe teacher set | High if tiled; unknown as teacher quality | ~$0.04/image gen | Yes for image calls + agent orchestration |
| **Hosted FLUX LoRA (fal etc.)** | Faster LoRA experiments without RunPod ops | Still need joint sampler for city scale | Train ~$2–12; cheap per image | Yes via APIs; agent can drive training jobs |

**Recommendation for Los Angeles:** keep this repo’s renderer/viewer, but treat **London/Toronto’s joint-sampling LoRA path** as the production target. Use **Cursor agents** to build the pipeline. Use **Grok Imagine and/or Gemini** only as *teachers* (and for early style pilots), not as the city-scale sampler. Plan for one H100-class training run and a MultiDiffusion (or equivalent tiled-diffusion) inference stage.

---

## Lineage

```
Isometric NYC (Coenen)
  └─ tile-by-tile generation + neighbor infill + Oxen/Modal LoRA
       └─ Tiny London (Starkov)
            ├─ same orthographic Google 3D Tiles renderer idea
            ├─ Gemini teacher + automatic QA (no hand labels)
            ├─ Qwen-Image-2.1-Turbo LoRA
            └─ MultiDiffusion / joint latent (no seams)
                 └─ Isometric Toronto (Fewell)
                      └─ same method, cheaper (~$92), laptop inference for core
```

London and Toronto did **not** invent a new art style pipeline from scratch; they fixed NYC’s hard problems: **seam formation**, **consistency**, and **hand labeling cost**.

---

## 1. Isometric NYC (this repo’s heritage)

### Pipeline

1. Orthographic / isometric render of Google Photorealistic 3D Tiles (and earlier whitebox/CityDB paths).
2. Fine-tune / use an image-edit model (Oxen LoRA, Modal Qwen edit, Nano Banana / Gemini) on ~40 style pairs.
3. Generate **one tile (or 2×2 / strip) at a time**, feeding finished neighbors as context (“infill”).
4. Heavy app tooling for queueing, water masks, bounds, DZI/PMTiles export, postprocess.

### Strengths

- Rich open tooling already in this repo (viewer, bounds, generation app, export).
- Good for **interactive** generation and small areas (e.g. Hollywood Bowl pilot).
- Coding-agent friendly; most of this codebase was agent-written.

### Failure modes (called out by London)

- Prompted / per-tile models act like a **slightly different artist every tile**.
- ~1/3 of tile boundaries still showed semantic seams even with neighbor context and checks.
- Hand repair does not scale to Greater London–sized areas (Los Angeles County is larger still).

### Where this leaves us

Ideal for **bootstrap**: get a Hollywood Bowl `render.png` → Gemini/Grok stylization → validate camera/style. Not ideal as the final city-wide sampler.

---

## 2. Tiny London — the modern baseline

### Rules Starkov set

1. No seams, by construction (not repair).
2. No hand-labelled training data.
3. Close to zero $ cost (relative to naive approaches).

### Pipeline (condensed)

| Step | What |
| --- | --- |
| **Camera** | One orthographic camera; 3,570 pixel-registered 2048² shots from Google 3D Tiles |
| **Teacher** | Gemini 3 Pro Image redraws ~2,500 frames as pixel art |
| **QA** | Automatic checks vs render + OpenStreetMap; ~31% of attempts rejected |
| **Train** | Rank-32 LoRA on Qwen-Image-2.1-Turbo (~6.3k examples, ~4h on H100) |
| **Sample** | Whole city as **one latent**; overlapping 1024 windows (MultiDiffusion); pin finished blocks (RePaint) |
| **Repair** | OSM finds invented water landmarks; local redraw without cutting a seam |
| **Serve** | OpenSeadragon + DZI/WebP on R2 |

Published LoRA: [`ktoyame/tiny-london-lora`](https://huggingface.co/ktoyame/tiny-london-lora) (Qwen Research License — **non-commercial** constraints on the base Turbo weights).

### Key technical insights

- **Seams are a sampling problem**, not a “need more training data” problem.
- Teacher prompt should describe **drawing technique**, not nouns of objects (nouns hallucinate).
- Red 2 px border + Coenen-style infill prompt retained for edit-mode LoRA.
- Joint sampling with pinned blocks grows the map outward without stitch lines.

### Scale numbers (Greater London)

- ~1,591 km² → ~14B pixels inside the city outline
- Final sampling run ~31 GPU-hours; ~70 H100-hours across all experiments

---

## 3. Isometric Toronto — same method, cheaper

Fewell explicitly followed Tiny London.

| Item | Toronto published figures |
| --- | --- |
| Teacher | Gemini 3 Pro Image (Batch API for half price) |
| Student | Qwen-Image-2.1-Turbo, rank-32 LoRA (ai-toolkit / RunPod H100) |
| Training set | **~344 accepted pairs** (not thousands) — enough when pixel-registered |
| Core generation | Whole downtown as one latent on a **laptop** (M5 Pro, mflux, 8 steps) |
| Total paid | **~$91.97** (Gemini ~$58 + RunPod ~$34) |
| Extra polish | Zoom fade into hard pixel-art layer; live traffic sprites from OSM + city data |

### Lessons especially relevant to Los Angeles

1. **Get the camera right first** — registered pairs beat clever training.
2. A few hundred clean teacher pairs can beat thousands of dirty ones.
3. **Pick earlier checkpoints** — later steps can overfit (greens drifted).
4. Spend budget on the **sampler**, not endless LoRA steps, if the pain is consistency.
5. Hard dollar caps on Gemini + prepaid GPU credit prevent runaway spend.

---

## 4. Cursor / Grok-centered options

“Using just Cursor/Grok” splits into two roles:

### A. Cursor as the build agent (strong fit)

Cursor (Composer/cloud agents) already matches how NYC/London/Toronto were engineered: orchestrate renderer, dataset QA, training jobs, inference, viewer. For Los Angeles we can use agents to:

- Drive Google 3D Tiles frustum sweeps for LA bounds
- Run teacher jobs + automatic QA (render alignment, water polygons, invented buildings)
- Train LoRA via RunPod / fal / Modal scripts
- Implement MultiDiffusion / tiled diffusion sampler
- Export DZI and ship the existing `src/app` viewer

This does **not** require inventing a new product — it is packaging the London/Toronto method for LA.

### B. Grok Imagine as the image model (partial fit)

xAI **Grok Imagine** (`grok-imagine-image-2.0`) today:

- Text-to-image and **image edit** with up to **5 reference images**
- ~$0.04 / image; 1k/2k resolution
- **No public LoRA / fine-tune API** (as of docs reviewed for this note)

| Use of Grok | Verdict |
| --- | --- |
| Style pilots / “does Hollywood Bowl look good in style X?” | Good |
| Teacher model replacing Gemini for training pairs | **Worth A/B testing** — measure reject rate vs Gemini with the same QA |
| City-scale tile-by-tile generation | Same seam failure mode as NYC attempt #1 |
| Drop-in replacement for Qwen LoRA + MultiDiffusion | **No** — no fine-tune + no joint sampler |

**Practical Cursor+Grok path:** agent-written pipeline where Grok (and/or Gemini) produces teacher pairs; a separate open model (Qwen-Image / FLUX) gets the LoRA; GPU job does joint sampling. Grok is not the whole stack.

---

## 5. Approaches beyond London / Toronto

Ideas that are *related* but not what they shipped:

### 5.1 Hosted LoRA trainers (fal FLUX, etc.)

- Train style LoRAs in a few dollars without babysitting RunPod.
- FLUX edit LoRAs can learn “render → illustration” if pairs are clean.
- Still need a **large-canvas sampler** (MultiDiffusion / ComfyUI Tiled Diffusion / custom) for seam-free city maps.
- Good for **fast style iteration** before committing to Qwen-Turbo parity with London.

### 5.2 ComfyUI Tiled Diffusion / MultiDiffusion forks

- Community nodes already support MultiDiffusion-style large canvases and some Qwen-Image-Edit paths.
- Useful if we want a GUI for experiments; production LA should still be a scripted sampler with checkpoints (London’s resume-friendly blocks).

### 5.3 ControlNet / depth / canny conditioned generation

- Feed depth or edge maps from the 3D render so geometry is locked harder than edit-only LoRAs.
- London/Toronto mostly relied on **edit-mode pairs** that already aligned; ControlNet is an alternative if teacher fidelity is weak.
- Extra training/infra complexity — try only if registered edit pairs underperform on LA sprawl (freeways, low-rise).

### 5.4 Reuse London LoRA zero-shot on Los Angeles

- Published LoRA is London-trained; author notes it was **not tested on other cities**.
- Worth a **cheap smoke test** on Hollywood Bowl / downtown LA renders before training an LA LoRA.
- License: Qwen Research License may restrict commercial use — check before shipping a product.

### 5.5 Procedural / OSM-first dioramas (non-diffusion)

- Projects on [isometriccities.com](https://isometriccities.com/) include non-AI maps built from OSM / real-time 3D.
- Different aesthetic; useful as a **fallback layer** or for traffic/land-use overlays (Toronto’s live streetcars are a good example of hybrid).

### 5.6 Progressive pixelation on zoom (Toronto)

- Independent of the generator: at high zoom, fade to a global palette + ordered dither.
- Cheap CPU postprocess; improves “SimCity” feel when diffusion edges look mushy.
- Easy win to add to this repo’s viewer regardless of generator choice.

### 5.7 Region-specialized LoRAs

- LA is not London: freeways, parking lots, wildfire hills, ports, grid + canyon topography.
- Train **core + valley + coastal** teacher subsets (Toronto balanced towers vs parks/water).
- Optional second LoRA for signage (Toronto v2) if we care about readable Hollywood / Santa Monica signs.

---

## 6. Suggested Los Angeles roadmap

### Phase 0 — Prove the camera (this week’s hardware)

1. Add API keys (`GOOGLE_TILES_API_KEY`, teacher key).
2. Render Hollywood Bowl (and a downtown strip) with the existing `web_render` path.
3. Stylize a handful of frames with Gemini and/or Grok; compare fidelity under automatic checks.

### Phase 1 — Teacher set for LA

1. Sweep a modest bbox (e.g. Hollywood → Downtown → Santa Monica corridor) with one orthographic camera.
2. Teacher redraw + QA against render, LA water polygons (Geohub / County), building footprints.
3. Target **a few hundred** clean pairs first (Toronto-scale), not London-scale.

### Phase 2 — Student LoRA

1. Train rank-32 LoRA on Qwen-Image-2.1-Turbo (ai-toolkit) **or** parallel fal FLUX edit LoRA for speed comparison.
2. Hold out frames; pick checkpoint by eye + metrics (not last step).

### Phase 3 — Joint sampling

1. Implement MultiDiffusion-style joint denoise with pinned blocks (port ideas from London’s `joint/sampler.py` description).
2. Generate downtown LA as one latent; only then expand boroughs/regions.
3. OSM/Geohub repair pass for water hallucinations.

### Phase 4 — Productize

1. DZI/WebP → existing `src/app` viewer.
2. Optional Toronto-style pixel layer + clickable buildings from Assessor/Geohub IDs.
3. License review (Google 3D Tiles ToS, Qwen Research License, Cesium ion plan).

---

## 7. What we still need operationally

| Dependency | Role |
| --- | --- |
| Google Photorealistic 3D Tiles API key | Renders |
| Gemini and/or Grok Imagine API key | Teacher / pilots |
| GPU (RunPod / Modal / GCP H100) | LoRA train + joint sample |
| LA open data (water, buildings) | Automatic QA + repairs |
| Bun + Playwright | Existing web renderer |

This investigation does not change generation code yet; it is the decision record for the next implementation branch.

---

## References (primary)

1. Andy Coenen — [isometric.nyc writeup](https://cannoneyed.com/projects/isometric-nyc) · [github.com/cannoneyed/isometric-nyc](https://github.com/cannoneyed/isometric-nyc)
2. Boris Starkov — [tiny.london/how](https://tiny.london/how/) · [HF LoRA](https://huggingface.co/ktoyame/tiny-london-lora)
3. John Fewell — [iso.sloptoronto.ca/how](https://iso.sloptoronto.ca/how)
4. Bar-Tal et al. — MultiDiffusion (2023)
5. xAI — [Grok Imagine image generation](https://docs.x.ai/developers/model-capabilities/images/generation)
