#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run.sh <action> [options]

Actions (run):
  start                Run a machine from the registry

Actions (config management):
  list                 List registered machines (default: active)
  get                  Get a machine config, validation, and version history
  create               Create a new machine from a template
  update               Apply a structured mutation to an existing machine
  validate             Run full validation suite on a machine
  diff                 Diff two versions of a machine config
  duplicate            Fork a machine under a new name
  deprecate            Soft-delete a machine (config preserved)
  select-model         Choose a model profile by purpose

Actions (maintenance — no LLM, direct SQL):
  cull-stats           Show checkpoint/lease/config counts and DB size
  cull-trim            Delete intermediate checkpoints for terminated executions
  cull-purge           Delete all data for old terminated executions
  doctor               Check environment health and recommend fixes

Global options:
  --db <path>          Registry DB path
                       (default: $FLATMACHINE_DB or ~/.agents/machine-manager/machine_manager.db)
  --json               Output as JSON
  -h, --help           Show this help

Environment:
  FLATMACHINE_MANAGER_HOME
                       Runtime state directory (default: ~/.agents/machine-manager)
  FLATMACHINE_DB       Override registry DB path directly
  FLATMACHINE_PROFILES Override profiles.yml path directly
  FLATMACHINE_MANAGER_SRC
                       Path to flatmachine_manager Python source
                       (default: <skill-dir>/python)

Templates:
  tool-loop            Agent + tools + human review (like coding agents)
  writer-critic        Iterative refinement loop (write → review → improve)
  ooda-workflow        Explore → Plan → Execute → Verify with human gates
  pipeline             Linear phase-separated processing (prep → expensive → wrap)
  signal-wait          Async workflow with external signal/approval gates
  distributed-worker   Worker pool pattern (checker → spawner → workers)

Examples:
  run.sh start --name my-bot --input '{"task": "hello world"}'
  run.sh start --name my-bot --input '{"task": "do stuff"}' --working-dir /tmp
  run.sh list
  run.sh create --name my-bot --template tool-loop --description "Code assistant"
  run.sh create --name writer --template writer-critic \
    --description "Tagline refinement" \
    --agent "You generate taglines:writer:Generate taglines:smart" \
    --agent "You score 1-10:critic:Score 1-10:fast"
  run.sh update --name writer --op add_state \
    --param state_name=review_gate --param after_state=review
  run.sh validate --name writer
  run.sh diff --name writer --v1 1 --v2 2
  run.sh duplicate --source writer --target writer-v2
  run.sh deprecate --name writer
  run.sh select-model --purpose creative
  run.sh cull-stats --machine-db ./my-machine.sqlite
  run.sh cull-trim --machine-db ./my-machine.sqlite --dry-run
  run.sh cull-purge --machine-db ./my-machine.sqlite --older-than 7
  run.sh doctor

Note:
  `start` executes the machine config embedded in the registry version
  (no temporary YAML file path resolution at runtime).
  The CLI subcommands above are the intended interface when called from
  an agent — no extra LLM layer needed.

Bootstrap:
  On first run, seeds runtime profiles at ~/.agents/machine-manager/profiles.yml,
  initializes the registry DB from schema.sql, and installs the Python package
  into the venv if needed. Idempotent.
EOF
}

# --- Help handling ---
if [[ $# -eq 0 ]] || [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

# --- Resolve paths ---
# Follow symlinks to find the real skill directory and its parent repo
REAL_SCRIPT="$(readlink -f "${BASH_SOURCE[0]}")"
SKILL_DIR="$(cd "$(dirname "$REAL_SCRIPT")" && pwd)"

# The shared venv lives at the skills-flatagents repo root
SKILLS_REPO="$(cd "$SKILL_DIR/.." && pwd)"
VENV="$SKILLS_REPO/.venv"

# Python source for flatmachine_manager (local skill copy by default)
PYTHON_DIR="${FLATMACHINE_MANAGER_SRC:-$SKILL_DIR/python}"

SCHEMA_SQL="$SKILL_DIR/schema.sql"
SKILL_PROFILES="$SKILL_DIR/config/profiles.yml"
RUNTIME_DIR="${FLATMACHINE_MANAGER_HOME:-$HOME/.agents/machine-manager}"
DEFAULT_DB="${FLATMACHINE_DB:-$RUNTIME_DIR/machine_manager.db}"
DEFAULT_PROFILES="${FLATMACHINE_PROFILES:-$RUNTIME_DIR/profiles.yml}"

# --- Bootstrap: venv ---
if [[ ! -d "$VENV" ]]; then
  echo "error: shared venv not found at $VENV" >&2
  echo "Run: cd $SKILLS_REPO && ./install.sh" >&2
  exit 1
fi

# --- Bootstrap: package ---
if [[ ! -d "$PYTHON_DIR/src/flatmachine_manager" ]]; then
  echo "error: flatmachine_manager source not found at $PYTHON_DIR" >&2
  echo "Set FLATMACHINE_MANAGER_SRC to the correct path" >&2
  exit 1
fi

EXPECTED_SRC="$(readlink -f "$PYTHON_DIR/src")"
INSTALLED_FILE="$("$VENV/bin/python" -c 'import flatmachine_manager, pathlib; print(pathlib.Path(flatmachine_manager.__file__).resolve())' 2>/dev/null || true)"

NEEDS_INSTALL=false
if [[ -z "$INSTALLED_FILE" ]]; then
  NEEDS_INSTALL=true
elif [[ "$INSTALLED_FILE" != "$EXPECTED_SRC/"* ]]; then
  NEEDS_INSTALL=true
fi

if [[ "$NEEDS_INSTALL" == "true" ]]; then
  echo "Installing flatmachine_manager into shared venv from $PYTHON_DIR..." >&2
  uv pip install --python "$VENV/bin/python" -e "$PYTHON_DIR" >&2
fi

# --- Bootstrap: runtime dir + profiles ---
mkdir -p "$RUNTIME_DIR"

if [[ ! -f "$DEFAULT_PROFILES" ]]; then
  if [[ -f "$SKILL_PROFILES" ]]; then
    echo "Seeding profiles: $DEFAULT_PROFILES" >&2
    cp "$SKILL_PROFILES" "$DEFAULT_PROFILES"
  else
    echo "warning: bundled profiles missing at $SKILL_PROFILES" >&2
  fi
fi

# Ensure CLI defaults resolve to runtime profiles unless explicitly overridden.
if [[ -z "${FLATMACHINE_PROFILES:-}" ]]; then
  export FLATMACHINE_PROFILES="$DEFAULT_PROFILES"
fi

# --- Bootstrap: DB ---
# Parse --db from args to avoid clobbering a user-specified path.
USER_DB=""
prev_was_db=false
for arg in "$@"; do
  if [[ "$prev_was_db" == "true" ]]; then
    USER_DB="$arg"
    break
  fi
  prev_was_db=false
  [[ "$arg" == "--db" ]] && prev_was_db=true
done

TARGET_DB="${USER_DB:-$DEFAULT_DB}"

if [[ ! -f "$TARGET_DB" ]]; then
  mkdir -p "$(dirname "$TARGET_DB")"

  if [[ ! -f "$SCHEMA_SQL" ]]; then
    echo "error: schema file not found at $SCHEMA_SQL" >&2
    exit 1
  fi

  echo "Initializing registry: $TARGET_DB (from schema.sql)" >&2
  if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$TARGET_DB" < "$SCHEMA_SQL"
  else
    "$VENV/bin/python" - "$TARGET_DB" "$SCHEMA_SQL" <<'PY'
import sqlite3
import sys

db_path = sys.argv[1]
schema_path = sys.argv[2]

with open(schema_path, "r", encoding="utf-8") as f:
    sql = f.read()

conn = sqlite3.connect(db_path)
conn.executescript(sql)
conn.close()
PY
  fi
fi

# --- Dispatch ---
if [[ -z "$USER_DB" ]]; then
  exec "$VENV/bin/python" -m flatmachine_manager.cli --db "$TARGET_DB" "$@"
else
  exec "$VENV/bin/python" -m flatmachine_manager.cli "$@"
fi
