#!/usr/bin/env python3
"""
Codebase Ripper CLI

Shotgun approach to codebase exploration:
1. Generate many commands (1 LLM call)
2. Validate against allowlist (0 LLM calls)
3. Execute all in parallel (0 LLM calls)
4. Extract relevant context (1 LLM call)

Total: 2 LLM calls for comprehensive coverage.
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
        description="Rip through a codebase to gather context (shotgun approach)"
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

    print(f"ripper {working_dir}")
    print(f"task {args.task[:60]}")

    result = await machine.execute({
        "task": args.task,
        "working_dir": str(working_dir),
        "token_budget": args.token_budget
    })

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        output = result or {}

        def parse_json_field(val):
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
                print(f"  {imp}")

        # Signatures
        sigs = parse_json_field(output.get('frozen_signatures', []))
        if sigs:
            print("\n## Signatures")
            for sig in sigs:
                print(f"  {sig}")

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
        print(f"Commands: {output.get('commands_generated', 0)} generated, {output.get('commands_valid', 0)} valid, {output.get('commands_rejected', 0)} rejected")
        print(f"Output: {output.get('output_tokens', 0)} tokens")
        print(f"Extracted: {len(imports)} imports, {len(sigs)} signatures, {len(segs)} segments")


def run():
    """Entry point for CLI."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
