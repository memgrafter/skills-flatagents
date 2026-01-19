---
name: socratic-teacher
description: Interactive Socratic teaching assistant that guides learners through discovery-based questioning
---

# Socratic Teacher

An interactive teaching skill that uses the Socratic method to guide learners toward deep understanding through carefully crafted probing questions. The machine adapts question difficulty based on learner responses and provides supportive feedback without giving away answers.

## Usage

```bash
./run.sh --topic "Python generators" --level 2 --max-rounds 10
```

## Arguments

- `--topic` (required): Learning topic to teach
- `--level` (optional, default 1): Learner proficiency level (1-5 scale)
- `--max-rounds` (optional, default 10): Maximum number of teaching rounds
- `--working-dir` (optional, default "."): Directory to save session transcripts
- `--cwd` (optional): User's current working directory

## Features

- **Adaptive questioning**: Questions scale in difficulty based on learner understanding
- **Response evaluation**: Evaluates learner responses for conceptual depth, not just correctness
- **Socratic feedback**: Provides hints and guided questions, never direct answers
- **Learning transcript**: Saves session history with mastery scores and identified gaps
- **Mastery detection**: Automatically ends session when learner demonstrates 85%+ mastery or max rounds reached

## Output

The skill outputs a JSON object with:

```json
{
  "topic": "Python generators",
  "final_mastery_score": 0.82,
  "learning_transcript": [...],
  "identified_gaps": ["state_preservation", "lazy_evaluation"],
  "strengths": ["function_calls", "return_values"],
  "termination_reason": "mastery",
  "rounds_completed": 6
}
```

## How It Works

1. **Question Generation**: LLM generates probing questions tailored to identified knowledge gaps
2. **Response Collection**: Interactive prompt collects learner response
3. **Evaluation**: Evaluator assesses response for accuracy, depth, and understanding
4. **Feedback**: Feedback agent provides Socratic guidance (hints, clarifying questions, praise)
5. **Update**: Understanding model updated with mastery score and new gaps
6. **Loop or End**: Process repeats until mastery achieved or max rounds exceeded
7. **Save**: Session transcript saved to disk (optional, non-blocking)

## Example Session

```
Topic: Python generators, Level: 2

Question: What do you think happens when you call a function with 'yield'?
Hint: Think about what the function returns...

Your response: It returns a value?

Feedback: Good instinct on 'returns'! Can you think about *when* it returns
compared to a regular function?

---

Question: When the yield happens, does the function stop running?
Your response: Yes, it pauses and comes back later?

Feedback: Exactly! It pauses. Now, what happens to the local variables
when it pauses?

---

[... more rounds ...]

Final Mastery: 82%
Identified gaps: state_preservation
Ready to learn: generator.send() method
```
