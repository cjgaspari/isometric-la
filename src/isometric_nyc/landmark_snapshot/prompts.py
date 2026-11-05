"""Prompts for landmark isometric stylization."""

from __future__ import annotations


def landmark_style_prompt(
  *,
  landmark_name: str,
  prompt_extra: str = "",
  special_instructions: str = "",
) -> str:
  """Build the stylization prompt for a single landmark print."""
  parts = [
    (
      f"Create a high-quality isometric pixel-art illustration of {landmark_name} "
      "in Los Angeles, in the style of classic 1990s/2000s city-builder games "
      "(SimCity 3000 aesthetic)."
    ),
    (
      "The attached render shows exact placement, volume, and silhouette. "
      "Preserve geometry faithfully: do not invent or remove major buildings, "
      "roads, or landforms. Translate materials into clean pixel art "
      "(brick, concrete, glass, foliage) with crisp isometric 2:1 edges and "
      "hard directional shadows."
    ),
    (
      "If a style reference image is attached, match its palette, line weight, "
      "and level of detail closely."
    ),
    (
      "Output should look like finished game art suitable for a large print: "
      "sharp pixels, coherent lighting, no photographic noise, no blurry "
      "upscale artifacts, no watermarks, no captions."
    ),
  ]
  if special_instructions.strip():
    parts.append(f"Special instructions: {special_instructions.strip()}")
  if prompt_extra.strip():
    parts.append(prompt_extra.strip())
  return "\n\n".join(parts)
