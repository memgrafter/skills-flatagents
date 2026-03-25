"""
FlatMachines skill CLI — single dispatcher for all actions.

Usage:
    python -m flatmachine_manager.cli <action> [options]

Actions:
    start        — Run a machine from the registry
    list, get, create, update, validate, diff, duplicate, deprecate, select-model
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import pathlib
import sys
import warnings
from typing import Any, Dict, List, Optional

import yaml

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
    """Parse agent shorthand: 'system:name:purpose:profile'.

    System prompt is the first field and is required.  Name is required.
    Purpose and profile are optional.
    """
    parts = spec.split(":", maxsplit=3)
    if len(parts) < 2:
        print(
            "error: agent spec requires at least 'system:name' — got: " + spec,
            file=sys.stderr,
        )
        sys.exit(1)

    system = parts[0].strip()
    if not system:
        print("error: system prompt (first field) cannot be empty", file=sys.stderr)
        sys.exit(1)

    agent: Dict[str, Any] = {"system": system, "name": parts[1].strip()}
    if len(parts) >= 3:
        agent["purpose"] = parts[2].strip()
    if len(parts) >= 4:
        agent["model_profile"] = parts[3].strip()
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

    # start
    p = sub.add_parser("start", help="Run a machine from the registry")
    p.add_argument("--name", required=True,
                   help="Machine name in the registry")
    p.add_argument("--input", dest="machine_input", default="{}",
                   help="JSON input for the machine (default: {})")
    p.add_argument("--version", type=int, default=None,
                   help="Specific version to run (default: latest)")
    p.add_argument("--working-dir", "-w", default=os.getcwd(),
                   help="Working directory for CLI tools (default: cwd)")
    p.add_argument("--profiles", default=None,
                   help="Path to profiles.yml (default: skill config/profiles.yml)")
    p.add_argument("--auto-approve", action="store_true",
                   help="Skip human review actions")

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
                   help="Agent spec as 'system:name:purpose:profile' (repeatable, system required)")
    p.add_argument("--system", default=None,
                   help="System prompt for the first agent (overrides system in --agent shorthand; "
                        "use when system prompt contains colons)")
    p.add_argument("--tools", default=None,
                   help="Comma-separated tool names to include (default: all). "
                        "Available: read, bash, write, edit")
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

    # --- Tool registry commands ---

    # list-tools
    p = sub.add_parser("list-tools", help="List available tools from the tool registry")
    p.add_argument("--provider", default=None,
                   help="Filter by provider (e.g., cli-tools, manager)")
    p.add_argument("--include-deprecated", action="store_true",
                   help="Include deprecated tools in output")

    # deprecate-tool
    p = sub.add_parser("deprecate-tool", help="Hide a tool from new machine creation")
    p.add_argument("--name", required=True, help="Tool name to deprecate")

    # undeprecate-tool
    p = sub.add_parser("undeprecate-tool", help="Restore a deprecated tool for new machines")
    p.add_argument("--name", required=True, help="Tool name to restore")

    # doctor
    p = sub.add_parser("doctor", help="Check environment health and recommend fixes")

    return parser


# ---------------------------------------------------------------------------
# Action dispatch
# ---------------------------------------------------------------------------

def _skill_config_path(name: str) -> str:
    """Resolve a path relative to the skill's config/ directory."""
    return str(pathlib.Path(__file__).resolve().parents[3] / "config" / name)


async def dispatch_start(args: argparse.Namespace) -> int:
    """Run a machine from the registry. Returns exit code."""
    # Suppress noisy warnings during execution
    warnings.filterwarnings("ignore", message=".*validation.*")
    warnings.filterwarnings("ignore", message=".*Flatmachine.*")
    warnings.filterwarnings("ignore", message=".*Flatagent.*")

    # Quiet logging unless LOG_LEVEL is set
    log_level = os.environ.get("LOG_LEVEL", "WARNING").upper()
    logging.getLogger().setLevel(log_level)
    for _name in ("flatagents", "flatmachines", "LiteLLM"):
        logging.getLogger(_name).setLevel(log_level)

    from flatmachines import FlatMachine
    from .hooks_registry import build_hooks_registry

    db_path = args.db or _default_db()
    registry = MachineRegistry(db_path=db_path)

    try:
        # Load config from registry
        if args.version is not None:
            version = registry.get_version(args.name, args.version)
        else:
            version = registry.get_latest(args.name)

        if not version:
            print(f"error: machine '{args.name}' not found in registry", file=sys.stderr)
            return 1

        # Always execute embedded config from registry (self-contained, no temp files).
        if not version.config_embedded:
            print(
                f"error: machine '{args.name}' v{version.version} has no embedded config in registry",
                file=sys.stderr,
            )
            print(
                "recreate or re-save the machine so config_embedded is populated",
                file=sys.stderr,
            )
            return 1

        try:
            machine_config = yaml.safe_load(version.config_embedded)
        except Exception as e:
            print(f"error: failed to parse embedded config: {e}", file=sys.stderr)
            return 1

        if not isinstance(machine_config, dict):
            print("error: embedded config is not a YAML object", file=sys.stderr)
            return 1

        # Resolve profiles
        profiles_path = args.profiles or _skill_config_path("profiles.yml")
        if not os.path.exists(profiles_path):
            profiles_path = None

        # Build hooks registry
        working_dir = os.path.abspath(args.working_dir)
        hooks_registry = build_hooks_registry(
            registry=registry,
            working_dir=working_dir,
            auto_approve=args.auto_approve,
        )

        # Parse input
        try:
            machine_input = json.loads(args.machine_input)
        except json.JSONDecodeError as e:
            print(f"error: invalid JSON input: {e}", file=sys.stderr)
            return 1

        # Create and run machine
        machine = FlatMachine(
            config_dict=machine_config,
            hooks_registry=hooks_registry,
            profiles_file=profiles_path,
        )

        result = await machine.execute(input=machine_input)

        # Print result
        if isinstance(result, dict):
            print(json.dumps(result, indent=2, default=str))
        else:
            print(result)

        return 0

    finally:
        registry.close()


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


def dispatch_tools(args: argparse.Namespace) -> tuple[str, bool]:
    """Handle tool registry commands (no LLM, direct SQL)."""
    from .tool_registry import ToolRegistry

    db_path = args.db or _default_db()
    tr = ToolRegistry(db_path=db_path)
    tr.seed_defaults()  # idempotent — ensures catalog is populated

    try:
        if args.action == "list-tools":
            entries = tr.list_tools(
                provider=args.provider,
                include_deprecated=args.include_deprecated,
            )
            if not entries:
                return "No tools found.", False

            lines = [
                "| Tool | Tool ID | Provider | Status | Description |",
                "|------|---------|----------|--------|-------------|",
            ]
            for e in entries:
                desc = e.description[:70].replace("\n", " ").strip()
                lines.append(
                    f"| {e.name} | {e.tool_id[:12]}… | {e.provider} | {e.status} | {desc} |"
                )
            return "\n".join(lines), False

        elif args.action == "deprecate-tool":
            try:
                tr.deprecate(args.name)
                return f"✓ Deprecated tool **{args.name}** — hidden from new machine creation.", False
            except ValueError as e:
                return str(e), True

        elif args.action == "undeprecate-tool":
            try:
                tr.undeprecate(args.name)
                return f"✓ Restored tool **{args.name}** — available for new machines.", False
            except ValueError as e:
                return str(e), True

        else:
            return f"Unknown tool action: {args.action}", True
    finally:
        tr.close()


def dispatch_doctor(args: argparse.Namespace) -> tuple[str, bool]:
    """Run environment health checks."""
    from .doctor import run_doctor
    import pathlib

    # cli.py path: <skills-repo>/flatmachine-manager/python/src/flatmachine_manager/cli.py
    db_path = args.db or _default_db()
    cli_file = pathlib.Path(__file__).resolve()
    skill_dir = str(cli_file.parents[3])
    skills_repo_dir = str(cli_file.parents[4])

    return run_doctor(skills_repo_dir, skill_dir, db_path), False


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

            # --system flag overrides system prompt on first agent
            if args.system:
                if not args.system.strip():
                    return "error: --system cannot be empty", True
                if agents:
                    agents[0]["system"] = args.system
                else:
                    agents = [{"system": args.system, "name": "worker"}]

            # --tools flag: comma-separated tool names
            tools = None
            if args.tools:
                tools = [t.strip() for t in args.tools.split(",")]

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
                "tools": tools,
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

    # Start command — runs machine, handles its own output
    if args.action == "start":
        rc = asyncio.run(dispatch_start(args))
        sys.exit(rc)

    # Direct commands — synchronous, no registry needed
    if args.action.startswith("cull-"):
        content, is_error = dispatch_cull(args)
    elif args.action in ("list-tools", "deprecate-tool", "undeprecate-tool"):
        content, is_error = dispatch_tools(args)
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
