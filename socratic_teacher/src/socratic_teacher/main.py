import argparse
import asyncio
import json
import logging
import os
from pathlib import Path

os.environ["LITELLM_LOG"] = "ERROR"
os.environ["LITELLM_LOG_LEVEL"] = "ERROR"
logging.basicConfig(level=logging.WARNING, force=True)
logging.getLogger("flatagents").setLevel(logging.WARNING)
logging.getLogger("flatagents.flatagent").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.ERROR)
logging.getLogger("LiteLLM").setLevel(logging.ERROR)

from flatagents import FlatMachine
from socratic_teacher.hooks import SocraticTeacherHooks


async def run(topic: str, level: int, max_rounds: int, working_dir: str):
    """Run the socratic teaching session."""
    machine_file = Path(__file__).parent.parent.parent / "machine.yml"
    hooks = SocraticTeacherHooks()
    machine = FlatMachine(config_file=str(machine_file), hooks=hooks)

    input_data = {
        "topic": topic,
        "learner_level": level,
        "max_rounds": max_rounds,
        "working_dir": working_dir,
    }

    result = await machine.execute(input=input_data)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Socratic teaching assistant for guided learning"
    )
    parser.add_argument("--topic", required=True, help="Learning topic")
    parser.add_argument(
        "--level",
        type=int,
        default=1,
        help="Learner level (1-5, default: 1)",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=10,
        help="Maximum teaching rounds (default: 10)",
    )
    parser.add_argument(
        "--working-dir",
        type=str,
        default=".",
        help="Working directory for session files",
    )
    parser.add_argument(
        "--cwd",
        type=str,
        default=None,
        help="Alias for --working-dir",
    )

    args = parser.parse_args()
    working_dir = args.working_dir
    if args.cwd and args.working_dir == ".":
        working_dir = args.cwd

    result = asyncio.run(run(args.topic, args.level, args.max_rounds, working_dir))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
