#!/bin/bash
# Test runner for the Coding Agent
# 
# Usage:
#   ./test.sh          # Run all tests
#   ./test.sh unit     # Run unit tests only
#   ./test.sh int      # Run integration tests only
#   ./test.sh -v       # Verbose mode

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Ensure venv exists and has test dependencies
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv .venv
fi

echo "Installing test dependencies..."
uv pip install --quiet --python ".venv/bin/python" -e ".[test]"

# Parse arguments
TEST_PATH="tests/"
PYTEST_ARGS=""

for arg in "$@"; do
    case $arg in
        unit)
            TEST_PATH="tests/unit/"
            ;;
        int|integration)
            TEST_PATH="tests/integration/"
            ;;
        -v|--verbose)
            PYTEST_ARGS="$PYTEST_ARGS -v"
            ;;
        *)
            PYTEST_ARGS="$PYTEST_ARGS $arg"
            ;;
    esac
done

echo "Running tests: $TEST_PATH"
.venv/bin/python -m pytest $TEST_PATH $PYTEST_ARGS
