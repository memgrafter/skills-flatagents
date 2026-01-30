---
name: website-scraper
description: Archive web pages with LLM summaries. Builds a searchable knowledge base from URLs with clean text extraction and structured markdown.
---

# Website Scraper

Build a permanent, searchable archive of web content with AI-generated summaries.

## Why use it

- **Preserve knowledge** — Capture articles before they disappear or change
- **Quick reference** — LLM summaries let you recall content without re-reading
- **Searchable archive** — YAML frontmatter enables programmatic queries
- **Clean context** — Raw text extraction removes ads/nav for better LLM processing

## When to use

- Saving articles, docs, or tutorials for future reference
- Building a research knowledge base
- Archiving sources for a project
- "Read later" with permanent storage

## When NOT to use

- JavaScript-heavy SPAs (no browser rendering)
- Sites requiring authentication
- Bulk scraping hundreds of URLs (one at a time)

## Usage

```bash
./run.sh "https://example.com/article"
```

## Examples

```bash
# Archive a blog post
./run.sh "https://simonwillison.net/2024/Dec/19/one-shot-python-tools/"

# Archive a GitHub repo README
./run.sh "https://github.com/SWE-agent/mini-swe-agent"

# Use custom archive location
DATA_DIR=~/research ./run.sh "https://arxiv.org/abs/2501.09891"
```

## Output

Two files per URL in `{year}/` folder:
- `{date}_{slug}.txt` — Raw text for LLM context
- `{date}_{slug}.md` — Summary with url/title/date frontmatter

Plus auto-updated `README.md` index per year.

## How it works

Fetches → extracts clean text (trafilatura) → LLM summarizes → saves both.

Cost: ~0.5 cents/page. Benefit: Permanent archive with instant recall.
