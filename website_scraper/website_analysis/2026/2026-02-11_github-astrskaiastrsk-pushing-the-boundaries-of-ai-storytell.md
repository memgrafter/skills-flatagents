---
url: https://github.com/astrskai/astrsk
title: 'GitHub - astrskai/astrsk: Pushing the boundaries of AI storytelling'
scraped_at: '2026-02-11T09:49:33.703297+00:00'
word_count: 875
raw_file: raw/2026-02-11_github-astrskaiastrsk-pushing-the-boundaries-of-ai-storytell.txt
tldr: Astrsk is a local-first, cross-platform AI storytelling/roleplaying application featuring a visual workflow editor,
  support for 10+ AI providers, and character card imports—available as a PWA or native desktop app.
key_quote: 100% Local-First - All data stored locally on your device - your stories stay yours
durability: medium
content_type: mixed
density: medium
originality: primary
reference_style: refer-back
scrape_quality: good
people: []
tools:
- astrsk
- electron
- vite
- pnpm
- pglite
libraries:
- react
- typescript
- tailwindcss
- tanstack-router
- tanstack-query
- zustand
- shadcn-ui
- drizzle-orm
- vercel-ai-sdk
companies:
- openai
- anthropic
- google
- deepseek
- ollama
- xai
tags:
- ai-storytelling
- local-first
- roleplaying
- pwa
- visual-workflow-editor
---

### TL;DR
Astrsk is a local-first, cross-platform AI storytelling/roleplaying application featuring a visual workflow editor, support for 10+ AI providers, and character card imports—available as a PWA or native desktop app.

### Key Quote
"100% Local-First - All data stored locally on your device - your stories stay yours"

### Summary
**What it does:**
- AI-powered storytelling and roleplaying platform with customizable AI agents
- Visual drag-and-drop flow editor for designing conversation workflows
- Supports character card imports (v2/v3) and custom agent creation

**Key features:**
- **Multi-provider support**: OpenAI, Anthropic, Google AI, DeepSeek, Ollama, xAI, and more
- **Local-first architecture**: All data stored in-browser using PGlite (PostgreSQL WASM)
- **Cross-platform**: PWA works in any browser; native apps for Windows, macOS, Linux
- **Offline capable**: Full functionality without internet (PWA)
- **No account required**: No data collection

**Tech stack:**
- Frontend: React 18, TypeScript 5, Vite 6, Tailwind CSS v4
- State: TanStack Router, TanStack Query v5, Zustand
- UI: shadcn/ui (Radix UI)
- Database: PGlite + Drizzle ORM (local only)
- AI: Vercel AI SDK with multiple providers
- Desktop: Electron with auto-updater

**Project structure:**
- Monorepo with `apps/pwa/`, `apps/electron/`, and `packages/design-system/`
- Uses Feature-Sliced Design architecture

**Installation:**
- Prebuilt binaries: `.exe` (Windows), `.dmg` (Mac), `.AppImage` (Linux—untested)
- From source: Requires Node.js v22+, pnpm v10+
- Commands: `pnpm install`, `pnpm dev:pwa`, `pnpm dev:electron`

**Self-hosting note:**
- Requires SSL for LAN access (OPFS, PGlite, service workers need secure context)
- Instructions provided for adding `@vitejs/plugin-basic-ssl`

### Assessment
**Durability**: Medium. The core concepts (local-first AI, visual flow editing) are durable, but version-specific details (React 18, Vite 6, Tailwind v4) will age. Tech stack versions should be treated as snapshot.

**Content type**: Reference / announcement (mixed). Primarily a project README serving as documentation and introduction.

**Density**: Medium. Well-structured README with good information per section, though some areas (like the visual flow editor capabilities) are described briefly without deep detail.

**Originality**: Primary source. This is the official repository documentation from the astrsk.ai team.

**Reference style**: Refer-back. Useful for installation commands, project structure navigation, and self-hosting SSL configuration.

**Scrape quality**: Good. The full README content appears captured, including code blocks, file structure, and commands. No obvious missing sections.