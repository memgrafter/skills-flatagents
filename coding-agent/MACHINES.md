# LLM Documentation: coding-agent

## Project Structure
```
/
├── pyproject.toml      # Project config, dependencies, metadata
├── run.sh              # Execution script
└── src/coding_agent/
    ├── __init__.py     # Package initialization
    ├── hooks.py        # System hooks/integrations
    └── main.py         # Core application entry point
```

## Core Components
- **main.py**: Primary application logic and orchestration
- **hooks.py**: System integration hooks for monitoring/automation
- **run.sh**: Shell script for application startup

## Entry Points
```bash
./run.sh            # Primary execution method
python -m src.coding_agent.main  # Direct Python execution
```

## Configuration (pyproject.toml)
- Package: coding-agent
- Python dependencies defined in project section
- Build system: standard setuptools/hatchling

## Usage Pattern
1. Execute via run.sh for standard operation
2. Direct Python execution for development/debugging
3. Modify hooks.py to integrate external systems
4. Extend main.py for core functionality changes