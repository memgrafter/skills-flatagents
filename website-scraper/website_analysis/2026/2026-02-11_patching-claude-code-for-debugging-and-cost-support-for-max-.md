---
url: https://mariozechner.at/posts/2025-08-06-cc-antidebug/
title: Patching Claude Code for debugging and /cost support for Max users
scraped_at: '2026-02-11T10:21:51.000260+00:00'
word_count: 709
raw_file: raw/2026-02-11_patching-claude-code-for-debugging-and-cost-support-for-max-.txt
tldr: Mario Zechner created `cc-antidebug`, an NPM tool that patches Claude Code to disable its anti-debugging checks and
  restore `/cost` token usage display for Pro/Max plan subscribers.
key_quote: You have a plan. You don't need to know the numbers. Numbers are bad for you.
durability: low
content_type: tutorial
density: medium
originality: primary
reference_style: refer-back
scrape_quality: good
people:
- Mario Zechner
tools:
- claude-code
- cc-antidebug
- biome
- vs-code
libraries:
- '@mariozechner/cc-antidebug'
companies: []
tags:
- claude-code
- debugging
- reverse-engineering
- npm-tools
- patching
---

### TL;DR
Mario Zechner created `cc-antidebug`, an NPM tool that patches Claude Code to disable its anti-debugging checks and restore `/cost` token usage display for Pro/Max plan subscribers.

### Key Quote
> "You have a plan. You don't need to know the numbers. Numbers are bad for you."

### Summary
**The Problems:**
- Claude Code detects attached debuggers (via environment variables like `--inspect-brk`) and exits, making it impossible to debug apps using the TypeScript/Python SDKs
- The `/cost` command is disabled for Pro/Max plans, showing only a condescending message instead of token usage data

**The Solution - Patching Process:**
1. Format the Claude Code binary using Biome (JavaScript formatter)
2. Search for anti-debugging strings (e.g., `--inspect-brk`)
3. Use regex to replace debugger checks with no-ops
4. Similarly patch the `/cost` logic by finding the "With your Claude Max subscription..." string and bypassing the plan check

**Tool: `@mariozechner/cc-antidebug`**

CLI Usage:
```bash
npx @mariozechner/cc-antidebug patch    # Apply patch
npx @mariozechner/cc-antidebug restore  # Restore original
```

Programmatic Usage:
```javascript
import { patchClaudeBinary, restoreClaudeBinary } from "@mariozechner/cc-antidebug";
patchClaudeBinary();
// ... debugging work ...
restoreClaudeBinary();
```

**Caveats:**
- Claude Code auto-updates, requiring patch reapplication
- Patches may break with new versions

### Assessment
**Durability (low):** Highly version-dependent. Claude Code updates frequently, and each update may break the patches. The approach is sound but will require maintenance.

**Content type:** Tutorial / tool announcement

**Density (medium):** Clear explanations with practical code examples. Some conversational padding but generally focused.

**Originality:** Primary source — the author created the tool and is documenting both the discovery process and usage.

**Reference style:** Refer-back — you'll return to this for the npm package name and commands when you need to apply the patch.

**Scrape quality:** Good — full content captured including code blocks and commands.