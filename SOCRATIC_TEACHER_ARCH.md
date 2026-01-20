# Socratic Teacher Machine Architecture

## Overview

An interactive Socratic teaching system with:
- **SQLite persistence** for sessions, topic trees, and progress tracking
- **Split-brain scoring** (Scorer + Extractor pattern) for robust evaluation
- **Topic tree generation** with auto-difficulty based on history
- **Session checkpoint/resume** for interrupted learning
- **Rubric generation** adapting to procedural vs conceptual tasks

## Machine Composition

```
┌─────────────────────────────────────────────────────────────────┐
│        socratic_teacher (MAIN ORCHESTRATOR)                     │
│                                                                 │
│  SQLite Storage (.socratic_teacher.db):                        │
│  ├── sessions       - Session metadata & state                  │
│  ├── session_rounds - Individual Q&A rounds (checkpoint data)   │
│  ├── topics         - Topic tree hierarchy                      │
│  └── topic_progress - User progress per topic                   │
│                                                                 │
│  Initialization Flow:                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ start → check_resume → [restore_session OR             │   │
│  │ check_topic_tree → generate_topic_tree → select_topic →│   │
│  │ check_auto_difficulty → generate_rubric] →             │   │
│  │ show_session_info → ask_question                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Main Loop:                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ask_question → wait_response →                         │   │
│  │ score_response (Scorer) → extract_evaluation (Extractor)│   │
│  │ → provide_feedback → checkpoint_round → check_mastery  │   │
│  │ → [loop OR complete_session] → save_session → done     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Agents (6):                                                    │
│  • topic_tree_generator  - Generate curriculum tree             │
│  • rubric_generator      - Create task-specific rubrics         │
│  • question_generator    - Socratic questions                   │
│  • response_scorer       - Verbose natural language critique    │
│  • feedback_provider     - Encouraging Socratic feedback        │
│  • (legacy) response_evaluator - Backwards compat               │
│                                                                 │
│  Sub-Machines:                                                  │
│  • file_writer       - Save session transcript to disk          │
│  • json_extractor    - Extract structured JSON from critique    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Split-Brain Scoring Pattern

The key architectural improvement: decouple reasoning from formatting.

```
┌────────────────────┐    ┌──────────────────────┐    ┌────────────┐
│  response_scorer   │───▶│    json_extractor    │───▶│  Structured│
│  (The Reasoner)    │    │    (The Architect)   │    │    Data    │
│                    │    │                      │    │            │
│  "Write a verbose  │    │  "Extract score,     │    │  {         │
│   critique. Don't  │    │   depth, gaps from   │    │   score:   │
│   worry about      │    │   this critique.     │    │   depth:   │
│   structure."      │    │   Output ONLY JSON." │    │   gaps:    │
│                    │    │                      │    │  }         │
└────────────────────┘    └──────────────────────┘    └────────────┘

Benefits:
- Scorer can hallucinate, use analogies, explore nuance freely
- Extractor has rich context to interpret ("mostly correct" → 0.8)
- Bulletproof parsing: no more regex failures on misplaced periods
- Trade latency (2 calls) for reliability (agent pipelines need this)
```

## SQLite Schema

```sql
-- Sessions: main session metadata
sessions (
    session_id TEXT PRIMARY KEY,
    topic TEXT, subject TEXT,
    learner_level INTEGER, task_type TEXT,
    status TEXT,  -- 'active', 'suspended', 'completed'
    mastery_score REAL,
    identified_gaps TEXT, strengths TEXT, rubric TEXT,
    termination_reason TEXT,
    created_at TEXT, updated_at TEXT,
    context_snapshot TEXT  -- Full context for resume
)

-- Session rounds: individual Q&A for checkpoint/resume
session_rounds (
    session_id TEXT, round_num INTEGER,
    question TEXT, response TEXT,
    score REAL, depth TEXT,
    gaps TEXT, strengths TEXT,
    critique TEXT,  -- Full verbose scorer output
    timestamp TEXT
)

-- Topics: hierarchical topic tree
topics (
    topic_id TEXT PRIMARY KEY,  -- e.g., "python:generators"
    subject TEXT, name TEXT,
    parent_topic_id TEXT,  -- NULL for root topics
    description TEXT,
    difficulty INTEGER,  -- 1-5
    prerequisites TEXT,  -- JSON array of topic_ids
    task_type TEXT  -- 'procedural' or 'conceptual'
)

-- Progress: user progress tracking
topic_progress (
    topic_id TEXT PRIMARY KEY,
    sessions_completed INTEGER,
    best_mastery_score REAL,
    avg_mastery_score REAL,
    total_rounds INTEGER,
    last_session_id TEXT,
    last_practiced TEXT
)
```

## Agent Definitions

### 1. `topic_tree_generator.yml`
**Purpose**: Generate curriculum tree for a subject

**Input**: subject, learner_context
**Output**: JSON array of topic objects

**Key Features**:
- Creates 8-15 topics with logical progression
- Marks procedural vs conceptual tasks
- Builds prerequisite relationships

### 2. `rubric_generator.yml`
**Purpose**: Create task-type-appropriate evaluation rubrics

**Input**: topic, task_type, difficulty_level, known_gaps

**Output**: Bulleted rubric with [REQUIRED] and [DEPTH] markers

**Key Insight** (from architect feedback):
- PROCEDURAL tasks: Focus on steps, order, binary checkpoints
- CONCEPTUAL tasks: Focus on understanding WHY, connections, edge cases

### 3. `response_scorer.yml` (NEW - replaces response_evaluator)
**Purpose**: Write verbose natural language critique

**Input**: topic, task_type, question, response, rubric, learner_level

**Output**: Free-form critique (passed to json_extractor)

**Prompt Design**:
- "Be verbose. Think out loud. Don't worry about format."
- Explore what's right, wrong, depth of understanding
- Give gut assessment: pass/fail, move harder or repeat?

### 4. `question_generator.yml`
**Purpose**: Generate Socratic probing questions

**Input**: topic, difficulty_level, understanding_gaps, history

**Output**: QUESTION: ..., HINT: ...

### 5. `feedback_provider.yml`
**Purpose**: Encouraging Socratic feedback

**Input**: question, response, score, depth

**Output**: Plain text feedback (never gives away answers)

## JSON Extractor Machine (Generic/Reusable)

Located at: `/json_extractor/`

A generic machine for extracting structured JSON from natural language.
Part of the Split-Brain pattern - can be reused across projects.

**Usage**:
```yaml
machines:
  json_extractor: ../json_extractor/machine.yml

extract_evaluation:
  machine: json_extractor
  input:
    text: "{{ context.verbose_critique }}"
    schema: "score (0.0-1.0), depth (surface/partial/deep), gaps (list)"
    context: "Educational evaluation extraction"
```

**Extraction Strategies** (in hooks):
1. Direct JSON parse
2. Find JSON object in text
3. Clean up trailing commas
4. Parse markdown code blocks
5. Line-by-line key:value fallback

## Session Flow

### New Session
```
1. check_resume → No active session
2. check_topic_tree → Missing for subject
3. generate_topic_tree → LLM generates curriculum
4. parse_topic_tree → Store in SQLite topics table
5. select_topic → User picks or uses provided
6. check_auto_difficulty → Based on topic_progress
7. generate_rubric → Task-appropriate rubric
8. show_session_info → Display and create session in DB
9. Main loop...
```

### Resume Session
```
1. check_resume → Found suspended session
2. User confirms resume
3. restore_session_state → Load from context_snapshot
4. show_resume_info → Display progress
5. ask_question → Continue where left off
```

### Graceful Quit
```
User types: /quit

1. handle_user_quit triggered
2. Session marked as "suspended" in SQLite
3. context_snapshot saved for resume
4. Transcript written to file
5. "Session saved! You can resume later."
```

## Context Schema

```yaml
context:
  # Input
  subject: ""         # Parent subject (e.g., "Python")
  topic: ""           # Specific topic (e.g., "Generators")
  learner_level: 0    # 0 = auto from history
  max_rounds: 10
  task_type: ""       # 'procedural' or 'conceptual', empty = auto

  # Session management
  session_id: ""
  resuming_session: false
  session_status: "active"

  # Topic tree
  topic_tree: []
  selected_topic: {}
  rubric: ""

  # Runtime state
  round_count: 0
  mastery_score: 0.0
  identified_gaps: []
  strengths: []

  # Current interaction
  question: ""
  learner_response: ""
  verbose_critique: ""    # Scorer output
  evaluation_score: 0.0
  evaluation_depth: "partial"
  evaluation_gaps: []
  evaluation_strengths: []
  feedback: ""

  # History
  question_history: []
  response_history: []
  evaluation_history: []

  # Control
  user_quit: false
  termination_reason: ""
```

## Commands

- `/quit` or `/q` - Gracefully save and exit (can resume later)
- `Ctrl+D` - Hard exit (session still checkpointed per-round)

## Example Flow

```
$ flatagents run socratic_teacher --topic "Python generators" --subject "Python"

======================================================================
Subject: Python
Topic: Python generators
Type: conceptual
Difficulty: ** (Level 2/5)
======================================================================
Commands: /quit to save and exit | Ctrl+D for hard exit
Starting session...

Question: What do you think happens inside a function when it encounters 'yield'?

Your response: It returns a value and pauses

[Scorer thinks aloud...]
"The learner correctly identified that yield causes a pause. They mentioned
'returns a value' which shows basic understanding. However, they didn't
address state preservation or the iterator protocol. This is a partial
understanding - they grasp the surface behavior but miss the deeper mechanics.
I'd say this is about 70% there. Pass, but needs probing on state."

[Extractor extracts: {score: 0.7, depth: "partial", gaps: ["state_preservation"]}]

Feedback: Good instinct! When yield pauses, what happens to the local
variables inside the function? Do they disappear?
[Score: 70.0% | Depth: partial]

...

Round 6:
Question: Can you explain why generators are "lazy"?

Your response: /quit

======================================================================
Session saved! You can resume later with the same topic.
Progress: 78.3% mastery after 5 rounds
======================================================================
```

## Files Structure

```
socratic_teacher/
├── machine.yml                    # Main orchestrator
├── profiles.yml                   # Model configurations
├── agents/
│   ├── topic_tree_generator.yml   # Curriculum generation
│   ├── rubric_generator.yml       # Task-specific rubrics
│   ├── question_generator.yml     # Socratic questions
│   ├── response_scorer.yml        # Verbose critique (NEW)
│   ├── feedback_provider.yml      # Encouraging feedback
│   └── response_evaluator.yml     # Legacy (backwards compat)
└── src/socratic_teacher/
    ├── __init__.py
    ├── main.py                    # CLI entry point
    ├── hooks.py                   # All custom actions
    ├── sqlite_store.py            # SQLite persistence (NEW)
    └── session_store.py           # Legacy JSONL (kept for migration)

json_extractor/                    # GENERIC/REUSABLE
├── machine.yml                    # Split-brain extractor
├── profiles.yml
├── hooks.py                       # JSON parsing strategies
├── __init__.py
└── agents/
    └── extractor.yml              # JSON extraction agent
```

## Future Enhancements

- [ ] Multi-subject learning paths
- [ ] Spaced repetition for gap topics
- [ ] Conversation branching on confusion patterns
- [ ] Export progress reports
- [ ] Web UI integration
