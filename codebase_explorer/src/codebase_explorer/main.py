#!/usr/bin/env python3
"""
Codebase Explorer CLI

Explores a codebase to gather context for a task using:
- tree: directory structure discovery
- ripgrep: code search
- file reading: full file contents

Features budget-aware frozen state management with two-pass removal.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Unbuffered output for live progress
sys.stdout.reconfigure(line_buffering=True)

# Reduce logging noise - only show warnings and above
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("flatagents").setLevel(logging.WARNING)
logging.getLogger("codebase_explorer").setLevel(logging.WARNING)

from flatagents import FlatMachine
from .hooks import CodebaseExplorerHooks

# Hard cap on API calls to prevent runaway costs
MAX_API_CALLS = 10


def parse_args():
    parser = argparse.ArgumentParser(
        description="Explore a codebase to gather context for a task"
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
        help="Maximum tokens for frozen context (default: 40000)"
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

    # Resolve working directory
    working_dir = Path(args.directory).resolve()
    if not working_dir.exists():
        print(f"Error: directory not found: {working_dir}", file=sys.stderr)
        sys.exit(1)

    # Create hooks
    hooks = CodebaseExplorerHooks(working_dir=str(working_dir))

    # Load machine with hooks
    machine_path = Path(__file__).parent.parent.parent / "machine.yml"
    machine = FlatMachine(config_file=str(machine_path), hooks=hooks)

    # Run exploration - hooks will print progress
    print(f"explore {working_dir}")
    print(f"task {args.task[:50]}")
    print(f"budget {args.token_budget} tokens {args.max_iterations} iters")

    result = await machine.execute({
        "task": args.task,
        "working_dir": str(working_dir),
        "token_budget": args.token_budget,
        "max_iterations": args.max_iterations
    })

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        # Output structured context in text format for LLM consumption
        output = result or {}

        def parse_json_field(val):
            """Parse JSON string fields from template output."""
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except json.JSONDecodeError:
                    return val
            return val

        # Summary
        if output.get('summary'):
            print("\n## Summary")
            print(output['summary'])

        # Imports
        imports = parse_json_field(output.get('frozen_imports', []))
        if imports:
            print("\n## Imports")
            for imp in imports:
                print(imp)

        # Signatures
        sigs = parse_json_field(output.get('frozen_signatures', []))
        if sigs:
            print("\n## Signatures")
            for sig in sigs:
                print(sig)

        # Code segments
        segs = parse_json_field(output.get('frozen_segments', []))
        if segs:
            print("\n## Code Segments")
            for seg in segs:
                if isinstance(seg, dict):
                    print(f"\n### {seg.get('file', 'unknown')}")
                    print("```")
                    print(seg.get('code', ''))
                    print("```")
                else:
                    print(seg)

        # Stats
        print(f"\n---")
        print(f"Explored: {len(imports)} imports, {len(sigs)} signatures, {len(segs)} segments")
        print(f"Tokens: {output.get('tokens_used', 0)}/{output.get('token_budget', 0)} | Calls: {output.get('api_calls', 0)}")


def run():
    """Entry point for CLI."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
