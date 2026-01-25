#!/usr/bin/env python3
"""
Codebase Ripper CLI

Shotgun approach to codebase exploration with iterative passes:
1. Generate many commands (1 LLM call per iteration)
2. Extract command list (1 LLM call per iteration)
3. Validate against allowlist (0 LLM calls)
4. Execute all in parallel (0 LLM calls)
5. Extract relevant context (1 LLM call per iteration)

Default: 2 iterations for deeper coverage.
Output: Clean text context ready for another LLM.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# Reduce noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("flatagents").setLevel(logging.WARNING)
logging.getLogger("codebase_ripper").setLevel(logging.WARNING)

from flatagents import FlatMachine
from .hooks import CodebaseRipperHooks


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rip through a codebase to gather context (shotgun approach with iterative passes)"
    )
    parser.add_argument(
        "task",
        help="The task to gather context for"
    )
    parser.add_argument(
        "-d", "--directory",
        default=".",
        help="Working directory to explore (default: current directory)"
    )
    parser.add_argument(
        "--token-budget",
        type=int,
        default=40000,
        help="Maximum tokens for extracted context (default: 40000)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
        help="Maximum exploration iterations (default: 2)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    working_dir = Path(args.directory).resolve()
    if not working_dir.exists():
        print(f"Error: directory not found: {working_dir}", file=sys.stderr)
        sys.exit(1)

    hooks = CodebaseRipperHooks(working_dir=str(working_dir))

    machine_path = Path(__file__).parent.parent.parent / "machine.yml"
    machine = FlatMachine(config_file=str(machine_path), hooks=hooks)

    print(f"# Codebase Ripper", file=sys.stderr)
    print(f"Directory: {working_dir}", file=sys.stderr)
    print(f"Task: {args.task[:60]}", file=sys.stderr)
    print(f"Iterations: {args.max_iterations}", file=sys.stderr)
    print(f"---", file=sys.stderr)

    result = await machine.execute({
        "task": args.task,
        "working_dir": str(working_dir),
        "token_budget": args.token_budget,
        "max_iterations": args.max_iterations
    })

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        output = result or {}
        
        # Print the context (this is what another LLM will consume)
        print(output.get('context', ''))
        
        # Stats to stderr
        print(f"\n---", file=sys.stderr)
        print(f"Iterations: {output.get('iterations', 0)}", file=sys.stderr)
        print(f"Commands: {output.get('commands_generated', 0)} generated, {output.get('commands_valid', 0)} valid, {output.get('commands_rejected', 0)} rejected", file=sys.stderr)
        print(f"Output tokens: {output.get('output_tokens', 0)}", file=sys.stderr)


def run():
    """Entry point for CLI."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
