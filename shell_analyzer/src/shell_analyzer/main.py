"""
Shell Analyzer - Execute commands and analyze output with validated citations.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from flatagents import FlatMachine
from shell_analyzer.hooks import ShellAnalyzerHooks


VALID_STYLES = ["compact", "detailed", "minimal", "errors-only"]


async def run(command: str, style: str = "compact") -> str:
    """
    Main pipeline: execute command, analyze, validate, return result.
    """
    machine_file = Path(__file__).parent.parent.parent / 'machine.yml'
    hooks = ShellAnalyzerHooks()
    machine = FlatMachine(config_file=str(machine_file), hooks=hooks)

    result = await machine.execute(input={"command": command, "style": style})

    if "result" in result:
        return result["result"]
    elif "error" in result:
        return f"Error: {result['error']}"
    else:
        return str(result)


def main():
    """Entry point for command-line invocation."""
    parser = argparse.ArgumentParser(description="Analyze shell command output")
    parser.add_argument("--style", "-s", choices=VALID_STYLES, default="compact",
                        help="Output style: compact, detailed, minimal, errors-only")
    parser.add_argument("command", nargs="+", help="Shell command to execute")

    args = parser.parse_args()
    command = " ".join(args.command)

    result = asyncio.run(run(command, args.style))
    print(result)


if __name__ == "__main__":
    main()
