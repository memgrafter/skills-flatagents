"""
FlatMachines skill CLI — single dispatcher for all 9 actions.

Usage:
    python -m flatmachine_manager.cli <action> [options]

Actions: list, get, create, update, validate, diff, duplicate, deprecate, select-model
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional

from .registry import MachineRegistry
from .tools import (
    tool_create_machine,
    tool_deprecate_machine,
    tool_diff_versions,
    tool_duplicate_machine,
    tool_get_machine,
    tool_list_machines,
    tool_select_model,
    tool_update_machine,
    tool_validate_machine,
)


def _default_db() -> str:
    return os.environ.get(
        "FLATMACHINE_DB",
        os.path.join(os.getcwd(), "flatmachine_registry.sqlite"),
    )


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _parse_agent(spec: str) -> Dict[str, Any]:
    """Parse agent shorthand: 'name:purpose:profile' or 'name:purpose'."""
    parts = spec.split(":", maxsplit=2)
    agent: Dict[str, Any] = {"name": parts[0].strip()}
    if len(parts) >= 2:
        agent["purpose"] = parts[1].strip()
    if len(parts) >= 3:
        agent["model_profile"] = parts[2].strip()
    return agent


def _parse_param(spec: str) -> tuple[str, str]:
    """Parse 'key=value' param."""
    if "=" not in spec:
        print(f"error: param must be key=value, got: {spec}", file=sys.stderr)
        sys.exit(1)
    k, v = spec.split("=", maxsplit=1)
    return k.strip(), v.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flatmachines",
        description="FlatMachines skill — manage state-machine configs",
    )
    parser.add_argument(
        "--db", default=None,
        help=f"Registry DB path (default: $FLATMACHINE_DB or ./flatmachine_registry.sqlite)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output as JSON",
    )

    sub = parser.add_subparsers(dest="action", help="Action to perform")

    # list
    p = sub.add_parser("list", help="List registered machines")
    p.add_argument("--status", default="active", choices=["active", "deprecated", "all"])

    # get
    p = sub.add_parser("get", help="Get a machine config and metadata")
    p.add_argument("--name", required=True)
    p.add_argument("--version", type=int, default=None)

    # create
    p = sub.add_parser("create", help="Create a machine from a template")
    p.add_argument("--name", required=True)
    p.add_argument("--template", required=True,
                   choices=["tool-loop", "writer-critic", "ooda-workflow",
                            "pipeline", "signal-wait", "distributed-worker"])
    p.add_argument("--description", required=True)
    p.add_argument("--agent", action="append", dest="agents", default=[],
                   help="Agent spec as 'name:purpose:profile' (repeatable)")
    p.add_argument("--context-field", action="append", dest="context_fields", default=[],
                   help="Context field as 'name=default' or 'name=@input' (from input)")

    # update
    p = sub.add_parser("update", help="Apply a structured mutation")
    p.add_argument("--name", required=True)
    p.add_argument("--op", required=True,
                   choices=["add_state", "remove_state", "update_state",
                            "add_agent", "update_agent", "update_context", "update_setting"])
    p.add_argument("--param", action="append", dest="params", default=[],
                   help="Operation param as 'key=value' (repeatable)")
    p.add_argument("--description", default="")

    # validate
    p = sub.add_parser("validate", help="Run full validation suite")
    p.add_argument("--name", required=True)
    p.add_argument("--version", type=int, default=None)

    # diff
    p = sub.add_parser("diff", help="Diff two versions of a machine")
    p.add_argument("--name", required=True)
    p.add_argument("--v1", type=int, required=True)
    p.add_argument("--v2", type=int, required=True)

    # duplicate
    p = sub.add_parser("duplicate", help="Fork a machine under a new name")
    p.add_argument("--source", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--version", type=int, default=None)
    p.add_argument("--description", default="")

    # deprecate
    p = sub.add_parser("deprecate", help="Soft-delete a machine")
    p.add_argument("--name", required=True)

    # select-model
    p = sub.add_parser("select-model", help="Choose a model profile by purpose")
    p.add_argument("--purpose", required=True,
                   choices=["fast", "smart", "cheap", "code", "routing", "creative", "analysis"])
    p.add_argument("--constraints", default="")

    # --- Maintenance commands (no LLM, direct SQL) ---

    # cull-stats
    p = sub.add_parser("cull-stats", help="Show checkpoint statistics for a machine DB")
    p.add_argument("--machine-db", required=True,
                   help="Path to the machine's SQLite database")

    # cull-trim
    p = sub.add_parser("cull-trim", help="Delete intermediate checkpoints for terminated executions")
    p.add_argument("--machine-db", required=True,
                   help="Path to the machine's SQLite database")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would be deleted without deleting")

    # cull-purge
    p = sub.add_parser("cull-purge", help="Delete all data for old terminated executions")
    p.add_argument("--machine-db", required=True,
                   help="Path to the machine's SQLite database")
    p.add_argument("--older-than", type=int, default=7,
                   help="Delete terminated executions older than N days (default: 7)")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would be deleted without deleting")

    # doctor
    p = sub.add_parser("doctor", help="Check environment health and recommend fixes")

    return parser


# ---------------------------------------------------------------------------
# Action dispatch
# ---------------------------------------------------------------------------

def dispatch_cull(args: argparse.Namespace) -> tuple[str, bool]:
    """Handle cull-* subcommands directly (no LLM, no registry)."""
    from .cull import stats, trim, purge

    if args.action == "cull-stats":
        return stats(args.machine_db), False
    elif args.action == "cull-trim":
        return trim(args.machine_db, dry_run=args.dry_run), False
    elif args.action == "cull-purge":
        return purge(args.machine_db, older_than_days=args.older_than, dry_run=args.dry_run), False
    else:
        return f"Unknown cull action: {args.action}", True


def dispatch_doctor(args: argparse.Namespace) -> tuple[str, bool]:
    """Run environment health checks."""
    from .doctor import run_doctor
    import pathlib

    # Resolve paths
    db_path = args.db or _default_db()
    # Walk up from cli.py → flatmachine_manager → src → python → repo
    cli_file = pathlib.Path(__file__).resolve()
    repo_dir = str(cli_file.parent.parent.parent.parent)
    skill_dir = str(pathlib.Path(repo_dir) / "skills" / "flatmachine-manager")

    return run_doctor(repo_dir, skill_dir, db_path), False


async def dispatch(args: argparse.Namespace) -> tuple[str, bool]:
    """Run the action, return (content, is_error)."""
    db_path = args.db or _default_db()
    registry = MachineRegistry(db_path=db_path)

    try:
        if args.action == "list":
            r = await tool_list_machines(registry, "cli", {"status": args.status})

        elif args.action == "get":
            a: Dict[str, Any] = {"name": args.name}
            if args.version is not None:
                a["version"] = args.version
            r = await tool_get_machine(registry, "cli", a)

        elif args.action == "create":
            agents = [_parse_agent(s) for s in args.agents] if args.agents else None

            context_fields = None
            if args.context_fields:
                context_fields = []
                for cf in args.context_fields:
                    k, v = _parse_param(cf)
                    if v == "@input":
                        context_fields.append({"name": k, "from_input": True})
                    else:
                        context_fields.append({"name": k, "default_value": v})

            r = await tool_create_machine(registry, "cli", {
                "name": args.name,
                "template": args.template,
                "description": args.description,
                "agents": agents,
                "context_fields": context_fields,
            })

        elif args.action == "update":
            params = {}
            for p in args.params:
                k, v = _parse_param(p)
                # Handle comma-separated lists for transitions_to
                if k == "transitions_to":
                    v = [t.strip() for t in v.split(",")]
                # Handle numeric values
                try:
                    v = int(v)
                except (ValueError, TypeError):
                    try:
                        v = float(v)
                    except (ValueError, TypeError):
                        pass
                params[k] = v

            r = await tool_update_machine(registry, "cli", {
                "name": args.name,
                "operation": args.op,
                "params": params,
                "description": args.description,
            })

        elif args.action == "validate":
            a = {"name": args.name}
            if args.version is not None:
                a["version"] = args.version
            r = await tool_validate_machine(registry, "cli", a)

        elif args.action == "diff":
            r = await tool_diff_versions(registry, "cli", {
                "name": args.name,
                "v1": args.v1,
                "v2": args.v2,
            })

        elif args.action == "duplicate":
            a = {
                "source": args.source,
                "target": args.target,
                "description": args.description,
            }
            if args.version is not None:
                a["version"] = args.version
            r = await tool_duplicate_machine(registry, "cli", a)

        elif args.action == "deprecate":
            r = await tool_deprecate_machine(registry, "cli", {"name": args.name})

        elif args.action == "select-model":
            r = await tool_select_model(registry, "cli", {
                "purpose": args.purpose,
                "constraints": args.constraints,
            })

        else:
            return f"Unknown action: {args.action}", True

        return r.content, r.is_error

    finally:
        registry.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    # Direct commands — synchronous, no registry needed
    if args.action.startswith("cull-"):
        content, is_error = dispatch_cull(args)
    elif args.action == "doctor":
        content, is_error = dispatch_doctor(args)
    else:
        content, is_error = asyncio.run(dispatch(args))

    if args.json_output:
        print(json.dumps({"content": content, "error": is_error}))
    else:
        print(content)

    sys.exit(1 if is_error else 0)


if __name__ == "__main__":
    main()
