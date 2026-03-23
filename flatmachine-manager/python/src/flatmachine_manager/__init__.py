"""FlatMachine Manager — CRUD machine for authoring and managing flatmachines."""

from .cli_hooks import CLIToolHooks
from .cli_tools import CLIToolProvider
from .hooks import ManagerHooks
from .hooks_registry import build_hooks_registry
from .registry import MachineRegistry
from .tools import ManagerToolProvider

__all__ = [
    "CLIToolHooks",
    "CLIToolProvider",
    "ManagerHooks",
    "ManagerToolProvider",
    "MachineRegistry",
    "build_hooks_registry",
]
