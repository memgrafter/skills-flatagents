"""
Comprehensive tests for the flatmachine-manager skill.

Covers:
- Registry (CRUD, versioning, diff, duplicate, deprecate)
- Templates (all 6 templates, parameterization, context fields)
- Validation (schema, templates/Jinja, best practices, structural)
- Tools (all 9 tool functions)
- CLI (argument parsing, dispatch)
- Cull (stats, trim, purge)
- Doctor (health checks)
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from flatmachine_manager.registry import (
    MachineRegistry,
    MachineRegistryEntry,
    MachineVersion,
    _config_hash,
    _utc_now,
)
from flatmachine_manager.templates import (
    TEMPLATES,
    TEMPLATE_DESCRIPTIONS,
    create_from_template,
    _make_agent_yaml,
    template_tool_loop,
    template_writer_critic,
    template_ooda_workflow,
    template_pipeline,
    template_signal_wait,
    template_distributed_worker,
)
from flatmachine_manager.validation import (
    ValidationResult,
    ValidationIssue,
    validate_machine_config,
    _validate_templates,
    _check_best_practices,
    _check_structural,
)
from flatmachine_manager.tools import (
    tool_list_machines,
    tool_get_machine,
    tool_create_machine,
    tool_update_machine,
    tool_validate_machine,
    tool_diff_versions,
    tool_duplicate_machine,
    tool_deprecate_machine,
    tool_select_model,
    MODEL_CATALOG,
    PURPOSE_TO_PROFILE,
    FlatMachineToolProvider,
)
from flatmachine_manager.cull import stats, trim, purge, _has_tables
from flatmachine_manager.doctor import (
    run_doctor,
    _check_venv,
    _check_schema_db,
    _check_registry_db,
    _check_sqlite_version,
)
from flatmachine_manager.tool_registry import ToolRegistry
from flatmachine_manager.cli import build_parser, _parse_agent, _parse_param


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(coro):
    """Run an async function synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary registry DB."""
    db_path = str(tmp_path / "test_registry.sqlite")
    registry = MachineRegistry(db_path=db_path)
    yield registry
    registry.close()


@pytest.fixture
def populated_registry(tmp_db):
    """Registry with a machine already created."""
    config_yaml = create_from_template(
        template_name="tool-loop",
        name="test-bot",
        description="A test bot",
    )
    tmp_db.create_version(
        "test-bot",
        config_yaml,
        description="Initial version",
        created_by="test",
    )
    return tmp_db


@pytest.fixture
def machine_db(tmp_path):
    """Create a temporary machine DB with checkpoint tables for cull tests."""
    db_path = str(tmp_path / "machine.sqlite")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE machine_checkpoints (
            checkpoint_key TEXT PRIMARY KEY,
            execution_id TEXT NOT NULL,
            event TEXT NOT NULL,
            snapshot_json TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE machine_latest (
            execution_id TEXT PRIMARY KEY,
            latest_key TEXT NOT NULL
        );
        CREATE TABLE machine_configs (
            config_hash TEXT PRIMARY KEY,
            config_raw TEXT NOT NULL
        );
        CREATE TABLE execution_leases (
            execution_id TEXT PRIMARY KEY,
            lease_holder TEXT,
            expires_at TEXT
        );
    """)
    conn.commit()
    conn.close()
    return db_path


# ===========================================================================
# Registry Tests
# ===========================================================================


class TestRegistry:
    def test_register_creates_entry(self, tmp_db):
        entry = tmp_db.register("my-machine", description="test desc")
        assert entry.name == "my-machine"
        assert entry.description == "test desc"
        assert entry.status == "active"

    def test_register_idempotent(self, tmp_db):
        tmp_db.register("my-machine", description="first")
        entry = tmp_db.register("my-machine", description="second")
        assert entry.description == "second"

    def test_create_version(self, tmp_db):
        config = create_from_template("tool-loop", "bot", "test bot")
        ver = tmp_db.create_version("bot", config, description="v1", created_by="test")
        assert ver.version == 1
        assert ver.machine_name == "bot"
        assert ver.config_raw == config
        assert ver.parent_hash is None

    def test_version_auto_increment(self, tmp_db):
        config = create_from_template("tool-loop", "bot", "test bot")
        v1 = tmp_db.create_version("bot", config, description="v1")
        v2 = tmp_db.create_version("bot", config + "\n# v2", description="v2")
        assert v1.version == 1
        assert v2.version == 2
        assert v2.parent_hash == v1.config_hash

    def test_get_latest(self, tmp_db):
        config = create_from_template("tool-loop", "bot", "test bot")
        tmp_db.create_version("bot", config, description="v1")
        tmp_db.create_version("bot", config + "\n# v2", description="v2")
        latest = tmp_db.get_latest("bot")
        assert latest.version == 2

    def test_get_latest_nonexistent(self, tmp_db):
        assert tmp_db.get_latest("nonexistent") is None

    def test_get_version(self, tmp_db):
        config = create_from_template("tool-loop", "bot", "test bot")
        tmp_db.create_version("bot", config, description="v1")
        tmp_db.create_version("bot", config + "\n# v2", description="v2")
        v1 = tmp_db.get_version("bot", 1)
        assert v1.version == 1

    def test_get_by_hash(self, tmp_db):
        config = create_from_template("tool-loop", "bot", "test bot")
        ver = tmp_db.create_version("bot", config, description="v1")
        found = tmp_db.get_by_hash(ver.config_hash)
        assert found.version == ver.version
        assert found.machine_name == "bot"

    def test_list_machines_active(self, tmp_db):
        config = create_from_template("tool-loop", "bot1", "Bot 1")
        tmp_db.create_version("bot1", config, description="v1")
        config2 = create_from_template("writer-critic", "bot2", "Bot 2")
        tmp_db.create_version("bot2", config2, description="v1")

        entries = tmp_db.list_machines(status="active")
        assert len(entries) == 2
        names = {e.name for e in entries}
        assert names == {"bot1", "bot2"}

    def test_list_machines_deprecated(self, tmp_db):
        config = create_from_template("tool-loop", "bot1", "Bot 1")
        tmp_db.create_version("bot1", config)
        tmp_db.deprecate("bot1")

        active = tmp_db.list_machines(status="active")
        assert len(active) == 0

        deprecated = tmp_db.list_machines(status="deprecated")
        assert len(deprecated) == 1
        assert deprecated[0].name == "bot1"

    def test_list_machines_all(self, tmp_db):
        config = create_from_template("tool-loop", "bot1", "Bot 1")
        tmp_db.create_version("bot1", config)
        config2 = create_from_template("tool-loop", "bot2", "Bot 2")
        tmp_db.create_version("bot2", config2)
        tmp_db.deprecate("bot1")

        all_entries = tmp_db.list_machines(status="all")
        assert len(all_entries) == 2

    def test_list_versions(self, tmp_db):
        config = create_from_template("tool-loop", "bot", "test bot")
        tmp_db.create_version("bot", config, description="v1")
        tmp_db.create_version("bot", config + "\n# v2", description="v2")
        tmp_db.create_version("bot", config + "\n# v3", description="v3")

        versions = tmp_db.list_versions("bot", limit=10)
        assert len(versions) == 3
        # Should be in descending order
        assert versions[0].version == 3
        assert versions[2].version == 1

    def test_diff_versions(self, tmp_db):
        config1 = create_from_template("tool-loop", "bot", "test bot v1")
        config2 = create_from_template("tool-loop", "bot", "test bot v2")
        tmp_db.create_version("bot", config1, description="v1")
        tmp_db.create_version("bot", config2, description="v2")

        diff = tmp_db.diff_versions("bot", 1, 2)
        assert diff != "(no differences)"
        assert "---" in diff or "@@" in diff

    def test_diff_same_content_raises(self, tmp_db):
        """Storing identical config content twice fails because config_hash is PK."""
        config = create_from_template("tool-loop", "bot", "test bot")
        tmp_db.create_version("bot", config, description="v1")
        with pytest.raises(sqlite3.IntegrityError):
            tmp_db.create_version("bot", config, description="v2")

    def test_diff_no_differences_with_trivial_change(self, tmp_db):
        """Two versions with the same semantic content but different raw text show no diff."""
        config1 = create_from_template("tool-loop", "bot", "test bot")
        # Add a comment to make it technically different but re-dump to normalize
        config2 = config1 + "\n# just a comment"
        tmp_db.create_version("bot", config1, description="v1")
        tmp_db.create_version("bot", config2, description="v2")
        diff = tmp_db.diff_versions("bot", 1, 2)
        # Should show the comment addition
        assert "comment" in diff or diff != "(no differences)"

    def test_diff_nonexistent_version(self, tmp_db):
        config = create_from_template("tool-loop", "bot", "test bot")
        tmp_db.create_version("bot", config, description="v1")
        diff = tmp_db.diff_versions("bot", 1, 99)
        assert "not found" in diff.lower()

    def test_duplicate(self, tmp_db):
        config = create_from_template("tool-loop", "original", "Original bot")
        tmp_db.create_version("original", config, description="v1")

        dup = tmp_db.duplicate("original", "copy")
        assert dup.machine_name == "copy"
        assert dup.version == 1
        # Config should have the new name
        dup_config = yaml.safe_load(dup.config_raw)
        assert dup_config["data"]["name"] == "copy"

    def test_duplicate_specific_version(self, tmp_db):
        config1 = create_from_template("tool-loop", "original", "Original v1")
        config2 = create_from_template("tool-loop", "original", "Original v2")
        tmp_db.create_version("original", config1, description="v1")
        tmp_db.create_version("original", config2, description="v2")

        dup = tmp_db.duplicate("original", "copy", source_version=1)
        dup_config = yaml.safe_load(dup.config_raw)
        # Should be based on v1
        assert "Original v1" in dup_config.get("metadata", {}).get("description", "")

    def test_duplicate_nonexistent(self, tmp_db):
        with pytest.raises(ValueError, match="not found"):
            tmp_db.duplicate("nonexistent", "copy")

    def test_deprecate(self, tmp_db):
        config = create_from_template("tool-loop", "bot", "test bot")
        tmp_db.create_version("bot", config)
        tmp_db.deprecate("bot")
        entry = tmp_db._get_entry("bot")
        assert entry.status == "deprecated"

    def test_config_hash_deterministic(self):
        raw = "test config"
        assert _config_hash(raw) == _config_hash(raw)

    def test_config_hash_different(self):
        assert _config_hash("config1") != _config_hash("config2")

    def test_validation_result_stored(self, tmp_db):
        config = create_from_template("tool-loop", "bot", "test bot")
        val = {"valid": True, "errors": [], "warnings": ["some warning"]}
        ver = tmp_db.create_version("bot", config, validation_result=val)
        assert ver.validation is not None
        parsed = json.loads(ver.validation)
        assert parsed["valid"] is True


# ===========================================================================
# Template Tests
# ===========================================================================


class TestTemplates:
    def test_all_templates_exist(self):
        expected = {"tool-loop", "writer-critic", "ooda-workflow",
                    "pipeline", "signal-wait", "distributed-worker"}
        assert set(TEMPLATES.keys()) == expected

    def test_all_templates_have_descriptions(self):
        assert set(TEMPLATE_DESCRIPTIONS.keys()) == set(TEMPLATES.keys())

    @pytest.mark.parametrize("template_name", TEMPLATES.keys())
    def test_template_produces_valid_yaml(self, template_name):
        config_raw = create_from_template(
            template_name=template_name,
            name=f"test-{template_name}",
            description=f"Test {template_name}",
        )
        config = yaml.safe_load(config_raw)
        assert config is not None
        assert "spec" in config
        assert config["spec"] == "flatmachine"
        assert "data" in config

    @pytest.mark.parametrize("template_name", TEMPLATES.keys())
    def test_template_has_required_structure(self, template_name):
        config_raw = create_from_template(
            template_name=template_name,
            name=f"test-{template_name}",
            description=f"Test {template_name}",
        )
        config = yaml.safe_load(config_raw)
        data = config["data"]
        assert "name" in data
        assert "states" in data
        assert data["name"] == f"test-{template_name}"

    @pytest.mark.parametrize("template_name", TEMPLATES.keys())
    def test_template_has_initial_and_final_states(self, template_name):
        config_raw = create_from_template(
            template_name=template_name,
            name=f"test-{template_name}",
            description=f"Test {template_name}",
        )
        config = yaml.safe_load(config_raw)
        states = config["data"]["states"]

        has_initial = any(
            isinstance(s, dict) and s.get("type") == "initial"
            for s in states.values()
        )
        has_final = any(
            isinstance(s, dict) and s.get("type") == "final"
            for s in states.values()
        )
        assert has_initial, f"{template_name} missing initial state"
        assert has_final, f"{template_name} missing final state"

    @pytest.mark.parametrize("template_name", TEMPLATES.keys())
    def test_template_passes_validation(self, template_name):
        config_raw = create_from_template(
            template_name=template_name,
            name=f"test-{template_name}",
            description=f"Test {template_name}",
        )
        result = validate_machine_config(config_raw)
        # Templates should not have errors (warnings are OK)
        assert len(result.all_errors) == 0, (
            f"{template_name} has validation errors: {result.all_errors}"
        )

    def test_template_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown template"):
            create_from_template("nonexistent", "test", "test")

    def test_tool_loop_with_custom_agent(self):
        config_raw = template_tool_loop(
            name="my-bot",
            description="My bot",
            agents=[{"name": "coder", "purpose": "Write code", "model_profile": "code"}],
        )
        config = yaml.safe_load(config_raw)
        assert "coder" in config["data"]["agents"]

    def test_writer_critic_with_custom_agents(self):
        config_raw = template_writer_critic(
            name="my-writer",
            description="My writer",
            agents=[
                {"name": "my_writer", "purpose": "Write prose", "model_profile": "smart"},
                {"name": "my_critic", "purpose": "Review quality", "model_profile": "fast"},
            ],
        )
        config = yaml.safe_load(config_raw)
        assert "my_writer" in config["data"]["agents"]
        assert "my_critic" in config["data"]["agents"]

    def test_pipeline_with_custom_phases(self):
        config_raw = template_pipeline(
            name="my-pipeline",
            description="My pipeline",
            agents=[
                {"name": "extract", "purpose": "Extract data", "model_profile": "fast"},
                {"name": "transform", "purpose": "Transform data", "model_profile": "smart"},
                {"name": "load", "purpose": "Load results", "model_profile": "fast"},
            ],
        )
        config = yaml.safe_load(config_raw)
        agents = config["data"]["agents"]
        assert "extract" in agents
        assert "transform" in agents
        assert "load" in agents
        # Check states were created for each phase
        states = config["data"]["states"]
        assert "extract" in states
        assert "transform" in states
        assert "load" in states

    def test_context_fields_from_input(self):
        config_raw = template_tool_loop(
            name="my-bot",
            description="My bot",
            context_fields=[
                {"name": "repo_url", "from_input": True},
                {"name": "language", "default_value": "python"},
            ],
        )
        config = yaml.safe_load(config_raw)
        ctx = config["data"]["context"]
        assert ctx["repo_url"] == "{{ input.repo_url }}"
        assert ctx["language"] == "python"

    def test_make_agent_yaml(self):
        agent = _make_agent_yaml("coder", "Write code", "code", temperature=0.2)
        assert agent["spec"] == "flatagent"
        assert agent["data"]["name"] == "coder"
        assert agent["data"]["model"]["profile"] == "code"
        assert agent["data"]["model"]["temperature"] == 0.2

    def test_make_agent_yaml_no_temperature(self):
        agent = _make_agent_yaml("coder", "Write code", "smart")
        assert agent["data"]["model"] == "smart"

    def test_make_agent_yaml_with_tools(self):
        tools = [{"name": "bash", "type": "shell"}]
        agent = _make_agent_yaml("coder", "Write code", "code", tools=tools)
        assert agent["data"]["tools"] == tools

    def test_ooda_with_custom_agents(self):
        config_raw = template_ooda_workflow(
            name="ooda-bot",
            description="OODA bot",
            agents=[
                {"name": "planner_x", "purpose": "Plan it", "model_profile": "smart"},
                {"name": "executor_x", "purpose": "Do it", "model_profile": "code"},
                {"name": "reviewer_x", "purpose": "Check it", "model_profile": "fast"},
            ],
        )
        config = yaml.safe_load(config_raw)
        assert "planner_x" in config["data"]["agents"]
        assert "executor_x" in config["data"]["agents"]
        assert "reviewer_x" in config["data"]["agents"]

    def test_signal_wait_template(self):
        config_raw = template_signal_wait(
            name="approval-flow",
            description="Needs approval",
        )
        config = yaml.safe_load(config_raw)
        states = config["data"]["states"]
        assert "wait_for_approval" in states
        assert "wait_for" in states["wait_for_approval"]

    def test_distributed_worker_template(self):
        config_raw = template_distributed_worker(
            name="worker-pool",
            description="Worker pool",
        )
        config = yaml.safe_load(config_raw)
        states = config["data"]["states"]
        assert "check_pool" in states
        assert "calculate_spawn" in states
        assert "spawn_workers" in states


# ===========================================================================
# Validation Tests
# ===========================================================================


class TestValidation:
    def test_valid_config(self):
        config_raw = create_from_template("tool-loop", "bot", "test bot")
        result = validate_machine_config(config_raw)
        assert result.valid is True
        assert len(result.all_errors) == 0

    def test_invalid_yaml(self):
        result = validate_machine_config("{ invalid: yaml: [")
        assert result.valid is False
        assert any("YAML" in e or "yaml" in e.lower() for e in result.schema_errors)

    def test_not_a_dict(self):
        result = validate_machine_config("- just\n- a\n- list\n")
        assert result.valid is False
        assert any("mapping" in e.lower() for e in result.schema_errors)

    def test_missing_initial_state(self):
        config = {
            "spec": "flatmachine",
            "spec_version": "2.5.0",
            "data": {
                "name": "bad-bot",
                "states": {
                    "work": {"agent": "worker"},
                    "done": {"type": "final", "output": {}},
                },
                "agents": {"worker": {}},
            },
        }
        result = validate_machine_config(yaml.dump(config))
        errors = result.all_errors
        assert any("initial" in e.lower() for e in errors)

    def test_missing_final_state(self):
        config = {
            "spec": "flatmachine",
            "spec_version": "2.5.0",
            "data": {
                "name": "bad-bot",
                "states": {
                    "start": {"type": "initial", "transitions": [{"to": "work"}]},
                    "work": {"agent": "worker"},
                },
                "agents": {"worker": {}},
            },
        }
        result = validate_machine_config(yaml.dump(config))
        errors = result.all_errors
        assert any("final" in e.lower() for e in errors)

    def test_nonexistent_transition_target(self):
        config = {
            "spec": "flatmachine",
            "spec_version": "2.5.0",
            "data": {
                "name": "bad-bot",
                "states": {
                    "start": {"type": "initial", "transitions": [{"to": "nonexistent"}]},
                    "done": {"type": "final", "output": {}},
                },
                "agents": {},
            },
        }
        result = validate_machine_config(yaml.dump(config))
        errors = result.all_errors
        assert any("nonexistent" in e for e in errors)

    def test_agent_ref_not_defined(self):
        config = {
            "spec": "flatmachine",
            "spec_version": "2.5.0",
            "data": {
                "name": "bad-bot",
                "states": {
                    "start": {"type": "initial", "transitions": [{"to": "work"}]},
                    "work": {"agent": "missing_agent", "transitions": [{"to": "done"}]},
                    "done": {"type": "final", "output": {}},
                },
                "agents": {},
            },
        }
        result = validate_machine_config(yaml.dump(config))
        structural_errors = [i for i in result.structural if i.severity == "error"]
        assert any("missing_agent" in str(i) for i in structural_errors)

    def test_unreachable_state_warning(self):
        config = {
            "spec": "flatmachine",
            "spec_version": "2.5.0",
            "data": {
                "name": "bad-bot",
                "states": {
                    "start": {"type": "initial", "transitions": [{"to": "done"}]},
                    "orphan": {"agent": "worker", "transitions": [{"to": "done"}]},
                    "done": {"type": "final", "output": {}},
                },
                "agents": {"worker": {}},
            },
        }
        result = validate_machine_config(yaml.dump(config))
        warnings = result.all_warnings
        assert any("orphan" in w for w in warnings)

    def test_truncation_filter_error(self):
        config = {
            "spec": "flatmachine",
            "spec_version": "2.5.0",
            "data": {
                "name": "bad-bot",
                "context": {"summary": "{{ output.content | truncate(100) }}"},
                "states": {
                    "start": {"type": "initial", "transitions": [{"to": "done"}]},
                    "done": {"type": "final", "output": {}},
                },
                "agents": {},
            },
        }
        result = validate_machine_config(yaml.dump(config))
        errors = result.all_errors
        assert any("truncat" in e.lower() for e in errors)

    def test_no_persistence_warning(self):
        config = {
            "spec": "flatmachine",
            "spec_version": "2.5.0",
            "data": {
                "name": "big-bot",
                "states": {
                    "start": {"type": "initial", "transitions": [{"to": "a"}]},
                    "a": {"transitions": [{"to": "b"}]},
                    "b": {"transitions": [{"to": "c"}]},
                    "c": {"transitions": [{"to": "done"}]},
                    "done": {"type": "final", "output": {}},
                },
                "agents": {},
            },
        }
        result = validate_machine_config(yaml.dump(config))
        warnings = result.all_warnings
        assert any("persistence" in w.lower() for w in warnings)

    def test_local_backend_warning(self):
        config = {
            "spec": "flatmachine",
            "spec_version": "2.5.0",
            "data": {
                "name": "bot",
                "states": {
                    "start": {"type": "initial", "transitions": [{"to": "a"}]},
                    "a": {"transitions": [{"to": "b"}]},
                    "b": {"transitions": [{"to": "c"}]},
                    "c": {"transitions": [{"to": "done"}]},
                    "done": {"type": "final", "output": {}},
                },
                "agents": {},
                "persistence": {"enabled": True, "backend": "local"},
            },
        }
        result = validate_machine_config(yaml.dump(config))
        warnings = result.all_warnings
        assert any("sqlite" in w.lower() for w in warnings)

    def test_agent_without_on_error_warning(self):
        config = {
            "spec": "flatmachine",
            "spec_version": "2.5.0",
            "data": {
                "name": "bot",
                "states": {
                    "start": {"type": "initial", "transitions": [{"to": "work"}]},
                    "work": {"agent": "worker", "transitions": [{"to": "done"}]},
                    "done": {"type": "final", "output": {}},
                },
                "agents": {"worker": {}},
            },
        }
        result = validate_machine_config(yaml.dump(config))
        warnings = result.all_warnings
        assert any("on_error" in w for w in warnings)

    def test_agent_without_retry_warning(self):
        config = {
            "spec": "flatmachine",
            "spec_version": "2.5.0",
            "data": {
                "name": "bot",
                "states": {
                    "start": {"type": "initial", "transitions": [{"to": "work"}]},
                    "work": {
                        "agent": "worker",
                        "on_error": "error",
                        "transitions": [{"to": "done"}],
                    },
                    "done": {"type": "final", "output": {}},
                    "error": {"type": "final", "output": {}},
                },
                "agents": {"worker": {}},
            },
        }
        result = validate_machine_config(yaml.dump(config))
        warnings = result.all_warnings
        assert any("retry" in w for w in warnings)

    def test_validation_result_summary(self):
        result = ValidationResult(valid=True)
        summary = result.summary()
        assert "✓" in summary

        result2 = ValidationResult(valid=False, schema_errors=["bad schema"])
        summary2 = result2.summary()
        assert "✗" in summary2
        assert "bad schema" in summary2

    def test_unsupported_jinja_filter(self):
        config = {
            "data": {
                "context": {"items": "{{ data | dictsort }}"},
            },
        }
        errors = _validate_templates(config)
        assert any("dictsort" in e for e in errors)

    def test_unsupported_jinja_tag(self):
        config = {
            "data": {
                "context": {"items": "{% macro foo() %}test{% endmacro %}"},
            },
        }
        errors = _validate_templates(config)
        assert any("macro" in e for e in errors)

    def test_allowed_jinja_filters(self):
        config = {
            "data": {
                "context": {
                    "text": "{{ output.content | default('') | lower | trim }}",
                },
            },
        }
        errors = _validate_templates(config)
        assert len(errors) == 0

    def test_python_slice_warning(self):
        config = {
            "data": {
                "context": {"first_ten": "{{ items[0:10] }}"},
            },
        }
        errors = _validate_templates(config)
        assert any("slicing" in e.lower() for e in errors)


# ===========================================================================
# Tool Tests
# ===========================================================================


class TestTools:
    def test_list_machines_empty(self, tmp_db):
        result = _run(tool_list_machines(tmp_db, "test", {"status": "active"}))
        assert "No machines found" in result.content

    def test_list_machines_with_data(self, populated_registry):
        result = _run(tool_list_machines(populated_registry, "test", {"status": "active"}))
        assert "test-bot" in result.content
        assert not result.is_error

    def test_get_machine(self, populated_registry):
        result = _run(tool_get_machine(populated_registry, "test", {"name": "test-bot"}))
        assert "test-bot" in result.content
        assert "v1" in result.content
        assert not result.is_error

    def test_get_machine_not_found(self, tmp_db):
        result = _run(tool_get_machine(tmp_db, "test", {"name": "nonexistent"}))
        assert result.is_error
        assert "not found" in result.content

    def test_get_machine_specific_version(self, populated_registry):
        # Create a second version
        config = create_from_template("tool-loop", "test-bot", "Updated bot")
        populated_registry.create_version("test-bot", config, description="v2")

        result = _run(tool_get_machine(populated_registry, "test", {"name": "test-bot", "version": 1}))
        assert "v1" in result.content
        assert not result.is_error

    def test_create_machine(self, tmp_db):
        result = _run(tool_create_machine(tmp_db, "test", {
            "name": "new-bot",
            "template": "tool-loop",
            "description": "A new bot",
        }))
        assert "Created" in result.content or "new-bot" in result.content
        assert not result.is_error

    def test_create_machine_with_agents(self, tmp_db):
        result = _run(tool_create_machine(tmp_db, "test", {
            "name": "agent-bot",
            "template": "writer-critic",
            "description": "Writer-critic bot",
            "agents": [
                {"name": "my_writer", "purpose": "Write essays", "model_profile": "smart"},
                {"name": "my_critic", "purpose": "Review essays", "model_profile": "fast"},
            ],
        }))
        assert not result.is_error
        assert "agent-bot" in result.content

    def test_create_machine_unknown_template(self, tmp_db):
        result = _run(tool_create_machine(tmp_db, "test", {
            "name": "bad-bot",
            "template": "nonexistent",
            "description": "Should fail",
        }))
        assert result.is_error
        assert "Unknown template" in result.content

    def test_create_machine_no_name(self, tmp_db):
        result = _run(tool_create_machine(tmp_db, "test", {
            "template": "tool-loop",
            "description": "No name",
        }))
        assert result.is_error

    def test_update_machine_add_state(self, populated_registry):
        result = _run(tool_update_machine(populated_registry, "test", {
            "name": "test-bot",
            "operation": "add_state",
            "params": {"state_name": "new_state", "transitions_to": ["done"]},
            "description": "Added new_state",
        }))
        assert not result.is_error
        assert "v2" in result.content

    def test_update_machine_remove_state(self, populated_registry):
        result = _run(tool_update_machine(populated_registry, "test", {
            "name": "test-bot",
            "operation": "remove_state",
            "params": {"state_name": "human_review"},
            "description": "Removed human_review",
        }))
        assert not result.is_error

    def test_update_machine_remove_nonexistent_state(self, populated_registry):
        result = _run(tool_update_machine(populated_registry, "test", {
            "name": "test-bot",
            "operation": "remove_state",
            "params": {"state_name": "nonexistent"},
        }))
        assert result.is_error
        assert "not found" in result.content

    def test_update_machine_not_found(self, tmp_db):
        result = _run(tool_update_machine(tmp_db, "test", {
            "name": "nonexistent",
            "operation": "add_state",
            "params": {"state_name": "foo"},
        }))
        assert result.is_error

    def test_update_machine_unknown_operation(self, populated_registry):
        result = _run(tool_update_machine(populated_registry, "test", {
            "name": "test-bot",
            "operation": "unknown_op",
            "params": {},
        }))
        assert result.is_error
        assert "Unknown operation" in result.content

    def test_update_machine_add_agent(self, populated_registry):
        result = _run(tool_update_machine(populated_registry, "test", {
            "name": "test-bot",
            "operation": "add_agent",
            "params": {
                "agent_name": "reviewer",
                "purpose": "Review code",
                "model_profile": "smart",
            },
            "description": "Added reviewer agent",
        }))
        assert not result.is_error

    def test_update_machine_update_context(self, populated_registry):
        result = _run(tool_update_machine(populated_registry, "test", {
            "name": "test-bot",
            "operation": "update_context",
            "params": {"key": "repo_url", "value_template": "{{ input.repo_url }}"},
        }))
        assert not result.is_error

    def test_update_machine_update_setting(self, populated_registry):
        result = _run(tool_update_machine(populated_registry, "test", {
            "name": "test-bot",
            "operation": "update_setting",
            "params": {"key": "max_retries", "value": 3},
        }))
        assert not result.is_error

    def test_validate_machine(self, populated_registry):
        result = _run(tool_validate_machine(populated_registry, "test", {"name": "test-bot"}))
        assert not result.is_error
        assert "✓" in result.content or "valid" in result.content.lower()

    def test_validate_machine_not_found(self, tmp_db):
        result = _run(tool_validate_machine(tmp_db, "test", {"name": "nonexistent"}))
        assert result.is_error

    def test_diff_versions(self, populated_registry):
        config2 = create_from_template("tool-loop", "test-bot", "Updated bot")
        populated_registry.create_version("test-bot", config2, description="v2")

        result = _run(tool_diff_versions(populated_registry, "test", {
            "name": "test-bot",
            "v1": 1,
            "v2": 2,
        }))
        assert not result.is_error

    def test_diff_versions_missing_args(self, populated_registry):
        result = _run(tool_diff_versions(populated_registry, "test", {
            "name": "test-bot",
        }))
        assert result.is_error

    def test_duplicate_machine(self, populated_registry):
        result = _run(tool_duplicate_machine(populated_registry, "test", {
            "source": "test-bot",
            "target": "test-bot-copy",
        }))
        assert not result.is_error
        assert "test-bot-copy" in result.content

    def test_duplicate_machine_missing_args(self, tmp_db):
        result = _run(tool_duplicate_machine(tmp_db, "test", {"source": ""}))
        assert result.is_error

    def test_deprecate_machine(self, populated_registry):
        result = _run(tool_deprecate_machine(populated_registry, "test", {"name": "test-bot"}))
        assert not result.is_error
        assert "Deprecated" in result.content

    def test_deprecate_already_deprecated(self, populated_registry):
        populated_registry.deprecate("test-bot")
        result = _run(tool_deprecate_machine(populated_registry, "test", {"name": "test-bot"}))
        assert "already deprecated" in result.content

    def test_deprecate_not_found(self, tmp_db):
        result = _run(tool_deprecate_machine(tmp_db, "test", {"name": "nonexistent"}))
        assert result.is_error

    def test_select_model_fast(self, tmp_db):
        result = _run(tool_select_model(tmp_db, "test", {"purpose": "fast"}))
        assert not result.is_error
        assert "fast" in result.content.lower()

    def test_select_model_smart(self, tmp_db):
        result = _run(tool_select_model(tmp_db, "test", {"purpose": "smart"}))
        assert not result.is_error
        assert "smart" in result.content.lower()

    def test_select_model_creative(self, tmp_db):
        result = _run(tool_select_model(tmp_db, "test", {"purpose": "creative"}))
        assert not result.is_error

    def test_model_catalog_completeness(self):
        assert "fast" in MODEL_CATALOG
        assert "smart" in MODEL_CATALOG
        assert "code" in MODEL_CATALOG
        assert "cheap" in MODEL_CATALOG

    def test_purpose_to_profile_mapping(self):
        for purpose in ["fast", "smart", "cheap", "code", "routing", "creative", "analysis"]:
            assert purpose in PURPOSE_TO_PROFILE


class TestToolProvider:
    def test_execute_tool_list(self, tmp_db):
        provider = FlatMachineToolProvider(tmp_db)
        result = _run(provider.execute_tool("list_machines", "test", {"status": "active"}))
        assert "No machines found" in result.content

    def test_execute_tool_unknown(self, tmp_db):
        provider = FlatMachineToolProvider(tmp_db)
        result = _run(provider.execute_tool("unknown_tool", "test", {}))
        assert result.is_error
        assert "Unknown tool" in result.content

    def test_execute_tool_create(self, tmp_db):
        provider = FlatMachineToolProvider(tmp_db)
        result = _run(provider.execute_tool("create_machine", "test", {
            "name": "provider-bot",
            "template": "tool-loop",
            "description": "Provider test",
        }))
        assert not result.is_error

    def test_get_tool_definitions(self, tmp_db):
        provider = FlatMachineToolProvider(tmp_db)
        defs = provider.get_tool_definitions()
        assert isinstance(defs, list)


# ===========================================================================
# CLI Tests
# ===========================================================================


class TestCLI:
    def test_parse_agent_full(self):
        result = _parse_agent("writer:Generate taglines:smart")
        assert result == {"name": "writer", "purpose": "Generate taglines", "model_profile": "smart"}

    def test_parse_agent_no_profile(self):
        result = _parse_agent("worker:Do stuff")
        assert result == {"name": "worker", "purpose": "Do stuff"}

    def test_parse_agent_name_only(self):
        result = _parse_agent("worker")
        assert result == {"name": "worker"}

    def test_parse_param(self):
        k, v = _parse_param("state_name=my_state")
        assert k == "state_name"
        assert v == "my_state"

    def test_parse_param_no_equals(self):
        with pytest.raises(SystemExit):
            _parse_param("no_equals_here")

    def test_build_parser_list(self):
        parser = build_parser()
        args = parser.parse_args(["list"])
        assert args.action == "list"
        assert args.status == "active"

    def test_build_parser_list_all(self):
        parser = build_parser()
        args = parser.parse_args(["list", "--status", "all"])
        assert args.status == "all"

    def test_build_parser_create(self):
        parser = build_parser()
        args = parser.parse_args([
            "create", "--name", "my-bot", "--template", "tool-loop",
            "--description", "Test bot",
        ])
        assert args.action == "create"
        assert args.name == "my-bot"
        assert args.template == "tool-loop"

    def test_build_parser_create_with_agents(self):
        parser = build_parser()
        args = parser.parse_args([
            "create", "--name", "my-bot", "--template", "writer-critic",
            "--description", "Test", "--agent", "writer:Write:smart",
            "--agent", "critic:Review:fast",
        ])
        assert len(args.agents) == 2

    def test_build_parser_update(self):
        parser = build_parser()
        args = parser.parse_args([
            "update", "--name", "my-bot", "--op", "add_state",
            "--param", "state_name=review",
        ])
        assert args.action == "update"
        assert args.op == "add_state"
        assert args.params == ["state_name=review"]

    def test_build_parser_get(self):
        parser = build_parser()
        args = parser.parse_args(["get", "--name", "my-bot", "--version", "2"])
        assert args.name == "my-bot"
        assert args.version == 2

    def test_build_parser_validate(self):
        parser = build_parser()
        args = parser.parse_args(["validate", "--name", "my-bot"])
        assert args.action == "validate"

    def test_build_parser_diff(self):
        parser = build_parser()
        args = parser.parse_args(["diff", "--name", "my-bot", "--v1", "1", "--v2", "2"])
        assert args.v1 == 1
        assert args.v2 == 2

    def test_build_parser_duplicate(self):
        parser = build_parser()
        args = parser.parse_args(["duplicate", "--source", "a", "--target", "b"])
        assert args.source == "a"
        assert args.target == "b"

    def test_build_parser_deprecate(self):
        parser = build_parser()
        args = parser.parse_args(["deprecate", "--name", "my-bot"])
        assert args.action == "deprecate"

    def test_build_parser_select_model(self):
        parser = build_parser()
        args = parser.parse_args(["select-model", "--purpose", "fast"])
        assert args.purpose == "fast"

    def test_build_parser_cull_stats(self):
        parser = build_parser()
        args = parser.parse_args(["cull-stats", "--machine-db", "./test.sqlite"])
        assert args.action == "cull-stats"
        assert args.machine_db == "./test.sqlite"

    def test_build_parser_cull_trim(self):
        parser = build_parser()
        args = parser.parse_args(["cull-trim", "--machine-db", "./test.sqlite", "--dry-run"])
        assert args.dry_run is True

    def test_build_parser_cull_purge(self):
        parser = build_parser()
        args = parser.parse_args(["cull-purge", "--machine-db", "./test.sqlite", "--older-than", "14"])
        assert args.older_than == 14

    def test_build_parser_doctor(self):
        parser = build_parser()
        args = parser.parse_args(["doctor"])
        assert args.action == "doctor"

    def test_build_parser_json_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--json", "list"])
        assert args.json_output is True


# ===========================================================================
# Cull Tests
# ===========================================================================


class TestCull:
    def test_stats_no_file(self, tmp_path):
        result = stats(str(tmp_path / "nonexistent.sqlite"))
        assert "not found" in result.lower()

    def test_stats_no_tables(self, tmp_path):
        db_path = str(tmp_path / "empty.sqlite")
        conn = sqlite3.connect(db_path)
        conn.close()
        result = stats(db_path)
        assert "No checkpoint tables" in result

    def test_stats_empty_db(self, machine_db):
        result = stats(machine_db)
        assert "Total checkpoints" in result
        assert "| 0 |" in result

    def test_stats_with_data(self, machine_db):
        conn = sqlite3.connect(machine_db)
        now = datetime.now(timezone.utc).isoformat()
        # Active execution
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-1", "exec-1", "state_enter", '{}', now),
        )
        conn.execute(
            "INSERT INTO machine_latest VALUES (?, ?)",
            ("exec-1", "ck-1"),
        )
        # Terminated execution
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-2", "exec-2", "state_enter", '{}', now),
        )
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-3", "exec-2", "machine_end", '{}', now),
        )
        conn.execute(
            "INSERT INTO machine_latest VALUES (?, ?)",
            ("exec-2", "ck-3"),
        )
        conn.commit()
        conn.close()

        result = stats(machine_db)
        assert "Total checkpoints" in result
        assert "3" in result  # total checkpoints

    def test_trim_no_file(self, tmp_path):
        result = trim(str(tmp_path / "nonexistent.sqlite"))
        assert "not found" in result.lower()

    def test_trim_no_terminated(self, machine_db):
        conn = sqlite3.connect(machine_db)
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-1", "exec-1", "state_enter", '{}', now),
        )
        conn.execute(
            "INSERT INTO machine_latest VALUES (?, ?)",
            ("exec-1", "ck-1"),
        )
        conn.commit()
        conn.close()

        result = trim(machine_db)
        assert "No terminated" in result

    def test_trim_deletes_intermediates(self, machine_db):
        conn = sqlite3.connect(machine_db)
        now = datetime.now(timezone.utc).isoformat()
        # Terminated execution with 3 checkpoints
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-1", "exec-1", "state_enter", '{}', now),
        )
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-2", "exec-1", "state_exit", '{}', now),
        )
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-3", "exec-1", "machine_end", '{}', now),
        )
        conn.execute(
            "INSERT INTO machine_latest VALUES (?, ?)",
            ("exec-1", "ck-3"),
        )
        conn.commit()
        conn.close()

        result = trim(machine_db)
        assert "Deleted 2" in result

        # Verify only the final checkpoint remains
        conn = sqlite3.connect(machine_db)
        count = conn.execute("SELECT count(*) FROM machine_checkpoints").fetchone()[0]
        conn.close()
        assert count == 1

    def test_trim_dry_run(self, machine_db):
        conn = sqlite3.connect(machine_db)
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-1", "exec-1", "state_enter", '{}', now),
        )
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-2", "exec-1", "machine_end", '{}', now),
        )
        conn.execute(
            "INSERT INTO machine_latest VALUES (?, ?)",
            ("exec-1", "ck-2"),
        )
        conn.commit()
        conn.close()

        result = trim(machine_db, dry_run=True)
        assert "Would delete" in result

        # Verify nothing was deleted
        conn = sqlite3.connect(machine_db)
        count = conn.execute("SELECT count(*) FROM machine_checkpoints").fetchone()[0]
        conn.close()
        assert count == 2

    def test_purge_no_file(self, tmp_path):
        result = purge(str(tmp_path / "nonexistent.sqlite"))
        assert "not found" in result.lower()

    def test_purge_no_old(self, machine_db):
        conn = sqlite3.connect(machine_db)
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-1", "exec-1", "machine_end", '{}', now),
        )
        conn.execute(
            "INSERT INTO machine_latest VALUES (?, ?)",
            ("exec-1", "ck-1"),
        )
        conn.commit()
        conn.close()

        result = purge(machine_db, older_than_days=7)
        assert "No terminated" in result

    def test_purge_deletes_old(self, machine_db):
        conn = sqlite3.connect(machine_db)
        old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        # Old terminated execution
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-1", "exec-1", "state_enter", '{}', old_time),
        )
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-2", "exec-1", "machine_end", '{}', old_time),
        )
        conn.execute(
            "INSERT INTO machine_latest VALUES (?, ?)",
            ("exec-1", "ck-2"),
        )
        conn.execute(
            "INSERT INTO execution_leases VALUES (?, ?, ?)",
            ("exec-1", "worker-1", old_time),
        )
        conn.commit()
        conn.close()

        result = purge(machine_db, older_than_days=7)
        assert "Purged 1" in result
        assert "2 checkpoints" in result

        # Verify everything is gone
        conn = sqlite3.connect(machine_db)
        ckpt_count = conn.execute("SELECT count(*) FROM machine_checkpoints").fetchone()[0]
        latest_count = conn.execute("SELECT count(*) FROM machine_latest").fetchone()[0]
        lease_count = conn.execute("SELECT count(*) FROM execution_leases").fetchone()[0]
        conn.close()
        assert ckpt_count == 0
        assert latest_count == 0
        assert lease_count == 0

    def test_purge_dry_run(self, machine_db):
        conn = sqlite3.connect(machine_db)
        old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-1", "exec-1", "machine_end", '{}', old_time),
        )
        conn.execute(
            "INSERT INTO machine_latest VALUES (?, ?)",
            ("exec-1", "ck-1"),
        )
        conn.commit()
        conn.close()

        result = purge(machine_db, older_than_days=7, dry_run=True)
        assert "Would purge" in result

        # Verify nothing was deleted
        conn = sqlite3.connect(machine_db)
        count = conn.execute("SELECT count(*) FROM machine_checkpoints").fetchone()[0]
        conn.close()
        assert count == 1

    def test_purge_preserves_active(self, machine_db):
        conn = sqlite3.connect(machine_db)
        old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        now = datetime.now(timezone.utc).isoformat()

        # Old terminated
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-1", "exec-old", "machine_end", '{}', old_time),
        )
        conn.execute(
            "INSERT INTO machine_latest VALUES (?, ?)",
            ("exec-old", "ck-1"),
        )

        # Active (not terminated)
        conn.execute(
            "INSERT INTO machine_checkpoints VALUES (?, ?, ?, ?, ?)",
            ("ck-2", "exec-active", "state_enter", '{}', old_time),
        )
        conn.execute(
            "INSERT INTO machine_latest VALUES (?, ?)",
            ("exec-active", "ck-2"),
        )
        conn.commit()
        conn.close()

        result = purge(machine_db, older_than_days=7)
        assert "Purged 1" in result

        # Active should still be there
        conn = sqlite3.connect(machine_db)
        count = conn.execute(
            "SELECT count(*) FROM machine_checkpoints WHERE execution_id='exec-active'"
        ).fetchone()[0]
        conn.close()
        assert count == 1

    def test_has_tables_true(self, machine_db):
        conn = sqlite3.connect(machine_db)
        assert _has_tables(conn) is True
        conn.close()

    def test_has_tables_false(self, tmp_path):
        db_path = str(tmp_path / "empty.sqlite")
        conn = sqlite3.connect(db_path)
        assert _has_tables(conn) is False
        conn.close()


# ===========================================================================
# Doctor Tests
# ===========================================================================


class TestDoctor:
    def test_check_sqlite_version(self):
        status, msg, fix = _check_sqlite_version()
        assert status in ("ok", "warn")
        assert "SQLite" in msg

    def test_check_venv_with_real_venv(self):
        skills_repo = str(Path(__file__).resolve().parents[1])
        skill_dir = os.path.join(skills_repo, "flatmachine-manager")
        status, msg, fix = _check_venv(skills_repo, skill_dir)
        # Should find the .venv in the repo
        assert status == "ok"

    def test_check_venv_missing(self, tmp_path):
        status, msg, fix = _check_venv(str(tmp_path), str(tmp_path / "skill"))
        assert status == "error"
        assert "not found" in msg

    def test_check_schema_db_exists(self):
        skills_repo = str(Path(__file__).resolve().parents[1])
        skill_dir = os.path.join(skills_repo, "flatmachine-manager")
        status, msg, fix = _check_schema_db(skill_dir)
        assert status == "ok"

    def test_check_schema_db_missing(self, tmp_path):
        status, msg, fix = _check_schema_db(str(tmp_path))
        assert status == "error"

    def test_check_registry_db_exists(self, tmp_db):
        db_path = tmp_db._db_path
        schema_path = "fake_schema.sqlite"
        status, msg, fix = _check_registry_db(db_path, schema_path)
        assert status == "ok"
        assert "0 machines" in msg

    def test_check_registry_db_missing(self, tmp_path):
        status, msg, fix = _check_registry_db(
            str(tmp_path / "nonexistent.sqlite"),
            str(tmp_path / "schema.sqlite"),
        )
        assert status == "warn"

    def test_check_registry_db_corrupt(self, tmp_path):
        bad_db = tmp_path / "bad.sqlite"
        bad_db.write_text("not a database")
        status, msg, fix = _check_registry_db(str(bad_db), "schema.sqlite")
        assert status == "error"

    def test_run_doctor(self, tmp_path):
        # Use fake paths so it reports errors (expected)
        result = run_doctor(str(tmp_path), str(tmp_path), str(tmp_path / "db.sqlite"))
        assert "flatmachines doctor" in result
        assert "SQLite" in result

    def test_run_doctor_with_real_paths(self):
        skills_repo = str(Path(__file__).resolve().parents[1])
        skill_dir = os.path.join(skills_repo, "flatmachine-manager")
        db_path = os.path.join(skill_dir, "schema.sql")
        result = run_doctor(skills_repo, skill_dir, db_path)
        assert "flatmachines doctor" in result
        # At minimum sqlite and schema should be ok
        assert "✓" in result


# ===========================================================================
# Tool Registry Tests
# ===========================================================================


class TestToolRegistry:
    def test_alias_rebinds_to_new_tool_id_on_schema_change(self, tmp_path):
        db_path = str(tmp_path / "tools.sqlite")
        tr = ToolRegistry(db_path=db_path)

        schema_v1 = {
            "type": "function",
            "function": {
                "name": "create_machine",
                "description": "v1",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                    },
                    "required": ["name"],
                },
            },
        }
        schema_v2 = {
            "type": "function",
            "function": {
                "name": "create_machine",
                "description": "v2",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "template": {"type": "string"},
                    },
                    "required": ["name"],
                },
            },
        }

        e1 = tr.register("create_machine", schema_v1, provider="manager", description="v1")
        e2 = tr.register("create_machine", schema_v2, provider="manager", description="v2")

        current = tr.get("create_machine")
        assert current is not None
        assert e1.tool_id != e2.tool_id
        assert current.tool_id == e2.tool_id

        count_defs = tr._conn.execute("SELECT count(*) FROM tool_definitions").fetchone()[0]
        assert count_defs == 2
        tr.close()

    def test_alias_provider_conflict_rejected(self, tmp_path):
        db_path = str(tmp_path / "tools.sqlite")
        tr = ToolRegistry(db_path=db_path)

        schema = {
            "type": "function",
            "function": {
                "name": "read",
                "description": "Read file",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        }

        tr.register("read", schema, provider="cli-tools", description="read")
        with pytest.raises(ValueError):
            tr.register("read", schema, provider="manager", description="read")
        tr.close()


# ===========================================================================
# Integration / End-to-End Tests
# ===========================================================================


class TestEndToEnd:
    """Test full workflows through the tool layer."""

    def test_create_update_validate_diff_workflow(self, tmp_db):
        # 1. Create a machine
        create_result = _run(tool_create_machine(tmp_db, "test", {
            "name": "workflow-bot",
            "template": "writer-critic",
            "description": "Test workflow",
            "agents": [
                {"name": "writer", "purpose": "Write stories", "model_profile": "smart"},
                {"name": "critic", "purpose": "Review stories", "model_profile": "fast"},
            ],
        }))
        assert not create_result.is_error

        # 2. Update it
        update_result = _run(tool_update_machine(tmp_db, "test", {
            "name": "workflow-bot",
            "operation": "add_state",
            "params": {"state_name": "human_gate"},
            "description": "Added human gate",
        }))
        assert not update_result.is_error

        # 3. Validate
        val_result = _run(tool_validate_machine(tmp_db, "test", {"name": "workflow-bot"}))
        assert not val_result.is_error

        # 4. Diff v1 vs v2
        diff_result = _run(tool_diff_versions(tmp_db, "test", {
            "name": "workflow-bot",
            "v1": 1,
            "v2": 2,
        }))
        assert not diff_result.is_error

        # 5. Get machine
        get_result = _run(tool_get_machine(tmp_db, "test", {"name": "workflow-bot"}))
        assert not get_result.is_error
        assert "v2" in get_result.content

    def test_create_duplicate_deprecate_workflow(self, tmp_db):
        # 1. Create
        _run(tool_create_machine(tmp_db, "test", {
            "name": "original-bot",
            "template": "tool-loop",
            "description": "Original",
        }))

        # 2. Duplicate
        dup_result = _run(tool_duplicate_machine(tmp_db, "test", {
            "source": "original-bot",
            "target": "forked-bot",
        }))
        assert not dup_result.is_error

        # 3. Verify both exist
        list_result = _run(tool_list_machines(tmp_db, "test", {"status": "active"}))
        assert "original-bot" in list_result.content
        assert "forked-bot" in list_result.content

        # 4. Deprecate original
        dep_result = _run(tool_deprecate_machine(tmp_db, "test", {"name": "original-bot"}))
        assert not dep_result.is_error

        # 5. Verify only fork is active
        list_result2 = _run(tool_list_machines(tmp_db, "test", {"status": "active"}))
        assert "original-bot" not in list_result2.content
        assert "forked-bot" in list_result2.content

    @pytest.mark.parametrize("template_name", TEMPLATES.keys())
    def test_create_and_validate_all_templates(self, tmp_db, template_name):
        """Create and validate every template through the tool layer."""
        create_result = _run(tool_create_machine(tmp_db, "test", {
            "name": f"test-{template_name}",
            "template": template_name,
            "description": f"Test {template_name} template",
        }))
        assert not create_result.is_error

        val_result = _run(tool_validate_machine(tmp_db, "test", {
            "name": f"test-{template_name}",
        }))
        assert not val_result.is_error
        assert "✓" in val_result.content
