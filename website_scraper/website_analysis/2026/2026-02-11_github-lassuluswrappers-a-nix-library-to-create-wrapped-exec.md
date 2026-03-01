---
url: https://github.com/Lassulus/wrappers
title: 'GitHub - Lassulus/wrappers: A Nix library to create wrapped executables via the module system'
scraped_at: '2026-02-11T10:06:16.022150+00:00'
word_count: 1030
raw_file: 2026-02-11_github-lassuluswrappers-a-nix-library-to-create-wrapped-exec.txt
tldr: A Nix library that lets you create wrapped executables with custom flags, environment variables, and runtime dependencies
  using the Nix module system, solving the problem of maintaining separate wrapper configurations across NixOS, home-manager,
  nix-darwin, and devenv.
key_quote: Are you annoyed by rewriting modules for every platform? nixos, home-manager, nix-darwin, devenv? Then this library
  is for you!
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- Lassulus
- viperML
- Vimjoyer
tools:
- nix
- nixos
- home-manager
- nix-darwin
- devenv
- lndir
libraries:
- wrappers
companies: []
tags:
- nix
- nixos
- wrapper-library
- module-system
- configuration-management
---

### TL;DR
A Nix library that lets you create wrapped executables with custom flags, environment variables, and runtime dependencies using the Nix module system, solving the problem of maintaining separate wrapper configurations across NixOS, home-manager, nix-darwin, and devenv.

### Key Quote
> "Are you annoyed by rewriting modules for every platform? nixos, home-manager, nix-darwin, devenv? Then this library is for you!"

### Summary

**Core Components:**
- `lib.wrapPackage` — Low-level function to wrap packages with flags, env vars, runtime dependencies
- `lib.wrapModule` — High-level function to create reusable wrapper modules with type-safe options
- `wrapperModules` — Pre-built modules for common packages (mpv, notmuch, etc.)

**wrapPackage Options:**
- `package` / `exePath` / `binName` — Target package and binary
- `runtimeInputs` — Packages added to PATH
- `env` — Attribute set of environment variables
- `flags` — Attrset where `true` = flag alone, `"string"` = flag with arg, `false`/`null` = omit
- `flagSeparator` — `" "` (default) or `"="` for `--flag=value` style
- `args` — Direct argv list (overrides flags)
- `preHook` — Shell script before command
- `filesToPatch` — Glob patterns for files needing path updates (default: `["share/applications/*.desktop"]`)
- `filesToExclude` — Glob patterns to exclude from wrapped package

**wrapModule Features:**
- Uses `lib.evalModules` for type-safe configuration
- Custom `wlib.types.file` type with `content` and `path` options
- `apply` function instantiates wrapper, returns config with `.wrapper` attribute
- `apply` can be chained to extend configurations

**Example Usage:**
```nix
# mpv with scripts and config
(wrappers.wrapperModules.mpv.apply {
  pkgs = pkgs;
  scripts = [ pkgs.mpvScripts.mpris ];
  "mpv.conf".content = ''vo=gpu'';
}).wrapper

# Simple package wrap
wrappers.lib.wrapPackage {
  inherit pkgs;
  package = pkgs.curl;
  runtimeInputs = [ pkgs.jq ];
  env = { CURL_CA_BUNDLE = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"; };
  flags = { "--silent" = true; "--connect-timeout" = "30"; };
}
```

**Technical Details:**
- Preserves all outputs from original package (man pages, completions)
- Uses `lndir` for symlinking directory structures
- Handles multi-output derivations correctly
- Desktop files patched by default to update Exec= and Icon= paths

**Inspiration/Alternatives:**
- Inspired by `wrapper-manager` by viperML
- Goal: upstream schema into nixpkgs with optional `module.nix` per package

### Assessment

**Durability (medium):** The library API will evolve, but the concept of module-based wrapping is stable. Depends on Nix ecosystem patterns that may shift. No version tag visible.

**Content type:** Reference / tutorial mixed

**Density (high):** Dense with specific options, types, and working code examples. Minimal fluff.

**Originality:** Primary source — this is the canonical repository

**Reference style:** Refer-back — you'll return to look up specific options and patterns when building wrappers

**Scrape quality (good):** Full README captured with all examples, option tables, and API documentation intact. Code blocks preserved.