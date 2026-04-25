"""Codebase Ripper - Shotgun approach to codebase exploration."""

from .hooks import CodebaseRipperHooks

__all__ = ["CodebaseRipperHooks", "main", "run"]


def __getattr__(name):
    if name in {"main", "run"}:
        from .main import main, run
        return {"main": main, "run": run}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
