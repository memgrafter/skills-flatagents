"""
Coding Agent Demo for FlatAgents.

An agentic coding assistant that plans, implements, and verifies
code changes with human approval gates.

Usage:
    python -m coding_agent.main "Add input validation"
    ./run.sh "Create a hello world function" --cwd /path/to/project
    ./run.sh "Add feature" --cwd /project --claude  # Claude Code mode
"""

import argparse
import asyncio
from pathlib import Path
import os
import sys
import warnings
from typing import Any, Dict, Optional

# Suppress Pydantic serialization warnings
warnings.filterwarnings('ignore', message='.*Pydantic serializer warnings.*')
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')

from flatagents import FlatMachine, setup_logging, get_logger
from .hooks import CodingAgentHooks
from .claude_hooks import ClaudeCodingAgentHooks

# Configure logging (respects LOG_LEVEL env var for quiet mode)
log_level = os.environ.get('LOG_LEVEL', 'INFO')
setup_logging(level=log_level)
logger = get_logger(__name__)


async def run(task: str, cwd: str = ".", max_iterations: int = 5, claude_mode: bool = False):
    """
    Run the coding agent workflow.

    Args:
        task: The coding task to accomplish
        cwd: Working directory for the codebase
        max_iterations: Maximum revision iterations
        claude_mode: If True, use checkpoint/exit for approvals instead of input()
    """
    logger.info("=" * 70)
    logger.info("🤖 Coding Agent")
    logger.info("=" * 70)

    # Resolve paths
    config_path = Path(__file__).parent.parent.parent / 'machine.yml'
    working_dir = Path(cwd).expanduser().resolve()

    # Capture actual directory user ran from (for safety checks)
    user_cwd = Path.cwd().resolve()

    # Choose hooks class based on mode
    if claude_mode:
        hooks = ClaudeCodingAgentHooks(working_dir=str(working_dir))
    else:
        hooks = CodingAgentHooks(working_dir=str(working_dir))

    # Check for checkpoint restore in Claude mode
    checkpoint_context: Optional[Dict[str, Any]] = None
    resume_state: Optional[str] = None
    if claude_mode:
        checkpoint = ClaudeCodingAgentHooks.load_checkpoint(str(working_dir))
        if checkpoint:
            resume_state = checkpoint.get("review_type")
            checkpoint_context = checkpoint.get("context", {})
            logger.info(f"Resuming from checkpoint (review_type: {resume_state})")

    # Create machine with appropriate hooks
    machine = FlatMachine(
        config_file=str(config_path),
        hooks=hooks
    )

    logger.info(f"Machine: {machine.machine_name}")
    logger.info(f"Task: {task}")
    logger.info(f"Working Dir: {working_dir}")
    if claude_mode:
        logger.info("Mode: Claude Code (checkpoint/exit)")
    logger.info("-" * 70)

    # Build input - merge checkpoint context if resuming
    machine_input: Dict[str, Any] = {
        "task": task,
        "cwd": str(working_dir),
        "user_cwd": str(user_cwd),  # For path safety validation
        "max_iterations": max_iterations
    }

    # If resuming, merge the saved context into input
    # This preserves values like codebase_context, plan, changes, file_contents
    if checkpoint_context:
        # Merge checkpoint context, but let explicit input override
        for key, value in checkpoint_context.items():
            if key not in machine_input:
                machine_input[key] = value

        # Add resume info so machine can potentially skip states
        machine_input["_resume_from"] = resume_state

    # Execute
    result = await machine.execute(input=machine_input)

    # Display results
    logger.info("=" * 70)
    logger.info("📊 RESULTS")
    logger.info("=" * 70)
    logger.info(f"Status: {result.get('status', 'unknown')}")
    logger.info(f"Iterations: {result.get('iterations', 0)}")

    if result.get('changes'):
        changes = result['changes']
        if isinstance(changes, dict):
            logger.info(f"Summary: {changes.get('summary', '')}")
            files = changes.get('files', [])
            logger.info(f"Files affected: {len(files)}")

    logger.info("-" * 70)
    logger.info(f"Total API calls: {machine.total_api_calls}")
    logger.info(f"Estimated cost: ${machine.total_cost:.4f}")

    return result


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Coding Agent - Plans, implements, and verifies code changes"
    )
    parser.add_argument(
        "task",
        help="The coding task to accomplish"
    )
    parser.add_argument(
        "--cwd", "-c",
        default=".",
        help="Working directory for the codebase (default: current directory)"
    )
    parser.add_argument(
        "--max-iterations", "-m",
        type=int,
        default=5,
        help="Maximum revision iterations (default: 5)"
    )
    parser.add_argument(
        "--claude",
        action="store_true",
        help="Claude Code mode: use checkpoint/exit for approvals instead of input()"
    )
    args = parser.parse_args()
    
    asyncio.run(run(
        task=args.task,
        cwd=args.cwd,
        max_iterations=args.max_iterations,
        claude_mode=args.claude
    ))


if __name__ == "__main__":
    main()
