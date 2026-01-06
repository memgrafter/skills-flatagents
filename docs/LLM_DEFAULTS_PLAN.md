# Global Defaults for FlatAgents

## Overview

Add support for global model defaults to eliminate duplication across all 9 agent configs. Currently every config hardcodes `provider: cerebras` and `name: zai-glm-4.6`.

**Configuration Sources (in precedence order):**
1. Agent config file (full override)
2. Environment variables (`FLATAGENT_MODEL_*`)
3. `~/.flatagents/defaults.yml`
4. Built-in fallbacks

**Override Semantics:** Full replacement - if an agent config has ANY model fields, its entire model section replaces the defaults.

## Implementation Strategy

### 1. Create Default Config Schema

**File:** `~/.flatagents/defaults.yml` (created by installer)

```yaml
# Global defaults for all FlatAgent instances
# Override behavior: If agent config specifies ANY model fields,
# the entire model section from this file is ignored

model:
  provider: cerebras
  name: zai-glm-4.6
  temperature: 0.7
  max_tokens: 2048
  output_tokens: 1024
```

### 2. Environment Variables

**Convention:** `FLATAGENT_MODEL_<FIELD>` (uppercase with underscores)

```bash
FLATAGENT_MODEL_PROVIDER=cerebras
FLATAGENT_MODEL_NAME=zai-glm-4.6
FLATAGENT_MODEL_TEMPERATURE=0.7
FLATAGENT_MODEL_MAX_TOKENS=2048
FLATAGENT_MODEL_OUTPUT_TOKENS=1024
```

Environment variables override the defaults.yml file.

### 3. Config Loader Implementation

**Approach:** Create a wrapper in `shared/` rather than modifying the flatagents library (which is installed from PyPI).

**New File:** `shared/config_loader.py`

**Key Components:**
- `load_defaults()` - Load from `~/.flatagents/defaults.yml` and env vars
- `apply_defaults(agent_config, defaults)` - Merge with full override semantics
- `FlatAgentWithDefaults` - Wrapper class that auto-applies defaults

**Logic:**
```python
def load_defaults():
    """Returns dict with model defaults from file + env var overrides."""
    # 1. Load ~/.flatagents/defaults.yml
    # 2. Override individual fields from FLATAGENT_MODEL_* env vars
    # 3. Type conversion for numbers (int for tokens, float for temp)

def apply_defaults(agent_config, defaults):
    """Apply defaults with full override semantics."""
    # If agent has data.model section → use it entirely, ignore defaults
    # Otherwise → use defaults.model
    # Merge other sections (system, user, mcp) normally
```

### 4. Update Installation

**File:** `install.sh`

Add after venv creation:
```bash
# Create ~/.flatagents directory and defaults if needed
FLATAGENTS_DIR="$HOME/.flatagents"
DEFAULTS_FILE="$FLATAGENTS_DIR/defaults.yml"

if [[ ! -d "$FLATAGENTS_DIR" ]]; then
    mkdir -p "$FLATAGENTS_DIR"
fi

if [[ ! -f "$DEFAULTS_FILE" ]]; then
    # Create defaults.yml with current common settings
    cat > "$DEFAULTS_FILE" << 'EOF'
# FlatAgents Global Defaults
[... yaml content ...]
EOF
fi
```

Only creates if doesn't exist (respects user customization).

### 5. Migrate Skills to Use Defaults

**Pattern:** Replace `FlatAgent(config_file=...)` with `FlatAgentWithDefaults(config_file=...)`

**Files to update:**
- `search_refiner/src/search_refiner/main.py:95-96` (2 agents)
- `shell_analyzer/src/shell_analyzer/main.py:166-167` (1 agent)
- `test_writer/src/test_writer/main.py:147,169,189,208` (4 agents)

### 6. Clean Up Agent Configs

**Remove redundant model sections from:**
- `search_refiner/config/search.yml` - Remove entire model section (matches defaults)
- `search_refiner/config/refiner.yml` - Keep only `output_tokens: 500`

**Keep full model sections in configs that differ:**
- `shell_analyzer/config/analyzer.yml` - Has `temperature: 0.1`, `output_tokens: 500`
- `test_writer/config/*.yml` - Various custom temps and token limits

**Result:** Most configs shrink significantly, only specifying what differs from defaults.

## Critical Files

**New Files:**
1. `shared/config_loader.py` - Core implementation
2. `tests/test_config_loader.py` - Unit tests

**Modified Files:**
3. `shared/__init__.py` - Export new functions/classes
4. `install.sh` - Create ~/.flatagents/defaults.yml
5. `search_refiner/src/search_refiner/main.py` - Use wrapper
6. `shell_analyzer/src/shell_analyzer/main.py` - Use wrapper
7. `test_writer/src/test_writer/main.py` - Use wrapper
8. `search_refiner/config/search.yml` - Remove redundant model section
9. `search_refiner/config/refiner.yml` - Keep only diffs from defaults

## Implementation Steps

1. **Create config_loader.py**
   - Implement load_defaults(), apply_defaults(), FlatAgentWithDefaults
   - Handle missing files gracefully
   - Type conversion for env vars

2. **Add tests**
   - Test loading from defaults.yml
   - Test env var override
   - Test full override semantics
   - Test backward compatibility (no defaults file)

3. **Update shared/__init__.py**
   - Export FlatAgentWithDefaults and helpers

4. **Update install.sh**
   - Create ~/.flatagents/ directory
   - Generate defaults.yml if not exists

5. **Migrate one skill (shell_analyzer)**
   - Test with defaults
   - Test with env var overrides
   - Validate backward compatibility

6. **Migrate remaining skills**
   - search_refiner (2 agents)
   - test_writer (4 agents)

7. **Clean up configs**
   - Remove redundant model sections
   - Keep only agent-specific overrides

## Edge Cases

- **Missing defaults file:** Fall back gracefully, no crash
- **Invalid YAML:** Log warning, use built-in defaults
- **Partial model config in agent:** Even one field triggers full override
- **Type conversion errors:** Handle gracefully, skip bad env vars
- **Directory permissions:** Don't block install if can't create ~/.flatagents/

## Backward Compatibility

- Existing configs work unchanged (wrapper checks for model section)
- If ~/.flatagents/defaults.yml doesn't exist, no defaults applied
- Standard FlatAgent class continues to work normally
- Zero breaking changes
