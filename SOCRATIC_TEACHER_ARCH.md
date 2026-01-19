# Socratic Teacher Machine Architecture

## Machine Composition

```
┌─────────────────────────────────────────────────────────────┐
│        socratic_teacher (MAIN ORCHESTRATOR)                │
│                                                             │
│  Context:                                                   │
│  - topic, difficulty, max_rounds, round_count              │
│  - understanding_model (knowledge gaps)                     │
│  - question_history, response_history                       │
│  - mastery_score                                            │
│  - session_transcript (for persistence)                     │
│                                                             │
│  States Flow:                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ start → ask_question → wait_response →              │   │
│  │ evaluate_response → check_mastery → provide_feedback│   │
│  │ └──→ (loop or end) → save_session (optional)        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Agents Used (embedded):                                    │
│  • question_generator   (ask state)                        │
│  • response_evaluator   (evaluate state)                   │
│  • feedback_provider    (feedback state)                   │
│                                                             │
│  Sub-Machines (optional):                                  │
│  • file_writer (save session transcript/profile to disk)   │
│  • session_analyzer (analyze learning progress)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Agent Definitions (New)

### 1. `question_generator.yml`
**Purpose**: Generate probing questions aligned to Socratic method

**Input**:
```yaml
topic: str                           # Learning topic
difficulty_level: int                # 1-5 scale
understanding_gaps: list[str]        # Known knowledge gaps
previous_questions: list[str]        # History to avoid repetition
conversation_depth: int              # How many Q&A rounds so far
```

**Output**:
```yaml
question: str                        # The probing question
reasoning: str                       # Why this question?
follow_up_prompt: str               # Hint to nudge thinking
```

**Prompt Template**: Generates open-ended questions that reveal thinking, avoid directly answering, scaffold complexity progressively.

---

### 2. `response_evaluator.yml`
**Purpose**: Assess learner response against question intent and learning objectives

**Input**:
```yaml
question: str
learner_response: str
expected_concepts: list[str]        # Key ideas to assess
understanding_level: int            # Baseline (0-5)
topic: str
```

**Output**:
```yaml
score: float                         # 0.0 (incorrect) to 1.0 (mastery)
depth: str                           # "surface" | "partial" | "deep"
identified_gaps: list[str]           # What they don't understand
correct_elements: list[str]          # What they got right
next_difficulty: int                 # Recommended next level
```

**Prompt Template**: Evaluate for conceptual understanding (not just right/wrong), identify misconceptions, recommend direction.

---

### 3. `feedback_provider.yml`
**Purpose**: Generate Socratic feedback (hints, confirmations, or guided questions)

**Input**:
```yaml
question: str
learner_response: str
evaluation_result: dict              # score, gaps, etc.
is_correct: bool
response_depth: str                  # "surface" | "partial" | "deep"
```

**Output**:
```yaml
feedback_type: str                   # "confirm" | "hint" | "redirect" | "probe_deeper"
feedback_text: str                   # Actual feedback (never the answer)
next_question: str                   # Optional follow-up to redirect thinking
encouragement: str
```

**Prompt Template**: Praise effort, ask clarifying questions, guide toward gaps, never give away answers.

---

## Optional Sub-Machine: `session_analyzer`

**Purpose**: Periodically analyze learning trajectory (optional for MVP)

**Triggers**: After every 3-5 rounds or on user request

**Flow**:
- Analyze question history, response scores, gaps evolution
- Generate learning report (strengths, misconceptions, readiness)
- Output: `{ overall_mastery: float, learning_path_recommendation: str }`

---

## Session Context (in main machine)

```yaml
data:
  context:
    # Input
    topic: "{{ input.topic }}"
    learner_level: "{{ input.level | default(1) }}"  # 1-5
    max_rounds: "{{ input.max_rounds | default(10) }}"

    # Runtime
    round_count: 0
    understanding_model:
      mastery_score: 0.0              # 0.0-1.0
      identified_gaps: []
      strengths: []

    question: ""
    learner_response: ""
    evaluation: {}
    feedback: ""

    # History for continuity
    question_history: []
    response_history: []
    evaluation_history: []
    session_transcript: ""  # Formatted for file output

    # Control
    session_complete: false
    termination_reason: ""  # "mastery", "max_rounds", "user_quit"
```

---

## State Machine States

```yaml
states:
  start:
    type: initial
    transitions:
      - to: ask_question

  ask_question:
    agent: question_generator
    input:
      topic: "{{ context.topic }}"
      difficulty_level: "{{ context.understanding_model.mastery_score | scale_to_difficulty }}"
      understanding_gaps: "{{ context.understanding_model.identified_gaps }}"
      previous_questions: "{{ context.question_history }}"
      conversation_depth: "{{ context.round_count }}"
    output_to_context:
      question: "{{ output.question }}"
      follow_up_prompt: "{{ output.follow_up_prompt }}"
    transitions:
      - to: wait_response

  wait_response:
    # Action: pause & collect user input
    action: collect_learner_response
    transitions:
      - to: evaluate_response

  evaluate_response:
    agent: response_evaluator
    input:
      question: "{{ context.question }}"
      learner_response: "{{ context.learner_response }}"
      expected_concepts: "{{ context.understanding_model.identified_gaps }}"
      topic: "{{ context.topic }}"
    output_to_context:
      evaluation: "{{ output }}"
    transitions:
      - to: provide_feedback

  provide_feedback:
    agent: feedback_provider
    input:
      question: "{{ context.question }}"
      learner_response: "{{ context.learner_response }}"
      evaluation_result: "{{ context.evaluation }}"
    output_to_context:
      feedback: "{{ output.feedback_text }}"
      feedback_type: "{{ output.feedback_type }}"
    transitions:
      - to: check_mastery

  check_mastery:
    action: update_understanding_model
    transitions:
      - condition: "context.understanding_model.mastery_score >= 0.85"
        to: save_session
      - condition: "context.round_count >= context.max_rounds"
        to: save_session
      - to: ask_question  # Loop back

  save_session:
    # Optional: Call file_writer to persist session transcript
    machine: file_writer
    input:
      changes: "{{ context.session_transcript }}"  # Formatted transcript
      working_dir: "{{ input.working_dir | default('.') }}"
    transitions:
      - to: done
    on_error: done  # Skip if file writing fails

  done:
    type: final
    output:
      topic: "{{ context.topic }}"
      final_mastery_score: "{{ context.understanding_model.mastery_score }}"
      learning_transcript: "{{ context.question_history }}"
      identified_gaps: "{{ context.understanding_model.identified_gaps }}"
      session_summary: "{{ context.feedback }}"
```

---

## Execution Flow Example

```
User Input: topic=Python generators, level=2, max_rounds=8

Round 1:
  → question_generator: "What do you think happens when you call a function with 'yield'?"
  → User: "It returns a value?"
  → evaluator: score=0.3, depth="surface", gaps=["generator_protocol", "lazy_evaluation"]
  → feedback: "Good instinct on 'returns'. Can you think about *when* it returns?" (hint, not answer)

Round 2:
  → question_generator: "When the yield happens, does the function stop running?"
  → User: "Yes, it pauses and comes back later?"
  → evaluator: score=0.7, depth="partial", gaps=["state_preservation"]
  → feedback: "Exactly! It pauses. Now, what happens to the local variables?"

Round 3-8:
  → (similar loop, progressively scaffolding toward generator protocol)

Final:
  → mastery_score = 0.82 → "Ready to explore advanced use cases"
```

---

## Reuse from Existing Machines

| Existing | Reused For | How |
|----------|-----------|-----|
| `coding_agent` | Main loop pattern | Plan → Evaluate → Feedback → Iterate |
| `response_evaluator` | Agent scaffolding | Similar multi-criteria output structure |
| `shell_analyzer` | Retry/error handling | Backoff retry pattern for agent calls |
| `file_writer` | Session persistence | Save transcript/profile to disk via sub-machine call |

## New Machines/Agents to Build

1. **socratic_teacher/machine.yml** — Main orchestrator
2. **socratic_teacher/agents/question_generator.yml** — Ask probing questions
3. **socratic_teacher/agents/response_evaluator.yml** — Assess responses
4. **socratic_teacher/agents/feedback_provider.yml** — Socratic feedback
5. **(Optional) socratic_teacher/agents/session_analyzer.yml** — Periodic progress review

## Existing Machines to Integrate

1. **file_writer** — Sub-machine call for session persistence (save_session state)

---

## MVP vs. Future

**MVP (v1)**:
- Core 5-state loop: ask → response → evaluate → feedback → check_mastery → save_session
- 3 agents (question_generator, response_evaluator, feedback_provider)
- Simple mastery scoring (avg of evaluation scores)
- Session transcript saved via file_writer (optional, non-blocking)
- No session analyzer

**Future (v2+)**:
- Session analyzer sub-machine for progress insights
- Adaptive difficulty curves
- Learner profile persistence across sessions
- Multi-topic learning paths
- Conversation branching based on learner confusion patterns
