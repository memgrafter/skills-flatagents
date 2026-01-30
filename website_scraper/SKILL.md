---
name: website-scraper
description: Scrape a URL to clean text and generate an LLM-friendly summary. Saves raw content and markdown summary with YAML frontmatter for programmatic access.
---

# Website Scraper

Archive web pages as clean text and generate summaries optimized for LLM consumption.

## Why use it

- **Clean extraction** — Removes boilerplate, ads, navigation; keeps article content
- **LLM-optimized** — Raw text format maximizes summary quality
- **Organized archive** — Year folders, date-ordered, YAML frontmatter for programmatic access
- **Dual output** — Raw .txt for archival, .md summary for quick reference

## When to use

- Archiving articles, documentation, or reference material
- Building a knowledge base from web sources
- Capturing content before it disappears
- Creating searchable summaries of web resources

## When NOT to use

- JavaScript-heavy SPAs (no browser rendering)
- Sites requiring authentication
- Bulk scraping (one URL at a time)

## Usage

```bash
# Basic usage
./run.sh "https://example.com/article"

# With custom data directory
DATA_DIR=/path/to/archive ./run.sh "https://example.com/article"
```

## Output

Creates two files in `DATA_DIR/{year}/`:

1. **`{date}_{slug}.txt`** — Raw extracted text (no formatting)
2. **`{date}_{slug}.md`** — Summary with YAML frontmatter:

```yaml
---
url: https://example.com/article
title: Article Title
scraped_at: 2026-01-30T08:56:00Z
word_count: 1234
---

## Summary

Key points extracted by LLM...
```

Also updates `DATA_DIR/{year}/README.md` with an index of all scraped pages.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `~/code/skills-flatagents/website_scraper/website_analysis` | Archive location |

## How it works

1. **Scrape** — Fetches URL, extracts clean text via trafilatura
2. **Summarize** — LLM generates structured summary
3. **Save** — Writes .txt and .md files, updates year index

Cost: ~1-2 cents per page (Cerebras). Benefit: Permanent, searchable archive with LLM-ready summaries.
