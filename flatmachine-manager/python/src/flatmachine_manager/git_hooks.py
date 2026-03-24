"""
Git Diff Staged Hooks.

Extends CLIToolHooks with a git_diff_staged tool that runs
``git diff --staged <target>`` and returns the unified diff.

The target path is resolved so the command works whether the
caller passes a repo-level subdirectory, ``~``, or ``/``.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from flatagents.tools import ToolResult

from .cli_hooks import CLIToolHooks
from .cli_tools import CLIToolProvider, _truncate_tail


# -- tool implementation ----------------------------------------------------

async def tool_git_diff_staged(
    working_dir: str,
    _id: str,
    args: Dict[str, Any],
) -> ToolResult:
    """Run ``git diff --staged`` scoped to *target* (directory or file).

    The command discovers the git toplevel for *target* automatically,
    so it works for repo-internal paths, home-dir paths, and ``/``-rooted
    paths alike.
    """
    raw_target = args.get("target", ".")
    stat_only = args.get("stat_only", False)

    try:
        # Resolve the target to an absolute path
        target = Path(raw_target).expanduser()
        if not target.is_absolute():
            target = Path(working_dir) / target
        target = target.resolve()

        if not target.exists():
            return ToolResult(
                content=f"Target path does not exist: {target}",
                is_error=True,
            )

        # Find the git repo root that owns this target
        try:
            repo_root = subprocess.run(
                ["git", "-C", str(target if target.is_dir() else target.parent),
                 "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=10,
            )
            if repo_root.returncode != 0:
                return ToolResult(
                    content=f"Not inside a git repository: {target}\n{repo_root.stderr.strip()}",
                    is_error=True,
                )
            toplevel = repo_root.stdout.strip()
        except FileNotFoundError:
            return ToolResult(content="git is not installed or not on PATH", is_error=True)

        # Build the diff command
        cmd = ["git", "-C", toplevel, "diff", "--staged"]
        if stat_only:
            cmd.append("--stat")
        cmd.append("--")
        cmd.append(str(target))

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
        )

        output = result.stdout or ""
        if result.stderr:
            output = output + "\n" + result.stderr if output else result.stderr

        if not output.strip():
            return ToolResult(content="(no staged changes found)")

        # Truncate if enormous
        truncated, was_truncated, _ = _truncate_tail(output)
        if was_truncated:
            truncated += "\n\n[output truncated — use stat_only=true for a summary]"

        return ToolResult(content=truncated)

    except subprocess.TimeoutExpired:
        return ToolResult(content="git diff --staged timed out after 30s", is_error=True)
    except Exception as e:
        return ToolResult(content=f"Error running git diff --staged: {e}", is_error=True)


# -- composite tool provider ------------------------------------------------

class GitDiffStagedToolProvider(CLIToolProvider):
    """CLIToolProvider + git_diff_staged.

    Inherits read / bash / write / edit execution and adds the
    ``git_diff_staged`` tool on top.
    """

    async def execute_tool(
        self, name: str, tool_call_id: str, arguments: Dict[str, Any],
    ) -> ToolResult:
        if name == "git_diff_staged":
            return await tool_git_diff_staged(self.working_dir, tool_call_id, arguments)
        return await super().execute_tool(name, tool_call_id, arguments)


# -- hooks ------------------------------------------------------------------

class GitDiffStagedHooks(CLIToolHooks):
    """CLIToolHooks variant whose provider also handles git_diff_staged.

    Use ``hooks: ["logging", "git-diff-staged"]`` in the machine config
    (replaces ``cli-tools`` since this hook is a strict superset).
    """

    def __init__(self, working_dir: str = "."):
        super().__init__(working_dir=working_dir)
        # Replace the base-class provider with the extended one
        self._provider = GitDiffStagedToolProvider(working_dir)

    # on_tool_result: augment label for the new tool
    def on_tool_result(
        self,
        state_name: str,
        tool_result: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        name = tool_result.get("name", "")
        if name == "git_diff_staged":
            args = tool_result.get("arguments", {})
            is_error = tool_result.get("is_error", False)
            target = args.get("target", ".")
            stat = " (stat)" if args.get("stat_only") else ""
            label = f"git_diff_staged: {target}{stat}"

            from .cli_hooks import _red, _green, _bold
            status = _red("✗") if is_error else _green("✓")
            print(f"  {status} {_bold(label)}")
            return context

        return super().on_tool_result(state_name, tool_result, context)
