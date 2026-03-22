#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run.sh <action> [options]

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
  --db <path>          Registry DB path (default: $FLATMACHINE_DB or ./machine_manager.db)
  --json               Output as JSON
  -h, --help           Show this help

Environment:
  FLATMACHINE_DB       Override default registry DB path
  FLATMACHINE_MANAGER_SRC
                       Path to flatmachine_manager Python source
                       (default: ~/code/prototyping/flatmachines_manager/python)

Templates:
  tool-loop            Agent + tools + human review (like coding agents)
  writer-critic        Iterative refinement loop (write → review → improve)
  ooda-workflow        Explore → Plan → Execute → Verify with human gates
  pipeline             Linear phase-separated processing (prep → expensive → wrap)
  signal-wait          Async workflow with external signal/approval gates
  distributed-worker   Worker pool pattern (checker → spawner → workers)

Examples:
  run.sh list
  run.sh create --name my-bot --template tool-loop --description "Code assistant"
  run.sh create --name writer --template writer-critic \
    --description "Tagline refinement" \
    --agent "writer:Generate taglines:smart" \
    --agent "critic:Score 1-10:fast"
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

Bootstrap:
  On first run, copies machine_manager_schema.sqlite → machine_manager.db
  and installs the Python package into the venv if needed. Idempotent.
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

# Python source for flatmachine_manager (in prototyping repo by default)
PYTHON_DIR="${FLATMACHINE_MANAGER_SRC:-$HOME/code/prototyping/flatmachines_manager/python}"

SCHEMA_DB="$SKILL_DIR/machine_manager_schema.sqlite"
DEFAULT_DB="${FLATMACHINE_DB:-./machine_manager.db}"

# --- Bootstrap: venv ---
if [[ ! -d "$VENV" ]]; then
  echo "error: shared venv not found at $VENV" >&2
  echo "Run: cd $SKILLS_REPO && ./install.sh" >&2
  exit 1
fi

# --- Bootstrap: package ---
if ! "$VENV/bin/python" -c "import flatmachine_manager" 2>/dev/null; then
  if [[ ! -d "$PYTHON_DIR" ]]; then
    echo "error: flatmachine_manager source not found at $PYTHON_DIR" >&2
    echo "Set FLATMACHINE_MANAGER_SRC to the correct path" >&2
    exit 1
  fi
  echo "Installing flatmachine_manager into shared venv..." >&2
  uv pip install --python "$VENV/bin/python" -e "$PYTHON_DIR" >&2
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

if [[ ! -f "$TARGET_DB" ]] && [[ -f "$SCHEMA_DB" ]]; then
  echo "Initializing registry: $TARGET_DB (from schema)" >&2
  cp "$SCHEMA_DB" "$TARGET_DB"
fi

# --- Dispatch ---
if [[ -z "$USER_DB" ]]; then
  exec "$VENV/bin/python" -m flatmachine_manager.cli --db "$TARGET_DB" "$@"
else
  exec "$VENV/bin/python" -m flatmachine_manager.cli "$@"
fi
