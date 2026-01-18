#!/bin/bash
# Lint spec_version references in skills-flatagents repo
# Usage: lint-spec-versions.sh [expected-version]
# Exit: 0 if linting passes, 1 if version validation fails
#
# This is a simplified version of the flatagents linter adapted for skills-flatagents
# It performs a broad semver scan and warns about versions not matching expected

set -e

# Get the repo root - script can be run from anywhere
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Expected version (default 0.7.1)
EXPECTED_VERSION="${1:-0.7.1}"

# Strict semver validation
if ! [[ "$EXPECTED_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be semver format (e.g., 0.7.1), got: $EXPECTED_VERSION"
    exit 1
fi

echo "Scanning $REPO_ROOT for semver patterns..."
echo "Expected version: $EXPECTED_VERSION"
echo ""

# =============================================================================
# BROAD SEMVER SCAN - Find any semver that doesn't match expected version
# =============================================================================
echo "Running broad semver scan..."
echo ""

STRAY_VERSIONS=()

# Use rg to find all semver patterns, then filter
# Exclusions:
# - .venv, __pycache__, .git, node_modules, .egg-info
# - lock files, egg-info directories
# - Historical version refs (vX.X.X)
# - npm/pip dependency patterns (^X.X.X, ~X.X.X, >=X.X.X, etc)
# - package.json/pyproject.toml "version" fields
# - Other legitimate exceptions

while IFS=: read -r file lineno content; do
    [[ -z "$file" ]] && continue

    # Extract semver from content
    VERSION=$(echo "$content" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    [[ -z "$VERSION" ]] && continue

    # Skip if matches expected version
    [[ "$VERSION" == "$EXPECTED_VERSION" ]] && continue

    # Skip vX.X.X historical references (e.g., "added in v0.1.0")
    echo "$content" | grep -qE "v$VERSION" && continue

    # Skip npm/pip dependency patterns: ^X.X.X, ~X.X.X, >=X.X.X, etc
    echo "$content" | grep -qE '[\"\'"'"'][\^~><!=]+[0-9]+\.[0-9]+\.[0-9]+' && continue

    # Skip package.json/pyproject.toml "version" field (project version, not spec version)
    if [[ "$file" == *"package.json" ]] || [[ "$file" == *"pyproject.toml" ]]; then
        echo "$content" | grep -qE '"version"|^version' && continue
    fi

    # Skip .egg-info requires.txt lines (dependency versions are allowed to vary)
    [[ "$file" == *".egg-info/requires.txt" ]] && continue

    # Looks like a real mismatch - add to list
    STRAY_VERSIONS+=("$file:$lineno: $VERSION (expected $EXPECTED_VERSION)")
done < <(rg -n '[0-9]+\.[0-9]+\.[0-9]+' \
    --glob '*.yml' --glob '*.yaml' --glob '*.md' --glob '*.py' --glob '*.toml' --glob '*.txt' \
    --glob '!**/.venv/**' --glob '!**/__pycache__/**' --glob '!**/.git/**' --glob '!**/node_modules/**' \
    --glob '!**/.egg-info/**' --glob '!*-lock.json' --glob '!*.lock' \
    "$REPO_ROOT" 2>/dev/null || true)

# Report results
if [[ ${#STRAY_VERSIONS[@]} -gt 0 ]]; then
    echo "⚠️  Found ${#STRAY_VERSIONS[@]} semver(s) not matching expected version ($EXPECTED_VERSION):"
    echo ""
    for stray in "${STRAY_VERSIONS[@]}"; do
        echo "  ⚠️  $stray"
    done
    echo ""
    echo "Review these - they may be:"
    echo "  - Spec versions needing to be updated to $EXPECTED_VERSION"
    echo "  - Dependency version constraints (allowed to vary)"
    echo "  - Documentation examples (usually safe to ignore)"
    echo "  - Other legitimate non-spec versions"
    echo ""
else
    echo "✓ No stray semver versions found"
    echo ""
fi

# Always exit 0 - this is a warning-only linter
echo "Linting complete!"
exit 0
