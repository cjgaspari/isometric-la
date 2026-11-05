"""CLI for landmark snapshot prints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from isometric_nyc.landmark_snapshot.config import (
  discover_landmark_configs,
  load_landmark_config,
)
from isometric_nyc.landmark_snapshot.render import render_landmark
from isometric_nyc.landmark_snapshot.stylize import stylize_landmark

DEFAULT_OUT = Path("exports/landmarks")


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    prog="landmark-snapshot",
    description=(
      "Generate high-resolution isometric landmark artwork for print. "
      "Render with Google 3D Tiles, then stylize locally (mflux) or via "
      "cloud (Gemini / Grok)."
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Hollywood Bowl at 2K via Gemini (cloud stylize)
  uv run landmark-snapshot landmarks/hollywoodwood_bowl.json --backend gemini

  # Native 4K Gemini print
  uv run landmark-snapshot landmarks/hollywoodwood_bowl.json --backend gemini --resolution 4k

  # On-device stylize (Apple Silicon + mflux)
  uv run landmark-snapshot landmarks/hollywoodwood_bowl.json --backend local --resolution 2k

  # Render only (no stylize)
  uv run landmark-snapshot landmarks/hollywoodwood_bowl.json --render-only

  # Re-stylize an existing job directory
  uv run landmark-snapshot --job-dir exports/landmarks/hollywoodwood-bowl --backend gemini --skip-render
""",
  )
  parser.add_argument(
    "landmarks",
    nargs="*",
    type=Path,
    help="Landmark JSON file(s) or a directory of them",
  )
  parser.add_argument(
    "--job-dir",
    type=Path,
    default=None,
    help="Existing job directory (implies using its landmark/view metadata)",
  )
  parser.add_argument(
    "--output-dir",
    type=Path,
    default=DEFAULT_OUT,
    help=f"Parent output directory (default: {DEFAULT_OUT})",
  )
  parser.add_argument(
    "--backend",
    choices=["local", "gemini", "grok"],
    default="gemini",
    help="Stylize backend (default: gemini). Prefer 'local' on Mac with mflux.",
  )
  parser.add_argument(
    "--resolution",
    choices=["1k", "2k", "4k"],
    default=None,
    help="Override print resolution from the landmark JSON",
  )
  parser.add_argument(
    "--render-only",
    action="store_true",
    help="Only capture render.png",
  )
  parser.add_argument(
    "--skip-render",
    action="store_true",
    help="Skip render; stylize existing render.png in the job dir",
  )
  parser.add_argument(
    "--port",
    type=int,
    default=5173,
    help="Port for web_render Vite server",
  )
  parser.add_argument(
    "--existing-server",
    action="store_true",
    help="Reuse an already-running web_render server on --port",
  )
  return parser


def _apply_resolution_override(config_path: Path, resolution: str | None):
  config = load_landmark_config(config_path)
  if resolution is None:
    return config
  # Rebuild with overridden print resolution.
  from dataclasses import replace

  from isometric_nyc.landmark_snapshot.config import PrintSpec

  return replace(
    config,
    print=PrintSpec(
      resolution=resolution,  # type: ignore[arg-type]
      width_px=None,
      height_px=None,
      aspect_ratio=config.print.aspect_ratio,
    ),
  )


def run_one(
  config_path: Path | None,
  *,
  output_dir: Path,
  backend: str,
  resolution: str | None,
  render_only: bool,
  skip_render: bool,
  port: int,
  existing_server: bool,
  job_dir: Path | None = None,
) -> Path:
  if job_dir is not None:
    job_dir = Path(job_dir)
    landmark_meta = job_dir / "landmark.json"
    view_path = job_dir / "view.json"
    if config_path is None:
      # Synthesize from job metadata + view.json
      if not view_path.exists():
        raise FileNotFoundError(f"No view.json in {job_dir}")
      view = json.loads(view_path.read_text())
      meta = {}
      if landmark_meta.exists():
        meta = json.loads(landmark_meta.read_text())
      tmp = {
        "id": meta.get("id", job_dir.name),
        "name": meta.get("name", view.get("name", job_dir.name)),
        "lat": view["lat"],
        "lon": view["lon"],
        "size_meters": view.get("size_meters", 350),
        "camera_azimuth_degrees": view.get("camera_azimuth_degrees", -15),
        "camera_elevation_degrees": view.get("camera_elevation_degrees", -45),
        "view_height_meters": view.get("view_height_meters", 250),
        "style_reference": meta.get("style_reference", "references/style_c.png"),
        "prompt_extra": meta.get("prompt_extra", ""),
        "print": {
          "resolution": resolution or "2k",
          "width_px": view.get("width_px"),
          "height_px": view.get("height_px"),
          "aspect_ratio": "1:1"
          if view.get("width_px") == view.get("height_px")
          else "16:9",
        },
      }
      from isometric_nyc.landmark_snapshot.config import LandmarkConfig, PrintSpec

      config = LandmarkConfig(
        id=str(tmp["id"]),
        name=str(tmp["name"]),
        lat=float(tmp["lat"]),
        lon=float(tmp["lon"]),
        size_meters=float(tmp["size_meters"]),
        camera_azimuth_degrees=float(tmp["camera_azimuth_degrees"]),
        camera_elevation_degrees=float(tmp["camera_elevation_degrees"]),
        view_height_meters=float(tmp["view_height_meters"]),
        print=PrintSpec(
          resolution=(resolution or "2k"),  # type: ignore[arg-type]
          width_px=tmp["print"].get("width_px"),
          height_px=tmp["print"].get("height_px"),
          aspect_ratio=str(tmp["print"]["aspect_ratio"]),
        ),
        style_reference=str(tmp["style_reference"]),
        prompt_extra=str(tmp["prompt_extra"]),
      )
    else:
      config = _apply_resolution_override(config_path, resolution)
  else:
    assert config_path is not None
    config = _apply_resolution_override(config_path, resolution)
    job_dir = output_dir / config.id

  job_dir.mkdir(parents=True, exist_ok=True)
  print(f"\n📍 {config.name} → {job_dir}")
  print(f"   pixels={config.print.pixels()} resolution={config.print.resolution}")

  if not skip_render:
    render_landmark(
      config,
      job_dir,
      port=port,
      existing_server=existing_server,
    )
  elif not (job_dir / "render.png").exists():
    raise FileNotFoundError(
      f"--skip-render set but {job_dir / 'render.png'} is missing"
    )

  if render_only:
    return job_dir

  stylize_landmark(config, job_dir, backend=backend)
  return job_dir


def main(argv: list[str] | None = None) -> int:
  parser = build_parser()
  args = parser.parse_args(argv)

  if not args.landmarks and args.job_dir is None:
    parser.error("Provide landmark JSON path(s) or --job-dir")

  config_paths: list[Path] = []
  for item in args.landmarks:
    config_paths.extend(discover_landmark_configs(item))

  if args.job_dir and not config_paths:
    run_one(
      None,
      output_dir=args.output_dir,
      backend=args.backend,
      resolution=args.resolution,
      render_only=args.render_only,
      skip_render=args.skip_render,
      port=args.port,
      existing_server=args.existing_server,
      job_dir=args.job_dir,
    )
    return 0

  if not config_paths:
    parser.error("No landmark JSON files found")

  for path in config_paths:
    run_one(
      path,
      output_dir=args.output_dir,
      backend=args.backend,
      resolution=args.resolution,
      render_only=args.render_only,
      skip_render=args.skip_render,
      port=args.port,
      existing_server=args.existing_server,
      job_dir=args.job_dir if len(config_paths) == 1 else None,
    )
  return 0


if __name__ == "__main__":
  sys.exit(main())
