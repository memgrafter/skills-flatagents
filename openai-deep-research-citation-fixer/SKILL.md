---
name: openai-deep-research-citation-fixer
description: >
  Deterministically fixes broken OpenAI Deep Research markdown citations without
  using an LLM: creates a .bkp backup, rewrites citation markers, rebuilds
  references, and runs strict regex validation.
---

Use this when a Deep Research markdown export contains broken markers like `citeturn...` or `entity...` and you want a one-command cleanup.

By default it warns/stops if `Citations`/`References` are not pasted at the bottom of the document.

## Why use it

- No LLM needed (fully deterministic Python transform)
- Safe by default (`<file>.bkp` created before write)
- Rebuilds clean `## References` with anchor IDs
- Warns if citations are not at the bottom (safer for paste workflows)
- Runs direct-match validation and returns JSON pass/fail report

## When to use

- OpenAI Deep Research markdown files with broken citations
- Reports that have `Citations · N` blocks with duplicated URL lines
- Batch cleanup workflows where repeatability matters

## When NOT to use

- Non-markdown files
- Cases where you need semantic remapping from `turn...` IDs to exact per-claim URLs (not available in exported markdown)

## Usage

```bash
~/code/skills-flatagents/openai-deep-research-citation-fixer/run.sh ~/Downloads/deep-research-report.md
```

Dry-run (transform + validate, no write):

```bash
~/code/skills-flatagents/openai-deep-research-citation-fixer/run.sh ~/Downloads/deep-research-report.md --no-overwrite
```

Skip bottom-placement warning (advanced/use with intent):

```bash
~/code/skills-flatagents/openai-deep-research-citation-fixer/run.sh ~/Downloads/deep-research-report.md --skip-bottom-warning
```

Auto-accept warning prompts (automation friendly; implies skip):

```bash
~/code/skills-flatagents/openai-deep-research-citation-fixer/run.sh ~/Downloads/deep-research-report.md --yes
```

## Output

JSON report with:
- file path
- backup path
- replacement stats
- validation checks
- final `ok: true/false`
