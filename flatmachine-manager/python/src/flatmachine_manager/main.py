"""
FlatMachine Manager — CRUD machine for creating and managing flatmachines.

Default: interactive REPL. Use -p for single-shot mode.

Usage:
    python -m flatmachine_manager.main                              # REPL
    python -m flatmachine_manager.main -p "create a writer-critic"  # single-shot
    python -m flatmachine_manager.main --standalone "list machines"
    python -m flatmachine_manager.main --demo                       # run demo
"""

import argparse
import asyncio
import logging
import os
import warnings
from pathlib import Path

# Suppress validation warnings until schemas are regenerated
warnings.filterwarnings("ignore", message=".*validation.*")
warnings.filterwarnings("ignore", message=".*Flatmachine.*")
warnings.filterwarnings("ignore", message=".*Flatagent.*")

from flatmachines import FlatMachine  # noqa: E402

from .hooks import ManagerHooks  # noqa: E402
from .registry import MachineRegistry  # noqa: E402

try:
    import readline  # noqa: F401 — enables arrow keys, history in input()
except ImportError:
    pass

# Quiet by default
_log_level = os.environ.get("LOG_LEVEL", "WARNING").upper()
logging.getLogger().setLevel(_log_level)
for _name in ("flatagents", "flatmachines", "LiteLLM"):
    logging.getLogger(_name).setLevel(_log_level)


def _config_path(name: str) -> str:
    return str(Path(__file__).parent.parent.parent.parent / "config" / name)


def _default_db_path(working_dir: str) -> str:
    return os.path.join(working_dir, "flatmachine_registry.sqlite")


async def run_machine(
    task: str,
    working_dir: str,
    db_path: str,
    human_review: bool = True,
):
    """Run a single task via the FlatMachine Manager."""
    registry = MachineRegistry(db_path=db_path)
    try:
        hooks = ManagerHooks(registry=registry, auto_approve=not human_review)
        machine = FlatMachine(
            config_file=_config_path("machine.yml"),
            hooks=hooks,
        )

        result = await machine.execute(input={
            "task": task,
            "working_dir": working_dir,
            "db_path": db_path,
        })

        return result
    finally:
        registry.close()


async def run_standalone(task: str, working_dir: str, db_path: str):
    """Run a single task without interactive review."""
    result = await run_machine(task, working_dir, db_path, human_review=False)

    print("=" * 60)
    print("DONE")
    print("=" * 60)
    content = result.get("result") if isinstance(result, dict) else result
    if content:
        print(content)

    return result


async def repl(working_dir: str, db_path: str):
    """Interactive REPL — enter tasks, manager executes with human review."""
    print(f"FlatMachine Manager — {working_dir}")
    print(f"Registry: {db_path}")
    print()

    _interrupt_count = 0

    while True:
        try:
            task = input("fm> ").strip()
            _interrupt_count = 0
        except KeyboardInterrupt:
            _interrupt_count += 1
            if _interrupt_count >= 2:
                print()
                break
            print()
            continue
        except EOFError:
            print()
            break

        if not task:
            continue

        _interrupt_count = 0

        try:
            await run_machine(task, working_dir, db_path)
        except KeyboardInterrupt:
            print("\nInterrupted.")
        except Exception as e:
            print(f"Error: {e}")

        print()


def main():
    parser = argparse.ArgumentParser(
        description="FlatMachine Manager — CRUD machine for flatmachines"
    )
    parser.add_argument(
        "-p", "--print",
        metavar="TASK",
        dest="task",
        help="Run a single task and exit",
    )
    parser.add_argument(
        "--working-dir", "-w",
        default=os.getcwd(),
        help="Working directory (default: cwd)",
    )
    parser.add_argument(
        "--db-path", "-d",
        default=None,
        help="Path to registry SQLite database (default: <working_dir>/flatmachine_registry.sqlite)",
    )
    parser.add_argument(
        "--standalone", "-s",
        metavar="TASK",
        nargs="?",
        const=True,
        help="Run without interactive review",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the built-in demo (create → validate → update → diff → list)",
    )
    args = parser.parse_args()

    working_dir = os.path.abspath(args.working_dir)
    db_path = args.db_path or _default_db_path(working_dir)

    if args.demo:
        from .demo import run_demo
        asyncio.run(run_demo(db_path=args.db_path))
    elif args.standalone:
        task = args.standalone if isinstance(args.standalone, str) and args.standalone is not True else args.task
        if not task:
            parser.error("--standalone requires a task")
        asyncio.run(run_standalone(task, working_dir, db_path))
    elif args.task:
        asyncio.run(run_machine(args.task, working_dir, db_path))
    else:
        asyncio.run(repl(working_dir, db_path))


if __name__ == "__main__":
    main()
