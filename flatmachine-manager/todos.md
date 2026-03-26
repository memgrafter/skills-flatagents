# FlatMachines Manager — TODOs

## session notes — 2026-03-25

- `start` now executes embedded registry config only (`config_embedded`), removing temp-file ref-resolution failures.
- Tool registry now uses immutable tool definitions (Tool IDs) with alias rebinding, so schema evolution no longer breaks seeding.
- Runtime mutable state now defaults to `~/.agents/machine-manager` (DB + profiles), seeded by `run.sh`.
- Compatibility restored for existing behavior:
  - `_make_agent_yaml` synthesizes default system prompts when omitted.
  - `temperature` arg remains accepted (ignored) for backward compatibility.
  - `socratic_teacher.run()` accepts `cwd` alias.
- Test baseline after changes: `216 passed, 1 skipped, 3 warnings`.

## readiness punchlist (current)

- [ ] Resolve runtime warning noise (`Unhandled action: human_review`) during `start` runs
- [ ] Keep test gate green in CI (currently green locally)
- [x] Docs alignment for embedded `start` execution + tool ID alias model
- [x] Runtime data dir migration defaults to `~/.agents/machine-manager/`
- [ ] Add doctor check for tool-registry migration health (`tool_aliases` / `tool_definitions`)
- [ ] Add repeatable DB secret scan script (pre-commit/CI)

## runtime data directory

- [ ] Move all mutable state out of the skill directory into `~/.agents/machine-manager/`
  - `machine_manager.db` (registry) — currently created in cwd or repo root
  - Any machine `.sqlite` files (checkpoints, leases, configs)
  - Future: logs, backups
- [x] `run.sh` defaults `--db` to `~/.agents/machine-manager/machine_manager.db`
- [x] `run.sh` bootstrap creates `~/.agents/machine-manager/`, seeds `profiles.yml`, and initializes DB from `schema.sql`
- [ ] Skill directory stays read-only after install — no writes to `skills-flatagents/` or `~/.agents/skills/`
- [ ] `doctor` should check `~/.agents/machine-manager/` exists and is writable
- [ ] Update SKILL.md examples to reflect the new default path

## model profiles — user experience

- [ ] Profiles are hardcoded in Python (`MODEL_CATALOG` in `tools.py`) — users can't see or change them without editing source
- [ ] Need a user-facing config file (YAML or TOML) for profiles so users can define their own or override defaults
  - Candidate location: `~/.agents/machine-manager/profiles.yml` or the existing `config/profiles.yml`
  - Should be seeded with sensible defaults on first run
- [ ] Consider a single `default` profile that just works out of the box — new machines shouldn't require the user to pick a profile
  - `_make_agent_yaml` already defaults to `"default"` but there's no `default` entry in `MODEL_CATALOG`
- [ ] `select-model` CLI command should read from the config file, not hardcoded Python
- [ ] `create` should work with zero `--agent` flags if a default profile + system prompt are available
- [ ] Document how users add/edit profiles without touching Python

## codex prompt cache (session_id / prompt_cache_key)

- [ ] The session_id → prompt_cache_key plumbing is brittle — it's implemented piecemeal across multiple call sites instead of being an inherited property on the transport/client
  - `flatmachines/adapters/flatagent.py` `execute_with_tools()` manually injects `session_id` from `execution_id` into `extra` kwargs
  - `flatagents/flatagent.py` `call()` conditionally forwards `session_id` from `input_data` into `params` only if backend is codex
  - `flatagents/providers/openai_codex_client.py` `_resolve_session_id()` checks `params`, `model_config`, and `codex_session_id` — three separate paths
  - Any new call path (e.g. `execute()` without tools, a new adapter, a non-FlatMachine caller) silently loses the cache key
- [ ] Should be an inherited property on the codex client/transport — set once at construction or session start, automatically included on every send
  - Once a session_id is established for an execution, every LLM call within that execution should carry it without caller cooperation
  - New adapters and call paths get cache hits for free
- [ ] The installed flatmachines package (1.1.1 → 2.0.0) was missing the fix entirely — stale packages silently lose all cache benefit with no warning or error
- [ ] **Cache busting on state/agent transitions**: `execution_id` is set once per machine run and never changes, but the message chain is correctly reset when state or agent identity changes (`_tool_loop_chain_state` / `_tool_loop_chain_agent` guards). This means a different state or agent sends a completely different message prefix under the same `prompt_cache_key` — busting the codex KV cache for that key.
  - Same-state re-entry (e.g. `work → human_review → work` with same agent): chain is restored, cache key matches → OK
  - Cross-state or cross-agent transition (e.g. writer-critic, ooda-workflow, pipeline): chain resets to `[]` but `execution_id` stays the same → same cache key, different messages → **bust**
  - Fix is **not** as simple as `f"{execution_id}:{state_name}:{agent_name}"` — that still busts when the same agent in the same state starts a fresh chain (e.g. re-entered after chain guard mismatch, or a new run of the same state with no history)
  - The real discriminant is whether the message prefix being sent matches what the backend cached under that key. The only reliable signal is whether we're **continuing from a restored chain** or **starting fresh**:
    - Continuing from restored chain (`has_prior_chain=True`) → reuse the cache key that was active when the chain was built
    - Starting fresh (`has_prior_chain=False`) → generate a **new** cache key (e.g. `f"{execution_id}:{uuid4()}"`) so the backend doesn't try to match against a stale prefix
  - The cache key should be stored alongside `_tool_loop_chain` / `_tool_loop_chain_state` / `_tool_loop_chain_agent` and restored or regenerated together
  - This means the codex client cannot own the key — it must come from the orchestrator, because only the orchestrator knows if the conversation is a continuation or a fresh start

## doctor enhancements

- [ ] Check schema version compatibility between `schema.sql` and active `machine_manager.db`
- [ ] Detect schema drift (columns added/removed) and report specific mismatches
- [ ] Check for stale leases (execution_leases with expired TTL but not cleaned up)
- [ ] Check for orphaned checkpoints (executions with no latest pointer)
- [ ] Validate that all agent refs in stored machine configs resolve

## backup + reset

- [ ] `backup` command: copy `machine_manager.db` to `machine_manager.db.<timestamp>.bak`
  - Where do backups go? Same directory? A `backups/` subdir?
  - How many backups to retain before auto-pruning?
- [ ] `reset` command: backup current DB, then re-initialize `machine_manager.db` from `schema.sql`
  - This gives a fresh slate with sample machines
  - Must warn/confirm if the DB has user-created machines
- [ ] `export` command: dump all user-created machines (not samples) to YAML files for portability
- [ ] `import` command: load YAML files back into a fresh DB

## schema migrations

- [ ] Define a schema version table (`schema_version` with single row)
- [ ] Ship migration scripts as numbered SQL files (e.g., `migrations/001_add_tags_column.sql`)
- [ ] `doctor` should detect version mismatch and recommend running migrations
- [ ] `migrate` command: apply pending migrations in order
- [ ] Decide: should `run.sh` auto-migrate on boot, or require explicit `migrate`?
  - Auto-migrate is convenient but risky if migration is destructive
  - Recommendation: auto-migrate for additive changes (new columns/tables), require explicit for destructive

## schema generation

- [ ] Script to regenerate `schema.sql` from current code
  - Should be idempotent and reproducible
  - Run as part of CI/release process
- [ ] Optionally add sample-data seed SQL (separate from schema) for demos

## cull improvements

- [ ] `cull-trim` should report per-execution counts, not just totals
- [ ] `cull-purge` should vacuum the DB after large deletes to reclaim space
- [ ] Consider auto-cull on machine termination (configurable via persistence config)
- [ ] WAL checkpoint before reporting DB size in `cull-stats` (WAL can inflate apparent size)
