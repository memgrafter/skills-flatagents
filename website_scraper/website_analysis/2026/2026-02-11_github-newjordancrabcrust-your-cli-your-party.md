---
url: https://github.com/newjordan/CrabCrust
title: 'GitHub - newjordan/CrabCrust: Your CLI - Your Party'
scraped_at: '2026-02-11T09:54:40.918889+00:00'
word_count: 861
raw_file: 2026-02-11_github-newjordancrabcrust-your-cli-your-party.txt
tldr: A Rust-based CLI tool that wraps git commands (and potentially others) with arcade-style Braille-based terminal animations,
  turning commits into save disk animations and pushes into rocket launches.
key_quote: Every git commit becomes a save animation, every push launches a rocket, and every command feels like a celebration!
durability: medium
content_type: reference
density: medium
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- newjordan
tools:
- crabcrust
- git
libraries:
- ratatui
- crossterm
companies: []
tags:
- rust
- cli-tools
- git
- terminal-animations
- developer-tools
---

### TL;DR
A Rust-based CLI tool that wraps git commands (and potentially others) with arcade-style Braille-based terminal animations, turning commits into save disk animations and pushes into rocket launches.

### Key Quote
"Every git commit becomes a save animation, every push launches a rocket, and every command feels like a celebration!"

### Summary
**What it does:**
- Wraps CLI commands (primarily git) with procedural Unicode Braille animations
- Uses Braille patterns (U+2800 to U+28FF) for 8× terminal resolution (2×4 dots per cell = 256 patterns)
- Renders inline using 1/3 of terminal height to avoid workflow disruption

**Installation:**
```bash
git clone https://github.com/newjordan/CrabCrust.git
cd CrabCrust
cargo build --release
cargo install --path .  # optional system install
```

**Basic usage:**
```bash
crabcrust git commit -m "message"  # Shows floppy disk save animation
crabcrust git push                  # Shows rocket launch
crabcrust git pull                  # Shows spinner
crabcrust demo all                  # Test all animations
```

**Recommended setup** — add to `.bashrc` or `.zshrc`:
```bash
alias git="crabcrust git"
```

**Current animations:**
- **Spinner**: Rotating circle with trailing effect (loading states, pull, status)
- **Rocket**: Launch animation with procedural stars, flame effects (git push, 2 sec)
- **Save**: Floppy disk with progress bar and checkmark (git commit, 1.5 sec)

**Architecture:**
- `braille/` — High-res Braille grid rendering
- `rendering/` — Terminal management (Ratatui + Crossterm)
- `animation/` — Animation engine with procedural animations
- `executor/` — Command execution & output capture
- `wrapper/` — CLI wrappers (git, cargo, etc.)

**Extensibility:**
- Custom animations implement the `Animation` trait with `update()`, `render()`, and `name()` methods
- `BrailleGrid` provides `draw_circle()` and line drawing via Bresenham's algorithm

**Experimental (WIP):**
- GIF/video to Braille conversion pipeline (`cargo build --release --features gif`)

**Planned features:**
- Cargo wrapper, config file for custom mappings, plugin system, more animations (download, merge, error states)

**License:** Dual-licensed Apache 2.0 or MIT

### Assessment
**Durability**: Medium. Core concepts (Braille rendering, animation traits) are stable, but the tool appears to be in early development with experimental features and planned changes. Git integration should remain relevant.

**Content type**: Reference / announcement (project README)

**Density**: Medium. Clear documentation with code examples, but some sections are aspirational (planned features, experimental work) rather than currently functional.

**Originality**: Primary source. This is the project's own documentation.

**Reference style**: Refer-back. You'd return for installation commands, the Animation trait API, and architecture overview when extending or troubleshooting.

**Scrape quality**: Good. All sections captured including code blocks, directory structure, and usage examples. No images were present in the source (the actual animation demos would need to be run to see output).