"""
Validation pipeline for flatmachine configs.

Integrates:
1. JSON Schema validation (via flatmachines SDK)
2. Jinja2 template checking
3. Best practices compliance (from BEST_PRACTICES.md + TIPS.md)
4. Structural integrity checks
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ValidationIssue:
    severity: str  # error, warning, info
    rule: str
    message: str
    path: str = ""  # dot-path to the problematic field

    def __str__(self):
        prefix = f"[{self.severity.upper()}]"
        loc = f" at {self.path}" if self.path else ""
        return f"{prefix} {self.rule}{loc}: {self.message}"


@dataclass
class ValidationResult:
    valid: bool = True
    schema_errors: List[str] = field(default_factory=list)
    template_errors: List[str] = field(default_factory=list)
    best_practices: List[ValidationIssue] = field(default_factory=list)
    structural: List[ValidationIssue] = field(default_factory=list)

    @property
    def all_errors(self) -> List[str]:
        errs = list(self.schema_errors) + list(self.template_errors)
        errs += [str(i) for i in self.best_practices if i.severity == "error"]
        errs += [str(i) for i in self.structural if i.severity == "error"]
        return errs

    @property
    def all_warnings(self) -> List[str]:
        warns = []
        warns += [str(i) for i in self.best_practices if i.severity == "warning"]
        warns += [str(i) for i in self.structural if i.severity == "warning"]
        return warns

    def summary(self) -> str:
        lines = []
        if self.valid:
            lines.append("✓ Machine config is valid")
        else:
            lines.append("✗ Machine config has errors")

        if self.schema_errors:
            lines.append(f"\nSchema errors ({len(self.schema_errors)}):")
            for e in self.schema_errors:
                lines.append(f"  - {e}")

        if self.template_errors:
            lines.append(f"\nTemplate errors ({len(self.template_errors)}):")
            for e in self.template_errors:
                lines.append(f"  - {e}")

        bp_errors = [i for i in self.best_practices if i.severity == "error"]
        bp_warnings = [i for i in self.best_practices if i.severity == "warning"]
        bp_info = [i for i in self.best_practices if i.severity == "info"]

        if bp_errors:
            lines.append(f"\nBest practice violations ({len(bp_errors)}):")
            for i in bp_errors:
                lines.append(f"  ✗ {i}")
        if bp_warnings:
            lines.append(f"\nBest practice warnings ({len(bp_warnings)}):")
            for i in bp_warnings:
                lines.append(f"  ⚠ {i}")
        if bp_info:
            lines.append(f"\nBest practice info ({len(bp_info)}):")
            for i in bp_info:
                lines.append(f"  ℹ {i}")

        if self.structural:
            lines.append(f"\nStructural issues ({len(self.structural)}):")
            for i in self.structural:
                lines.append(f"  {'✗' if i.severity == 'error' else '⚠'} {i}")

        total_issues = len(self.all_errors) + len(self.all_warnings)
        if total_issues == 0:
            lines.append("\nNo issues found.")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def _validate_schema(config: Dict[str, Any]) -> List[str]:
    """Run JSON Schema validation via flatmachines SDK if available."""
    try:
        from flatmachines.validation import validate_flatmachine_config
        return validate_flatmachine_config(config, warn=False, strict=False)
    except ImportError:
        return []
    except Exception as e:
        return [f"Schema validation failed: {e}"]


# ---------------------------------------------------------------------------
# Template/Jinja2 validation
# ---------------------------------------------------------------------------

_JINJA_BLOCK_RE = re.compile(r'{{[\s\S]*?}}|{%-?[\s\S]*?-?%}')
_ALLOWED_TAGS = {"if", "elif", "else", "endif", "for", "endfor", "set"}
_ALLOWED_FILTERS = {
    "default", "length", "lower", "upper", "trim", "replace",
    "join", "first", "last", "truncate", "tojson", "int", "float",
}
_DISALLOWED_PATTERNS = [
    (re.compile(r'\[[0-9]*:[0-9]*\]'), "Python-style slicing is not portable across SDKs"),
    (re.compile(r'\|\s*(map|dictsort|list|select|reject|attr|round)\b'), "Unsupported Jinja2 filter"),
]


def _validate_templates(config: Dict[str, Any]) -> List[str]:
    """Check Jinja2 templates for cross-SDK compatibility."""
    errors = []

    def _check_value(value: Any, path: str):
        if not isinstance(value, str):
            return
        for match in _JINJA_BLOCK_RE.finditer(value):
            block = match.group()

            # Check tags
            tag_match = re.search(r'{%\s*([A-Za-z_][\w-]*)', block)
            if tag_match:
                tag = tag_match.group(1)
                if tag not in _ALLOWED_TAGS:
                    errors.append(f"{path}: unsupported tag '{{% {tag} %}}'")

            # Check filters
            for fmatch in re.finditer(r'\|\s*([A-Za-z_][\w-]*)', block):
                filt = fmatch.group(1)
                if filt not in _ALLOWED_FILTERS:
                    errors.append(f"{path}: unsupported filter '|{filt}'")

            # Check disallowed patterns
            for pattern, msg in _DISALLOWED_PATTERNS:
                if pattern.search(block):
                    errors.append(f"{path}: {msg}")

    def _walk(obj: Any, path: str):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _walk(v, f"{path}[{i}]")
        elif isinstance(obj, str):
            _check_value(obj, path)

    _walk(config, "config")
    return errors


# ---------------------------------------------------------------------------
# Best practices checks
# ---------------------------------------------------------------------------

def _check_best_practices(config: Dict[str, Any]) -> List[ValidationIssue]:
    """Check compliance with BEST_PRACTICES.md and TIPS.md rules."""
    issues = []
    data = config.get("data", {})
    states = data.get("states", {})
    agents = data.get("agents", {})
    persistence = data.get("persistence", {})

    # Rule 1: Persistence should be enabled for machines with >3 states
    non_trivial = len(states) > 3
    if non_trivial and not persistence.get("enabled"):
        issues.append(ValidationIssue(
            severity="warning",
            rule="persistence-recommended",
            message="Machine has >3 states but persistence is not enabled. "
                    "Enable persistence for checkpoint/resume safety.",
        ))

    # Rule 2: Prefer sqlite backend over local
    if persistence.get("enabled") and persistence.get("backend") == "local":
        issues.append(ValidationIssue(
            severity="warning",
            rule="prefer-sqlite-backend",
            message="Use 'sqlite' backend instead of 'local' to avoid FD churn "
                    "and stale file cleanup (BEST_PRACTICES.md §1).",
        ))

    # Rule 3: Agent states should have on_error
    for sname, sdef in states.items():
        if not isinstance(sdef, dict):
            continue
        if sdef.get("agent") and not sdef.get("on_error"):
            issues.append(ValidationIssue(
                severity="warning",
                rule="agent-state-needs-on_error",
                message=f"Agent state '{sname}' has no on_error handler.",
                path=f"data.states.{sname}",
            ))

    # Rule 4: Agent states should have retry execution
    for sname, sdef in states.items():
        if not isinstance(sdef, dict):
            continue
        if sdef.get("agent"):
            execution = sdef.get("execution", {})
            if not isinstance(execution, dict) or execution.get("type") != "retry":
                issues.append(ValidationIssue(
                    severity="warning",
                    rule="agent-state-needs-retry",
                    message=f"Agent state '{sname}' lacks execution retry with backoff.",
                    path=f"data.states.{sname}.execution",
                ))

    # Rule 5: Check for JSON output schemas between LLM stages (anti-pattern)
    for aname, adef in agents.items():
        if isinstance(adef, dict):
            adata = adef.get("data", adef)
            output = adata.get("output", {})
            if isinstance(output, dict) and len(output) > 2:
                issues.append(ValidationIssue(
                    severity="info",
                    rule="prefer-plain-text-output",
                    message=f"Agent '{aname}' has {len(output)} output fields. "
                            "Consider using plain text output.content instead "
                            "(TIPS.md §1: avoid JSON between model stages).",
                    path=f"data.agents.{aname}.data.output",
                ))

    # Rule 6: Check for |truncate in templates (non-truncation invariant)
    def _check_truncate(obj, path):
        if isinstance(obj, str) and ("| truncate" in obj or "|truncate" in obj):
            issues.append(ValidationIssue(
                severity="error",
                rule="no-truncation",
                message="Template uses |truncate filter. Never truncate data "
                        "between stages (BEST_PRACTICES.md §2 hard rule).",
                path=path,
            ))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                _check_truncate(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _check_truncate(v, f"{path}[{i}]")

    _check_truncate(data, "data")

    # Rule 7: Must have at least one initial and one final state
    has_initial = any(
        isinstance(s, dict) and s.get("type") == "initial"
        for s in states.values()
    )
    has_final = any(
        isinstance(s, dict) and s.get("type") == "final"
        for s in states.values()
    )
    if not has_initial:
        issues.append(ValidationIssue(
            severity="error",
            rule="needs-initial-state",
            message="Machine has no initial state (type: initial).",
        ))
    if not has_final:
        issues.append(ValidationIssue(
            severity="error",
            rule="needs-final-state",
            message="Machine has no final state (type: final).",
        ))

    # Rule 8: Transitions should reference existing states
    all_state_names = set(states.keys())
    for sname, sdef in states.items():
        if not isinstance(sdef, dict):
            continue
        transitions = sdef.get("transitions", [])
        if isinstance(transitions, list):
            for t in transitions:
                if isinstance(t, dict):
                    target = t.get("to", "")
                    if target and target not in all_state_names:
                        issues.append(ValidationIssue(
                            severity="error",
                            rule="transition-target-exists",
                            message=f"Transition from '{sname}' targets '{target}' which doesn't exist.",
                            path=f"data.states.{sname}.transitions",
                        ))

    return issues


# ---------------------------------------------------------------------------
# Structural validation
# ---------------------------------------------------------------------------

def _check_structural(config: Dict[str, Any]) -> List[ValidationIssue]:
    """Check structural integrity of the config."""
    issues = []
    data = config.get("data", {})
    states = data.get("states", {})
    agents = data.get("agents", {})

    # Check agent references exist
    for sname, sdef in states.items():
        if not isinstance(sdef, dict):
            continue
        agent_ref = sdef.get("agent")
        if agent_ref and agent_ref not in agents:
            issues.append(ValidationIssue(
                severity="error",
                rule="agent-ref-exists",
                message=f"State '{sname}' references agent '{agent_ref}' which is not defined in agents.",
                path=f"data.states.{sname}.agent",
            ))

    # Check for unreachable states
    reachable = set()
    initial_states = [
        sname for sname, sdef in states.items()
        if isinstance(sdef, dict) and sdef.get("type") == "initial"
    ]

    def _collect_reachable(state_name):
        if state_name in reachable:
            return
        reachable.add(state_name)
        sdef = states.get(state_name, {})
        if not isinstance(sdef, dict):
            return
        for t in sdef.get("transitions", []):
            if isinstance(t, dict) and t.get("to"):
                _collect_reachable(t["to"])
        on_error = sdef.get("on_error")
        if isinstance(on_error, str):
            _collect_reachable(on_error)
        elif isinstance(on_error, dict):
            for target in on_error.values():
                _collect_reachable(target)

    for s in initial_states:
        _collect_reachable(s)

    for sname in states:
        if sname not in reachable and initial_states:
            issues.append(ValidationIssue(
                severity="warning",
                rule="unreachable-state",
                message=f"State '{sname}' is not reachable from any initial state.",
                path=f"data.states.{sname}",
            ))

    return issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_machine_config(config_raw: str) -> ValidationResult:
    """Run full validation suite on a machine config YAML string."""
    result = ValidationResult()

    # Parse YAML
    try:
        config = yaml.safe_load(config_raw)
    except yaml.YAMLError as e:
        result.valid = False
        result.schema_errors.append(f"Invalid YAML: {e}")
        return result

    if not isinstance(config, dict):
        result.valid = False
        result.schema_errors.append("Config must be a YAML mapping")
        return result

    # 1. Schema validation
    result.schema_errors = _validate_schema(config)

    # 2. Template validation
    result.template_errors = _validate_templates(config)

    # 3. Best practices
    result.best_practices = _check_best_practices(config)

    # 4. Structural integrity
    result.structural = _check_structural(config)

    # Determine overall validity
    has_errors = bool(result.schema_errors) or bool(result.template_errors)
    has_errors = has_errors or any(i.severity == "error" for i in result.best_practices)
    has_errors = has_errors or any(i.severity == "error" for i in result.structural)
    result.valid = not has_errors

    return result
