# URL Registry

Manage a queue of URLs to scrape with status tracking.

## Quick Start

```bash
# Import URLs from browser tabs export
./registry.py import ~/Downloads/tabs.txt --auto-skip

# See what's pending
./registry.py list

# Scrape the next URL
./registry.py run

# Scrape all pending
./registry.py run --all
```

## Commands

| Command | Description |
|---------|-------------|
| `import FILE` | Import from browser tabs export (alternating title/URL lines) |
| `add URL` | Add single URL to queue |
| `list` | Show all pending URLs |
| `stats` | Show counts by status |
| `next` | Show next URL to scrape |
| `run` | Scrape next pending URL |
| `run --all` | Scrape all pending URLs |
| `skip URL` | Mark URL as skipped |

## Options

```bash
# Import with auto-skip for non-scrapable URLs (YouTube, Discord, etc.)
./registry.py import FILE --auto-skip

# Add URL with title and note
./registry.py add URL --title "Article Title" --note "Why I saved this"

# Skip with reason
./registry.py skip URL --reason "paywall"

# Use custom registry file
./registry.py --registry /path/to/urls.csv list
```

## CSV Format

The registry is a simple CSV file (`url_registry.csv`):

```csv
url,title,added_at,status,scraped_at,note
https://example.com,Example,2026-01-30T...,pending,,saved for research
https://scraped.com,Done,2026-01-30T...,scraped,2026-01-30T...,
https://youtube.com/...,Video,2026-01-30T...,skipped: not scrapable,,
```

### Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Ready to scrape |
| `scraped` | Successfully scraped |
| `failed: <reason>` | Scrape failed |
| `skipped: <reason>` | Intentionally skipped |

## Auto-Skip Patterns

These URLs are automatically skipped with `--auto-skip`:

- YouTube (`youtube.com`)
- Discord (`discord.com`)
- X/Twitter (`x.com`, `twitter.com`)
- Google Chrome pages (`google.com/chrome`)
- Cerebras Cloud dashboard
- Firecrawl app pages
- Privacy.com login

## Browser Tabs Export Format

The import command expects alternating title/URL lines:

```
Article Title Here
https://example.com/article

Another Article
https://example.com/another
```

This matches the output of browser extensions like "Export Tabs URLs".

## Summary Quality Pipeline

When URLs are scraped, they go through a validation pipeline:

1. **Summarizer** generates markdown with:
   - TL;DR (one sentence)
   - Key Quote (verbatim from source)
   - Summary (structured by content type)
   - Assessment (durability, density, originality, etc.)

2. **Programmatic validation** checks:
   - Required sections present
   - TL;DR not empty
   - Key Quote contains quoted text

3. **Judge** evaluates quality against 4 needs:
   - Recall — Will this help remember the content?
   - Decide — Does it help judge whether to re-read?
   - Evaluate — Are properties assessed?
   - Find — Are there specific details to confirm identity?

4. **Frontmatter extraction** creates structured YAML:
   - Properties: durability, content_type, density, originality, reference_style, scrape_quality
   - Entities: people, tools, libraries, companies
   - Tags: 3-5 semantic topics

5. **Frontmatter validation** checks:
   - YAML parses correctly
   - Required fields present
   - Enum values valid
   - tldr/key_quote match summary sections

Retries up to 3 times per stage if validation fails.
