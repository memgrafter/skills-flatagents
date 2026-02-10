---
url: https://github.com/newjordan/BlockN
title: 'GitHub - newjordan/BlockN: Classic Shwamp garbage.'
scraped_at: '2026-02-10T23:35:33.698778+00:00'
word_count: 199
raw_file: 2026-02-10_github-newjordanblockn-classic-shwamp-garbage.txt
tldr: BlockN is the production-ready, shareable branch of LegoGen—a procedural classical architecture generator with PyQt5/PyVista
  GUI and headless CLI that exports Greek/Roman column structures to GLB, JSON, and PNG formats.
key_quote: This repository is the stripped, shareable production branch of LegoGen. It keeps the stable classical generator,
  GUI viewer, and export pipeline, and excludes in-progress planning/session artifacts.
durability: medium
content_type: reference
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- newjordan
tools:
- BlockN
- LegoGen
- PyQt5
- PyVista
libraries: []
companies: []
tags:
- procedural-generation
- 3d-architecture
- classical-architecture
- python-gui
- cli-tool
---

### TL;DR
BlockN is the production-ready, shareable branch of LegoGen—a procedural classical architecture generator with PyQt5/PyVista GUI and headless CLI that exports Greek/Roman column structures to GLB, JSON, and PNG formats.

### Key Quote
> "This repository is the stripped, shareable production branch of LegoGen. It keeps the stable classical generator, GUI viewer, and export pipeline, and excludes in-progress planning/session artifacts."

### Summary
**What it does**: Procedurally generates 3D classical architecture (temples, colonnades) in Greek/Roman orders (Doric, Ionic) with configurable parameters and preset systems.

**Components**:
- `main.py` — PyQt5 + PyVista desktop GUI viewer
- `cli.py` — Headless generation and export
- Classical generator with preset/override controls
- Export formats: GLB, JSON, PNG
- Unit test suite (geometry, scene, classical generation)

**Setup**:
```bash
python3 -m venv .venv-public
source .venv-public/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 main.py
```

**CLI Examples**:
- Basic: `python3 cli.py generate --classical-order Doric --seed 123 --out builds/classical.glb --summary`
- Monumental preset with overrides: `--classical-preset monumental --classical-front-columns 8 --classical-side-columns 8 --classical-pediment-slope 1.1`
- Canonical preset with wrap controls: `--classical-preset canonical --classical-wrap-min-front-span 22 --classical-wrap-front-coverage 0.60`

**Architecture notes**: Recommends keeping separate venvs (`.venv-public` vs `.venv-dev`) to prevent dependency/config drift between production and experimental repos.

### Assessment
**Durability**: Medium. Core procedural generation concepts are stable, but specific CLI flags and PyVista/PyQt5 dependencies will age. No version numbers or dates visible.

**Content type**: Reference / Tool documentation

**Density**: High. README is concise and packed with actionable commands, parameter examples, and architectural guidance.

**Originality**: Primary source — this is the canonical repo for the tool.

**Reference style**: Refer-back. You'd return to this for CLI syntax, parameter names, and setup commands when using or updating the tool.

**Scrape quality**: Good. All essential content captured—setup, usage examples, test commands, and architectural notes are present. No obvious missing sections, though no screenshots or visual examples of output are included (may not exist in original).