"""Landmark snapshot configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

ResolutionName = Literal["1k", "2k", "4k"]
BackendName = Literal["local", "gemini", "grok"]

# Native generation sizes (square edge). Match common model image_size knobs.
RESOLUTION_PX: dict[str, int] = {
  "1k": 1024,
  "2k": 2048,
  "4k": 4096,
}

# Aspect ratios supported by Gemini ImageConfig / common edit models.
ASPECT_RATIOS = {
  "1:1",
  "16:9",
  "9:16",
  "4:3",
  "3:4",
  "3:2",
  "2:3",
}


@dataclass(frozen=True)
class PrintSpec:
  """Target print / output pixel size."""

  resolution: ResolutionName = "2k"
  width_px: int | None = None
  height_px: int | None = None
  aspect_ratio: str = "1:1"

  def pixels(self) -> tuple[int, int]:
    return resolve_print_pixels(
      resolution=self.resolution,
      width_px=self.width_px,
      height_px=self.height_px,
      aspect_ratio=self.aspect_ratio,
    )


@dataclass(frozen=True)
class LandmarkConfig:
  """One landmark snapshot job."""

  id: str
  name: str
  lat: float
  lon: float
  size_meters: float = 350.0
  camera_azimuth_degrees: float = -15.0
  camera_elevation_degrees: float = -45.0
  view_height_meters: float = 250.0
  print: PrintSpec = field(default_factory=PrintSpec)
  style_reference: str = "references/style_c.png"
  prompt_extra: str = ""
  special_instructions: str = ""

  def view_dict(self) -> dict[str, Any]:
    width, height = self.print.pixels()
    return {
      "name": self.name,
      "lat": self.lat,
      "lon": self.lon,
      "size_meters": self.size_meters,
      "camera_azimuth_degrees": self.camera_azimuth_degrees,
      "camera_elevation_degrees": self.camera_elevation_degrees,
      "view_height_meters": self.view_height_meters,
      "width_px": width,
      "height_px": height,
      "special_instructions": self.special_instructions,
    }


def resolve_print_pixels(
  resolution: str = "2k",
  width_px: int | None = None,
  height_px: int | None = None,
  aspect_ratio: str = "1:1",
) -> tuple[int, int]:
  """Resolve output width/height from resolution name and aspect ratio."""
  if width_px is not None and height_px is not None:
    return int(width_px), int(height_px)

  if resolution not in RESOLUTION_PX:
    raise ValueError(
      f"Unknown resolution {resolution!r}; expected one of {sorted(RESOLUTION_PX)}"
    )
  if aspect_ratio not in ASPECT_RATIOS:
    raise ValueError(
      f"Unsupported aspect_ratio {aspect_ratio!r}; expected one of {sorted(ASPECT_RATIOS)}"
    )

  edge = RESOLUTION_PX[resolution]
  aw, ah = (int(x) for x in aspect_ratio.split(":"))
  if aw >= ah:
    width = edge
    height = max(1, round(edge * ah / aw))
  else:
    height = edge
    width = max(1, round(edge * aw / ah))
  return width, height


def load_landmark_config(path: Path | str) -> LandmarkConfig:
  """Load a landmark JSON config file."""
  path = Path(path)
  raw = json.loads(path.read_text())
  print_raw = raw.get("print") or {}
  print_spec = PrintSpec(
    resolution=print_raw.get("resolution", raw.get("resolution", "2k")),
    width_px=print_raw.get("width_px"),
    height_px=print_raw.get("height_px"),
    aspect_ratio=print_raw.get(
      "aspect_ratio", raw.get("aspect_ratio", "1:1")
    ),
  )
  landmark_id = raw.get("id") or path.stem
  return LandmarkConfig(
    id=str(landmark_id),
    name=str(raw.get("name", landmark_id)),
    lat=float(raw["lat"]),
    lon=float(raw["lon"]),
    size_meters=float(raw.get("size_meters", 350)),
    camera_azimuth_degrees=float(raw.get("camera_azimuth_degrees", -15)),
    camera_elevation_degrees=float(raw.get("camera_elevation_degrees", -45)),
    view_height_meters=float(raw.get("view_height_meters", 250)),
    print=print_spec,
    style_reference=str(raw.get("style_reference", "references/style_c.png")),
    prompt_extra=str(raw.get("prompt_extra", "")),
    special_instructions=str(raw.get("special_instructions", "")),
  )


def discover_landmark_configs(path: Path | str) -> list[Path]:
  """Return landmark JSON paths from a file or directory."""
  path = Path(path)
  if path.is_file():
    return [path]
  if not path.is_dir():
    raise FileNotFoundError(f"Landmark path not found: {path}")
  return sorted(path.glob("*.json"))
