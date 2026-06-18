# Image To SVG Skill

`image-to-svg` converts reference images into pure, self-contained SVG files.
It is designed for Codex workflows where the final artifact should be editable
vector code rather than an embedded raster image.

## What Changed

The skill now distinguishes between two very different tasks:

- Simple graphics, icons, sketches, UI screenshots, and clean cartoons can use
  handcrafted SVG structure.
- Photographs, portraits, places, products, and other camera images should
  preserve source geometry first, using posterized color-region vectorization.

This distinction prevents complex photos from being redrawn as unrelated
cartoon illustrations.

## Repository Layout

```text
skills/image-to-svg/
  SKILL.md
  agents/openai.yaml
  scripts/posterize_photo_svg.py
```

`SKILL.md` contains the agent workflow. `agents/openai.yaml` contains UI-facing
metadata. `scripts/posterize_photo_svg.py` is a reusable OpenCV/Pillow helper
for source-aligned photo vectorization.

## Photo Conversion Strategy

For photographs, the helper script:

1. Resizes the image while preserving aspect ratio.
2. Smooths the image to reduce photographic noise.
3. Clusters pixels in Lab color space.
4. Converts cluster masks into simplified SVG contour paths.
5. Computes fills from source RGB means.
6. Adds a dark-detail layer for edges and important low-luminance features.
7. Optionally adds a local detail pass for faces, hands, labels, or products.

The result is a posterized SVG that keeps framing, scale, and major silhouettes
closer to the source image than a hand-drawn recreation.

## Example Usage

```powershell
python .\skills\image-to-svg\scripts\posterize_photo_svg.py `
  "D:\path\to\source.png" `
  "D:\path\to\output.svg" `
  --long-side 1200 `
  --clusters 34 `
  --min-area 26
```

For an important face or product label, add a detail region after resizing:

```powershell
python .\skills\image-to-svg\scripts\posterize_photo_svg.py `
  "D:\path\to\portrait.png" `
  "D:\path\to\portrait.svg" `
  --long-side 1200 `
  --clusters 36 `
  --detail-roi 205,635,250,410
```

The `--detail-roi` value is `x,y,w,h` in the resized output coordinate system.

## Validation Checklist

Before delivery, verify:

- The SVG parses as XML.
- The SVG renders to a nonblank preview.
- The preview matches the source framing, subject placement, and major colors.
- For portraits, the person has not been replaced by a generic cartoon face.
- Any simplification is clearly reported as posterized/source-aligned
  vectorization.

On Windows, a quick XML parse check can be run with:

```powershell
$xml = New-Object System.Xml.XmlDocument
$xml.Load((Resolve-Path .\output.svg))
```

## Install

Copy the skill folder into Codex's skill directory:

```powershell
Copy-Item -Recurse -Force .\skills\image-to-svg "$env:USERPROFILE\.codex\skills\image-to-svg"
```

Then restart Codex or reload available skills.
