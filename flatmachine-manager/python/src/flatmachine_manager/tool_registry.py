"""
Tool Registry — SQLite-backed, immutable tool catalog.

Tools are registered once and never modified. Deprecation hides them
from new machine creation but preserves them for existing machines.

Follows the same layout pattern as MachineRegistry.
"""

from __future__ import annotations

import json
import sqlite3
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ToolEntry:
    name: str
    description: str
    schema_json: str
    provider: str
    status: str
    created_at: str

    @property
    def schema(self) -> Dict[str, Any]:
        """Parsed OpenAI function-calling schema."""
        return json.loads(self.schema_json)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_schema(schema: Dict[str, Any]) -> str:
    """Canonical JSON for comparison — sorted keys, no whitespace variance."""
    return json.dumps(schema, sort_keys=True, separators=(",", ":"))


class ToolRegistry:
    """SQLite-backed, immutable tool catalog."""

    def __init__(self, db_path: str = "flatmachine_registry.sqlite"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.executescript(textwrap.dedent("""\
            CREATE TABLE IF NOT EXISTS tool_registry (
                name         TEXT PRIMARY KEY,
                description  TEXT NOT NULL DEFAULT '',
                schema_json  TEXT NOT NULL,
                provider     TEXT NOT NULL DEFAULT '',
                status       TEXT NOT NULL DEFAULT 'active',
                created_at   TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tool_provider
                ON tool_registry(provider);
            CREATE INDEX IF NOT EXISTS idx_tool_status
                ON tool_registry(status);
        """))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # --- Registration (insert-only) ---

    def register(
        self,
        name: str,
        schema: Dict[str, Any],
        provider: str,
        description: str = "",
    ) -> ToolEntry:
        """Register a tool. Immutable — rejects if name exists with different schema.

        If the same name+schema already exists, this is a no-op and returns
        the existing entry. If the name exists with a *different* schema,
        raises ValueError.
        """
        canonical = _normalize_schema(schema)
        existing = self.get(name)

        if existing is not None:
            if _normalize_schema(existing.schema) == canonical:
                return existing  # idempotent
            raise ValueError(
                f"Tool '{name}' already registered with a different schema. "
                "Tools are immutable — register under a new name or deprecate the old one."
            )

        now = _utc_now()
        self._conn.execute(
            """INSERT INTO tool_registry (name, description, schema_json, provider, status, created_at)
               VALUES (?, ?, ?, ?, 'active', ?)""",
            (name, description, json.dumps(schema), provider, now),
        )
        self._conn.commit()

        return ToolEntry(
            name=name, description=description,
            schema_json=json.dumps(schema), provider=provider,
            status="active", created_at=now,
        )

    def register_batch(
        self,
        tools: List[Dict[str, Any]],
        provider: str,
    ) -> List[ToolEntry]:
        """Register multiple tools from OpenAI function-calling format.

        Each item should be {"type": "function", "function": {"name": ..., "description": ..., ...}}.
        """
        entries = []
        for tool_def in tools:
            fn = tool_def.get("function", {})
            name = fn.get("name", "")
            desc = fn.get("description", "")
            if not name:
                continue
            entry = self.register(name, tool_def, provider, description=desc)
            entries.append(entry)
        return entries

    # --- Lookup ---

    def get(self, name: str) -> Optional[ToolEntry]:
        """Get a tool by name regardless of status."""
        row = self._conn.execute(
            "SELECT name, description, schema_json, provider, status, created_at "
            "FROM tool_registry WHERE name = ?",
            (name,),
        ).fetchone()
        return self._row_to_entry(row) if row else None

    def list_tools(
        self,
        *,
        provider: Optional[str] = None,
        include_deprecated: bool = False,
    ) -> List[ToolEntry]:
        """List tools, optionally filtered by provider."""
        conditions = []
        params: list = []

        if not include_deprecated:
            conditions.append("status = 'active'")
        if provider is not None:
            conditions.append("provider = ?")
            params.append(provider)

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = self._conn.execute(
            f"SELECT name, description, schema_json, provider, status, created_at "
            f"FROM tool_registry{where} ORDER BY provider, name",
            params,
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def is_available(self, name: str) -> bool:
        """True only if the tool exists and is active."""
        row = self._conn.execute(
            "SELECT status FROM tool_registry WHERE name = ?",
            (name,),
        ).fetchone()
        return row is not None and row[0] == "active"

    # --- Lifecycle ---

    def deprecate(self, name: str) -> None:
        """Hide tool from new machine creation. Existing machines unaffected."""
        entry = self.get(name)
        if entry is None:
            raise ValueError(f"Tool '{name}' not found")
        if entry.status == "deprecated":
            return  # already deprecated
        self._conn.execute(
            "UPDATE tool_registry SET status = 'deprecated' WHERE name = ?",
            (name,),
        )
        self._conn.commit()

    def undeprecate(self, name: str) -> None:
        """Restore a deprecated tool so it's available for new machines again."""
        entry = self.get(name)
        if entry is None:
            raise ValueError(f"Tool '{name}' not found")
        if entry.status == "active":
            return  # already active
        self._conn.execute(
            "UPDATE tool_registry SET status = 'active' WHERE name = ?",
            (name,),
        )
        self._conn.commit()

    # --- Seeding ---

    def seed_from_cli_tools(self) -> List[ToolEntry]:
        """Auto-seed CLI tool definitions (read, bash, write, edit)."""
        from .templates import CLI_TOOL_DEFINITIONS
        return self.register_batch(CLI_TOOL_DEFINITIONS, provider="cli-tools")

    def seed_from_agent_yaml(self, agent_yaml_path: str, provider: str = "manager") -> List[ToolEntry]:
        """Auto-seed tool definitions from an agent YAML file."""
        path = Path(agent_yaml_path)
        if not path.exists():
            return []
        with open(path) as f:
            config = yaml.safe_load(f)
        tools = config.get("data", {}).get("tools", []) or []
        return self.register_batch(tools, provider=provider)

    def seed_defaults(self) -> None:
        """Seed all known tool sources. Idempotent."""
        self.seed_from_cli_tools()
        # Resolve agent.yml relative to skill config dir
        config_dir = Path(__file__).resolve().parents[3] / "config"
        agent_yml = config_dir / "agent.yml"
        if agent_yml.exists():
            self.seed_from_agent_yaml(str(agent_yml), provider="manager")

    # --- Internal ---

    @staticmethod
    def _row_to_entry(row) -> ToolEntry:
        return ToolEntry(
            name=row[0], description=row[1], schema_json=row[2],
            provider=row[3], status=row[4], created_at=row[5],
        )
