"""Tests for landmark snapshot config helpers."""

from pathlib import Path

import pytest

from isometric_nyc.landmark_snapshot.config import (
  discover_landmark_configs,
  load_landmark_config,
  resolve_print_pixels,
)


def test_resolve_print_pixels_square_2k() -> None:
  assert resolve_print_pixels("2k", aspect_ratio="1:1") == (2048, 2048)


def test_resolve_print_pixels_4k() -> None:
  assert resolve_print_pixels("4k", aspect_ratio="1:1") == (4096, 4096)


def test_resolve_print_pixels_widescreen() -> None:
  w, h = resolve_print_pixels("2k", aspect_ratio="16:9")
  assert w == 2048
  assert h == 1152


def test_resolve_print_pixels_explicit_override() -> None:
  assert resolve_print_pixels("1k", width_px=3000, height_px=2000) == (3000, 2000)


def test_resolve_print_pixels_rejects_bad_resolution() -> None:
  with pytest.raises(ValueError, match="Unknown resolution"):
    resolve_print_pixels("8k")


def test_load_hollywoodwood_bowl_config() -> None:
  path = Path("landmarks/hollywoodwood_bowl.json")
  cfg = load_landmark_config(path)
  assert cfg.id == "hollywoodwood-bowl"
  assert cfg.name == "Hollywood Bowl"
  assert cfg.print.resolution == "2k"
  assert cfg.print.pixels() == (2048, 2048)
  view = cfg.view_dict()
  assert view["lat"] == pytest.approx(34.1122)
  assert view["width_px"] == 2048


def test_discover_landmarks_dir() -> None:
  paths = discover_landmark_configs("landmarks")
  assert len(paths) >= 4
  assert any(p.name == "hollywoodwood_bowl.json" for p in paths)
