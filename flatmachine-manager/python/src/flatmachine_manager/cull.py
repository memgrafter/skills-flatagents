"""
Cull — remove checkpoint bloat from terminated machines.

Direct SQL operations, no LLM. Three modes:

1. Trim: keep only the latest checkpoint per terminated execution (delete intermediates)
2. Purge: delete all checkpoints for terminated executions older than N days
3. Stats: show checkpoint counts and DB size

A terminated execution has event='machine_end' on its latest checkpoint.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def _has_tables(conn: sqlite3.Connection) -> bool:
    """Check if checkpoint tables exist."""
    row = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='machine_checkpoints'"
    ).fetchone()
    return row[0] > 0


def stats(db_path: str) -> str:
    """Show checkpoint statistics."""
    if not os.path.exists(db_path):
        return f"Database not found: {db_path}"

    conn = _connect(db_path)
    try:
        if not _has_tables(conn):
            return f"No checkpoint tables in {db_path}"

        # Total checkpoints
        total = conn.execute("SELECT count(*) FROM machine_checkpoints").fetchone()[0]

        # Distinct executions
        execs = conn.execute("SELECT count(DISTINCT execution_id) FROM machine_checkpoints").fetchone()[0]

        # Terminated executions (latest checkpoint has event='machine_end')
        terminated = conn.execute("""
            SELECT count(*) FROM machine_latest ml
            JOIN machine_checkpoints mc ON mc.checkpoint_key = ml.latest_key
            WHERE mc.event = 'machine_end'
        """).fetchone()[0]

        # Active (not terminated)
        active = execs - terminated

        # Checkpoints in terminated executions
        terminated_checkpoints = conn.execute("""
            SELECT count(*) FROM machine_checkpoints mc
            WHERE mc.execution_id IN (
                SELECT ml.execution_id FROM machine_latest ml
                JOIN machine_checkpoints mc2 ON mc2.checkpoint_key = ml.latest_key
                WHERE mc2.event = 'machine_end'
            )
        """).fetchone()[0]

        # DB file size
        db_size = os.path.getsize(db_path)
        if db_size > 1024 * 1024:
            size_str = f"{db_size / (1024 * 1024):.1f} MB"
        elif db_size > 1024:
            size_str = f"{db_size / 1024:.1f} KB"
        else:
            size_str = f"{db_size} bytes"

        # Config store entries
        config_count = 0
        try:
            config_count = conn.execute("SELECT count(*) FROM machine_configs").fetchone()[0]
        except sqlite3.OperationalError:
            pass

        # Lease entries
        lease_count = 0
        try:
            lease_count = conn.execute("SELECT count(*) FROM execution_leases").fetchone()[0]
        except sqlite3.OperationalError:
            pass

        lines = [
            f"## Checkpoint Stats: {db_path}",
            f"",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Total checkpoints | {total} |",
            f"| Executions | {execs} |",
            f"| Active executions | {active} |",
            f"| Terminated executions | {terminated} |",
            f"| Checkpoints in terminated | {terminated_checkpoints} |",
            f"| Config store entries | {config_count} |",
            f"| Lease entries | {lease_count} |",
            f"| DB file size | {size_str} |",
        ]
        return "\n".join(lines)

    finally:
        conn.close()


def trim(db_path: str, dry_run: bool = False) -> str:
    """Delete intermediate checkpoints for terminated executions.

    Keeps only the latest (machine_end) checkpoint per terminated execution.
    Active executions are never touched.
    """
    if not os.path.exists(db_path):
        return f"Database not found: {db_path}"

    conn = _connect(db_path)
    try:
        if not _has_tables(conn):
            return f"No checkpoint tables in {db_path}"

        # Find terminated execution IDs and their latest keys
        terminated = conn.execute("""
            SELECT ml.execution_id, ml.latest_key
            FROM machine_latest ml
            JOIN machine_checkpoints mc ON mc.checkpoint_key = ml.latest_key
            WHERE mc.event = 'machine_end'
        """).fetchall()

        if not terminated:
            return "No terminated executions to trim."

        total_deleted = 0

        for row in terminated:
            eid = row["execution_id"]
            latest_key = row["latest_key"]

            # Count intermediates
            count = conn.execute("""
                SELECT count(*) FROM machine_checkpoints
                WHERE execution_id = ? AND checkpoint_key != ?
            """, (eid, latest_key)).fetchone()[0]

            if count > 0:
                if not dry_run:
                    conn.execute("""
                        DELETE FROM machine_checkpoints
                        WHERE execution_id = ? AND checkpoint_key != ?
                    """, (eid, latest_key))

                total_deleted += count

        if not dry_run and total_deleted > 0:
            conn.commit()
            conn.execute("PRAGMA optimize")

        action = "Would delete" if dry_run else "Deleted"
        return (
            f"{action} {total_deleted} intermediate checkpoints "
            f"across {len(terminated)} terminated executions."
        )

    finally:
        conn.close()


def purge(
    db_path: str,
    older_than_days: int = 7,
    dry_run: bool = False,
) -> str:
    """Delete all data for terminated executions older than N days.

    Removes checkpoints, latest pointers, leases, and orphaned configs.
    Active executions are never touched.
    """
    if not os.path.exists(db_path):
        return f"Database not found: {db_path}"

    conn = _connect(db_path)
    try:
        if not _has_tables(conn):
            return f"No checkpoint tables in {db_path}"

        cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()

        # Find terminated executions older than cutoff
        old_terminated = conn.execute("""
            SELECT ml.execution_id, ml.latest_key
            FROM machine_latest ml
            JOIN machine_checkpoints mc ON mc.checkpoint_key = ml.latest_key
            WHERE mc.event = 'machine_end'
              AND mc.created_at < ?
        """, (cutoff,)).fetchall()

        if not old_terminated:
            return f"No terminated executions older than {older_than_days} days."

        eids = [r["execution_id"] for r in old_terminated]
        placeholders = ",".join("?" * len(eids))

        # Count what we'll delete
        checkpoint_count = conn.execute(
            f"SELECT count(*) FROM machine_checkpoints WHERE execution_id IN ({placeholders})",
            eids,
        ).fetchone()[0]

        if not dry_run:
            # Delete checkpoints
            conn.execute(
                f"DELETE FROM machine_checkpoints WHERE execution_id IN ({placeholders})",
                eids,
            )

            # Delete latest pointers
            conn.execute(
                f"DELETE FROM machine_latest WHERE execution_id IN ({placeholders})",
                eids,
            )

            # Delete leases
            try:
                conn.execute(
                    f"DELETE FROM execution_leases WHERE execution_id IN ({placeholders})",
                    eids,
                )
            except sqlite3.OperationalError:
                pass  # Table may not exist

            conn.commit()

            # Vacuum orphaned configs (configs not referenced by any remaining checkpoint)
            try:
                conn.execute("""
                    DELETE FROM machine_configs
                    WHERE config_hash NOT IN (
                        SELECT DISTINCT json_extract(snapshot_json, '$.config_hash')
                        FROM machine_checkpoints
                        WHERE json_extract(snapshot_json, '$.config_hash') IS NOT NULL
                    )
                """)
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Table may not exist or json_extract not available

            conn.execute("PRAGMA optimize")

        action = "Would purge" if dry_run else "Purged"
        return (
            f"{action} {len(eids)} terminated executions "
            f"({checkpoint_count} checkpoints) "
            f"older than {older_than_days} days."
        )

    finally:
        conn.close()
