# FlatMachines Manager — TODOs

## runtime data directory

- [ ] Move all mutable state out of the skill directory into `~/.agents/machine-manager/`
  - `machine_manager.db` (registry) — currently created in cwd or repo root
  - Any machine `.sqlite` files (checkpoints, leases, configs)
  - Future: logs, backups
- [ ] `run.sh` should default `--db` to `~/.agents/machine-manager/machine_manager.db`
- [ ] `run.sh` bootstrap should `mkdir -p ~/.agents/machine-manager/` and copy schema there
- [ ] Skill directory stays read-only after install — no writes to `skills-flatagents/` or `~/.agents/skills/`
- [ ] `doctor` should check `~/.agents/machine-manager/` exists and is writable
- [ ] Update SKILL.md examples to reflect the new default path

## doctor enhancements

- [ ] Check schema version compatibility between `machine_manager_schema.sqlite` and active `machine_manager.db`
- [ ] Detect schema drift (columns added/removed) and report specific mismatches
- [ ] Check for stale leases (execution_leases with expired TTL but not cleaned up)
- [ ] Check for orphaned checkpoints (executions with no latest pointer)
- [ ] Validate that all agent refs in stored machine configs resolve

## backup + reset

- [ ] `backup` command: copy `machine_manager.db` to `machine_manager.db.<timestamp>.bak`
  - Where do backups go? Same directory? A `backups/` subdir?
  - How many backups to retain before auto-pruning?
- [ ] `reset` command: backup current DB, then copy `machine_manager_schema.sqlite` to `machine_manager.db`
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

## schema DB generation

- [ ] Script to regenerate `machine_manager_schema.sqlite` from current code
  - Should be idempotent and reproducible
  - Run as part of CI/release process
- [ ] Consider shipping `schema.sql` alongside the `.sqlite` for auditability
  - `sqlite3 machine_manager_schema.sqlite .dump > schema.sql`

## cull improvements

- [ ] `cull-trim` should report per-execution counts, not just totals
- [ ] `cull-purge` should vacuum the DB after large deletes to reclaim space
- [ ] Consider auto-cull on machine termination (configurable via persistence config)
- [ ] WAL checkpoint before reporting DB size in `cull-stats` (WAL can inflate apparent size)
