---
url: https://github.com/cachix/devenv
title: 'GitHub - cachix/devenv: Fast, Declarative, Reproducible, and Composable Developer Environments using Nix'
scraped_at: '2026-02-11T10:03:32.246558+00:00'
word_count: 613
raw_file: 2026-02-11_github-cachixdevenv-fast-declarative-reproducible-and-compos.txt
tldr: devenv.sh is a Nix-based tool that creates declarative, reproducible developer environments with built-in language support,
  services (like Postgres), process management, and direnv integration.
key_quote: devenv.sh - Fast, Declarative, Reproducible, and Composable Developer Environments
durability: medium
content_type: reference
density: medium
originality: primary
reference_style: skim-once
scrape_quality: good
people: []
tools:
- devenv
- nix
- direnv
- watchexec
libraries: []
companies:
- cachix
tags:
- developer-environments
- nix
- declarative-configuration
- reproducible-builds
- dev-tools
---

### TL;DR
devenv.sh is a Nix-based tool that creates declarative, reproducible developer environments with built-in language support, services (like Postgres), process management, and direnv integration.

### Key Quote
"devenv.sh - Fast, Declarative, Reproducible, and Composable Developer Environments"

### Summary
A developer environment manager built on Nix that simplifies creating project-specific shells:

**Core Workflow**
- `devenv init` → generates `devenv.nix`, `devenv.yaml`, `.gitignore`, `.envrc`
- `devenv shell` → activates the environment
- `devenv up` → starts processes in foreground

**Configuration (`devenv.nix`) supports:**
- **Environment variables**: `env.GREET = "devenv"`
- **Packages**: `packages = [ pkgs.git ]`
- **Languages**: `languages.rust.enable = true` (presets for many languages)
- **Services**: `services.postgres.enable = true` (built-in service definitions)
- **Scripts**: `scripts.hello.exec = ''...''`
- **Processes**: Long-running services via `processes.dev.exec`
- **Tasks**: `tasks."myproj:setup".exec` with dependency ordering
- **Tests**: `enterTest` for CI validation
- **Git hooks**: `git-hooks.hooks.shellcheck.enable = true`
- **Outputs**: Build artifacts via `outputs = { ... }`

**Key CLI Commands (v1.9.0)**
- `generate` — AI-powered scaffold generation
- `search` — Find packages in nixpkgs
- `test` — Run tests
- `container` — Build/copy/run containers
- `direnvrc` — direnv integration
- `mcp` — Model Context Protocol server for AI assistants
- `repl` — Interactive config inspection

**Notable Options**
- `--clean` — Isolate from host environment variables
- `--impure` — Relax hermeticity
- `--profile` — Multiple configuration profiles
- `--override-input` — Override nix inputs

### Assessment
**Durability**: Medium. Version 1.9.0 shown; Nix ecosystem evolves slowly but CLI options and features may change. Core concepts are stable.

**Content type**: Reference / documentation

**Density**: Medium. Shows substantial configuration example and comprehensive CLI reference, but this is a README overview rather than deep documentation.

**Originality**: Primary source — official GitHub repository README

**Reference style**: Skim-once to understand capabilities, then refer-back for CLI options. Full docs at devenv.sh/reference/options/.

**Scrape quality**: Good. Captured the full README with configuration example and complete CLI help output.