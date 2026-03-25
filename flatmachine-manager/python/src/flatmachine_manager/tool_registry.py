"""
Tool Registry — SQLite-backed tool catalog with stable aliases.

Design:
- Tool definitions are immutable and identified by tool_id (schema hash based)
- Alias names (e.g. "create_machine") are mutable pointers to a current tool_id
- Existing machines can keep prior embedded schemas; new machines follow current alias

This avoids schema-drift failures when tool schemas evolve over time.
"""

from __future__ import annotations

import hashlib
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
    tool_id: str
    name: str  # alias name used by models/tool-calling
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


def _tool_id(provider: str, name: str, canonical_schema: str) -> str:
    """Deterministic tool id from provider + alias + canonical schema."""
    material = f"{provider}:{name}:{canonical_schema}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class ToolRegistry:
    """SQLite-backed tool catalog with immutable definitions + mutable aliases."""

    def __init__(self, db_path: str = "flatmachine_registry.sqlite"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.executescript(textwrap.dedent("""\
            CREATE TABLE IF NOT EXISTS tool_definitions (
                tool_id      TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                description  TEXT NOT NULL DEFAULT '',
                schema_json  TEXT NOT NULL,
                provider     TEXT NOT NULL DEFAULT '',
                status       TEXT NOT NULL DEFAULT 'active',
                created_at   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tool_aliases (
                alias        TEXT PRIMARY KEY,
                tool_id      TEXT NOT NULL REFERENCES tool_definitions(tool_id),
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tool_defs_provider
                ON tool_definitions(provider);
            CREATE INDEX IF NOT EXISTS idx_tool_defs_status
                ON tool_definitions(status);
        """))
        self._conn.commit()
        self._migrate_legacy_table_if_needed()

    def _migrate_legacy_table_if_needed(self) -> None:
        """Migrate legacy tool_registry(name PK) rows into definitions+aliases once."""
        legacy_exists = self._conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='tool_registry'"
        ).fetchone() is not None
        if not legacy_exists:
            return

        # Already using new layout
        alias_count = self._conn.execute("SELECT count(*) FROM tool_aliases").fetchone()[0]
        if alias_count > 0:
            return

        rows = self._conn.execute(
            "SELECT name, description, schema_json, provider, status, created_at FROM tool_registry"
        ).fetchall()
        if not rows:
            return

        for name, description, schema_json, provider, status, created_at in rows:
            try:
                canonical = _normalize_schema(json.loads(schema_json))
            except Exception:
                # Skip malformed legacy rows
                continue

            tid = _tool_id(provider, name, canonical)
            self._conn.execute(
                """INSERT OR IGNORE INTO tool_definitions
                   (tool_id, name, description, schema_json, provider, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (tid, name, description, schema_json, provider, status, created_at),
            )
            self._conn.execute(
                """INSERT INTO tool_aliases (alias, tool_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(alias) DO UPDATE SET
                     tool_id = excluded.tool_id,
                     updated_at = excluded.updated_at""",
                (name, tid, created_at, created_at),
            )

        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # --- Registration ---

    def register(
        self,
        name: str,
        schema: Dict[str, Any],
        provider: str,
        description: str = "",
    ) -> ToolEntry:
        """Register/update alias to the matching immutable definition.

        Behavior:
        - Same alias + same schema + same provider => no-op
        - Same alias + changed schema (or first time) => create/reuse definition, repoint alias
        - Same alias but different provider => error (prevents ambiguous ownership)
        """
        canonical = _normalize_schema(schema)
        existing = self.get(name)

        if existing is not None:
            if existing.provider != provider:
                raise ValueError(
                    f"Tool alias '{name}' is owned by provider '{existing.provider}', "
                    f"cannot register under provider '{provider}'"
                )
            if _normalize_schema(existing.schema) == canonical:
                return existing  # idempotent

        tid = _tool_id(provider, name, canonical)
        now = _utc_now()
        schema_json = json.dumps(schema)

        self._conn.execute(
            """INSERT OR IGNORE INTO tool_definitions
               (tool_id, name, description, schema_json, provider, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'active', ?)""",
            (tid, name, description, schema_json, provider, now),
        )

        self._conn.execute(
            """INSERT INTO tool_aliases (alias, tool_id, created_at, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(alias) DO UPDATE SET
                 tool_id = excluded.tool_id,
                 updated_at = excluded.updated_at""",
            (name, tid, now, now),
        )

        self._conn.commit()
        entry = self.get(name)
        if entry is None:
            raise RuntimeError(f"Failed to register tool alias '{name}'")
        return entry

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
        """Get the current tool definition for an alias name."""
        row = self._conn.execute(
            """SELECT d.tool_id, a.alias, d.description, d.schema_json, d.provider, d.status, d.created_at
               FROM tool_aliases a
               JOIN tool_definitions d ON d.tool_id = a.tool_id
               WHERE a.alias = ?""",
            (name,),
        ).fetchone()
        return self._row_to_entry(row) if row else None

    def list_tools(
        self,
        *,
        provider: Optional[str] = None,
        include_deprecated: bool = False,
    ) -> List[ToolEntry]:
        """List current alias-bound tools, optionally filtered by provider."""
        conditions = []
        params: list = []

        if not include_deprecated:
            conditions.append("d.status = 'active'")
        if provider is not None:
            conditions.append("d.provider = ?")
            params.append(provider)

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = self._conn.execute(
            f"""SELECT d.tool_id, a.alias, d.description, d.schema_json, d.provider, d.status, d.created_at
                 FROM tool_aliases a
                 JOIN tool_definitions d ON d.tool_id = a.tool_id
                 {where}
                 ORDER BY d.provider, a.alias""",
            params,
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def is_available(self, name: str) -> bool:
        """True only if alias exists and currently points to an active tool."""
        row = self._conn.execute(
            """SELECT d.status
               FROM tool_aliases a
               JOIN tool_definitions d ON d.tool_id = a.tool_id
               WHERE a.alias = ?""",
            (name,),
        ).fetchone()
        return row is not None and row[0] == "active"

    # --- Lifecycle ---

    def deprecate(self, name: str) -> None:
        """Hide current alias-bound tool from new machine creation."""
        entry = self.get(name)
        if entry is None:
            raise ValueError(f"Tool '{name}' not found")
        if entry.status == "deprecated":
            return  # already deprecated
        self._conn.execute(
            "UPDATE tool_definitions SET status = 'deprecated' WHERE tool_id = ?",
            (entry.tool_id,),
        )
        self._conn.commit()

    def undeprecate(self, name: str) -> None:
        """Restore a deprecated alias-bound tool."""
        entry = self.get(name)
        if entry is None:
            raise ValueError(f"Tool '{name}' not found")
        if entry.status == "active":
            return  # already active
        self._conn.execute(
            "UPDATE tool_definitions SET status = 'active' WHERE tool_id = ?",
            (entry.tool_id,),
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
            tool_id=row[0], name=row[1], description=row[2], schema_json=row[3],
            provider=row[4], status=row[5], created_at=row[6],
        )
