# Website Scraper Improvement Plan

## Goal
Make the scraper safe for local/private use and reliable across modern web sources by adding secret redaction, JS rendering fallback, and first-class YouTube ingestion.

## Current Gaps
- Static-only extraction fails on JS-heavy pages.
- YouTube is skipped instead of processed.
- Scraped content can include sensitive data and is written directly to disk.
- Untrusted scraped content is passed directly to LLM prompts without strong guardrails.
- Generated artifacts are stored in-repo by default, increasing accidental commit risk.

## Priorities

### P0 - Security and Data Hygiene
1. Add a redaction pipeline before any LLM call and before file write.
2. Detect and mask high-risk patterns:
   - API keys and bearer tokens
   - OAuth/access/refresh tokens
   - cookie/session values
   - email addresses (configurable)
   - known secret-like key/value pairs
3. Keep a clear marker format for redacted values (for audit/debug), e.g. `[REDACTED_API_KEY]`.
4. Make output path default to outside the repo (user-local data dir).
5. Add ignore rules for generated/local artifacts:
   - `website_analysis/`
   - `dumps/`
   - `url_registry.csv` (if treated as local state)
6. Minimize env propagation in subprocess execution (allowlist instead of full env pass-through).

Acceptance criteria:
- No secrets/tokens survive into `.txt`, `.md`, or model inputs in standard test fixtures.
- Fresh run does not create tracked artifacts in repo by default.

### P1 - Extraction Reliability (JS + Source Adapters)
1. Implement extraction strategy chain:
   - Strategy A: `trafilatura` (fast path)
   - Strategy B: Playwright render + DOM text extraction (fallback)
2. Trigger fallback when:
   - extraction empty/too short
   - boilerplate-dominant text detected
   - known JS-heavy domains
3. Add source-specific adapter for YouTube:
   - fetch metadata (title/channel/date/duration/url)
   - fetch transcript/subtitles when available
   - use transcript as primary content for summary
4. Update queue logic to route YouTube URLs to adapter instead of skip.

Acceptance criteria:
- JS-heavy test URLs succeed with meaningful word count.
- YouTube URLs no longer auto-skip; at minimum metadata-only summaries are produced when transcript unavailable.

### P1 - Prompt and Injection Hardening
1. Add explicit prompt policy in summarizer/judge/frontmatter agents:
   - scraped text is untrusted data, never instructions
   - ignore instruction-like text embedded in pages
2. Bound and sanitize raw content before injection into prompts:
   - truncate with deterministic policy
   - normalize/control suspicious delimiters and tool-like directives
3. Add quality/safety checks:
   - detect likely prompt-injection strings
   - annotate scrape quality and confidence

Acceptance criteria:
- Prompt-injection fixture does not alter system behavior.
- Summaries remain format-valid and instruction-safe.

### P2 - URL Canonicalization and Privacy Controls
1. Improve dedup/canonicalization:
   - normalized host/path
   - remove tracking params (`utm_*`, `fbclid`, etc.)
   - retain identity-critical params where needed
2. Add configurable URL privacy policy:
   - strip/retain query params by domain rules
3. Add auth-awareness:
   - classify likely-auth pages and mark as restricted/manual mode
   - prevent accidental scrape of private app dashboards by default

Acceptance criteria:
- Duplicate rate reduced without collapsing distinct resources.
- Sensitive query parameters not stored in registry/output.

### P2 - Testing, Observability, and Regression Safety
1. Unit tests:
   - redaction rules
   - summary/frontmatter validation helpers
   - URL normalization/canonicalization
   - source routing (web vs YouTube adapter)
2. Integration tests:
   - static page success
   - JS fallback success
   - YouTube transcript + metadata-only fallback
3. Structured logging fields:
   - `source_type`, `strategy_used`, `redactions_count`, `content_length`, `fallback_used`

Acceptance criteria:
- CI-level test coverage on critical path.
- Logs make failures diagnosable without exposing secrets.

## Implementation Sequence
1. P0 security controls first.
2. JS fallback framework and extraction strategy chain.
3. YouTube adapter and registry flow updates.
4. Prompt hardening and injection safeguards.
5. Canonicalization/privacy improvements.
6. Test suite + observability rollout.

## File-Level Change Plan
- `src/website_scraper/hooks.py`
  - add redaction + extraction strategy chain + content safety guards
- `src/website_scraper/registry.py`
  - replace YouTube skip with adapter routing metadata
  - improve canonicalization/dedup logic
- `registry.py`
  - tighten subprocess env handling
  - route URL types cleanly
- `agents/summarizer.yml`
  - explicit untrusted-content policy
- `agents/judge_summary.yml`
  - explicit untrusted-content policy
- `agents/frontmatter.yml`
  - explicit untrusted-content policy
- `src/website_scraper/main.py`
  - safer default output dir behavior
- `README.md` and `REGISTRY.md`
  - update capabilities, security model, and limitations
- repo `.gitignore`
  - ignore generated artifacts and local dump files

## Rollout Notes
- Ship behind feature flags where practical:
  - `SCRAPER_ENABLE_JS_FALLBACK=1`
  - `SCRAPER_ENABLE_YOUTUBE=1`
  - `SCRAPER_STRICT_REDACTION=1`
- Provide a migration note for existing archives, including optional retroactive redaction tool.
