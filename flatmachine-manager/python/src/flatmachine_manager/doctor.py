"""
Doctor — check environment health and recommend fixes.

Read-only diagnostics. Does not modify anything.
"""

from __future__ import annotations

import os
import shlex
import sqlite3
from typing import List, Optional, Tuple


# (status, message, fix)
Check = Tuple[str, str, str]  # "ok" | "warn" | "error"


def _venv_python_candidates(skills_repo_dir: str, skill_dir: str) -> List[str]:
    """Return supported venv python paths (shared first, local fallback)."""
    return [
        os.path.join(skills_repo_dir, ".venv", "bin", "python"),
        os.path.join(skill_dir, "python", ".venv", "bin", "python"),
    ]


def _resolve_venv_python(skills_repo_dir: str, skill_dir: str) -> Optional[str]:
    for python in _venv_python_candidates(skills_repo_dir, skill_dir):
        if os.path.isfile(python):
            return python
    return None


def _check_venv(skills_repo_dir: str, skill_dir: str) -> Check:
    python = _resolve_venv_python(skills_repo_dir, skill_dir)
    if python:
        return ("ok", f"venv python found: {python}", "")

    candidates = _venv_python_candidates(skills_repo_dir, skill_dir)
    fix = (
        f"Try: cd {skills_repo_dir} && ./install.sh"
        f" OR cd {skill_dir}/python && bash run.sh"
    )
    return (
        "error",
        f"venv python not found (checked: {', '.join(candidates)})",
        fix,
    )


def _check_package(skills_repo_dir: str, skill_dir: str) -> Check:
    python = _resolve_venv_python(skills_repo_dir, skill_dir)
    if not python:
        return ("error", "Cannot check package — venv missing", "Fix venv first")

    ret = os.system(f'"{python}" -c "import flatmachine_manager" 2>/dev/null')
    if ret == 0:
        return ("ok", f"flatmachine_manager package installed ({python})", "")

    return (
        "error",
        "flatmachine_manager not installed in venv",
        f"uv pip install --python {python} -e {skill_dir}/python",
    )


def _check_schema_db(skill_dir: str) -> Check:
    """Check that schema.sql exists."""
    schema_sql = os.path.join(skill_dir, "schema.sql")

    if os.path.isfile(schema_sql):
        size = os.path.getsize(schema_sql)
        return ("ok", f"Schema SQL exists: {schema_sql} ({size} bytes)", "")

    return (
        "error",
        f"Schema definition missing: {schema_sql}",
        "Add flatmachine-manager/schema.sql",
    )


def _registry_init_fix(schema_path: str, db_path: str) -> str:
    q_schema = shlex.quote(schema_path)
    q_db = shlex.quote(db_path)
    return f"mkdir -p $(dirname {q_db}) && sqlite3 {q_db} < {q_schema}"


def _check_registry_db(db_path: str, schema_path: str) -> Check:
    if not os.path.isfile(db_path):
        return ("warn", f"Registry DB not found: {db_path}", _registry_init_fix(schema_path, db_path))

    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row

        # Check tables exist
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }

        required = {"machine_registry", "machine_versions"}
        missing = required - tables
        if missing:
            conn.close()
            return (
                "error",
                f"Registry DB missing tables: {', '.join(missing)}",
                f"Backup and re-initialize: cp {shlex.quote(db_path)} {shlex.quote(db_path)}.bak && {_registry_init_fix(schema_path, db_path)}",
            )

        # Check we can read
        count = conn.execute("SELECT count(*) FROM machine_registry").fetchone()[0]
        conn.close()
        return ("ok", f"Registry DB: {db_path} ({count} machines)", "")

    except sqlite3.Error as e:
        return (
            "error",
            f"Registry DB unreadable: {e}",
            f"Backup and re-initialize: cp {shlex.quote(db_path)} {shlex.quote(db_path)}.bak && {_registry_init_fix(schema_path, db_path)}",
        )


def _check_sqlite_version() -> Check:
    version = sqlite3.sqlite_version
    parts = [int(x) for x in version.split(".")]
    if parts[0] >= 3 and parts[1] >= 35:
        return ("ok", f"SQLite version: {version}", "")
    return (
        "warn",
        f"SQLite version {version} is old (recommend 3.35+)",
        "Upgrade system SQLite or Python for better JSON/WAL support",
    )


def run_doctor(skills_repo_dir: str, skill_dir: str, db_path: str) -> str:
    """Run all checks, return formatted report."""
    schema_path = os.path.join(skill_dir, "schema.sql")

    checks: List[Tuple[str, Check]] = [
        ("SQLite version", _check_sqlite_version()),
        ("Virtual environment", _check_venv(skills_repo_dir, skill_dir)),
        ("Python package", _check_package(skills_repo_dir, skill_dir)),
        ("Schema definition", _check_schema_db(skill_dir)),
        ("Registry DB", _check_registry_db(db_path, schema_path)),
    ]

    icons = {"ok": "✓", "warn": "⚠", "error": "✗"}
    lines = ["## flatmachines doctor", ""]

    errors = 0
    warnings = 0

    for label, (status, msg, fix) in checks:
        icon = icons.get(status, "?")
        lines.append(f"  {icon} **{label}**: {msg}")
        if fix:
            lines.append(f"    Fix: `{fix}`")
        if status == "error":
            errors += 1
        elif status == "warn":
            warnings += 1

    lines.append("")
    if errors == 0 and warnings == 0:
        lines.append("All checks passed.")
    else:
        parts = []
        if errors:
            parts.append(f"{errors} error(s)")
        if warnings:
            parts.append(f"{warnings} warning(s)")
        lines.append(f"{', '.join(parts)} found. See fixes above.")

    return "\n".join(lines)
