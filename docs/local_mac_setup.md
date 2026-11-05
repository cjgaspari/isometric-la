# Local Mac Spec — Isometric Los Angeles (prefer on-device)

Opinionated build for running the London/Toronto-style pipeline on Apple Silicon, with as much as possible **on-device**. This is what I would buy / use if the constraint is “any Mac available now” and “local models if possible.”

---

## Honest boundaries

| Stage | Fully on-device models? | Still needs network? |
| --- | --- | --- |
| 3D isometric **renders** | Yes (browser/Playwright on Mac) | **Yes** — Google Photorealistic 3D Tiles API |
| **Teacher** stylization | Possible with local edit models; quality usually below Gemini | Optional if local teacher |
| **LoRA training** | Yes on a high-RAM Studio (MPS) | Hugging Face weight download once |
| **Joint / MultiDiffusion sampling** | Yes (mflux / MLX) — Toronto proved downtown on a laptop | No after weights are local |
| **Viewer / DZI** | Yes | No |

You can eliminate cloud **GPUs** and cloud **image APIs**. You cannot eliminate Google’s tile CDN unless you switch to a fully open 3D source (OSM + terrain + footprints) with a different look.

---

## Hardware I would pick

### Primary machine (buy / use this)

**Mac Studio, Apple M3 Ultra or M4 Ultra, 192 GB unified memory (256 GB if the budget allows), ≥2 TB SSD.**

| Why this SKU | Reason |
| --- | --- |
| **Studio over MacBook** | Sustained GPU hours for joint sampling + training; better thermals; desk-bound project |
| **Ultra over Max** | More GPU cores + memory controllers; joint sampling is bandwidth-heavy |
| **192–256 GB RAM** | Qwen-Image / Qwen-Image-2.1 edit + LoRA train in fp32 on MPS is tight; 256 GB is the only config publicly confirmed for Qwen Image LoRA training. 192 GB is the practical “try train locally” floor; 128 GB is inference-first |
| **≥2 TB SSD** | Base weights (Qwen ~20–40 GB depending on quant), renders, teacher pairs, latents, DZI pyramids, multiple LoRA checkpoints |

**Secondary / cheaper acceptable:** MacBook Pro **M4 Max 128 GB** (or M5 Pro/Max **48–64 GB** like Toronto’s laptop) — excellent for **inference** and small-bbox joint maps; **not** what I’d trust for comfortable local LoRA training of the full edit stack.

### What I would *not* use as the only machine

- Any Mac with **≤36 GB** usable Metal working set for this pipeline (many 48 GB machines only expose ~32 GB safely to GPU).
- Intel Macs.
- Relying on a cloud “Modal” GPU while calling it local — different product.

### Accessories

- External **4 TB** SSD (Thunderbolt) for `generations/`, render caches, DZI exports.
- Gigabit+ Ethernet (Studio) — tile downloads and weight pulls are large.
- Leave **headroom**: quit browsers/IDEs during train/sample jobs; macOS + Chrome will fight you for unified memory.

---

## Software stack (local)

```text
macOS 15+
uv (Python 3.12)
bun + Playwright (Chromium)     # web_render / Google 3D Tiles
mflux (MLX)                     # Qwen-Image-2.1 (+ LoRA) inference
PyTorch 2.10+ MPS               # LoRA training only (fp32)
this repo (isometric-los-angeles)
optional: ComfyUI (MPS)         # edit experiments if mflux edit path lags
```

### Env keys still required (even “local”)

```bash
GOOGLE_TILES_API_KEY=...          # renders
# optional if you keep a cloud teacher for A/B:
# GEMINI_API_KEY=...
# XAI_API_KEY=...                 # Grok Imagine teacher A/B
```

No RunPod / Modal / fal required for the path below.

---

## On-device pipeline (exact shape)

### Phase A — Renders (local compute, remote tiles)

1. Install repo deps: `uv sync`, `bun` in `src/web_render` and `src/app`.
2. Set `VITE_GOOGLE_TILES_API_KEY`.
3. Drive one **orthographic** camera over an LA bbox (start: Hollywood Bowl → Downtown corridor).
4. Export pixel-registered 1024² or 2048² `render.png` shots (same frustum-offset discipline as London).

**Machine load:** light CPU/GPU; network-bound.

### Phase B — Teacher set (prefer local; cloud optional)

**Default (all-local):** use **Qwen-Image-Edit** / **Qwen-Image-2.1 edit** on-device (mflux or ComfyUI MPS) with:

- Input = render (+ optional red outline, Coenen/London prompt DNA)
- Output = isometric illustration target
- **Automatic QA** (keep London/Toronto discipline): reject shifts, invented water, invented buildings vs Geohub water/footprints

**Reality check:** local teachers will have a **higher reject rate** than Gemini 3 Pro Image. Budget 2–3× attempts per accepted pair. That is still fine for a Hollywood / downtown pilot (tens to low hundreds of pairs).

**Optional hybrid:** Gemini or Grok Imagine only for the teacher set (~$40–80 at Toronto scale), then everything else local. Fastest path to a clean LoRA if quality matters more than purity.

### Phase C — LoRA train (on-device)

**Target model:** Qwen-Image-2.1-Turbo or Qwen-Image-Edit (match whatever you will sample with).

**Trainer:** Hugging Face Diffusers DreamBooth/LoRA script on **MPS**, with:

```bash
--mixed_precision="no"    # fp32 required on MPS; fp16 → NaN
--offload
--cache_latents
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

**Config I’d start with (Toronto-shaped):**

| Knob | Value |
| --- | --- |
| Pairs | 300–500 accepted |
| Rank | 32 |
| Steps | 3,000–5,000 (save every 500; pick early checkpoint) |
| Resolution | 512–1024 |
| Batch | 1 |

**Expect:** multi-hour to overnight on Ultra 192/256 GB; much slower than one H100 (~4 h). Worth it if the goal is zero rented GPU.

**If training OOMs on 128 GB:** drop to 512 px, aggressive offload, or train a **FLUX.2 Klein edit LoRA** (smaller) for a pilot style, then revisit Qwen on a bigger Studio.

### Phase D — Joint sampling (on-device) — the important part

This is where Toronto’s laptop win matters.

1. Implement / port a **MultiDiffusion-style** loop over one shared latent (overlapping 1024 windows, tent weights, pinned finished blocks).
2. Run inference with **mflux** + your LoRA on Qwen-Image-2.1 (8-step turbo path if available).
3. Start with a **small canvas** (Hollywood Bowl + surrounding hills), then grow pinned blocks toward downtown.

**RAM guidance:**

| Unified memory | Practical joint-map size |
| --- | --- |
| 48–64 GB | District / downtown core (Toronto-class) |
| 128 GB | Multi-district LA corridor |
| 192–256 GB | Comfortable block growth + fewer swaps |

**Disk:** write block checkpoints often (London’s VM-restart lesson applies to sleep/lid-close too — use `caffeinate` / prevent sleep).

### Phase E — Post + viewer (local)

1. Palette / ordered-dither **pixel zoom layer** (Toronto trick) — CPU, cheap.
2. `export_dzi` → `src/app` with `MAP_ID=... bun run dev`.
3. Optional OSM/Geohub repair pass for water hallucinations.

---

## Recommended “buy this” SKU (one line)

> **Mac Studio M4 Ultra (or M3 Ultra), 256 GB unified memory, 2 TB SSD**  
> — primary for train + sample.  
> Optional: keep a **128 GB M4 Max laptop** as a satellite for renders/QA while the Studio trains.

If choosing **one** machine under a tighter budget:

> **Mac Studio M4 Max, 128 GB, 2 TB** — strong for inference + small joint maps; treat LoRA train as “try, else one short cloud train.”

---

## Week-1 local checklist (Hollywood Bowl)

1. Studio (or Max) with ≥128 GB free after OS.
2. `uv sync` + `bun` + Playwright browsers.
3. Google Tiles key working → one Bowl `render.png`.
4. Local Qwen edit → 10 stylized frames; wire reject metrics.
5. Smoke-train LoRA 500 steps on those frames (proves MPS path).
6. Single-window then 2×2 joint denoise with the LoRA in mflux.
7. Only then expand the bbox.

---

## What “100% local models” forces you to accept

- Weaker / noisier **teacher** than Gemini unless you invest more reject/retry compute.
- **Slower LoRA train** than RunPod H100 (but free and private).
- Google **tiles** still leave the building.
- Joint sampling of **all of LA County** on one Mac is a multi-day (or multi-week) job — same strategy as Toronto: finish a core, then grow blocks.

That is still the right architecture: **local Ultra Studio as the factory**, Cursor as the orchestrator, cloud teachers only if the local teacher reject rate is intolerable.
