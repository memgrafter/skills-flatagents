"""
Domain-specific tools for flatmachine CRUD operations.

Replaces the general read/write/bash/edit tools from coding_machine_cli
with 7 purpose-built tools that prevent YAML hallucination and enforce
best practices.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from flatagents.tools import ToolResult

from .registry import MachineRegistry, MachineVersion
from .templates import TEMPLATES, TEMPLATE_DESCRIPTIONS, create_from_template
from .validation import validate_machine_config


# ---------------------------------------------------------------------------
# Model profile catalog
# ---------------------------------------------------------------------------

MODEL_CATALOG = {
    "default": {
        "profile": "default",
        "description": "gpt-5.3-codex — general-purpose default for all tasks",
        "provider": "openai-codex",
        "model": "gpt-5.3-codex",
        "strengths": ["general purpose", "balanced cost and quality"],
        "weaknesses": ["not optimized for any specific use case"],
    },
    "fast": {
        "profile": "fast",
        "description": "gpt-5.3-codex — good for routing, classification, and simple tasks",
        "provider": "openai-codex",
        "model": "gpt-5.3-codex",
        "strengths": ["speed", "balanced"],
        "weaknesses": ["less suited for complex reasoning"],
    },
    "smart": {
        "profile": "smart",
        "description": "gpt-5.3-codex — precise reasoning, analysis, and planning",
        "provider": "openai-codex",
        "model": "gpt-5.3-codex",
        "strengths": ["reasoning", "instruction following", "precision"],
        "weaknesses": ["higher cost per call"],
    },
    "code": {
        "profile": "code",
        "description": "gpt-5.3-codex — optimized for code generation, editing, and tool use",
        "provider": "openai-codex",
        "model": "gpt-5.3-codex",
        "strengths": ["code generation", "tool use", "large context"],
        "weaknesses": ["general purpose"],
    },
    "cheap": {
        "profile": "cheap",
        "description": "gpt-5.3-codex — balanced cost/quality for high-volume tasks",
        "provider": "openai-codex",
        "model": "gpt-5.3-codex",
        "strengths": ["balanced", "reliable"],
        "weaknesses": ["less precise than smart profile"],
    },
}

PURPOSE_TO_PROFILE = {
    "fast": "fast",
    "smart": "smart",
    "cheap": "cheap",
    "code": "code",
    "routing": "fast",
    "creative": "smart",
    "analysis": "smart",
}


# ---------------------------------------------------------------------------
# Tool: list_machines
# ---------------------------------------------------------------------------

async def tool_list_machines(
    registry: MachineRegistry,
    _id: str,
    args: Dict[str, Any],
) -> ToolResult:
    """List all registered flatmachines."""
    status = args.get("status", "active")
    try:
        entries = registry.list_machines(status=status)
        if not entries:
            return ToolResult(content="No machines found in registry.")

        lines = ["| Name | Version | Spec | Status | Description |",
                  "|------|---------|------|--------|-------------|"]
        for e in entries:
            v = f"v{e.latest_version}" if e.latest_version else "-"
            lines.append(f"| {e.name} | {v} | - | {e.status} | {e.description[:60]} |")
        return ToolResult(content="\n".join(lines))
    except Exception as e:
        return ToolResult(content=f"Error listing machines: {e}", is_error=True)


# ---------------------------------------------------------------------------
# Tool: get_machine
# ---------------------------------------------------------------------------

async def tool_get_machine(
    registry: MachineRegistry,
    _id: str,
    args: Dict[str, Any],
) -> ToolResult:
    """Get a flatmachine definition and metadata."""
    name = args.get("name", "")
    version = args.get("version")

    try:
        if version is not None:
            ver = registry.get_version(name, int(version))
        else:
            ver = registry.get_latest(name)

        if not ver:
            return ToolResult(
                content=f"Machine '{name}' not found" + (f" at version {version}" if version else ""),
                is_error=True,
            )

        # Build response
        lines = [
            f"## {ver.machine_name} v{ver.version}",
            f"**Spec version:** {ver.spec_version}",
            f"**Hash:** {ver.config_hash[:12]}...",
            f"**Created:** {ver.created_at}",
            f"**Created by:** {ver.created_by or 'unknown'}",
            f"**Description:** {ver.description}",
        ]

        # Validation status
        if ver.validation:
            val = json.loads(ver.validation)
            valid = val.get("valid", "unknown")
            lines.append(f"**Valid:** {valid}")

        # Version history
        versions = registry.list_versions(name, limit=5)
        if len(versions) > 1:
            lines.append(f"\n**Version history** (latest {len(versions)}):")
            for v in versions:
                marker = " ← current" if v.version == ver.version else ""
                lines.append(f"  v{v.version}: {v.description or 'no description'}{marker}")

        # Config
        lines.append(f"\n```yaml\n{ver.config_raw}\n```")

        return ToolResult(content="\n".join(lines))
    except Exception as e:
        return ToolResult(content=f"Error getting machine: {e}", is_error=True)


# ---------------------------------------------------------------------------
# Tool: create_machine
# ---------------------------------------------------------------------------

async def tool_create_machine(
    registry: MachineRegistry,
    _id: str,
    args: Dict[str, Any],
) -> ToolResult:
    """Create a new flatmachine from a template."""
    name = args.get("name", "")
    template = args.get("template", "")
    description = args.get("description", "")
    agents = args.get("agents")
    states = args.get("states")
    context_fields = args.get("context_fields")

    if not name:
        return ToolResult(content="Machine name is required", is_error=True)
    if not template:
        return ToolResult(content="Template is required", is_error=True)
    if template not in TEMPLATES:
        return ToolResult(
            content=f"Unknown template: {template}\n\nAvailable templates:\n"
                    + "\n".join(f"  - {k}: {v}" for k, v in TEMPLATE_DESCRIPTIONS.items()),
            is_error=True,
        )

    tools = args.get("tools")

    try:
        # Generate config from template
        config_raw = create_from_template(
            template_name=template,
            name=name,
            description=description,
            agents=agents,
            states=states,
            context_fields=context_fields,
            tools=tools,
            db_path=registry._db_path,
        )

        # Validate
        val_result = validate_machine_config(config_raw)

        # Store in registry
        ver = registry.create_version(
            name=name,
            config_raw=config_raw,
            description=description,
            created_by="flatmachine-manager",
            validation_result={
                "valid": val_result.valid,
                "errors": val_result.all_errors,
                "warnings": val_result.all_warnings,
            },
        )

        # Build response
        lines = [
            f"✓ Created **{name}** v{ver.version} from template `{template}`",
            f"  Hash: {ver.config_hash[:12]}...",
            f"  Spec version: {ver.spec_version}",
        ]

        if val_result.valid:
            lines.append("  Validation: ✓ passed")
        else:
            lines.append("  Validation: ✗ has errors")
            for e in val_result.all_errors[:5]:
                lines.append(f"    - {e}")

        if val_result.all_warnings:
            lines.append(f"  Warnings ({len(val_result.all_warnings)}):")
            for w in val_result.all_warnings[:5]:
                lines.append(f"    - {w}")

        lines.append(f"\n```yaml\n{config_raw}\n```")
        return ToolResult(content="\n".join(lines))

    except Exception as e:
        return ToolResult(content=f"Error creating machine: {e}", is_error=True)


# ---------------------------------------------------------------------------
# Tool: update_machine
# ---------------------------------------------------------------------------

async def tool_update_machine(
    registry: MachineRegistry,
    _id: str,
    args: Dict[str, Any],
) -> ToolResult:
    """Apply a structured mutation to an existing machine."""
    name = args.get("name", "")
    operation = args.get("operation", "")
    params = args.get("params", {})
    change_desc = args.get("description", "")

    try:
        # Get current version
        current = registry.get_latest(name)
        if not current:
            return ToolResult(content=f"Machine '{name}' not found", is_error=True)

        config = yaml.safe_load(current.config_raw)
        data = config.get("data", {})

        if operation == "add_state":
            state_name = params.get("state_name", "")
            if not state_name:
                return ToolResult(content="state_name is required for add_state", is_error=True)

            new_state: Dict[str, Any] = {}
            if params.get("agent"):
                new_state["agent"] = params["agent"]
                new_state["execution"] = {"type": "retry", "backoffs": [2, 8, 16], "jitter": 0.1}
                new_state["on_error"] = params.get("on_error", "error_state")
                new_state["input"] = {"task": "{{ context.task }}"}
                new_state["output_to_context"] = {"result": "{{ output.content }}"}
            if params.get("description"):
                # Add as comment-like metadata
                pass
            if params.get("transitions_to"):
                new_state["transitions"] = [{"to": t} for t in params["transitions_to"]]

            data.setdefault("states", {})[state_name] = new_state

            # Wire previous state to point to new state
            after = params.get("after_state")
            if after and after in data.get("states", {}):
                prev_state = data["states"][after]
                if isinstance(prev_state, dict) and "transitions" in prev_state:
                    # Update last default transition to point to new state
                    transitions = prev_state["transitions"]
                    if transitions and isinstance(transitions[-1], dict):
                        if not transitions[-1].get("condition"):
                            transitions[-1]["to"] = state_name

        elif operation == "remove_state":
            state_name = params.get("state_name", "")
            states = data.get("states", {})
            if state_name in states:
                del states[state_name]
            else:
                return ToolResult(content=f"State '{state_name}' not found", is_error=True)

        elif operation == "update_state":
            state_name = params.get("state_name", "")
            field_name = params.get("field", "")
            value = params.get("value")
            states = data.get("states", {})
            if state_name not in states:
                return ToolResult(content=f"State '{state_name}' not found", is_error=True)
            states[state_name][field_name] = value

        elif operation == "add_agent":
            agent_name = params.get("agent_name", "")
            purpose = params.get("purpose", "")
            profile = params.get("model_profile", "default")
            system = params.get("system")

            from .templates import _make_agent_yaml
            agent_config = _make_agent_yaml(agent_name, purpose, profile, system=system)
            data.setdefault("agents", {})[agent_name] = agent_config

        elif operation == "update_agent":
            agent_name = params.get("agent_name", "")
            field_name = params.get("field", "")
            value = params.get("value")
            agents = data.get("agents", {})
            if agent_name not in agents:
                return ToolResult(content=f"Agent '{agent_name}' not found", is_error=True)
            agent = agents[agent_name]
            if isinstance(agent, dict):
                agent_data = agent.get("data", agent)
                agent_data[field_name] = value
            else:
                return ToolResult(content=f"Agent '{agent_name}' is a ref, not inline config", is_error=True)

        elif operation == "update_context":
            key = params.get("key", "")
            value_template = params.get("value_template", "")
            data.setdefault("context", {})[key] = value_template

        elif operation == "update_setting":
            key = params.get("key", "")
            value = params.get("value")
            if key == "persistence":
                data["persistence"] = value
            elif key == "hooks":
                data["hooks"] = value
            else:
                data.setdefault("settings", {})[key] = value

        else:
            return ToolResult(
                content=f"Unknown operation: {operation}. "
                        "Valid: add_state, remove_state, update_state, add_agent, "
                        "update_agent, update_context, update_setting",
                is_error=True,
            )

        # Serialize updated config
        new_config_raw = yaml.dump(config, default_flow_style=False, sort_keys=False)

        # Validate
        val_result = validate_machine_config(new_config_raw)

        # Store new version
        ver = registry.create_version(
            name=name,
            config_raw=new_config_raw,
            description=change_desc or f"{operation}: {json.dumps(params)[:100]}",
            created_by="flatmachine-manager",
            validation_result={
                "valid": val_result.valid,
                "errors": val_result.all_errors,
                "warnings": val_result.all_warnings,
            },
        )

        # Diff
        diff = registry.diff_versions(name, ver.version - 1, ver.version)

        lines = [
            f"✓ Updated **{name}** → v{ver.version} ({operation})",
            f"  Hash: {ver.config_hash[:12]}...",
        ]

        if val_result.valid:
            lines.append("  Validation: ✓ passed")
        else:
            lines.append("  Validation: ✗ has errors")
            for e in val_result.all_errors[:5]:
                lines.append(f"    - {e}")

        if diff and diff != "(no differences)":
            lines.append(f"\n```diff\n{diff}\n```")

        return ToolResult(content="\n".join(lines))

    except Exception as e:
        return ToolResult(content=f"Error updating machine: {e}", is_error=True)


# ---------------------------------------------------------------------------
# Tool: select_model
# ---------------------------------------------------------------------------

async def tool_select_model(
    registry: MachineRegistry,
    _id: str,
    args: Dict[str, Any],
) -> ToolResult:
    """Choose a model profile based on purpose."""
    purpose = args.get("purpose", "")
    constraints = args.get("constraints", "")

    recommended_key = PURPOSE_TO_PROFILE.get(purpose, "default")
    recommended = MODEL_CATALOG.get(recommended_key)

    lines = [f"## Model Selection for: {purpose}"]
    if constraints:
        lines.append(f"**Constraints:** {constraints}")

    if recommended:
        lines.append(f"\n### ✓ Recommended: `{recommended['profile']}`")
        lines.append(f"**Provider:** {recommended['provider']}")
        lines.append(f"**Model:** {recommended['model']}")
        lines.append(f"**Description:** {recommended['description']}")
        lines.append(f"**Strengths:** {', '.join(recommended['strengths'])}")
        lines.append(f"**Weaknesses:** {', '.join(recommended['weaknesses'])}")

    lines.append("\n### All available profiles:")
    for key, cat in MODEL_CATALOG.items():
        marker = " ← recommended" if key == recommended_key else ""
        lines.append(f"  - **{cat['profile']}**: {cat['description']}{marker}")

    lines.append(f"\n**Usage:** Set `model_profile: \"{recommended_key}\"` in agent config")

    return ToolResult(content="\n".join(lines))


# ---------------------------------------------------------------------------
# Tool: validate_machine
# ---------------------------------------------------------------------------

async def tool_validate_machine(
    registry: MachineRegistry,
    _id: str,
    args: Dict[str, Any],
) -> ToolResult:
    """Run full validation on a machine."""
    name = args.get("name", "")
    version = args.get("version")

    try:
        if version is not None:
            ver = registry.get_version(name, int(version))
        else:
            ver = registry.get_latest(name)

        if not ver:
            return ToolResult(
                content=f"Machine '{name}' not found",
                is_error=True,
            )

        result = validate_machine_config(ver.config_raw)
        return ToolResult(content=result.summary())

    except Exception as e:
        return ToolResult(content=f"Error validating machine: {e}", is_error=True)


# ---------------------------------------------------------------------------
# Tool: diff_versions
# ---------------------------------------------------------------------------

async def tool_diff_versions(
    registry: MachineRegistry,
    _id: str,
    args: Dict[str, Any],
) -> ToolResult:
    """Diff two versions of a machine config."""
    name = args.get("name", "")
    v1 = args.get("v1")
    v2 = args.get("v2")

    if v1 is None or v2 is None:
        return ToolResult(content="Both v1 and v2 are required", is_error=True)

    try:
        diff = registry.diff_versions(name, int(v1), int(v2))
        if diff == "(no differences)":
            return ToolResult(content=f"No differences between {name} v{v1} and v{v2}")
        return ToolResult(content=f"```diff\n{diff}\n```")
    except Exception as e:
        return ToolResult(content=f"Error diffing versions: {e}", is_error=True)


# ---------------------------------------------------------------------------
# Tool: duplicate_machine
# ---------------------------------------------------------------------------

async def tool_duplicate_machine(
    registry: MachineRegistry,
    _id: str,
    args: Dict[str, Any],
) -> ToolResult:
    """Duplicate a machine under a new name."""
    source = args.get("source", "")
    target = args.get("target", "")
    version = args.get("version")
    description = args.get("description", "")

    if not source or not target:
        return ToolResult(content="Both source and target names are required", is_error=True)

    try:
        ver = registry.duplicate(
            source_name=source,
            target_name=target,
            source_version=int(version) if version is not None else None,
            description=description,
            created_by="flatmachine-manager",
        )
        return ToolResult(
            content=f"✓ Duplicated **{source}**"
                    + (f" v{version}" if version else "")
                    + f" → **{target}** v{ver.version}\n"
                    f"  Hash: {ver.config_hash[:12]}..."
        )
    except Exception as e:
        return ToolResult(content=f"Error duplicating machine: {e}", is_error=True)


# ---------------------------------------------------------------------------
# Tool: deprecate_machine
# ---------------------------------------------------------------------------

async def tool_deprecate_machine(
    registry: MachineRegistry,
    _id: str,
    args: Dict[str, Any],
) -> ToolResult:
    """Mark a machine as deprecated. Config and versions are preserved for inspection."""
    name = args.get("name", "")
    if not name:
        return ToolResult(content="Machine name is required", is_error=True)

    try:
        entry = registry._get_entry(name)
        if not entry:
            return ToolResult(content=f"Machine '{name}' not found", is_error=True)
        if entry.status == "deprecated":
            return ToolResult(content=f"Machine '{name}' is already deprecated")

        registry.deprecate(name)
        return ToolResult(
            content=f"✓ Deprecated **{name}** (v{entry.latest_version})\n"
                    f"  Config and version history preserved for inspection.\n"
                    f"  Use `list_machines --status all` to see deprecated machines."
        )
    except Exception as e:
        return ToolResult(content=f"Error deprecating machine: {e}", is_error=True)


# ---------------------------------------------------------------------------
# Tool provider
# ---------------------------------------------------------------------------

class ManagerToolProvider:
    """Tool provider with domain-specific flatmachine CRUD tools."""

    def __init__(self, registry: MachineRegistry):
        self._registry = registry

    def get_tool_definitions(self) -> list:
        return []  # Definitions come from agent YAML

    async def execute_tool(
        self, name: str, tool_call_id: str, arguments: Dict[str, Any],
    ) -> ToolResult:
        if name == "list_machines":
            return await tool_list_machines(self._registry, tool_call_id, arguments)
        elif name == "get_machine":
            return await tool_get_machine(self._registry, tool_call_id, arguments)
        elif name == "create_machine":
            return await tool_create_machine(self._registry, tool_call_id, arguments)
        elif name == "update_machine":
            return await tool_update_machine(self._registry, tool_call_id, arguments)
        elif name == "select_model":
            return await tool_select_model(self._registry, tool_call_id, arguments)
        elif name == "validate_machine":
            return await tool_validate_machine(self._registry, tool_call_id, arguments)
        elif name == "diff_versions":
            return await tool_diff_versions(self._registry, tool_call_id, arguments)
        elif name == "duplicate_machine":
            return await tool_duplicate_machine(self._registry, tool_call_id, arguments)
        elif name == "deprecate_machine":
            return await tool_deprecate_machine(self._registry, tool_call_id, arguments)
        else:
            return ToolResult(content=f"Unknown tool: {name}", is_error=True)
