---
url: https://github.com/Schniz/fnm
title: 'GitHub - Schniz/fnm: 🚀 Fast and simple Node.js version manager, built in Rust'
scraped_at: '2026-01-30T20:40:37.095927+00:00'
word_count: 747
raw_file: 2026-01-30_github-schnizfnm-fast-and-simple-nodejs-version-manager-buil.txt
tldr: fnm is a cross-platform Node.js version manager written in Rust, designed for speed and ease of use, supporting `.nvmrc`/`.node-version`
  files and offering installation via package managers or a single binary.
key_quote: 🚀 Fast and simple Node.js version manager, built in Rust
durability: high
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- Schniz
tools:
- fnm
- node.js
- cargo
- rust
- brew
- winget
- scoop
- choco
- bash
- zsh
- fish
- powershell
- cmder
- curl
- unzip
libraries: []
companies:
- Vercel
tags:
- node.js
- version-management
- rust
- developer-tools
- shell-integration
---

### TL;DR
fnm is a cross-platform Node.js version manager written in Rust, designed for speed and ease of use, supporting `.nvmrc`/`.node-version` files and offering installation via package managers or a single binary.

### Key Quote
"🚀 Fast and simple Node.js version manager, built in Rust"

### Summary
- **What it does**: Manages multiple Node.js versions with a focus on performance (built in Rust) and cross-platform compatibility (macOS, Windows, Linux).
- **Installation**:
  - **Script (bash/zsh/fish)**: `curl -fsSL https://fnm.vercel.app/install | bash` (requires `curl` and `unzip`).
  - **macOS**: `brew install fnm` or `brew upgrade fnm`.
  - **Windows**: `winget install Schniz.fnm`, `scoop install fnm`, or `choco install fnm`.
  - **Cargo**: `cargo install fnm`.
  - **Manual**: Download binary and add to PATH.
- **Shell Setup**: Essential step requiring shell evaluation.
  - **Recommended command**: `eval "$(fnm env --use-on-cd --shell <shell_name>)"`
  - **Bash**: Add to `~/.bashrc`.
  - **Zsh**: Add to `~/.zshrc`.
  - **Fish**: Source in `~/.config/fish/conf.d/fnm.fish`.
  - **PowerShell**: Add to profile (`Microsoft.PowerShell_profile.ps1`).
- **Key Features**:
  - Reads `.node-version` and `.nvmrc` files automatically.
  - Supports `--use-on-cd` to switch versions when changing directories.
  - Ships with built-in shell completions (`fnm completions --shell <SHELL>`).
- **Configuration**:
  - Default install dir: `$XDG_DATA_HOME/fnm` (Linux) or `$HOME/Library/Application Support/fnm` (macOS).
  - Flags: `--skip-shell` (prevents modifying shell config), `--install-dir` (custom path).
- **Uninstallation**: Delete the `.fnm` folder and remove lines from shell configuration files.
- **Development**: Build via `cargo build --release` from the git repository.

### Assessment
- **Durability**: High. While installation URLs may eventually shift, the core usage patterns (`eval "$(fnm env...)"`) and shell integration methods are stable system administration concepts.
- **Content type**: Reference / Tutorial. It provides installation instructions and configuration snippets.
- **Density**: High. Packed with specific file paths, package manager commands, and shell configuration code.
- **Originality**: Primary source. This is the official documentation for the tool.
- **Reference style**: Refer-back. This is a "keep handy" resource for copying shell integration lines during environment setup.
- **Scrape quality**: Good. The text captures all commands, flags, and logical sections of the README, though code bullets were flattened into plain text.