"""
Template catalog for flatmachine creation.

Each template is a complete, valid machine config with placeholder agents
and states. The LLM's job is parameterization, not generation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import yaml

SPEC_VERSION = "2.5.0"

# Standard CLI tool schemas (read, bash, write, edit).
# Matches flatagents/sdk/examples/coding_agent_cli/config/agent.yml.
CLI_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read",
            "description": (
                "Read the contents of a file. Output is truncated to 2000 lines "
                "or 50KB (whichever is hit first). Use offset/limit for large files. "
                "When you need the full file, continue with offset until complete."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read (relative or absolute)",
                    },
                    "offset": {
                        "type": "number",
                        "description": "Line number to start reading from (1-indexed)",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of lines to read",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": (
                "Execute a bash command in the current working directory. Returns "
                "stdout and stderr. Output is truncated to last 2000 lines or 50KB "
                "(whichever is hit first). Optionally provide a timeout in seconds."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Bash command to execute",
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds (optional, default 30)",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write",
            "description": (
                "Write content to a file. Creates the file if it doesn't exist, "
                "overwrites if it does. Automatically creates parent directories."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write (relative or absolute)",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit",
            "description": (
                "Edit a file by replacing exact text. The oldText must match exactly "
                "(including whitespace). Use this for precise, surgical edits."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to edit (relative or absolute)",
                    },
                    "oldText": {
                        "type": "string",
                        "description": "Exact text to find and replace (must match exactly)",
                    },
                    "newText": {
                        "type": "string",
                        "description": "New text to replace the old text with",
                    },
                },
                "required": ["path", "oldText", "newText"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _filter_cli_tools(
    tool_names: Optional[List[str]],
    db_path: Optional[str] = None,
) -> List[Dict]:
    """Filter tool definitions to only the named tools.

    Uses the ToolRegistry when available to validate that requested tools
    are active (not deprecated). Falls back to CLI_TOOL_DEFINITIONS if
    the registry is unavailable.

    Args:
        tool_names: List of tool names to include, or None for all CLI tools.
        db_path: Path to the registry DB (must match the CLI's --db).

    Returns:
        Filtered list of tool definitions.

    Raises:
        ValueError: If any requested tool is unknown or deprecated.
    """
    if tool_names is None:
        return CLI_TOOL_DEFINITIONS

    if db_path is None:
        # Fallback: filter CLI_TOOL_DEFINITIONS directly (no registry)
        available = {t["function"]["name"] for t in CLI_TOOL_DEFINITIONS}
        unknown = set(tool_names) - available
        if unknown:
            raise ValueError(
                f"Unknown tool(s): {', '.join(sorted(unknown))}. "
                f"Available: {', '.join(sorted(available))}"
            )
        filtered = [t for t in CLI_TOOL_DEFINITIONS if t["function"]["name"] in tool_names]
        if not filtered:
            raise ValueError(
                f"No tools selected. Available: {', '.join(sorted(available))}"
            )
        return filtered

    # Registry-backed validation
    from .tool_registry import ToolRegistry

    tr = ToolRegistry(db_path=db_path)
    tr.seed_defaults()  # idempotent

    try:
        unavailable = []
        deprecated = []
        schemas = []

        for name in tool_names:
            entry = tr.get(name)
            if entry is None:
                unavailable.append(name)
            elif entry.status == "deprecated":
                deprecated.append(name)
            else:
                schemas.append(entry.schema)

        if unavailable:
            active = tr.list_tools()
            available_names = sorted(e.name for e in active)
            raise ValueError(
                f"Unknown tool(s): {', '.join(sorted(unavailable))}. "
                f"Available: {', '.join(available_names)}"
            )
        if deprecated:
            raise ValueError(
                f"Deprecated tool(s): {', '.join(sorted(deprecated))}. "
                "Use 'undeprecate-tool' to restore, or choose a different tool."
            )
        if not schemas:
            active = tr.list_tools()
            available_names = sorted(e.name for e in active)
            raise ValueError(
                f"No tools selected. Available: {', '.join(available_names)}"
            )
        return schemas
    finally:
        tr.close()


def _make_agent_yaml(
    name: str,
    purpose: str,
    model_profile: str = "default",
    temperature: Optional[float] = None,
    tools: Optional[List[Dict]] = None,
    system: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a flatagent config dict.

    Raises:
        ValueError: If system prompt is empty or not provided.
    """
    if not system or not system.strip():
        raise ValueError(
            f"Agent '{name}' has no system prompt. "
            "A system prompt is required — pass it via "
            "--agent 'system:name:purpose:profile' or --system 'prompt'."
        )

    model: Any
    if temperature is not None:
        model = {"profile": model_profile, "temperature": temperature}
    else:
        model = model_profile

    agent: Dict[str, Any] = {
        "spec": "flatagent",
        "spec_version": SPEC_VERSION,
        "data": {
            "name": name,
            "model": model,
            "system": system,
            "user": "{{ input.task }}",
        },
        "metadata": {
            "description": purpose,
        },
    }
    if tools:
        agent["data"]["tools"] = tools
    return agent


def _extract_agent(
    agent_dict: Dict[str, Any],
    defaults: Dict[str, Any],
) -> Dict[str, Any]:
    """Extract agent fields from a user-provided dict, falling back to defaults.

    Returns dict with: name, purpose, model_profile, system, temperature, tools
    """
    return {
        "name": agent_dict.get("name", defaults.get("name", "agent")),
        "purpose": agent_dict.get("purpose", defaults.get("purpose", "")),
        "model_profile": agent_dict.get("model_profile", defaults.get("model_profile", "default")),
        "system": agent_dict.get("system", defaults.get("system")),
        "temperature": agent_dict.get("temperature", defaults.get("temperature")),
        "tools": agent_dict.get("tools", defaults.get("tools")),
    }


def _find_agent(
    agents: Optional[List[Dict]],
    match_substrings: List[str],
    defaults: Dict[str, Any],
) -> Dict[str, Any]:
    """Find an agent from the list whose name contains one of the substrings.

    Falls back to defaults if no match or agents is None.
    Always returns a dict with all standard agent fields.
    """
    if agents:
        for a in agents:
            n = a.get("name", "").lower()
            for sub in match_substrings:
                if sub in n:
                    return _extract_agent(a, defaults)
    return _extract_agent({}, defaults)


def _apply_context_fields(
    ctx: Dict[str, Any],
    context_fields: Optional[List[Dict]],
) -> None:
    """Merge user-specified context fields into the context dict (mutates ctx)."""
    if not context_fields:
        return
    for cf in context_fields:
        cname = cf["name"]
        if cf.get("from_input"):
            ctx[cname] = "{{ input." + cname + " }}"
        else:
            ctx[cname] = cf.get("default_value", "")


_DEFAULT_EXECUTION = {"type": "retry", "backoffs": [2, 8, 16], "jitter": 0.1}

_ERROR_STATE = {
    "type": "final",
    "output": {"error": "{{ context.last_error }}"},
}


def _build_machine(
    name: str,
    description: str,
    *,
    context: Dict[str, Any],
    agents: Dict[str, Any],
    states: Dict[str, Any],
    hooks: Any,
    tags: List[str],
) -> str:
    """Build a complete machine config dict and return as YAML string."""
    machine = {
        "spec": "flatmachine",
        "spec_version": SPEC_VERSION,
        "data": {
            "name": name,
            "context": context,
            "agents": agents,
            "states": states,
            "persistence": {"enabled": True, "backend": "sqlite"},
            "hooks": hooks,
        },
        "metadata": {
            "description": description,
            "tags": tags,
        },
    }
    # Omit agents key if empty (distributed-worker has none)
    if not agents:
        del machine["data"]["agents"]
    return yaml.dump(machine, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Template: tool-loop
# ---------------------------------------------------------------------------

def template_tool_loop(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
    tools: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> str:
    """Agent + tools + human review. Like coding agents."""
    tool_defs = _filter_cli_tools(tools, db_path=db_path)
    a = _extract_agent(
        (agents[0] if agents else {}),
        {"name": "worker", "purpose": description, "model_profile": "default", "tools": tool_defs},
    )

    ctx: Dict[str, Any] = {
        "task": "{{ input.task }}",
        "working_dir": "{{ input.working_dir | default('.') }}",
        "human_approved": False,
    }
    _apply_context_fields(ctx, context_fields)

    return _build_machine(
        name, description,
        context=ctx,
        agents={
            a["name"]: _make_agent_yaml(a["name"], a["purpose"], a["model_profile"],
                                        system=a["system"], tools=a["tools"]),
        },
        states={
            "start": {
                "type": "initial",
                "transitions": [{"to": "work"}],
            },
            "work": {
                "agent": a["name"],
                "tool_loop": {
                    "max_turns": 20,
                    "max_tool_calls": 80,
                    "max_cost": 2.0,
                    "tool_timeout": 60,
                    "total_timeout": 600,
                },
                "execution": _DEFAULT_EXECUTION,
                "on_error": "error_state",
                "input": {"task": "{{ context.task }}"},
                "output_to_context": {"result": "{{ output.content }}"},
                "transitions": [{"to": "human_review"}],
            },
            "human_review": {
                "action": "human_review",
                "transitions": [
                    {"condition": "context.human_approved == true", "to": "done"},
                    {"to": "work"},
                ],
            },
            "error_state": _ERROR_STATE,
            "done": {
                "type": "final",
                "output": {"result": "{{ context.result }}"},
            },
        },
        hooks=["logging", "cli-tools"],
        tags=["tool-use", "human-in-loop"],
    )


# ---------------------------------------------------------------------------
# Template: writer-critic
# ---------------------------------------------------------------------------

def template_writer_critic(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
    tools: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> str:
    """Iterative refinement: write → review → improve until quality threshold."""
    writer = _find_agent(agents, ["writ"], {
        "name": "writer", "purpose": "Generate content based on the task", "model_profile": "smart",
    })
    critic = _find_agent(agents, ["critic", "review"], {
        "name": "critic", "purpose": "Review and score content quality", "model_profile": "fast",
    })

    ctx: Dict[str, Any] = {
        "task": "{{ input.task }}",
        "content": "",
        "score": 0,
        "round": 0,
        "max_rounds": 5,
        "quality_threshold": 8,
    }
    _apply_context_fields(ctx, context_fields)

    return _build_machine(
        name, description,
        context=ctx,
        agents={
            writer["name"]: _make_agent_yaml(writer["name"], writer["purpose"], writer["model_profile"], system=writer["system"]),
            critic["name"]: _make_agent_yaml(critic["name"], critic["purpose"], critic["model_profile"], system=critic["system"]),
        },
        states={
            "start": {
                "type": "initial",
                "transitions": [{"to": "write"}],
            },
            "write": {
                "agent": writer["name"],
                "execution": _DEFAULT_EXECUTION,
                "on_error": "error_state",
                "input": {
                    "task": "{{ context.task }}",
                    "previous_content": "{{ context.content }}",
                    "feedback": "{{ context.feedback | default('') }}",
                    "round": "{{ context.round }}",
                },
                "output_to_context": {"content": "{{ output.content }}"},
                "transitions": [{"to": "review"}],
            },
            "review": {
                "agent": critic["name"],
                "execution": _DEFAULT_EXECUTION,
                "on_error": "error_state",
                "input": {
                    "content": "{{ context.content }}",
                    "task": "{{ context.task }}",
                },
                "output_to_context": {
                    "score": "{{ output.score }}",
                    "feedback": "{{ output.content }}",
                    "round": "{{ context.round + 1 }}",
                },
                "transitions": [
                    {"condition": "context.score >= context.quality_threshold", "to": "done"},
                    {"condition": "context.round >= context.max_rounds", "to": "done"},
                    {"to": "write"},
                ],
            },
            "error_state": _ERROR_STATE,
            "done": {
                "type": "final",
                "output": {
                    "content": "{{ context.content }}",
                    "score": "{{ context.score }}",
                    "rounds": "{{ context.round }}",
                },
            },
        },
        hooks="logging",
        tags=["writer-critic", "iterative-refinement"],
    )


# ---------------------------------------------------------------------------
# Template: ooda-workflow
# ---------------------------------------------------------------------------

def template_ooda_workflow(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
    tools: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> str:
    """Explore → Plan → Execute → Verify with human gates."""
    tool_defs = _filter_cli_tools(tools, db_path=db_path)
    planner = _find_agent(agents, ["plan"], {
        "name": "planner", "purpose": "Analyze task and produce implementation plan", "model_profile": "smart",
    })
    executor = _find_agent(agents, ["exec", "cod", "implement"], {
        "name": "executor", "purpose": "Execute the approved plan", "model_profile": "code",
        "tools": tool_defs,
    })
    reviewer = _find_agent(agents, ["review", "verif"], {
        "name": "reviewer", "purpose": "Review results for correctness", "model_profile": "fast",
    })

    ctx: Dict[str, Any] = {
        "task": "{{ input.task }}",
        "plan": "",
        "plan_approved": False,
        "result": "",
        "result_approved": False,
        "iteration": 0,
        "max_iterations": 5,
        "human_feedback": "",
    }
    _apply_context_fields(ctx, context_fields)

    return _build_machine(
        name, description,
        context=ctx,
        agents={
            planner["name"]: _make_agent_yaml(planner["name"], planner["purpose"], planner["model_profile"], system=planner["system"]),
            executor["name"]: _make_agent_yaml(executor["name"], executor["purpose"], executor["model_profile"],
                                               system=executor["system"], tools=executor.get("tools")),
            reviewer["name"]: _make_agent_yaml(reviewer["name"], reviewer["purpose"], reviewer["model_profile"], system=reviewer["system"]),
        },
        states={
            "start": {
                "type": "initial",
                "transitions": [{"to": "plan"}],
            },
            "plan": {
                "agent": planner["name"],
                "execution": _DEFAULT_EXECUTION,
                "on_error": "error_state",
                "input": {
                    "task": "{{ context.task }}",
                    "feedback": "{{ context.human_feedback }}",
                },
                "output_to_context": {"plan": "{{ output.content }}"},
                "transitions": [{"to": "review_plan"}],
            },
            "review_plan": {
                "action": "human_review_plan",
                "transitions": [
                    {"condition": "context.plan_approved == true", "to": "execute"},
                    {"condition": "context.iteration >= context.max_iterations", "to": "max_iterations"},
                    {"to": "plan"},
                ],
            },
            "execute": {
                "agent": executor["name"],
                "execution": _DEFAULT_EXECUTION,
                "on_error": "error_state",
                "input": {
                    "plan": "{{ context.plan }}",
                    "task": "{{ context.task }}",
                },
                "output_to_context": {"result": "{{ output.content }}"},
                "transitions": [{"to": "verify"}],
            },
            "verify": {
                "agent": reviewer["name"],
                "execution": _DEFAULT_EXECUTION,
                "on_error": "error_state",
                "input": {
                    "task": "{{ context.task }}",
                    "plan": "{{ context.plan }}",
                    "result": "{{ context.result }}",
                },
                "output_to_context": {
                    "review": "{{ output.content }}",
                    "iteration": "{{ context.iteration + 1 }}",
                },
                "transitions": [{"to": "review_result"}],
            },
            "review_result": {
                "action": "human_review_result",
                "transitions": [
                    {"condition": "context.result_approved == true", "to": "done"},
                    {"condition": "context.iteration >= context.max_iterations", "to": "max_iterations"},
                    {"to": "execute"},
                ],
            },
            "max_iterations": {
                "type": "final",
                "output": {
                    "status": "max_iterations",
                    "result": "{{ context.result }}",
                    "iterations": "{{ context.iteration }}",
                },
            },
            "error_state": _ERROR_STATE,
            "done": {
                "type": "final",
                "output": {
                    "status": "completed",
                    "result": "{{ context.result }}",
                    "iterations": "{{ context.iteration }}",
                },
            },
        },
        hooks=["logging", "cli-tools"],
        tags=["ooda", "human-in-loop", "plan-execute-verify"],
    )


# ---------------------------------------------------------------------------
# Template: pipeline
# ---------------------------------------------------------------------------

def template_pipeline(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
    tools: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> str:
    """Linear phase-separated: prep → expensive → wrap."""
    phase_agents = agents if agents else [
        {"name": "prep", "purpose": "Prepare and validate input", "model_profile": "fast"},
        {"name": "process", "purpose": "Main processing step", "model_profile": "smart"},
        {"name": "wrap", "purpose": "Format and finalize output", "model_profile": "fast"},
    ]
    phases = [_extract_agent(a, {"name": f"phase_{i}", "purpose": f"Phase {i+1}"})
              for i, a in enumerate(phase_agents)]

    ctx: Dict[str, Any] = {
        "task": "{{ input.task }}",
        "result": "",
    }
    _apply_context_fields(ctx, context_fields)

    agent_configs = {}
    state_configs: Dict[str, Any] = {
        "start": {"type": "initial", "transitions": [{"to": phases[0]["name"]}]},
    }

    for i, p in enumerate(phases):
        agent_configs[p["name"]] = _make_agent_yaml(
            p["name"], p["purpose"], p["model_profile"], system=p["system"],
        )
        next_state = phases[i + 1]["name"] if i + 1 < len(phases) else "done"
        state_configs[p["name"]] = {
            "agent": p["name"],
            "execution": _DEFAULT_EXECUTION,
            "on_error": "error_state",
            "input": {"task": "{{ context.task }}", "previous": "{{ context.result }}"},
            "output_to_context": {"result": "{{ output.content }}"},
            "transitions": [{"to": next_state}],
        }

    state_configs["error_state"] = _ERROR_STATE
    state_configs["done"] = {
        "type": "final",
        "output": {"result": "{{ context.result }}"},
    }

    return _build_machine(
        name, description,
        context=ctx,
        agents=agent_configs,
        states=state_configs,
        hooks="logging",
        tags=["pipeline", "phase-separated"],
    )


# ---------------------------------------------------------------------------
# Template: signal-wait
# ---------------------------------------------------------------------------

def template_signal_wait(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
    tools: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> str:
    """Async workflow with external signal/approval gates."""
    a = _extract_agent(
        (agents[0] if agents else {}),
        {"name": "worker", "purpose": description, "model_profile": "default"},
    )

    ctx: Dict[str, Any] = {
        "task": "{{ input.task }}",
        "task_id": "{{ input.task_id | default('default') }}",
        "result": "",
        "approved": False,
    }
    _apply_context_fields(ctx, context_fields)

    return _build_machine(
        name, description,
        context=ctx,
        agents={
            a["name"]: _make_agent_yaml(a["name"], a["purpose"], a["model_profile"], system=a["system"]),
        },
        states={
            "start": {
                "type": "initial",
                "transitions": [{"to": "work"}],
            },
            "work": {
                "agent": a["name"],
                "execution": _DEFAULT_EXECUTION,
                "on_error": "error_state",
                "input": {"task": "{{ context.task }}"},
                "output_to_context": {"result": "{{ output.content }}"},
                "transitions": [{"to": "wait_for_approval"}],
            },
            "wait_for_approval": {
                "wait_for": "approval/{{ context.task_id }}",
                "timeout": 86400,
                "output_to_context": {
                    "approved": "{{ output.approved }}",
                    "reviewer_feedback": "{{ output.feedback | default('') }}",
                },
                "transitions": [
                    {"condition": "context.approved == true", "to": "done"},
                    {"to": "rejected"},
                ],
            },
            "rejected": {
                "type": "final",
                "output": {
                    "status": "rejected",
                    "result": "{{ context.result }}",
                    "feedback": "{{ context.reviewer_feedback }}",
                },
            },
            "error_state": _ERROR_STATE,
            "done": {
                "type": "final",
                "output": {
                    "status": "approved",
                    "result": "{{ context.result }}",
                },
            },
        },
        hooks="logging",
        tags=["signal-wait", "approval-gate", "async"],
    )


# ---------------------------------------------------------------------------
# Template: distributed-worker
# ---------------------------------------------------------------------------

def template_distributed_worker(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
    tools: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> str:
    """Worker pool pattern: checker → spawner → workers."""
    ctx: Dict[str, Any] = {
        "worker_config_path": "{{ input.worker_config_path | default('./worker.yml') }}",
        "max_workers": 4,
        "pool_state": {},
        "spawn_plan": {},
    }
    _apply_context_fields(ctx, context_fields)

    return _build_machine(
        name, description,
        context=ctx,
        agents={},
        states={
            "start": {
                "type": "initial",
                "transitions": [{"to": "check_pool"}],
            },
            "check_pool": {
                "action": "get_pool_state",
                "on_error": "error_state",
                "transitions": [{"to": "calculate_spawn"}],
            },
            "calculate_spawn": {
                "action": "calculate_spawn",
                "on_error": "error_state",
                "transitions": [
                    {"condition": "context.spawn_plan.count > 0", "to": "spawn_workers"},
                    {"to": "done"},
                ],
            },
            "spawn_workers": {
                "action": "spawn_workers",
                "on_error": "error_state",
                "transitions": [{"to": "done"}],
            },
            "error_state": _ERROR_STATE,
            "done": {
                "type": "final",
                "output": {
                    "pool_state": "{{ context.pool_state }}",
                    "spawn_plan": "{{ context.spawn_plan }}",
                },
            },
        },
        hooks=["logging", "distributed-worker"],
        tags=["distributed", "worker-pool"],
    )


# ---------------------------------------------------------------------------
# Template dispatch
# ---------------------------------------------------------------------------

TEMPLATES = {
    "tool-loop": template_tool_loop,
    "writer-critic": template_writer_critic,
    "ooda-workflow": template_ooda_workflow,
    "pipeline": template_pipeline,
    "signal-wait": template_signal_wait,
    "distributed-worker": template_distributed_worker,
}

TEMPLATE_DESCRIPTIONS = {
    "tool-loop": "Agent + tools + human review (like coding agents)",
    "writer-critic": "Iterative refinement loop (write → review → improve)",
    "ooda-workflow": "Explore → Plan → Execute → Verify with human gates",
    "pipeline": "Linear phase-separated processing (prep → expensive → wrap)",
    "signal-wait": "Async workflow with external signal/approval gates",
    "distributed-worker": "Worker pool pattern (checker → spawner → workers)",
}


def create_from_template(
    template_name: str,
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
    tools: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> str:
    """Create a machine config YAML from a named template."""
    fn = TEMPLATES.get(template_name)
    if not fn:
        raise ValueError(
            f"Unknown template: {template_name}. "
            f"Available: {', '.join(TEMPLATES.keys())}"
        )
    return fn(
        name=name,
        description=description,
        agents=agents,
        states=states,
        context_fields=context_fields,
        tools=tools,
        db_path=db_path,
    )
