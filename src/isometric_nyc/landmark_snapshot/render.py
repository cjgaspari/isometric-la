"""Capture a high-res isometric 3D-tiles render for a landmark."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from isometric_nyc.landmark_snapshot.config import LandmarkConfig

WEB_RENDER_DIR = Path(__file__).resolve().parents[2] / "web_render"
DEFAULT_PORT = 5173


def write_job_view_json(job_dir: Path, config: LandmarkConfig) -> Path:
  """Write view.json used by the web renderer and stylize step."""
  job_dir.mkdir(parents=True, exist_ok=True)
  view_path = job_dir / "view.json"
  view_path.write_text(json.dumps(config.view_dict(), indent=2) + "\n")
  (job_dir / "landmark.json").write_text(
    json.dumps(
      {
        "id": config.id,
        "name": config.name,
        "style_reference": config.style_reference,
        "prompt_extra": config.prompt_extra,
      },
      indent=2,
    )
    + "\n"
  )
  return view_path


def start_web_render_server(port: int = DEFAULT_PORT) -> subprocess.Popen[Any]:
  """Start the Vite web_render dev server."""
  if not WEB_RENDER_DIR.exists():
    raise FileNotFoundError(f"web_render directory not found: {WEB_RENDER_DIR}")

  process = subprocess.Popen(
    ["bun", "run", "dev", "--port", str(port), "--strictPort"],
    cwd=WEB_RENDER_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
  )
  # Give Vite a moment; callers also wait on TILES_LOADED.
  time.sleep(4)
  if process.poll() is not None:
    out = process.stdout.read().decode() if process.stdout else ""
    raise RuntimeError(f"web_render server failed to start:\n{out}")
  return process


def capture_web_render(
  config: LandmarkConfig,
  output_path: Path,
  *,
  port: int = DEFAULT_PORT,
  timeout_ms: int = 120_000,
) -> Path:
  """
  Screenshot Google 3D Tiles isometric view via Playwright.

  Requires:
    - bun deps installed in src/web_render
    - VITE_GOOGLE_TILES_API_KEY / GOOGLE_TILES_API_KEY available to Vite
    - playwright chromium installed
  """
  from playwright.sync_api import sync_playwright

  width, height = config.print.pixels()
  params = {
    "export": "true",
    "lat": config.lat,
    "lon": config.lon,
    "width": width,
    "height": height,
    "azimuth": config.camera_azimuth_degrees,
    "elevation": config.camera_elevation_degrees,
    "view_height": config.view_height_meters,
  }
  url = f"http://127.0.0.1:{port}/?{urlencode(params)}"
  output_path.parent.mkdir(parents=True, exist_ok=True)

  with sync_playwright() as p:
    browser = p.chromium.launch(
      headless=True,
      args=["--enable-webgl", "--use-gl=angle", "--ignore-gpu-blocklist"],
    )
    context = browser.new_context(
      viewport={"width": width, "height": height},
      device_scale_factor=1,
    )
    page = context.new_page()
    page.goto(url, wait_until="networkidle")
    try:
      page.wait_for_function("window.TILES_LOADED === true", timeout=timeout_ms)
    except Exception as exc:  # noqa: BLE001 — continue with best-effort screenshot
      print(f"⚠️  Tile load wait ended early ({exc}); capturing anyway")
    page.screenshot(path=str(output_path), type="png")
    context.close()
    browser.close()

  if not output_path.exists():
    raise RuntimeError(f"Failed to write render to {output_path}")
  return output_path


def render_landmark(
  config: LandmarkConfig,
  job_dir: Path,
  *,
  port: int = DEFAULT_PORT,
  keep_server: bool = False,
  existing_server: bool = False,
) -> Path:
  """
  Full render step: write job metadata and capture render.png.

  If existing_server=True, assumes web_render is already listening on port.
  """
  write_job_view_json(job_dir, config)
  render_path = job_dir / "render.png"
  server: subprocess.Popen[Any] | None = None
  try:
    if not existing_server:
      print(f"🌐 Starting web_render on port {port}...")
      server = start_web_render_server(port)
    print(f"📸 Capturing {config.name} at {config.print.pixels()}...")
    capture_web_render(config, render_path, port=port)
    print(f"✅ Render saved: {render_path}")
    return render_path
  finally:
    if server is not None and not keep_server:
      server.terminate()
      try:
        server.wait(timeout=5)
      except subprocess.TimeoutExpired:
        server.kill()
