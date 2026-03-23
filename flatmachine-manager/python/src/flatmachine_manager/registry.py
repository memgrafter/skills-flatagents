"""
Machine Registry — SQLite-backed lifecycle management for flatmachines.

Provides versioned storage with embedded refs, validation results,
and full lifecycle metadata. Supersedes the flat ConfigStore for
registry/discovery use cases.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import textwrap
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class MachineRegistryEntry:
    name: str
    namespace: str
    description: str
    status: str
    created_at: str
    updated_at: str
    latest_version: Optional[int] = None


@dataclass
class MachineVersion:
    config_hash: str
    machine_name: str
    version: int
    spec_version: str
    config_raw: str
    config_embedded: Optional[str]
    parent_hash: Optional[str]
    created_at: str
    created_by: str
    description: str
    validation: Optional[str]  # JSON string


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _config_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _resolve_refs(config: Dict[str, Any], base_dir: str) -> Dict[str, Any]:
    """Resolve path-based agent/machine refs to inline configs.

    Reads referenced YAML files and embeds them directly, making the
    config self-contained.
    """
    import copy
    config = copy.deepcopy(config)
    data = config.get("data", {})

    # Resolve agent refs
    agents = data.get("agents", {})
    for name, ref in list(agents.items()):
        if isinstance(ref, str) and not ref.startswith("{"):
            path = Path(base_dir) / ref
            if path.exists():
                with open(path) as f:
                    agents[name] = yaml.safe_load(f)

    # Resolve machine refs
    machines = data.get("machines", {})
    for name, ref in list(machines.items()):
        if isinstance(ref, str) and not ref.startswith("{"):
            path = Path(base_dir) / ref
            if path.exists():
                with open(path) as f:
                    machines[name] = yaml.safe_load(f)

    return config


class MachineRegistry:
    """SQLite-backed registry for flatmachine lifecycle management."""

    def __init__(self, db_path: str = "flatmachine_registry.sqlite"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.executescript(textwrap.dedent("""\
            CREATE TABLE IF NOT EXISTS machine_registry (
                name         TEXT PRIMARY KEY,
                namespace    TEXT DEFAULT '',
                description  TEXT DEFAULT '',
                status       TEXT DEFAULT 'active',
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS machine_versions (
                config_hash      TEXT PRIMARY KEY,
                machine_name     TEXT NOT NULL REFERENCES machine_registry(name),
                version          INTEGER NOT NULL,
                spec_version     TEXT NOT NULL,
                config_raw       TEXT NOT NULL,
                config_embedded  TEXT,
                parent_hash      TEXT,
                created_at       TEXT NOT NULL,
                created_by       TEXT DEFAULT '',
                description      TEXT DEFAULT '',
                validation       TEXT,
                UNIQUE(machine_name, version)
            );

            CREATE INDEX IF NOT EXISTS idx_versions_machine
                ON machine_versions(machine_name, version DESC);
        """))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # --- Registry operations ---

    def register(
        self,
        name: str,
        *,
        namespace: str = "",
        description: str = "",
    ) -> MachineRegistryEntry:
        """Create a machine identity. Idempotent — updates description if exists."""
        now = _utc_now()
        self._conn.execute(
            """INSERT INTO machine_registry (name, namespace, description, status, created_at, updated_at)
               VALUES (?, ?, ?, 'active', ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                 description = excluded.description,
                 updated_at = excluded.updated_at""",
            (name, namespace, description, now, now),
        )
        self._conn.commit()
        return self._get_entry(name)

    def _get_entry(self, name: str) -> Optional[MachineRegistryEntry]:
        row = self._conn.execute(
            "SELECT name, namespace, description, status, created_at, updated_at FROM machine_registry WHERE name = ?",
            (name,),
        ).fetchone()
        if not row:
            return None

        # Get latest version number
        vrow = self._conn.execute(
            "SELECT MAX(version) FROM machine_versions WHERE machine_name = ?",
            (name,),
        ).fetchone()
        latest = vrow[0] if vrow and vrow[0] is not None else None

        return MachineRegistryEntry(
            name=row[0], namespace=row[1], description=row[2],
            status=row[3], created_at=row[4], updated_at=row[5],
            latest_version=latest,
        )

    # --- Version operations ---

    def create_version(
        self,
        name: str,
        config_raw: str,
        *,
        description: str = "",
        created_by: str = "",
        base_dir: str = ".",
        validation_result: Optional[Dict] = None,
    ) -> MachineVersion:
        """Store a new version. Auto-registers machine if needed."""
        # Parse config
        config = yaml.safe_load(config_raw)
        spec_version = config.get("spec_version", "unknown")

        # Auto-register if not exists
        entry = self._get_entry(name)
        if not entry:
            machine_desc = ""
            meta = config.get("metadata", {})
            if isinstance(meta, dict):
                machine_desc = meta.get("description", "")
            self.register(name, description=machine_desc)

        # Compute version number
        row = self._conn.execute(
            "SELECT MAX(version) FROM machine_versions WHERE machine_name = ?",
            (name,),
        ).fetchone()
        version = (row[0] or 0) + 1

        # Get parent hash
        parent_hash = None
        if version > 1:
            prow = self._conn.execute(
                "SELECT config_hash FROM machine_versions WHERE machine_name = ? AND version = ?",
                (name, version - 1),
            ).fetchone()
            if prow:
                parent_hash = prow[0]

        # Resolve refs for embedded config
        embedded_config = _resolve_refs(config, base_dir)
        config_embedded = yaml.dump(embedded_config, default_flow_style=False)

        # Compute hash
        ch = _config_hash(config_raw)

        # Validation JSON
        val_json = json.dumps(validation_result) if validation_result else None

        now = _utc_now()
        self._conn.execute(
            """INSERT INTO machine_versions
               (config_hash, machine_name, version, spec_version, config_raw,
                config_embedded, parent_hash, created_at, created_by, description, validation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ch, name, version, spec_version, config_raw,
             config_embedded, parent_hash, now, created_by, description, val_json),
        )
        self._conn.execute(
            "UPDATE machine_registry SET updated_at = ? WHERE name = ?",
            (now, name),
        )
        self._conn.commit()

        return MachineVersion(
            config_hash=ch, machine_name=name, version=version,
            spec_version=spec_version, config_raw=config_raw,
            config_embedded=config_embedded, parent_hash=parent_hash,
            created_at=now, created_by=created_by,
            description=description, validation=val_json,
        )

    def get_latest(self, name: str) -> Optional[MachineVersion]:
        row = self._conn.execute(
            """SELECT config_hash, machine_name, version, spec_version, config_raw,
                      config_embedded, parent_hash, created_at, created_by, description, validation
               FROM machine_versions WHERE machine_name = ?
               ORDER BY version DESC LIMIT 1""",
            (name,),
        ).fetchone()
        return self._row_to_version(row) if row else None

    def get_version(self, name: str, version: int) -> Optional[MachineVersion]:
        row = self._conn.execute(
            """SELECT config_hash, machine_name, version, spec_version, config_raw,
                      config_embedded, parent_hash, created_at, created_by, description, validation
               FROM machine_versions WHERE machine_name = ? AND version = ?""",
            (name, version),
        ).fetchone()
        return self._row_to_version(row) if row else None

    def get_by_hash(self, config_hash: str) -> Optional[MachineVersion]:
        row = self._conn.execute(
            """SELECT config_hash, machine_name, version, spec_version, config_raw,
                      config_embedded, parent_hash, created_at, created_by, description, validation
               FROM machine_versions WHERE config_hash = ?""",
            (config_hash,),
        ).fetchone()
        return self._row_to_version(row) if row else None

    def list_machines(
        self, *, status: str = "active",
    ) -> List[MachineRegistryEntry]:
        if status == "all":
            rows = self._conn.execute(
                "SELECT name, namespace, description, status, created_at, updated_at FROM machine_registry ORDER BY name"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT name, namespace, description, status, created_at, updated_at FROM machine_registry WHERE status = ? ORDER BY name",
                (status,),
            ).fetchall()

        entries = []
        for row in rows:
            vrow = self._conn.execute(
                "SELECT MAX(version) FROM machine_versions WHERE machine_name = ?",
                (row[0],),
            ).fetchone()
            entries.append(MachineRegistryEntry(
                name=row[0], namespace=row[1], description=row[2],
                status=row[3], created_at=row[4], updated_at=row[5],
                latest_version=vrow[0] if vrow else None,
            ))
        return entries

    def list_versions(self, name: str, *, limit: int = 20) -> List[MachineVersion]:
        rows = self._conn.execute(
            """SELECT config_hash, machine_name, version, spec_version, config_raw,
                      config_embedded, parent_hash, created_at, created_by, description, validation
               FROM machine_versions WHERE machine_name = ?
               ORDER BY version DESC LIMIT ?""",
            (name, limit),
        ).fetchall()
        return [self._row_to_version(r) for r in rows]

    def diff_versions(self, name: str, v1: int, v2: int) -> str:
        ver1 = self.get_version(name, v1)
        ver2 = self.get_version(name, v2)
        if not ver1 or not ver2:
            return f"Version not found: v{v1 if not ver1 else v2}"
        lines1 = ver1.config_raw.splitlines(keepends=True)
        lines2 = ver2.config_raw.splitlines(keepends=True)
        diff = unified_diff(
            lines1, lines2,
            fromfile=f"{name} v{v1}", tofile=f"{name} v{v2}",
        )
        return "".join(diff) or "(no differences)"

    def duplicate(
        self,
        source_name: str,
        target_name: str,
        *,
        source_version: Optional[int] = None,
        description: str = "",
        created_by: str = "",
    ) -> MachineVersion:
        """Duplicate a machine (or specific version) under a new name.

        Copies the config, rewrites data.name, and stores as v1 of target.
        """
        if source_version is not None:
            src = self.get_version(source_name, source_version)
        else:
            src = self.get_latest(source_name)
        if not src:
            raise ValueError(f"Source machine '{source_name}' not found")

        # Rewrite machine name inside config
        config = yaml.safe_load(src.config_raw)
        data = config.get("data", {})
        data["name"] = target_name
        new_raw = yaml.dump(config, default_flow_style=False, sort_keys=False)

        desc = description or f"Duplicated from {source_name} v{src.version}"
        return self.create_version(
            target_name,
            new_raw,
            description=desc,
            created_by=created_by,
            validation_result=json.loads(src.validation) if src.validation else None,
        )

    def deprecate(self, name: str) -> None:
        now = _utc_now()
        self._conn.execute(
            "UPDATE machine_registry SET status = 'deprecated', updated_at = ? WHERE name = ?",
            (now, name),
        )
        self._conn.commit()

    @staticmethod
    def _row_to_version(row) -> MachineVersion:
        return MachineVersion(
            config_hash=row[0], machine_name=row[1], version=row[2],
            spec_version=row[3], config_raw=row[4], config_embedded=row[5],
            parent_hash=row[6], created_at=row[7], created_by=row[8],
            description=row[9], validation=row[10],
        )
