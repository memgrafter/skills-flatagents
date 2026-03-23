"""
FlatMachine Manager Hooks.

Provides the domain-specific tool provider, per-call display,
and human review for the CRUD machine.
"""

from typing import Any, Dict, List

from flatmachines import MachineHooks
from .tools import ManagerToolProvider
from .registry import MachineRegistry


def _dim(text: str) -> str:
    return f"\033[2m{text}\033[0m"


def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


def _green(text: str) -> str:
    return f"\033[32m{text}\033[0m"


def _red(text: str) -> str:
    return f"\033[31m{text}\033[0m"


class ManagerHooks(MachineHooks):
    """Hooks for flatmachine management workflow with per-call display and human review."""

    def __init__(self, registry: MachineRegistry, auto_approve: bool = False):
        self._provider = ManagerToolProvider(registry)
        self._auto_approve = auto_approve

    def get_tool_provider(self, state_name: str):
        return self._provider

    def on_action(self, action_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if action_name == "human_review":
            return self._human_review(context)
        return context

    def on_tool_calls(self, state_name: str, tool_calls: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Print agent thinking/content and token usage before tool execution."""
        content = context.get("_tool_loop_content")
        if content and content.strip():
            print()
            print(_dim(content.strip()))

        usage = context.get("_tool_loop_usage") or {}
        parts = []
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if input_tokens is not None or output_tokens is not None:
            parts.append(f"tokens: {input_tokens or 0}→{output_tokens or 0}")
        cost = context.get("_tool_loop_cost")
        if cost:
            parts.append(f"${cost:.4f}")
        if parts:
            print(_dim(" | ".join(parts)))

        return context

    def on_tool_result(self, state_name: str, tool_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Print tool call result."""
        name = tool_result.get("name", "")
        args = tool_result.get("arguments", {})
        is_error = tool_result.get("is_error", False)

        # Build label based on tool type
        if name == "create_machine":
            label = f"create_machine: {args.get('name', '?')} (template: {args.get('template', '?')})"
        elif name == "update_machine":
            label = f"update_machine: {args.get('name', '?')} ({args.get('operation', '?')})"
        elif name == "get_machine":
            label = f"get_machine: {args.get('name', '?')}"
        elif name == "list_machines":
            label = f"list_machines (status: {args.get('status', 'active')})"
        elif name == "select_model":
            label = f"select_model: {args.get('purpose', '?')}"
        elif name == "validate_machine":
            label = f"validate_machine: {args.get('name', '?')}"
        elif name == "diff_versions":
            label = f"diff_versions: {args.get('name', '?')} v{args.get('v1', '?')}→v{args.get('v2', '?')}"
        elif name == "duplicate_machine":
            label = f"duplicate_machine: {args.get('source', '?')} → {args.get('target', '?')}"
        elif name == "deprecate_machine":
            label = f"deprecate_machine: {args.get('name', '?')}"
        else:
            label = f"{name}: {args}"

        status = _red("✗") if is_error else _green("✓")
        print(f"  {status} {_bold(label)}")

        return context

    def _human_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Show results, ask for follow-up or accept."""
        result = context.get("result", "")
        if result:
            print()
            print(result)

        if self._auto_approve:
            context["human_approved"] = True
            return context

        print()
        try:
            response = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            response = ""

        if response:
            chain = context.get("_tool_loop_chain", [])
            chain.append({"role": "user", "content": response})
            context["_tool_loop_chain"] = chain
            context["human_approved"] = False
        else:
            context["human_approved"] = True

        return context
