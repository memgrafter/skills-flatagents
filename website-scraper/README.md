# Website Scraper

A FlatAgents skill that scrapes web pages to clean text and generates LLM-optimized summaries.

## Features

- **Clean extraction** — Uses trafilatura to remove boilerplate, ads, navigation
- **LLM summaries** — Generates structured markdown summaries
- **Organized archive** — Year folders, date-ordered files, YAML frontmatter
- **GitHub-ready** — Each year folder has a README.md index

## Installation

```bash
# From skills-flatagents root
./install.sh

# Or install trafilatura manually
pip install trafilatura
```

## Usage

```bash
# Basic usage
./run.sh "https://example.com/article"

# With custom data directory
DATA_DIR=/path/to/archive ./run.sh "https://example.com/article"

# Or pass as second argument
./run.sh "https://example.com/article" /path/to/archive
```

## Output Structure

```
website_analysis/
├── 2026/
│   ├── README.md                           # Year index
│   ├── 2026-01-30_article-title.txt        # Raw extracted text
│   └── 2026-01-30_article-title.md         # Summary with frontmatter
└── 2027/
    └── ...
```

### Summary Format

```markdown
---
url: https://example.com/article
title: "Article Title"
scraped_at: 2026-01-30T08:56:00Z
word_count: 1234
raw_file: 2026-01-30_article-title.txt
---

Overview of the article...

## Key Points

- Point 1
- Point 2
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `~/code/skills-flatagents/website_scraper/website_analysis` | Archive location |

## Limitations

- No JavaScript rendering (static HTML only)
- No authentication support
- One URL at a time

## Development

```bash
# Run directly with Python
PYTHONPATH=src python -m website_scraper.main "https://example.com"
```
