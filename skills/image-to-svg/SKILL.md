---
name: image-to-svg
description: Convert a provided image, screenshot, sketch, logo reference, poster, icon, cartoon frame, GIF, animated image, or visual composition into a handcrafted or carefully vectorized SVG implementation. Use when the user asks to turn an image into SVG code, vector art, an SVG illustration, a simplified vector recreation, a high-fidelity flat/cartoon SVG trace, a GIF-to-SVG animation, or an animated SVG. The final deliverable should be pure, self-contained SVG code by default, not a raster image.
---

# Image To SVG

## Purpose

Transform an input image into a clean, maintainable, self-contained SVG file that captures the image's essential composition, shapes, colors, and visual hierarchy at an appropriate abstraction level.

This skill is for deliberate vector reconstruction, not blind automatic tracing. Prefer semantic SVG for simple graphics, but preserve source alignment for photographs, portraits, screenshots, dense cartoons, and any image where the user's likely expectation is "make this image into SVG" rather than "make an inspired illustration."

## Output Contract

Every completed task should produce:

- A `.svg` file saved in the workspace when a workspace is available, or a complete fenced `svg` code block when file output is not appropriate.
- A self-contained SVG with `viewBox`, `title`, `desc`, grouped layers, and no external raster dependencies by default.
- For animation requests, a separate animated `.svg` when a static SVG already exists, unless the user asks to replace it.
- A short note describing the abstraction level and any intentional simplifications.
- Validation evidence: at minimum, confirm that the SVG parses and renders; for important visuals, inspect a rendered preview and iterate once if needed. For animated SVGs, render at least two time-separated frames or otherwise confirm visible motion.

Do not use `<image href="...">` to embed the original bitmap unless the user explicitly asks for a hybrid SVG. The normal deliverable is pure vector.

## Abstraction Levels

Choose an abstraction level from the image and user request. Do not use one default for every image type:

- For icons, logos, sketches, simple illustrations, and diagrams, default to `editorial-flat`.
- For photographs, portraits, real-world scenes, food/product/place images, and blurred-camera compositions, default to `posterized-photo` unless the user explicitly asks for a flat illustration.
- For screenshots and flat cartoons where silhouette alignment matters, default to the extraction-based strategies below.

- `iconic`: Minimal mark, silhouette, app icon, favicon, badge, or logo-like simplification.
- `editorial-flat`: Clean flat illustration with simplified geometry, restrained gradients, and readable subject identity.
- `poster`: Strong composition, graphic shapes, expressive color blocking, and stylized light/shadow.
- `posterized-photo`: Source-aligned color-region vectorization for photographic input. Preserve framing, object placement, silhouette, major color fields, and blur/light hierarchy; accept a larger SVG file to remain recognizably derived from the source.
- `semi-realistic`: More layered gradients, highlights, masks, and filters while still remaining maintainable SVG.
- `technical`: Faithful layout, UI screenshot abstraction, diagram, chart, wireframe, or product interface reconstruction.

State the selected level before or while implementing if the choice affects tradeoffs.

## Workflow

1. Inspect the input image.
   - If the image is attached in the conversation, analyze it directly.
   - If it is a local file, use the available image inspection tool before writing code.
   - If the input is a GIF or animated image, inspect its frame count, duration, dimensions, palette, and representative frames before choosing a conversion strategy.
   - If the image cannot be inspected, ask for the image or a path rather than inventing details.

2. Identify the visual structure.
   - Subject: primary object, person, scene, interface, symbol, or composition.
   - Frame: aspect ratio, viewBox, focal point, negative space.
   - Layers: background, large blocks, midground forms, foreground details, overlays.
   - Shape language: geometric, organic, hand-drawn, technical, rounded, angular.
   - Palette: 4 to 10 dominant colors, plus highlight/shadow colors when needed.
   - Text: exact text if readable; otherwise use simplified blocks or ask if exact text matters.

3. Decide implementation strategy.
   - Use native SVG primitives first: `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, and simple `path`.
   - Use `path` for meaningful silhouettes, not for every tiny pixel-level contour.
   - Use `linearGradient`, `radialGradient`, `clipPath`, `mask`, and restrained `filter` only when they materially improve the result.
   - For UI screenshots, reconstruct the layout with rectangles, typography, controls, icons, and spacing rather than tracing pixels.
   - For faces or realistic photos, do not invent a new face or redrawn character. Either use `posterized-photo` extraction to preserve alignment, or explicitly tell the user the result will be a loose stylized illustration before proceeding.
   - For dense flat cartoons or screenshots where manual path placement would likely drift, use the "aligned linework + color underlay" strategy below instead of guessing coordinates.
   - If the source is a complex photograph and no exact style is requested, start from a source-derived posterized SVG, then optionally add small semantic overlays. Do not begin with a hand-authored scene recreation unless the user asked for an illustration.

4. Implement the SVG.
   - Create a stable `viewBox` matching the input aspect ratio or intended output format.
   - Define reusable colors, gradients, filters, and clip paths in `<defs>`.
   - Organize visible content into named groups such as `background`, `main-subject`, `details`, and `foreground`.
   - Keep IDs descriptive and unique.
   - Add `role="img"`, `aria-labelledby`, `<title>`, and `<desc>`.
   - Prefer maintainable shapes over over-minified code.

5. Validate and iterate.
   - Confirm the SVG is valid XML/SVG and renders without blank output.
   - Render or open a preview whenever possible.
   - For photographs, portraits, products, or places, create a side-by-side comparison image or inspect the rendered preview next to the source before delivery.
   - Compare against the input image for composition, silhouette, color, and hierarchy.
   - Fix the largest mismatch first: framing, proportions, subject recognizability, palette, then details. If framing/proportions are wrong after the first preview, switch to an extraction-based strategy instead of continuing a hand-drawn version.
   - If linework is correct but colors look wrong, inspect fill coverage before changing colors: unfilled seams and jagged holes often come from subtracting strokes from color regions.
   - Check at small and large sizes for readability.

6. Deliver.
   - Provide the saved SVG path and a concise summary of design choices.
   - Include the full SVG code only when the user asked for inline code or the file is small enough to be useful inline.
   - Mention known simplifications honestly.

## Quality Rules

The SVG should be:

- Recognizable: the primary subject and composition are clearly derived from the source image.
- Abstracted: unnecessary photographic noise, compression artifacts, and tiny texture details are removed.
- Scalable: it remains legible at icon/thumbnail size and clean at large size.
- Maintainable: layers and IDs are understandable; repeated colors and gradients live in `<defs>` or CSS variables.
- Self-contained: no external images, fonts, stylesheets, scripts, or network dependencies unless requested.
- Accessible: includes `title`, `desc`, and appropriate ARIA attributes.
- Render-safe: no malformed paths, missing defs, broken references, or text overflowing the canvas.

Avoid:

- Blind autotrace output with hundreds of arbitrary paths.
- Embedding the original image as a shortcut.
- Excessive filters that slow rendering or hide weak drawing.
- Pixel-perfect promises for complex photos.
- Overly generic AI-looking gradients when the source has a specific visual identity.

## High-Fidelity Flat/Cartoon Strategy

Use this strategy for flat cartoons, anime frames, stickers, mascots, screenshots, or other images where silhouette alignment matters more than hand-authored minimalism.

### Layer Model

Build the SVG in this order:

1. `background`: a solid or simple gradient background derived from the border/background color.
2. `source-color-regions`: simplified color fills extracted from the source.
3. `ink-contours`: traced or reconstructed dark linework on top.
4. `animation-overlays` or `details`: optional semantic overlays for eyes, mouths, highlights, and motion.

Important: color fills should extend beneath the linework. Do not punch the black line mask out of the color layer; that creates visible gaps, white seams, and jagged "unfilled" edges.

### Reliable Extraction Recipe

When using local image processing tools such as PIL, OpenCV, or scikit-image:

- Use the original image size as the `viewBox` unless a different output size is requested.
- Smooth color fields before clustering with a cartoon-preserving filter, such as `cv2.pyrMeanShiftFiltering(...)` plus a small median blur.
- Detect ink separately using a tight dark-pixel mask, then close it lightly. Keep it as the top layer.
- Cluster non-ink pixels in Lab color space with a moderate `K`:
  - `K=12-18` for clean flat output.
  - `K=18-28` when small color details matter.
- Convert Lab arrays to `int32` before squaring color-distance differences. `uint8`/`int16` can overflow and assign large regions to the wrong colors.
- Use the border-majority cluster as the background.
- Compute each cluster's displayed color as the RGB mean from source pixels assigned to that cluster, not as a hand-picked palette unless the user requested stylization.
- For each color mask: close small holes, remove tiny speckles, then dilate by about 1px so color reaches under black strokes.
- Convert masks to SVG paths with contour simplification (`CHAIN_APPROX_TC89_KCOS` or `approxPolyDP`) and drop tiny contours.
- Add a same-color stroke (`stroke` equal to `fill`, `stroke-width` about `1-2`) on color-region paths to hide subpixel cracks between adjacent fills.

### Iteration Heuristics

- If silhouettes are wrong, fix linework/contours before touching color.
- If linework is right but the image looks patchy, reduce `K`, increase mask closing, remove small contours, and add same-color strokes.
- If colors are filled but visibly wrong, use source-derived clusters or sampled region means instead of a fixed palette.
- If the render looks jagged, smooth masks before contour extraction and use slightly larger `epsilon` in path simplification.
- If important details disappear, lower `min_area` only for detail colors such as mouth pink, small highlights, buttons, jewelry, or pupils.
- Keep a side-by-side comparison image when possible; it catches wrong fills faster than inspecting the SVG text.
- Expect a tradeoff: cleaner regions reduce jaggedness but flatten subtle antialiasing and gradients.

## Posterized Photo Strategy

Use this strategy for real photographs, portraits, landscapes, product photos, venue photos, food photos, and other camera images where composition fidelity matters more than hand-authored neatness.

### Why

Manual SVG reconstruction easily produces a different illustration: changed face, wrong body scale, simplified architecture, invented leaf shapes, or shifted foreground objects. For photos, the first pass should preserve the source geometry by deriving color regions from the pixels.

### Implementation Recipe

When local Python tools are available, prefer `scripts/posterize_photo_svg.py` from this skill directory as the starting point. If using custom code instead, follow this pattern:

1. Resize the source to a practical canvas such as 600-1200 px on the long side unless the user needs full resolution.
2. Preserve the original aspect ratio in the `viewBox`.
3. Smooth the image with `cv2.pyrMeanShiftFiltering`, bilateral filtering, or median blur before clustering.
4. Cluster in Lab color space, usually `K=28-48` for photos. Use fewer clusters for cleaner poster art and more clusters for portraits or detailed scenes.
5. For each cluster, compute the displayed fill from the source RGB mean of assigned pixels.
6. Convert each mask to simplified contours. Remove tiny speckles, close holes, dilate 1px, and add same-color strokes to avoid cracks.
7. Add a dark-detail layer from thresholded low-luminance regions, with small-area filtering.
8. For important subjects such as faces, hands, clothing logos, or product labels, add a local higher-resolution detail pass over that region instead of raising global complexity.
9. Keep output pure SVG. Do not embed the original bitmap unless the user explicitly approves a hybrid SVG.

### Acceptance Criteria

- The rendered SVG must match the source framing, scale, and subject placement before stylistic polish.
- In a portrait, the head/body location and clothing silhouette must match the source; do not replace the person with a generic cartoon face.
- For blurred backgrounds, preserve the soft large color masses rather than inventing crisp architecture.
- If the preview looks like a different image, discard or demote the hand-drawn version and regenerate from source-derived regions.
- Report the tradeoff honestly: "posterized/source-aligned vectorization" is closer to the photo but less hand-clean than a custom illustration.

## Animated SVG Strategy

Use this when the user asks for SVG motion, SVG animation, animated icons, "动图", or wants a static SVG made alive.

### Output Pattern

- Preserve the static SVG as the source of truth and create a separate animated SVG unless the user asks to overwrite it.
- Put the base artwork into `<defs>` as a reusable `master-art` group.
- Use `clipPath` regions to separate characters or major objects when the original SVG is not semantically layered.
- Animate clipped copies of `master-art` for coarse movement, then add small overlay shapes for semantic local motion.
- Prefer CSS keyframes embedded in `<style>` for broad browser support. Use SMIL only when it materially improves path or attribute animation.
- Include `prefers-reduced-motion: reduce` to disable or soften motion.

### Motion Design

For character or cartoon scenes, avoid only moving the whole canvas. Compose several motion layers:

- Staggered breathing or idle bob per character.
- Slight head/body rotation around plausible transform origins.
- Eye blinks using lid-cover overlays and/or blink lines.
- Pupil darts using small black overlay circles with highlight dots.
- Mouth/talking loops using subtle black or lip-colored ellipses/path overlays.
- Secondary motion such as dog nose sniffing, pendants swinging, hair/hat micro-movement, comic motion lines, or sparkle accents.
- Very gentle camera drift or parallax only when it does not crop the composition.

Keep motion readable but not chaotic. Use different durations and delays so the loop feels alive instead of synchronized.

### Animated Validation

- Render or screenshot at least two frames separated by time (`t0`, `t2`, `t5`, etc.).
- Confirm the frames differ meaningfully, either visually or with a pixel-difference check.
- Inspect still frames for accidental duplicate details, masks that cut off bodies, overlays that look like extra anatomy, and motion that breaks important line alignment.
- If an overlay looks wrong in a still frame, remove or simplify it; animation should improve the artwork, not reveal scaffolding.

## GIF To SVG Animation Strategy

Use this when the user provides a `.gif` or animated raster and asks to convert it to SVG, SVG animation, vector animation, or "gif 转 svg 动图".

### First Choose A Conversion Mode

Prefer pure SVG by default, but be explicit about limitations:

- **Semantic rebuild**: Best for icons, stickers, UI loaders, simple cartoons, logos, and character loops. Choose representative frames, reconstruct stable shapes once, and animate transforms, opacity, paths, masks, or overlay details.
- **Frame-difference vectorization**: Useful for flat pixel/cartoon GIFs with limited palettes. Vectorize the base frame, then vectorize only moving regions from selected keyframes.
- **Posterized frame sequence**: Acceptable for short, flat GIFs when semantic rebuilding is too slow. Convert each sampled frame to simplified color-region paths and show/hide them with CSS or SMIL. Warn that file size can grow quickly.
- **Hybrid raster-in-SVG**: Use only if the user explicitly accepts embedded raster frames. This violates the normal pure-vector deliverable, but can preserve photographic or noisy GIFs.

Do not promise faithful pure-vector conversion for photographic, noisy, long, high-resolution, or heavily compressed GIFs. Offer a stylized/abstracted SVG animation instead.

### GIF Inspection

Before implementing, gather:

- Dimensions, frame count, total duration, loop count if available.
- Frame delays and whether delays vary.
- Palette size or approximate dominant colors.
- Whether the background is stable.
- Whether motion is global camera motion, character limb motion, blinking/talking, object movement, particles, or full-frame noise.

Use frame extraction tools available locally. With Python/Pillow, inspect frames with `ImageSequence.Iterator`, save contact sheets, and sample keyframes. Use OpenCV/scikit-image when masks, difference maps, or clustering are needed.

### Pure SVG Workflow

1. Extract representative frames: first, last, evenly spaced frames, and frames near major motion changes. For loops, include the seam around the loop point.
2. Build a clean static base from the most representative frame using the high-fidelity flat/cartoon strategy when appropriate.
3. Detect moving regions by differencing frames against the base after light blur/thresholding.
4. Decide whether each moving region should become:
   - A transform animation on an existing group.
   - A path morph or alternate path.
   - An opacity-swapped overlay.
   - A mask/clip reveal.
   - A small semantic overlay such as eyelids, mouth shapes, sparkles, shadows, or motion lines.
5. Encode timing from the GIF's frame delays. Normalize to a concise loop duration when the original timing is noisy.
6. Keep IDs and groups semantic: `base-art`, `moving-arm`, `blink-cycle`, `frame-overlays`, `motion-lines`, etc.
7. Add `prefers-reduced-motion` behavior.

### Frame Sequence Workflow

Use this only when semantic rebuild is not practical and the GIF is short/simple:

- Sample frames instead of preserving every frame. Start with 8-16 keyframes for short loops.
- Posterize each frame into limited color regions. Use fewer colors than the source if needed to keep file size manageable.
- Avoid per-frame full-canvas path spam when only a small area changes; isolate changed bounding boxes.
- Use CSS `steps(n)` or SMIL opacity timing to swap frame groups.
- Validate file size and render performance. If the SVG becomes too large or sluggish, reduce frames, merge colors, or switch to semantic rebuild.

### GIF Validation

- Render/screenshot at multiple loop times, including the loop seam.
- Compare representative rendered SVG frames against original GIF frames for composition, timing, and motion readability.
- Check that the SVG remains pure vector unless the user explicitly approved embedded raster.
- Report frame sampling and simplifications honestly: number of source frames, number of SVG keyframes, whether timing was preserved or normalized, and what motion was rebuilt semantically.

## Image Generation Support

Use the installed `imagegen` skill or built-in image generation, including gpt-image-2 when that is the active image model, only as a supporting step. Never treat generated raster output as the final SVG deliverable.

Appropriate uses:

- The user wants a creative reinterpretation of the source before vectorizing.
- The input image is low quality and a cleaner reference would help.
- The user asks for variants before choosing one SVG direction.
- Missing details need a generated reference, and the user accepts creative inference.

Rules:

- Make clear that the generated image is a temporary reference.
- Preserve the user's original image as the source of truth unless they choose a generated variant.
- After image generation, still handcraft the final as pure SVG.
- Do not call image generation for simple icons, diagrams, UI screenshots, or cases where direct SVG construction is faster and more accurate.

## Practical SVG Patterns

For geometric icons:

```svg
<svg viewBox="0 0 64 64" role="img" aria-labelledby="title desc" xmlns="http://www.w3.org/2000/svg">
  <title id="title">Abstract icon</title>
  <desc id="desc">A simplified vector recreation based on the provided reference.</desc>
  <g id="mark" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
    <path d="M16 42 32 14l16 28H16Z"/>
    <path d="M25 34h14"/>
  </g>
</svg>
```

For illustrated scenes:

```svg
<svg viewBox="0 0 1200 800" role="img" aria-labelledby="title desc" xmlns="http://www.w3.org/2000/svg">
  <title id="title">Abstract scene</title>
  <desc id="desc">A layered flat SVG illustration based on the provided image.</desc>
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#dcecff"/>
      <stop offset="1" stop-color="#f8fbff"/>
    </linearGradient>
  </defs>
  <g id="background">
    <rect width="1200" height="800" fill="url(#sky)"/>
  </g>
  <g id="main-subject">
    <!-- Build the dominant silhouette first, then add only meaningful details. -->
  </g>
</svg>
```

Use examples as structural hints only; create the actual SVG from the user's image.

## When To Ask A Question

Ask one concise question only when the missing choice materially changes the outcome:

- The user wants exact text but the image text is unreadable.
- The user needs a specific abstraction level, brand palette, or output size.
- The image is unavailable or cannot be inspected.
- The user asks for exact likeness of a person or exact reproduction of a complex copyrighted artwork.

Otherwise, make a reasonable default choice and proceed.
