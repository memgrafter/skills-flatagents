---
name: create-gif
description: Turn a video URL or local clip into a crisp, size-efficient GIF with precise timing controls and proven quality/size presets (including hard skin-tone lighting cases).
---

Create reproducible GIFs quickly without guessing encode settings.

## Why use it

- **Precise clip timing** (exact start/end and offset fixes)
- **Better color fidelity** for difficult footage (explicit BT.709 → sRGB before palette quantization)
- **Predictable size/quality tuning** (resolution, fps, colors, lossy level)
- **Reusable presets** from tested runs, not one-off trial-and-error

## When to use

- You need a GIF deliverable (chat apps, docs, issue comments)
- Source is YouTube or local MP4
- You need to balance smoothness and file size intentionally
- Scene has skin tones/high contrast and default GIF conversion looks wrong

## When NOT to use

- If target supports MP4/WebP (these are dramatically smaller at better quality)
- Very long clips (GIF size grows fast)
- You need perfect color preservation (GIF is limited to 256 colors)

## Requirements (what must be installed)

- `yt-dlp`
- `ffmpeg`
- `imagemagick` (`magick`)
- `gifsicle`

## Usage

### Segment-first methodology (recommended)

1. **Define segment in seconds first** (example: start=14, end=23 or duration=9)
2. Download only the needed YouTube window
3. If timing is off, do final trim by seconds with ffmpeg (`-ss`, `-to`/`-t`)
4. Convert to GIF with the quality preset

Why seconds-based segmenting helps:
- **Fast iteration**: change `start/end` by 1s without rethinking timestamps
- **Reproducible edits**: exact same segment can be regenerated later
- **Clear intent**: `start+duration` is great when clip length is fixed
- **Less waste**: avoids downloading/processing full videos

### 1) Download time slice from YouTube

```bash
yt-dlp -f "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best" \
  --download-sections "*00:00:14-00:00:23" \
  --force-keyframes-at-cuts --merge-output-format mp4 \
  -o "yt_clip.%(ext)s" "<YOUTUBE_URL>"
```

### 1b) Alternative: start + duration (seconds)

If you know clip length, use ffmpeg on the downloaded clip:

```bash
# start at 15s, keep 8s
ffmpeg -y -ss 15 -t 8 -i yt_clip.mp4 -c copy yt_clip_segment.mp4
```

Or if you prefer start + end:

```bash
# start at 15s, end at 23s
ffmpeg -y -ss 15 -to 23 -i yt_clip.mp4 -c copy yt_clip_segment.mp4
```

### 2) Gold-standard preset (best compromise found)

```bash
ffmpeg -y -ss 1 -t 8 -i yt_clip.mp4 \
  -vf "fps=16,scale=520:-1:flags=lanczos,hqdn3d=1.0:1.0:3:3,colorspace=iall=bt709:ispace=bt709:itrc=bt709:iprimaries=bt709:irange=tv:space=gbr:trc=srgb:primaries=bt709:range=pc,format=rgb24,split[s0][s1];[s0]palettegen=max_colors=160:reserve_transparent=0:stats_mode=full[p];[s1][p]paletteuse=dither=sierra2_4a" \
  jack_typing_520w_16fps_srgb_160_raw.gif

magick jack_typing_520w_16fps_srgb_160_raw.gif -layers Optimize jack_typing_520w_16fps_srgb_160.gif
gifsicle -O3 --lossy=45 jack_typing_520w_16fps_srgb_160.gif -o jack_typing_520w_16fps_srgb_160_lossy45.gif
```

## Validated ranges tested

- **Width/size:** 420w, 480p, 520w, 560w, 640w
- **FPS:** 10, 12, 16, 20
- **Palette colors:** 96, 112, 128, 160, 192, 224, 256
- **Lossy levels:** 20, 30, 35, 40, 45, 50, 80
- **Dither modes:** none, bayer, sierra2_4a

## Output

Typical files produced:
- `*_raw.gif` (pre-optimization)
- `*.gif` (optimized)
- `*_lossyXX.gif` (final size/quality tradeoff)

## How it works

Cut exact segment → color-space normalize → generate/apply palette → optimize frames → optional lossy compression.

Trade-off: more fidelity requires bigger GIFs; this workflow gives controlled compromises instead of random artifacts.
