"""
Hooks registry for the flatmachine-manager skill.

Builds a HooksRegistry with the hooks this skill owns. Machine configs
reference hooks by name and the SDK resolves them at runtime.

Registry names (always available):
    "logging"             — LoggingHooks (SDK built-in)
    "metrics"             — MetricsHooks (SDK built-in)
    "cli-tools"           — CLIToolHooks (read/bash/write/edit + display + human review)

Registry names (when dependencies provided):
    "manager"             — ManagerHooks (CRUD tools + display + human review)
    "distributed-worker"  — DistributedWorkerHooks (needs registration + work backends)

Usage:
    from .hooks_registry import build_hooks_registry

    hr = build_hooks_registry(registry=my_registry, working_dir="/tmp/work")
    machine = FlatMachine(config_file=path, hooks_registry=hr)
"""

from __future__ import annotations

from typing import Optional

from flatmachines import HooksRegistry, LoggingHooks, MetricsHooks

from .cli_hooks import CLIToolHooks
from .git_hooks import GitDiffStagedHooks
from .hooks import ManagerHooks
from .registry import MachineRegistry


def build_hooks_registry(
    *,
    registry: Optional[MachineRegistry] = None,
    working_dir: str = ".",
    auto_approve: bool = False,
) -> HooksRegistry:
    """
    Build a HooksRegistry with all hooks owned by this skill.

    Args:
        registry: MachineRegistry instance (required for "manager" hooks)
        working_dir: Working directory for CLI tool hooks
        auto_approve: If True, manager hooks skip human review

    Returns:
        Fully populated HooksRegistry
    """
    hr = HooksRegistry()

    # SDK built-ins (zero-arg constructors)
    hr.register("logging", LoggingHooks)
    hr.register("metrics", MetricsHooks)

    # CLI tools — factory that captures working_dir
    hr.register("cli-tools", lambda: CLIToolHooks(working_dir=working_dir))

    # Git diff staged — superset of cli-tools with git_diff_staged tool
    hr.register("git-diff-staged", lambda: GitDiffStagedHooks(working_dir=working_dir))

    # Manager — factory that captures registry + auto_approve
    if registry is not None:
        hr.register(
            "manager",
            lambda: ManagerHooks(registry=registry, auto_approve=auto_approve),
        )

    # distributed-worker requires registration + work backends at construction
    # time. Register it explicitly when those backends are available:
    #
    #   from flatmachines.distributed_hooks import DistributedWorkerHooks
    #   hr.register("distributed-worker",
    #               lambda: DistributedWorkerHooks(registration=reg, work=work))

    return hr
