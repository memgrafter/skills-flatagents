#!/usr/bin/env python3
# Copyright (C) 2026 Trent Zock-Robbins
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0

"""CLI entrypoint for repo_map skill."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from flatmachines import FlatMachine

from .hooks import RepoMapHooks


logging.getLogger("flatmachines").setLevel(logging.ERROR)
logging.getLogger("flatmachines.utils").setLevel(logging.ERROR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a compact repo map using vendored Aider logic")
    parser.add_argument("task", nargs="?", default="", help="Optional hint text to bias ranking")
    parser.add_argument("-d", "--directory", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--map-tokens", type=int, default=2000, help="Target token budget for map")
    parser.add_argument(
        "--max-context-window",
        type=int,
        default=128000,
        help="Model context window for map scaling behavior",
    )
    parser.add_argument(
        "--refresh",
        choices=["auto", "always", "manual", "files"],
        default="auto",
        help="RepoMap refresh mode",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    working_dir = Path(args.directory).resolve()
    if not working_dir.exists():
        print(f"Error: directory not found: {working_dir}", file=sys.stderr)
        raise SystemExit(1)

    hooks = RepoMapHooks()
    machine_path = Path(__file__).parent.parent.parent / "machine.yml"
    machine = FlatMachine(config_file=str(machine_path), hooks=hooks)

    result = await machine.execute(
        {
            "task": args.task,
            "working_dir": str(working_dir),
            "map_tokens": args.map_tokens,
            "max_context_window": args.max_context_window,
            "refresh": args.refresh,
        }
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return

    output = result or {}
    print(output.get("repo_map", ""))
    if output.get("error"):
        print(f"\nerror: {output['error']}", file=sys.stderr)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
