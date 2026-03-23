"""
Template catalog for flatmachine creation.

Each template is a complete, valid machine config with placeholder agents
and states. The LLM's job is parameterization, not generation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import yaml

SPEC_VERSION = "2.5.0"


def _make_agent_yaml(
    name: str,
    purpose: str,
    model_profile: str = "default",
    temperature: Optional[float] = None,
    tools: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Generate a flatagent config dict."""
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
            "system": f"You are a specialist agent. Your purpose: {purpose}\n\nBe concise and precise in your output.",
            "user": "{{ input.task }}",
        },
        "metadata": {
            "description": purpose,
        },
    }
    if tools:
        agent["data"]["tools"] = tools
    return agent


def _base_context(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    ctx: Dict[str, str] = {}
    if extra:
        ctx.update(extra)
    return ctx


# ---------------------------------------------------------------------------
# Template: tool-loop
# ---------------------------------------------------------------------------

def template_tool_loop(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
) -> str:
    """Agent + tools + human review. Like coding agents."""
    agent_name = "worker"
    agent_purpose = description
    agent_profile = "default"

    if agents and len(agents) > 0:
        a = agents[0]
        agent_name = a.get("name", "worker")
        agent_purpose = a.get("purpose", description)
        agent_profile = a.get("model_profile", "default")

    ctx = {
        "task": "{{ input.task }}",
        "working_dir": "{{ input.working_dir | default('.') }}",
        "human_approved": False,
    }
    if context_fields:
        for cf in context_fields:
            cname = cf["name"]
            if cf.get("from_input"):
                ctx[cname] = "{{ input." + cname + " }}"
            else:
                ctx[cname] = cf.get("default_value", "")

    machine = {
        "spec": "flatmachine",
        "spec_version": SPEC_VERSION,
        "data": {
            "name": name,
            "context": ctx,
            "agents": {
                agent_name: _make_agent_yaml(agent_name, agent_purpose, agent_profile),
            },
            "states": {
                "start": {
                    "type": "initial",
                    "transitions": [{"to": "work"}],
                },
                "work": {
                    "agent": agent_name,
                    "tool_loop": {
                        "max_turns": 20,
                        "max_tool_calls": 80,
                        "max_cost": 2.0,
                        "tool_timeout": 60,
                        "total_timeout": 600,
                    },
                    "execution": {
                        "type": "retry",
                        "backoffs": [2, 8, 16],
                        "jitter": 0.1,
                    },
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
                "error_state": {
                    "type": "final",
                    "output": {
                        "error": "{{ context.last_error }}",
                        "error_type": "{{ context.last_error_type }}",
                    },
                },
                "done": {
                    "type": "final",
                    "output": {"result": "{{ context.result }}"},
                },
            },
            "persistence": {"enabled": True, "backend": "sqlite"},
        },
        "metadata": {
            "description": description,
            "tags": ["tool-use", "human-in-loop"],
        },
    }

    return yaml.dump(machine, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Template: writer-critic
# ---------------------------------------------------------------------------

def template_writer_critic(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
) -> str:
    """Iterative refinement: write → review → improve until quality threshold."""
    writer_name = "writer"
    critic_name = "critic"
    writer_purpose = "Generate content based on the task"
    critic_purpose = "Review and score content quality"
    writer_profile = "smart"
    critic_profile = "fast"

    if agents:
        for a in agents:
            n = a.get("name", "")
            if "writ" in n.lower():
                writer_name = n
                writer_purpose = a.get("purpose", writer_purpose)
                writer_profile = a.get("model_profile", writer_profile)
            elif "critic" in n.lower() or "review" in n.lower():
                critic_name = n
                critic_purpose = a.get("purpose", critic_purpose)
                critic_profile = a.get("model_profile", critic_profile)

    ctx: Dict[str, Any] = {
        "task": "{{ input.task }}",
        "content": "",
        "score": 0,
        "round": 0,
        "max_rounds": 5,
        "quality_threshold": 8,
    }
    if context_fields:
        for cf in context_fields:
            cname = cf["name"]
            if cf.get("from_input"):
                ctx[cname] = "{{ input." + cname + " }}"
            else:
                ctx[cname] = cf.get("default_value", "")

    machine = {
        "spec": "flatmachine",
        "spec_version": SPEC_VERSION,
        "data": {
            "name": name,
            "context": ctx,
            "agents": {
                writer_name: _make_agent_yaml(writer_name, writer_purpose, writer_profile),
                critic_name: _make_agent_yaml(critic_name, critic_purpose, critic_profile),
            },
            "states": {
                "start": {
                    "type": "initial",
                    "transitions": [{"to": "write"}],
                },
                "write": {
                    "agent": writer_name,
                    "execution": {"type": "retry", "backoffs": [2, 8, 16], "jitter": 0.1},
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
                    "agent": critic_name,
                    "execution": {"type": "retry", "backoffs": [2, 8, 16], "jitter": 0.1},
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
                "error_state": {
                    "type": "final",
                    "output": {"error": "{{ context.last_error }}"},
                },
                "done": {
                    "type": "final",
                    "output": {
                        "content": "{{ context.content }}",
                        "score": "{{ context.score }}",
                        "rounds": "{{ context.round }}",
                    },
                },
            },
            "persistence": {"enabled": True, "backend": "sqlite"},
        },
        "metadata": {
            "description": description,
            "tags": ["writer-critic", "iterative-refinement"],
        },
    }

    return yaml.dump(machine, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Template: ooda-workflow
# ---------------------------------------------------------------------------

def template_ooda_workflow(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
) -> str:
    """Explore → Plan → Execute → Verify with human gates."""
    planner_name = "planner"
    executor_name = "executor"
    reviewer_name = "reviewer"
    planner_profile = "smart"
    executor_profile = "code"
    reviewer_profile = "fast"

    if agents:
        for a in agents:
            n = a.get("name", "").lower()
            if "plan" in n:
                planner_name = a["name"]
                planner_profile = a.get("model_profile", planner_profile)
            elif "exec" in n or "cod" in n or "implement" in n:
                executor_name = a["name"]
                executor_profile = a.get("model_profile", executor_profile)
            elif "review" in n or "verif" in n:
                reviewer_name = a["name"]
                reviewer_profile = a.get("model_profile", reviewer_profile)

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
    if context_fields:
        for cf in context_fields:
            cname = cf["name"]
            if cf.get("from_input"):
                ctx[cname] = "{{ input." + cname + " }}"
            else:
                ctx[cname] = cf.get("default_value", "")

    machine = {
        "spec": "flatmachine",
        "spec_version": SPEC_VERSION,
        "data": {
            "name": name,
            "context": ctx,
            "agents": {
                planner_name: _make_agent_yaml(planner_name, "Analyze task and produce implementation plan", planner_profile),
                executor_name: _make_agent_yaml(executor_name, "Execute the approved plan", executor_profile),
                reviewer_name: _make_agent_yaml(reviewer_name, "Review results for correctness", reviewer_profile),
            },
            "states": {
                "start": {
                    "type": "initial",
                    "transitions": [{"to": "plan"}],
                },
                "plan": {
                    "agent": planner_name,
                    "execution": {"type": "retry", "backoffs": [2, 8, 16], "jitter": 0.1},
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
                    "agent": executor_name,
                    "execution": {"type": "retry", "backoffs": [2, 8, 16], "jitter": 0.1},
                    "on_error": "error_state",
                    "input": {
                        "plan": "{{ context.plan }}",
                        "task": "{{ context.task }}",
                    },
                    "output_to_context": {"result": "{{ output.content }}"},
                    "transitions": [{"to": "verify"}],
                },
                "verify": {
                    "agent": reviewer_name,
                    "execution": {"type": "retry", "backoffs": [2, 8, 16], "jitter": 0.1},
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
                "error_state": {
                    "type": "final",
                    "output": {"error": "{{ context.last_error }}"},
                },
                "done": {
                    "type": "final",
                    "output": {
                        "status": "completed",
                        "result": "{{ context.result }}",
                        "iterations": "{{ context.iteration }}",
                    },
                },
            },
            "persistence": {"enabled": True, "backend": "sqlite"},
        },
        "metadata": {
            "description": description,
            "tags": ["ooda", "human-in-loop", "plan-execute-verify"],
        },
    }

    return yaml.dump(machine, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Template: pipeline
# ---------------------------------------------------------------------------

def template_pipeline(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
) -> str:
    """Linear phase-separated: prep → expensive → wrap."""
    phase_agents = []
    if agents:
        phase_agents = agents
    else:
        phase_agents = [
            {"name": "prep", "purpose": "Prepare and validate input", "model_profile": "fast"},
            {"name": "process", "purpose": "Main processing step", "model_profile": "smart"},
            {"name": "wrap", "purpose": "Format and finalize output", "model_profile": "fast"},
        ]

    ctx: Dict[str, Any] = {
        "task": "{{ input.task }}",
        "result": "",
    }
    if context_fields:
        for cf in context_fields:
            cname = cf["name"]
            if cf.get("from_input"):
                ctx[cname] = "{{ input." + cname + " }}"
            else:
                ctx[cname] = cf.get("default_value", "")

    agent_configs = {}
    state_configs: Dict[str, Any] = {
        "start": {"type": "initial", "transitions": [{"to": phase_agents[0]["name"]}]},
    }

    for i, a in enumerate(phase_agents):
        aname = a["name"]
        purpose = a.get("purpose", f"Phase {i+1}")
        profile = a.get("model_profile", "default")

        agent_configs[aname] = _make_agent_yaml(aname, purpose, profile)

        next_state = phase_agents[i + 1]["name"] if i + 1 < len(phase_agents) else "done"
        state_configs[aname] = {
            "agent": aname,
            "execution": {"type": "retry", "backoffs": [2, 8, 16], "jitter": 0.1},
            "on_error": "error_state",
            "input": {"task": "{{ context.task }}", "previous": "{{ context.result }}"},
            "output_to_context": {"result": "{{ output.content }}"},
            "transitions": [{"to": next_state}],
        }

    state_configs["error_state"] = {
        "type": "final",
        "output": {"error": "{{ context.last_error }}"},
    }
    state_configs["done"] = {
        "type": "final",
        "output": {"result": "{{ context.result }}"},
    }

    machine = {
        "spec": "flatmachine",
        "spec_version": SPEC_VERSION,
        "data": {
            "name": name,
            "context": ctx,
            "agents": agent_configs,
            "states": state_configs,
            "persistence": {"enabled": True, "backend": "sqlite"},
        },
        "metadata": {
            "description": description,
            "tags": ["pipeline", "phase-separated"],
        },
    }

    return yaml.dump(machine, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Template: signal-wait
# ---------------------------------------------------------------------------

def template_signal_wait(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
) -> str:
    """Async workflow with external signal/approval gates."""
    worker_name = "worker"
    worker_profile = "default"

    if agents and len(agents) > 0:
        worker_name = agents[0].get("name", "worker")
        worker_profile = agents[0].get("model_profile", "default")

    ctx: Dict[str, Any] = {
        "task": "{{ input.task }}",
        "task_id": "{{ input.task_id | default('default') }}",
        "result": "",
        "approved": False,
    }
    if context_fields:
        for cf in context_fields:
            cname = cf["name"]
            if cf.get("from_input"):
                ctx[cname] = "{{ input." + cname + " }}"
            else:
                ctx[cname] = cf.get("default_value", "")

    machine = {
        "spec": "flatmachine",
        "spec_version": SPEC_VERSION,
        "data": {
            "name": name,
            "context": ctx,
            "agents": {
                worker_name: _make_agent_yaml(worker_name, description, worker_profile),
            },
            "states": {
                "start": {
                    "type": "initial",
                    "transitions": [{"to": "work"}],
                },
                "work": {
                    "agent": worker_name,
                    "execution": {"type": "retry", "backoffs": [2, 8, 16], "jitter": 0.1},
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
                "error_state": {
                    "type": "final",
                    "output": {"error": "{{ context.last_error }}"},
                },
                "done": {
                    "type": "final",
                    "output": {
                        "status": "approved",
                        "result": "{{ context.result }}",
                    },
                },
            },
            "persistence": {"enabled": True, "backend": "sqlite"},
        },
        "metadata": {
            "description": description,
            "tags": ["signal-wait", "approval-gate", "async"],
        },
    }

    return yaml.dump(machine, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Template: distributed-worker
# ---------------------------------------------------------------------------

def template_distributed_worker(
    name: str,
    description: str,
    agents: Optional[List[Dict]] = None,
    states: Optional[List[Dict]] = None,
    context_fields: Optional[List[Dict]] = None,
) -> str:
    """Worker pool pattern: checker → spawner → workers."""
    ctx: Dict[str, Any] = {
        "worker_config_path": "{{ input.worker_config_path | default('./worker.yml') }}",
        "max_workers": 4,
        "pool_state": {},
        "spawn_plan": {},
    }
    if context_fields:
        for cf in context_fields:
            cname = cf["name"]
            if cf.get("from_input"):
                ctx[cname] = "{{ input." + cname + " }}"
            else:
                ctx[cname] = cf.get("default_value", "")

    machine = {
        "spec": "flatmachine",
        "spec_version": SPEC_VERSION,
        "data": {
            "name": name,
            "context": ctx,
            "states": {
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
                "error_state": {
                    "type": "final",
                    "output": {"error": "{{ context.last_error }}"},
                },
                "done": {
                    "type": "final",
                    "output": {
                        "pool_state": "{{ context.pool_state }}",
                        "spawn_plan": "{{ context.spawn_plan }}",
                    },
                },
            },
            "persistence": {"enabled": True, "backend": "sqlite"},
            "hooks": "distributed-worker",
        },
        "metadata": {
            "description": description,
            "tags": ["distributed", "worker-pool"],
        },
    }

    return yaml.dump(machine, default_flow_style=False, sort_keys=False)


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
    )
