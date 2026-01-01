"""
Test Writer - Multi-agent orchestrator for iterative test generation.

Uses FlatMachine to orchestrate 4 agents through analyze → write → check → run → fix loops.

Exit codes:
- 0: Success (coverage target met)
- 1: Production bug detected
- 2: Max iterations reached or other failure
"""

import argparse
import asyncio
import sys
from pathlib import Path

from flatagents import FlatMachine
from test_writer.hooks import TestWriterHooks


async def run(
    target: str,
    coverage_target: int = 80,
    max_rounds: int = 3
) -> int:
    """
    Main orchestrator using FlatMachine.

    Returns exit code:
    - 0: Success
    - 1: Production bug
    - 2: Max iterations or failure
    """
    machine_file = Path(__file__).parent.parent.parent / 'machine.yml'
    hooks = TestWriterHooks()
    machine = FlatMachine(config_file=str(machine_file), hooks=hooks)

    result = await machine.execute(input={
        "target": target,
        "coverage_target": coverage_target,
        "max_rounds": max_rounds
    })

    # Extract exit code from result
    exit_code = result.get("exit_code", 2)

    if exit_code != 0:
        message = result.get("message", "Unknown error")
        print(f"\n{message}", file=sys.stderr)
        if "error_output" in result:
            print(f"\nLast error:\n{result['error_output']}", file=sys.stderr)

    return exit_code


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Write tests to reach a coverage target"
    )
    parser.add_argument(
        "target",
        help="Python file or directory to test"
    )
    parser.add_argument(
        "--target", "-t",
        dest="coverage_target",
        type=int,
        default=80,
        help="Coverage percentage to reach (default: 80)"
    )
    parser.add_argument(
        "--max-rounds", "-r",
        type=int,
        default=3,
        help="Maximum test generation rounds (default: 3)"
    )

    args = parser.parse_args()

    exit_code = asyncio.run(run(
        target=args.target,
        coverage_target=args.coverage_target,
        max_rounds=args.max_rounds
    ))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
