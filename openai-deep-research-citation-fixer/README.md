# openai-deep-research-citation-fixer

Deterministic markdown citation cleanup for OpenAI Deep Research exports.

## What it does

1. Creates backup: `<file>.bkp`
2. Replaces broken citation markers (`cite...`) with `([sources](#references))`
3. Replaces broken entity markers (`entity...`) with plain text labels
4. Rebuilds a clean `## References` section with numbered anchors
5. Warns/stops if citations are not pasted at the bottom (override with `--skip-bottom-warning` or `--yes`)
6. Validates output with strict regex/direct-match checks

## Script

- `fix_openai_deep_research_citations.py`

## Run

```bash
python3 fix_openai_deep_research_citations.py ~/Downloads/deep-research-report.md
```

Or via wrapper:

```bash
./run.sh ~/Downloads/deep-research-report.md
```

If the citations block is intentionally not at the bottom:

```bash
./run.sh ~/Downloads/deep-research-report.md --skip-bottom-warning
```

Automation shortcut (implies skip warning):

```bash
./run.sh ~/Downloads/deep-research-report.md --yes
```

## Validation checks

- `## References` exists
- no legacy marker glyphs remain (`  `)
- each reference line matches:
  - `N. <a id="ref-N"></a>[url](url)`
- numbering is contiguous and anchors match line numbers
- URL label text equals URL target
- expected count of inline `([sources](#references))` equals replaced cite marker count
