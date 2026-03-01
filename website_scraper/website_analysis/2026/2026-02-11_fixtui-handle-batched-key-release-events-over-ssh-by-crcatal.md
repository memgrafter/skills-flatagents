---
url: https://github.com/badlogic/pi-mono/pull/538#issuecomment-3720734306
title: 'fix(tui): handle batched key release events over SSH by crcatala · Pull Request #538 · badlogic/pi-mono'
scraped_at: '2026-02-11T10:17:19.428532+00:00'
word_count: 1025
raw_file: 2026-02-11_fixtui-handle-batched-key-release-events-over-ssh-by-crcatal.txt
tldr: 'A pull request documenting a TUI keyboard input bug over SSH where batched key events caused dropped characters, with
  two solution approaches discussed: regex filtering versus lower-level input splitting.'
key_quote: Over SSH (and sometimes locally with fast typing), the terminal batches multiple events into a single data chunk...
  When this batched input arrives, isKeyRelease() returns true because the string contains :3u. The code then drops the entire
  batch, including the valid key press events.
durability: medium
content_type: mixed
density: high
originality: primary
reference_style: skim-once
scrape_quality: good
people:
- crcatala
tools:
- ssh
- ghostty
- pi-mono
libraries:
- opentui
companies: []
tags:
- terminal-ui
- ssh
- keyboard-protocol
- kitty-protocol
- input-batching
---

### TL;DR
A pull request documenting a TUI keyboard input bug over SSH where batched key events caused dropped characters, with two solution approaches discussed: regex filtering versus lower-level input splitting.

### Key Quote
"Over SSH (and sometimes locally with fast typing), the terminal batches multiple events into a single data chunk... When this batched input arrives, isKeyRelease() returns true because the string contains :3u. The code then drops the entire batch, including the valid key press events."

### Summary
**Problem**: Characters dropped/skipped when typing quickly over SSH connections in pi-mono TUI (v0.37.8, MacOS → Ubuntu 24.04.3 via Ghostty terminal)

**Root Cause**:
- Recent Kitty keyboard protocol flag 2 addition (`\x1b[>3u`) enabled key release event reporting
- The `isKeyRelease()` check used `includes()` to detect release patterns (`:3u`, `:3~`)
- Over SSH, terminal batches multiple events: `"\x1b[97u\x1b[97;1:3u\x1b[98u\x1b[98;1:3u"` (press a, release a, press b, release b)
- Boolean check dropped entire batch if ANY release event present

**PR Author's Solution** (superseded):
- `filterKeyReleases()` using regex to strip only release sequences while preserving presses
- 42 test cases added covering CSI u releases, functional keys, arrow keys, batching scenarios

**Maintainer's Alternative** (merged):
- `StdinBuffer` class (adapted from OpenTUI, MIT) splits batched stdin into individual sequences at terminal layer
- Each `handleInput()` call receives single event
- Handles incomplete escape sequences across chunks
- Handles bracketed paste mode

**Outcome**: PR closed; maintainer implemented lower-level fix, released same day

### Assessment
**Durability**: Medium — The concepts (terminal batching, Kitty protocol, SSH latency effects) are durable, but specific code and version references will age.

**Content type**: Technical discussion / bug fix documentation

**Density**: High — Contains specific escape sequences, regex patterns, commit hashes, test coverage breakdowns, and clear before/after comparisons.

**Originality**: Primary source — This is the actual development discussion where the bug was diagnosed and resolved.

**Reference style**: Skim-once — Worth understanding the batching problem once; unlikely to reference again unless debugging similar terminal issues.

**Scrape quality**: Good — Captures the full PR description, code snippets, and maintainer response. The "rogue AI reviewer" comments at the end are amusing noise but complete.