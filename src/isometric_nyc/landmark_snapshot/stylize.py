"""Stylize a landmark render into isometric artwork (local or cloud)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

from isometric_nyc.landmark_snapshot.config import LandmarkConfig
from isometric_nyc.landmark_snapshot.prompts import landmark_style_prompt

GEMINI_MODEL = "gemini-3-pro-image-preview"
GROK_MODEL = "grok-imagine-image-2.0"
GROK_API_BASE = "https://api.x.ai/v1"


def _image_size_label(resolution: str) -> str:
  return resolution.upper()  # 1k -> 1K for Gemini ImageConfig


def stylize_landmark(
  config: LandmarkConfig,
  job_dir: Path,
  *,
  backend: str = "gemini",
  references_dir: Path | None = None,
) -> Path:
  """
  Produce generation.png in job_dir from render.png.

  Backends:
    - gemini: Google Gemini image (cloud; best quality today)
    - grok: xAI Grok Imagine edit (cloud alternative)
    - local: mflux Qwen-Image-2.1 edit on Apple Silicon (on-device)
  """
  load_dotenv()
  render_path = job_dir / "render.png"
  if not render_path.exists():
    raise FileNotFoundError(f"Missing render: {render_path}")

  style_path = Path(config.style_reference)
  if not style_path.is_absolute():
    style_path = Path.cwd() / style_path
  if references_dir is not None and not style_path.exists():
    alt = references_dir / Path(config.style_reference).name
    if alt.exists():
      style_path = alt

  prompt = landmark_style_prompt(
    landmark_name=config.name,
    prompt_extra=config.prompt_extra,
    special_instructions=config.special_instructions,
  )
  out_path = job_dir / "generation.png"

  if backend == "gemini":
    return _stylize_gemini(config, render_path, style_path, prompt, out_path)
  if backend == "grok":
    return _stylize_grok(config, render_path, style_path, prompt, out_path)
  if backend == "local":
    return _stylize_local_mflux(config, render_path, style_path, prompt, out_path)
  raise ValueError(f"Unknown backend {backend!r}; use local|gemini|grok")


def _stylize_gemini(
  config: LandmarkConfig,
  render_path: Path,
  style_path: Path,
  prompt: str,
  out_path: Path,
) -> Path:
  from google import genai
  from google.genai import types

  api_key = os.getenv("GEMINI_API_KEY")
  if not api_key:
    raise ValueError("GEMINI_API_KEY is required for backend=gemini")

  client = genai.Client(api_key=api_key)
  width, height = config.print.pixels()
  # Prefer configured print aspect; fall back to measured render.
  aspect = config.print.aspect_ratio

  contents: list[object] = [
    prompt,
    "Primary reference — isometric 3D render (preserve structure):",
    Image.open(render_path),
  ]
  if style_path.exists():
    contents.extend(
      [
        "Style reference — match palette and pixel-art language:",
        Image.open(style_path),
      ]
    )

  print(
    f"🎨 Gemini stylize ({GEMINI_MODEL}, {config.print.resolution}/"
    f"{aspect}, {width}x{height})..."
  )
  response = client.models.generate_content(
    model=GEMINI_MODEL,
    contents=contents,
    config=types.GenerateContentConfig(
      response_modalities=["TEXT", "IMAGE"],
      image_config=types.ImageConfig(
        aspect_ratio=aspect,
        image_size=_image_size_label(config.print.resolution),
      ),
    ),
  )

  saved = False
  for part in response.parts:
    if part.text:
      print(part.text)
    elif image := part.as_image():
      image.save(str(out_path))
      saved = True
  if not saved:
    raise RuntimeError("Gemini returned no image")
  print(f"✅ Generation saved: {out_path}")
  return out_path


def _stylize_grok(
  config: LandmarkConfig,
  render_path: Path,
  style_path: Path,
  prompt: str,
  out_path: Path,
) -> Path:
  """
  Cloud alternative via xAI Images API (edit with reference images).

  Requires XAI_API_KEY. Native sizes are 1k/2k — 4k falls back to 2k with a warning.
  """
  import base64

  import requests

  api_key = os.getenv("XAI_API_KEY")
  if not api_key:
    raise ValueError("XAI_API_KEY is required for backend=grok")

  resolution = config.print.resolution
  if resolution == "4k":
    print("⚠️  Grok Imagine supports up to 2k; using 2k instead of 4k")
    resolution = "2k"

  def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")

  images = [{"url": f"data:image/png;base64,{_b64(render_path)}"}]
  if style_path.exists():
    images.append({"url": f"data:image/png;base64,{_b64(style_path)}"})

  payload: dict[str, object] = {
    "model": GROK_MODEL,
    "prompt": prompt,
    "resolution": resolution,
    "images": images,
  }

  print(f"🎨 Grok stylize ({GROK_MODEL}, {resolution})...")
  headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
  }
  resp = requests.post(
    f"{GROK_API_BASE}/images/edits",
    headers=headers,
    json=payload,
    timeout=300,
  )
  if resp.status_code >= 400:
    # Fallback for API shape drift: single image_url generation.
    resp = requests.post(
      f"{GROK_API_BASE}/images/generations",
      headers=headers,
      json={
        "model": GROK_MODEL,
        "prompt": prompt,
        "resolution": resolution,
        "image_url": f"data:image/png;base64,{_b64(render_path)}",
      },
      timeout=300,
    )
  resp.raise_for_status()
  body = resp.json()
  data_list = body.get("data") or []
  if not data_list:
    raise RuntimeError(f"Grok returned no image data: {body}")
  item = data_list[0]
  if item.get("b64_json"):
    out_path.write_bytes(base64.b64decode(item["b64_json"]))
  elif item.get("url"):
    img = requests.get(item["url"], timeout=120)
    img.raise_for_status()
    out_path.write_bytes(img.content)
  else:
    raise RuntimeError(f"Unrecognized Grok image payload: {item}")
  print(f"✅ Generation saved: {out_path}")
  return out_path


def _stylize_local_mflux(
  config: LandmarkConfig,
  render_path: Path,
  style_path: Path,
  prompt: str,
  out_path: Path,
) -> Path:
  """
  On-device Apple Silicon path via mflux CLI if installed.

  Tries common edit entrypoints; fails with install instructions if missing.
  """
  width, height = config.print.pixels()
  candidates = [
    "mflux-generate-qwen-2.1-edit",
    "mflux-generate-qwen-edit",
    "mflux-generate-flux2-edit",
  ]
  cmd_name = next((c for c in candidates if shutil.which(c)), None)
  if cmd_name is None:
    raise RuntimeError(
      "Local backend requires mflux on PATH (Apple Silicon / MLX).\n"
      "  Install: uv tool install mflux\n"
      "  Then retry with --backend local\n"
      "Or use --backend gemini / --backend grok for cloud stylization."
    )

  # mflux CLIs differ slightly; use a conservative common flag set and
  # fall back to copying a documented manual command on failure.
  cmd = [
    cmd_name,
    "--prompt",
    prompt,
    "--image-path",
    str(render_path),
    "--width",
    str(width),
    "--height",
    str(min(height, width)),  # many edit paths prefer square
    "--steps",
    "8",
    "--output",
    str(out_path),
  ]
  if style_path.exists():
    # Not all builds accept a second ref; include when supported via env note.
    cmd.extend(["--ref-image-path", str(style_path)])

  print(f"🎨 Local mflux stylize ({cmd_name}, {width}x{height})...")
  try:
    subprocess.run(cmd, check=True)
  except subprocess.CalledProcessError:
    # Retry without optional ref flag.
    cmd = [c for c in cmd if c != "--ref-image-path" and c != str(style_path)]
    # Rebuild without ref pair cleanly:
    cmd = [
      cmd_name,
      "--prompt",
      prompt,
      "--image-path",
      str(render_path),
      "--width",
      str(width),
      "--height",
      str(height),
      "--steps",
      "8",
      "--output",
      str(out_path),
    ]
    print("⚠️  Retrying mflux without style-reference flags...")
    subprocess.run(cmd, check=True)

  if not out_path.exists():
    # Some mflux versions write to CWD with a fixed name.
    for candidate in Path.cwd().glob("*.png"):
      if candidate.stat().st_mtime >= render_path.stat().st_mtime:
        shutil.move(str(candidate), str(out_path))
        break
  if not out_path.exists():
    raise RuntimeError(
      f"mflux finished but {out_path} was not written. "
      "Check mflux --help for the correct output flag on your version."
    )
  print(f"✅ Generation saved: {out_path}")
  return out_path
