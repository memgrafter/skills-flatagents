---
url: https://github.com/OlaProeis/Ferrite
title: 'GitHub - OlaProeis/Ferrite: A fast, lightweight text editor for Markdown, JSON, YAML, and TOML files. Built with Rust
  and egui for a native, responsive experience.'
scraped_at: '2026-02-11T10:38:12.564408+00:00'
word_count: 2568
raw_file: 2026-02-11_github-olaproeisferrite-a-fast-lightweight-text-editor-for-m.txt
tldr: Ferrite is a native desktop text editor for Markdown, JSON, YAML, and TOML files, built with Rust and egui, notable
  for being 100% AI-generated and featuring a custom editor engine with virtual scrolling that handles 80MB files efficiently.
key_quote: This project is 100% AI-generated code. All Rust code, documentation, and configuration was written by Claude (Anthropic)
  via Cursor with MCP tools.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- ferrite
- cursor
- claude
libraries:
- egui
- eframe
- comrak
- syntect
- git2
- clap
companies:
- Anthropic
- SignPath Foundation
tags:
- text-editor
- rust
- ai-generated-code
- markdown
- desktop-application
---

### TL;DR
Ferrite is a native desktop text editor for Markdown, JSON, YAML, and TOML files, built with Rust and egui, notable for being 100% AI-generated and featuring a custom editor engine with virtual scrolling that handles 80MB files efficiently.

### Key Quote
> "This project is 100% AI-generated code. All Rust code, documentation, and configuration was written by Claude (Anthropic) via Cursor with MCP tools."

### Summary

**What it does**: A fast, lightweight text editor specializing in structured text formats (Markdown, JSON, YAML, TOML, CSV) with WYSIWYG editing, live preview, and developer-focused features.

**Installation**:
- Windows: MSI installer or portable ZIP
- Linux: .deb, .rpm, or tar.gz; also available on AUR
- macOS: tar.gz (experimental support)
- Build from source: Rust 1.70+, platform-specific GTK dependencies on Linux

**Standout features**:
- Custom editor engine with virtual scrolling (80MB file = ~80MB RAM)
- Multi-cursor editing (Ctrl+Click)
- Code folding with gutter indicators
- Split view: side-by-side raw editor and rendered preview
- Tree viewer for JSON/YAML/TOML with inline editing
- Native Mermaid diagram rendering (11 diagram types)
- CSV/TSV table view with rainbow columns
- Workspace mode with file tree, quick switcher (Ctrl+P), search-in-files
- Git integration with visual status indicators
- Integrated terminal with tiling, splitting, and layout persistence
- Multi-encoding support (UTF-8, Latin-1, Shift-JIS, Windows-1252, GBK)
- CJK paragraph indentation options

**Technical stack**: Rust 1.70+, egui/eframe 0.28, comrak (Markdown), syntect (syntax highlighting), git2 (Git integration)

**Code signing**: Windows releases v0.2.6.1+ are digitally signed via SignPath Foundation, resolving SmartScreen and antivirus false positives caused by Rust binary patterns and the Live Pipeline feature's use of `cmd.exe /C`.

**AI development workflow**: The author documents their AI-assisted development process publicly, including PRDs, handover prompts, and session context—intended as a learning resource for others.

**Current version**: v0.2.6.1 (first code-signed release)

### Assessment

**Durability**: Medium. The core concepts and feature set are stable, but version-specific details (v0.2.6.1, code signing status, experimental macOS support) will become stale as development progresses. The AI workflow documentation has higher durability as a methodology reference.

**Content type**: Reference / announcement (mixed). Primarily a comprehensive README serving as documentation, with announcement elements for the v0.2.6.1 release.

**Density**: High. Packed with specific features, keyboard shortcuts, installation commands, configuration paths, and technical details. Minimal padding.

**Originality**: Primary source. This is the official project repository with first-party documentation of a genuinely novel project (AI-generated codebase with transparent workflow documentation).

**Reference style**: Refer-back / deep-study. Worth revisiting for keyboard shortcuts, installation procedures, and as a case study for AI-assisted development workflows.

**Scrape quality**: Good. The README content is fully captured including tables, code blocks, and version details. No apparent missing sections.