-- FlatMachine Manager registry schema
--
-- This file is intentionally SQL (not a committed .sqlite database)
-- to avoid committing mutable database artifacts.

BEGIN;

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

COMMIT;
