# Repo Spotlight Skill - Planning Document

## Goal

Create a codebase analysis skill that produces a **reusable navigation artifact** - a map you consult to know where to look, then spotlight + ripgrep for details. Not a code dump.

**Key insight:** The map should be constant-size regardless of repo size, with drill-down capability for specific areas.

---

## Open Questions

### Persistence Layer (Unresolved)

How does the digest persist and get accessed?

| Option | Pros | Cons |
|--------|------|------|
| Stdout (ephemeral) | Simple | No reuse, manual paste |
| File in repo (`.claude/codebase-map.md`) | Persists, Claude can `Read` it | Gets stale, needs regen trigger |
| CLAUDE.md injection | Auto-loaded every session | Pollutes instructions, wasteful |
| MCP resource | Clean tool access | Requires MCP infrastructure |
| Cache + file watcher | Always fresh | Complex |

**Needs decision:** What's the intended access pattern?

---

## Research Summary

### Aider Repo Map
- Uses tree-sitter to extract symbols (classes, functions, signatures)
- Graph ranking algorithm finds most-referenced identifiers
- Token budget optimization - fits important parts to available context
- Source: https://aider.chat/docs/repomap.html

### Cerebras GLM 4.6 Thinking
- 131K context window on Cerebras
- Thinking blocks for reasoning (not interleaved like Sonnet)
- 1000+ tokens/sec inference speed
- Strong at tool use and agents
- Source: https://inference-docs.cerebras.ai/models/zai-glm-46

---

## Output Design (v3 - Scalable)

```markdown
## Overview
<what it does, 2-3 sentences>

## Directory Map
src/
  api/        - REST endpoints, request handling
  core/       - Business logic, domain models
  db/         - Database access, migrations
  utils/      - Shared helpers

tests/        - Mirrors src/ structure

## Hot Spots (most-referenced)
1. src/core/models.py - Domain entities (47 refs)
2. src/core/service.py - Main business logic (38 refs)
3. src/api/routes.py - Endpoint definitions (31 refs)

## Entry Points
- CLI: src/cli.py:main()
- API: src/api/app.py:create_app()

## To explore further
- "analyze src/api" - expand API layer
- "analyze src/core" - expand core domain
```

**~300 tokens regardless of repo size.** Scales because:
- Directory map is top-level only
- Hot spots limited to N most-referenced
- Detail comes from drill-down, not upfront enumeration

### Usage Pattern

```
1. Generate map (once, or on significant changes)
2. Consult map to understand structure
3. Spotlight specific area: "analyze src/api"
4. Ripgrep for specifics: grep "error" src/api/
5. Read specific files as needed
```

---

## Architecture

### Simple v1 (Two States)

```
┌─────────────────────────────────────────────────────┐
│                    FlatMachine                       │
├─────────────────────────────────────────────────────┤
│  start (action: build_repo_map)                     │
│    ↓                                                │
│  analyze (agent: analyzer with thinking)            │
│    ↓                                                │
│  done                                               │
└─────────────────────────────────────────────────────┘
```

### Hook: `build_repo_map`

```python
def _build_repo_map(self, context):
    root = Path(context["path"])

    # 1. Tree structure (top-level only, filtered)
    tree = get_directory_map(root, max_depth=2)

    # 2. Hot spots - most referenced files
    hot_spots = find_hot_spots(root, limit=10)

    # 3. Entry points detection
    entry_points = find_entry_points(root)

    # 4. Key files (README, config)
    key_files = read_key_files(root)

    # 5. Git context
    git_info = get_git_context(root)

    context["repo_map"] = {
        "tree": tree,
        "hot_spots": hot_spots,
        "entry_points": entry_points,
        "key_files": key_files,
        "git": git_info
    }
    return context
```

### Hot Spot Detection

```python
def find_hot_spots(root: Path, limit: int = 10) -> list:
    """Find most-referenced files by counting imports."""
    import_counts = {}

    for py_file in root.glob("**/*.py"):
        # Parse imports
        imports = extract_imports(py_file)
        for imp in imports:
            # Resolve to file path
            resolved = resolve_import(imp, root)
            if resolved:
                import_counts[resolved] = import_counts.get(resolved, 0) + 1

    # Sort by reference count
    sorted_files = sorted(import_counts.items(), key=lambda x: -x[1])
    return sorted_files[:limit]
```

### Agent: `analyzer.yml`

```yaml
spec: flatagent
spec_version: "0.6.0"

data:
  name: repo-analyzer

  model:
    provider: cerebras
    name: zai-glm-4.6
    temperature: 0.3

  system: |
    You are a senior software architect analyzing a codebase.
    Use your thinking to reason through the structure.

    Produce a concise navigation map that helps developers:
    1. Understand what the project does (2-3 sentences)
    2. Know where to look for specific functionality
    3. Identify the most important files

    Keep output under 500 tokens. This is a map, not documentation.

  user: |
    Analyze this codebase:

    ## Directory Structure
    {{ input.repo_map.tree }}

    ## Most Referenced Files
    {% for file, count in input.repo_map.hot_spots %}
    - {{ file }} ({{ count }} refs)
    {% endfor %}

    ## Entry Points
    {{ input.repo_map.entry_points }}

    ## Key Files
    {% for name, content in input.repo_map.key_files.items() %}
    ### {{ name }}
    ```
    {{ content[:2000] }}
    ```
    {% endfor %}

    ## Recent Git Activity
    {{ input.repo_map.git }}
```

---

## File Structure

```
repo_spotlight/
├── SKILL.md                          # Discovery metadata
├── machine.yml                       # FlatMachine config
├── run.sh                            # Entry point
├── agents/
│   └── analyzer.yml                  # Cerebras GLM 4.6 thinking
└── src/repo_spotlight/
    ├── __init__.py
    ├── main.py                       # CLI
    ├── hooks.py                      # build_repo_map action
    └── repo_map.py                   # Tree, hot spots, imports
```

---

## Future Enhancements

### Drill-Down Mode
```bash
./run.sh --focus src/api    # Detailed map of just src/api/
```

### Watch Mode
```bash
./run.sh --watch            # Regenerate on file changes
```

### Tree-Sitter Integration
For better cross-language symbol extraction (beyond Python AST).

### Reference Graph Visualization
Export dot/mermaid for dependency visualization.

### MCP Server Mode
Run as persistent server, expose `get_map` and `spotlight` tools.

---

## Dependencies

```toml
[project.optional-dependencies]
repo-spotlight = []  # stdlib only for v1 (ast, pathlib)
```

No external deps for v1. Tree-sitter optional for v2.

---

## Prior Art to Investigate

### Aider Repo Map
- Tree-sitter extracts symbols (classes, functions, signatures)
- Graph ranking algorithm finds most-referenced identifiers
- Token budget optimization - fits important parts to available context
- **Replicate:** Graph ranking, token budgeting
- Source: https://aider.chat/docs/repomap.html

### Augment Context Engine
- Indexes relationships/dependencies between code, not just files
- Dynamic relevance scoring (recently touched code weighted higher)
- 200k token window but intelligently surfaces only what matters per task
- Understands how changes ripple through services
- Available via MCP but we want to replicate core ideas locally
- **Replicate:** Relationship indexing, relevance scoring, smart retrieval
- Source: https://www.augmentcode.com/context-engine

### Context-Engine MCP (m1rl0k)
- Hybrid code search (dense vectors + lexical + reranker)
- ReFRAG micro-chunking for better retrieval
- Qdrant-powered indexing with auto-sync on file changes
- **Replicate:** Incremental updates, hybrid search approach
- Source: https://github.com/m1rl0k/Context-Engine

### Claude Context (Zilliz)
- ~40% token reduction with equivalent retrieval quality
- Hybrid search (BM25 + dense vector)
- **Replicate:** Token efficiency techniques
- Source: https://github.com/zilliztech/claude-context

**Note:** We want to replicate key parts locally, not consume external MCPs. Running locally means we can use simpler approaches (Python AST, git commands, file watching) without vector DB infrastructure.

---

## Status

**Phase:** Planning

**Blockers:**
1. **Persistence layer** - How does Claude access/reuse the map?
2. **Maintenance cost** - LLM generation is expensive; map generation should be LLM-free (deterministic code via static analysis). LLM only for optional one-time summary.

**Key Insight:** Map generation should be **code-only** (AST, imports, git). Fast, free, can run on every commit. LLM is for consumption, not generation.

**Next:**
1. Decide persistence model
2. Investigate prior art implementations deeper
3. Implement v1 (code-only generation)
