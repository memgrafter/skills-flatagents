---
name: website-scraper
description: "Turn a URL into a durable knowledge artifact: searchable markdown summary + local raw text archive, so you can recall it later without revisiting the web."
---

# Website Scraper

Archive web pages into a personal knowledge base with structured summaries and preserved source text.

## Why use it

- **Preserve disappearing pages** — keep a local copy before content changes or vanishes
- **Fast recall** — read a concise summary instead of re-reading the full page
- **Reliable re-use** — raw extracted text is saved for future LLM context
- **Searchable metadata** — YAML frontmatter supports filtering/query workflows

## When to use

- Saving tutorials, docs, blog posts, or repo READMEs for later
- Building a research/reference archive
- Capturing sources for ongoing project work
- Converting “read later” links into durable notes

## When NOT to use

- JavaScript-heavy SPAs that require browser rendering
- Pages behind auth/paywalls/captchas
- High-volume crawling (this flow is designed for one URL at a time)

## Usage

```bash
./run.sh "https://example.com/article"
```

## Examples

```bash
# Archive a blog post
./run.sh "https://simonwillison.net/2024/Dec/19/one-shot-python-tools/"

# Archive a GitHub README page
./run.sh "https://github.com/SWE-agent/mini-swe-agent"

# Use a custom archive location
DATA_DIR=~/research ./run.sh "https://arxiv.org/abs/2501.09891"
```

## Output

Per URL, the scraper writes:
- `{year}/{date}_{slug}.md` — summary + YAML frontmatter
- `{year}/raw/{date}_{slug}.txt` — raw extracted text (for LLM context)
- `{year}/README.md` — auto-updated index row

## How it works

Fetch page → extract clean text (trafilatura) → generate validated summary/frontmatter → save summary + raw text.

Cost: ~0.5 cents/page. Benefit: permanent, searchable, LLM-ready references.
