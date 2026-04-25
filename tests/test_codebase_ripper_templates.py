from pathlib import Path
import importlib
import sys

import yaml
from jinja2 import Environment

ROOT = Path(__file__).resolve().parent.parent
CODEBASE_RIPPER_DIR = ROOT / "codebase-ripper"

sys.path.insert(0, str(CODEBASE_RIPPER_DIR / "src"))

from codebase_ripper.hooks import CodebaseRipperHooks


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _render_user_template(path: Path, input_data: dict) -> str:
    config = _load_yaml(path)
    template = config["data"]["user"]
    return Environment().from_string(template).render(input=input_data)


def test_generator_template_accepts_string_iteration():
    rendered = _render_user_template(
        CODEBASE_RIPPER_DIR / "agents" / "generator.yml",
        {
            "task": "orient repo",
            "structure": "src/",
            "initial_context": "README.md",
            "allowlist": "",
            "blocked_patterns": "",
            "iteration": "1",
            "previous_summary": "Found training code in train.py",
            "accepted_count": "5",
            "accepted_commands": "rg train",
            "rejected_commands": "",
        },
    )

    assert "## Iteration 1" in rendered
    assert "Found training code in train.py" in rendered


def test_extractor_template_accepts_string_iteration():
    rendered = _render_user_template(
        CODEBASE_RIPPER_DIR / "agents" / "extractor.yml",
        {
            "task": "orient repo",
            "token_budget": "12000",
            "iteration": "1",
            "previous_context": "Earlier pass found checkpoints under models/",
            "aggregated_output": "command output",
        },
    )

    assert "## Iteration 1" in rendered
    assert "Earlier pass found checkpoints under models/" in rendered


def test_update_iteration_state_coerces_string_max_iterations():
    hooks = CodebaseRipperHooks()
    context = {"iteration": 0, "max_iterations": "3"}

    updated = hooks._update_iteration_state(context)

    assert updated["iteration"] == 1
    assert updated["max_iterations"] == 3
    assert updated["should_continue"] is True


def test_generator_extractor_prompt_matches_declared_output_shape():
    config = _load_yaml(CODEBASE_RIPPER_DIR / "agents" / "generator_extractor.yml")

    system_prompt = config["data"]["system"]
    user_prompt = config["data"]["user"]
    output_schema = config["data"]["output"]

    assert '{"commands": [' in system_prompt
    assert '{"commands": [' in user_prompt
    assert "commands" in output_schema



def test_machine_extract_commands_uses_native_output_path():
    config = _load_yaml(CODEBASE_RIPPER_DIR / "machine.yml")
    mapping = config["data"]["states"]["extract_commands"]["output_to_context"]["generated_commands"]

    assert mapping == "output.commands"



def test_package_import_does_not_eagerly_import_main_module():
    sys.modules.pop("codebase_ripper", None)
    sys.modules.pop("codebase_ripper.main", None)

    module = importlib.import_module("codebase_ripper")

    assert "codebase_ripper.main" not in sys.modules
    assert callable(module.run)
    assert "codebase_ripper.main" in sys.modules
