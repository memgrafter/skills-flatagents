# Stdout Hygiene Fixes (codebase_ripper + flatagents SDK)

## Applied now (codebase_ripper)
**Files:**
- `codebase_ripper/run.sh`
- `codebase_ripper/src/codebase_ripper/main.py`

Added safe defaults so stdout stays machine-readable:
- `FLATAGENTS_METRICS_ENABLED=false` (default)
- `FLATAGENTS_LOG_LEVEL=ERROR` (default)
- `LITELLM_LOG=ERROR` (default)

Also updated runtime logger levels to respect env defaults and suppress SDK/provider chatter by default:
- `flatagents` / `flatagents.utils` logger level derives from `FLATAGENTS_LOG_LEVEL` (default `ERROR`)
- `LiteLLM` / `litellm` logger level derives from `LITELLM_LOG` (default `ERROR`)

Rationale: `run.sh --json` should emit only JSON payloads on stdout. Logs/metrics should not be mixed into payload streams.

---

## SDK fixes recommended (flatagents)

### 1) Logging stream should default to stderr
**Current behavior:** `setup_logging()` attaches `StreamHandler(sys.stdout)`.

**Fix:** change default handler to `sys.stderr`.
- File: `flatagents/monitoring.py`
- Area: `setup_logging()`
- Replace: `logging.StreamHandler(sys.stdout)`
- With: `logging.StreamHandler(sys.stderr)`

Why: logs are operational diagnostics; stdout should remain data channel.

### 2) Metrics exporter should not default to console stdout
**Current behavior:** `_init_metrics()` defaults `OTEL_METRICS_EXPORTER` to `console`.

**Fix options (preferred order):**
1. Default to metrics disabled unless explicitly enabled in app (`FLATAGENTS_METRICS_ENABLED=false`), or
2. Default exporter to `otlp` when enabled, or
3. If `console` is used, emit to stderr (not stdout).

Why: console metric dumps (`resource_metrics` JSON blobs) break CLI JSON contracts.

### 3) Console metric exporter should write to stderr
**Current behavior:** custom compact exporter writes via `sys.stdout.write(...)`.

**Fix:** write to `sys.stderr.write(...)` and flush stderr.
- File: `flatagents/monitoring.py`
- Area: `_CompactConsoleMetricExporter.export()`

### 4) Add explicit SDK toggle for output channel hygiene
Add an env/config switch such as:
- `FLATAGENTS_STDOUT_HYGIENE=true` (default)

Behavior when enabled:
- logs -> stderr
- console metrics -> stderr
- no implicit `print()` from SDK internals

### 5) Document stdout/stderr contract for SDK consumers
In SDK docs, define:
- **stdout:** data/payload channel
- **stderr:** logs, warnings, telemetry, progress

Provide a short “CLI-safe defaults” snippet for wrapper scripts.

---

## Suggested migration policy
- Keep backward compatibility with an escape hatch:
  - `FLATAGENTS_LEGACY_STDOUT_LOGGING=true` (temporary)
- Announce deprecation, then remove legacy mode in next minor/major release.
