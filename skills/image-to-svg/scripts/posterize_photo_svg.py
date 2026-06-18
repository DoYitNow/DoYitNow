#!/usr/bin/env python3
"""Create a pure-vector posterized SVG from a photographic image.

This is a starting point for source-aligned photo-to-SVG work. It favors
recognizable framing and silhouettes over tiny photographic detail.
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def rgb_hex(rgb: np.ndarray) -> str:
    vals = np.clip(np.rint(rgb), 0, 255).astype(int)
    return "#{:02x}{:02x}{:02x}".format(vals[0], vals[1], vals[2])


def contour_to_path(contour: np.ndarray, offset_x: int = 0, offset_y: int = 0) -> str:
    pts = contour.reshape(-1, 2)
    if len(pts) < 3:
        return ""
    parts = [f"M{pts[0, 0] + offset_x:.1f} {pts[0, 1] + offset_y:.1f}"]
    for x, y in pts[1:]:
        parts.append(f"L{x + offset_x:.1f} {y + offset_y:.1f}")
    parts.append("Z")
    return " ".join(parts)


def add_mask_paths(
    svg: list[str],
    mask: np.ndarray,
    fill: str,
    group_id: str,
    *,
    min_area: float,
    opacity: float = 1.0,
    offset_x: int = 0,
    offset_y: int = 0,
    epsilon_scale: float = 0.0045,
) -> int:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)
    paths: list[tuple[float, str]] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        epsilon = max(0.45, min(3.2, epsilon_scale * cv2.arcLength(contour, True)))
        approx = cv2.approxPolyDP(contour, epsilon, True)
        path = contour_to_path(approx, offset_x, offset_y)
        if path:
            paths.append((area, path))

    if not paths:
        return 0

    svg.append(
        f'  <g id="{group_id}" fill="{fill}" stroke="{fill}" '
        f'stroke-width="0.65" opacity="{opacity:.3g}">'
    )
    for _, path in sorted(paths, reverse=True):
        svg.append(f'    <path d="{path}"/>')
    svg.append("  </g>")
    return len(paths)


def posterize_image(
    source: Path,
    output: Path,
    *,
    long_side: int,
    clusters: int,
    min_area: float,
    detail_roi: tuple[int, int, int, int] | None,
) -> None:
    image = Image.open(source).convert("RGB")
    src_w, src_h = image.size
    scale = long_side / max(src_w, src_h)
    width = max(1, round(src_w * scale))
    height = max(1, round(src_h * scale))
    image = image.resize((width, height), Image.Resampling.LANCZOS)
    rgb = np.array(image)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    smoothed = cv2.pyrMeanShiftFiltering(bgr, sp=13, sr=24)
    smoothed = cv2.medianBlur(smoothed, 5)
    lab = cv2.cvtColor(smoothed, cv2.COLOR_BGR2LAB)
    pixels = lab.reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 55, 0.45)
    _compactness, labels, _centers = cv2.kmeans(
        pixels,
        clusters,
        None,
        criteria,
        3,
        cv2.KMEANS_PP_CENTERS,
    )
    labels = labels.reshape((height, width))

    stats: list[dict[str, object]] = []
    for idx in range(clusters):
        mask = labels == idx
        if not mask.any():
            continue
        ys, _xs = np.where(mask)
        mean_rgb = rgb[mask].mean(axis=0)
        stats.append(
            {
                "idx": idx,
                "count": int(mask.sum()),
                "mean_y": float(ys.mean()),
                "color": rgb_hex(mean_rgb),
                "lightness": float(mean_rgb.mean()),
            }
        )

    border_px = max(4, min(width, height) // 80)
    border = np.concatenate(
        [
            labels[:border_px, :].ravel(),
            labels[-border_px:, :].ravel(),
            labels[:, :border_px].ravel(),
            labels[:, -border_px:].ravel(),
        ]
    )
    bg_idx = int(np.bincount(border).argmax())
    bg_color = next((s["color"] for s in stats if s["idx"] == bg_idx), "#f4f4ef")

    svg: list[str] = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc" xmlns="http://www.w3.org/2000/svg">',
        "  <title id=\"title\">Posterized SVG from photograph</title>",
        "  <desc id=\"desc\">A source-aligned, pure-vector posterized recreation generated from a photograph.</desc>",
        "  <defs>",
        "    <filter id=\"soften\"><feGaussianBlur stdDeviation=\"0.2\"/></filter>",
        "  </defs>",
        f'  <rect id="sampled-background" width="{width}" height="{height}" fill="{html.escape(str(bg_color))}"/>',
        '  <g id="posterized-color-regions" filter="url(#soften)">',
    ]

    total_paths = 0
    kernel = np.ones((3, 3), np.uint8)
    for stat in sorted(stats, key=lambda s: (float(s["lightness"]), float(s["mean_y"]))):
        idx = int(stat["idx"])
        if idx == bg_idx:
            continue
        mask = (labels == idx).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=1)
        total_paths += add_mask_paths(
            svg,
            mask,
            str(stat["color"]),
            f"cluster-{idx:02d}",
            min_area=min_area,
            opacity=0.985,
        )
    svg.append("  </g>")

    if detail_roi:
        add_detail_roi(svg, rgb, detail_roi, min_area=max(4.0, min_area * 0.25))

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    dark = ((gray < 100) & (hsv[:, :, 1] > 18)).astype(np.uint8) * 255
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8), iterations=1)
    add_mask_paths(svg, dark, "#263027", "sampled-dark-details", min_area=max(8.0, min_area * 0.4), opacity=0.55)

    svg.append(f"  <!-- source={source.name}; clusters={clusters}; color_paths={total_paths}; size={width}x{height} -->")
    svg.append("</svg>")
    output.write_text("\n".join(svg), encoding="utf-8")


def add_detail_roi(svg: list[str], rgb: np.ndarray, roi: tuple[int, int, int, int], *, min_area: float) -> None:
    x0, y0, w, h = roi
    x0 = max(0, min(x0, rgb.shape[1] - 1))
    y0 = max(0, min(y0, rgb.shape[0] - 1))
    w = max(1, min(w, rgb.shape[1] - x0))
    h = max(1, min(h, rgb.shape[0] - y0))
    crop = rgb[y0 : y0 + h, x0 : x0 + w]
    bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(cv2.bilateralFilter(bgr, 7, 34, 34), cv2.COLOR_BGR2LAB)
    pixels = lab.reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 45, 0.35)
    _compactness, labels, _centers = cv2.kmeans(pixels, 24, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    labels = labels.reshape((h, w))

    svg.append('  <g id="local-detail-pass">')
    kernel = np.ones((2, 2), np.uint8)
    for idx in range(24):
        mask_bool = labels == idx
        if mask_bool.sum() < min_area:
            continue
        color = rgb_hex(crop[mask_bool].mean(axis=0))
        mask = cv2.morphologyEx(mask_bool.astype(np.uint8) * 255, cv2.MORPH_CLOSE, kernel, iterations=1)
        add_mask_paths(
            svg,
            mask,
            color,
            f"local-cluster-{idx:02d}",
            min_area=min_area,
            opacity=0.94,
            offset_x=x0,
            offset_y=y0,
            epsilon_scale=0.005,
        )
    svg.append("  </g>")


def parse_roi(value: str | None) -> tuple[int, int, int, int] | None:
    if not value:
        return None
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--detail-roi must be x,y,w,h")
    return tuple(parts)  # type: ignore[return-value]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a source-aligned posterized SVG from a photograph.")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--long-side", type=int, default=1200)
    parser.add_argument("--clusters", type=int, default=34)
    parser.add_argument("--min-area", type=float, default=26)
    parser.add_argument("--detail-roi", type=parse_roi, default=None, help="Optional x,y,w,h region after resizing.")
    args = parser.parse_args()
    posterize_image(
        args.source,
        args.output,
        long_side=args.long_side,
        clusters=args.clusters,
        min_area=args.min_area,
        detail_roi=args.detail_roi,
    )


if __name__ == "__main__":
    main()
