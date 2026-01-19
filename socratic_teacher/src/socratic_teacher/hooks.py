import json
import os
import re
import sys
from datetime import datetime
from flatagents import MachineHooks

# Turn off litellm logging
os.environ["LITELLM_LOG"] = "ERROR"


class SocraticTeacherHooks(MachineHooks):
    """Hooks for Socratic teacher machine custom actions."""

    def __init__(self):
        super().__init__()
        self.debug = os.environ.get("SOCRATIC_DEBUG", "0") == "1"

    def _debug_print(self, label: str, data):
        """Print debug info if enabled."""
        if self.debug:
            print(f"\n[DEBUG {label}]", file=sys.stderr)
            if isinstance(data, (dict, list)):
                print(json.dumps(data, indent=2, default=str), file=sys.stderr)
            else:
                print(data, file=sys.stderr)

    def on_action(self, action: str, context: dict) -> dict:
        """Handle custom actions. Must return full context, not partial."""
        if action == "init_session":
            return self._init_session(context)
        elif action == "collect_learner_response":
            return self._collect_learner_response(context)
        elif action == "update_understanding_model":
            return self._update_understanding_model(context)
        elif action == "parse_question":
            return self._parse_question(context)
        elif action == "parse_evaluation":
            return self._parse_evaluation(context)
        elif action == "parse_feedback":
            return self._parse_feedback(context)
        return context  # Return full context, not empty dict

    def _init_session(self, context: dict) -> dict:
        """Initialize session from input."""
        input_data = context.get("_input", {})
        context["topic"] = input_data.get("topic", context.get("topic", ""))
        context["learner_level"] = int(input_data.get("learner_level", context.get("learner_level", 1)))
        context["max_rounds"] = int(input_data.get("max_rounds", context.get("max_rounds", 10)))
        context["working_dir"] = input_data.get("working_dir", context.get("working_dir", "."))
        return context

    def _collect_learner_response(self, context: dict) -> dict:
        """Collect learner response from stdin."""
        question = context.get("question", "")
        print(f"\nQuestion: {question}")
        if context.get("follow_up_prompt"):
            print(f"Hint: {context['follow_up_prompt']}")
        print("\nYour response: ", end="", flush=True)

        try:
            response = input().strip()
            if not response:
                print("No response provided. Please try again.")
                return context

            # Add to history
            context.setdefault("question_history", []).append(question)
            context.setdefault("response_history", []).append(response)
            context["learner_response"] = response
        except EOFError:
            context["learner_response"] = ""
            context["termination_reason"] = "input_eof"

        return context

    def _update_understanding_model(self, context: dict) -> dict:
        """Update understanding model based on evaluation."""
        score = context.get("evaluation_score", 0.0)
        depth = context.get("evaluation_depth", "surface")
        gaps = context.get("evaluation_gaps", [])
        correct_elements = context.get("evaluation_strengths", [])

        # Add to history
        evaluation_record = {
            "score": score,
            "depth": depth,
            "identified_gaps": gaps,
            "correct_elements": correct_elements,
        }
        context.setdefault("evaluation_history", []).append(evaluation_record)

        # Update mastery score (rolling average)
        current_mastery = context.get("mastery_score", 0.0)
        round_count = context.get("round_count", 0)
        context["mastery_score"] = (current_mastery * round_count + score) / (round_count + 1)

        # Merge gaps
        existing_gaps = set(context.get("identified_gaps", []))
        context["identified_gaps"] = list(existing_gaps | set(gaps))

        # Track strengths
        existing_strengths = set(context.get("strengths", []))
        if correct_elements:
            existing_strengths.update(correct_elements)
        context["strengths"] = list(existing_strengths)

        # Update round count
        context["round_count"] = round_count + 1

        # Set termination reason if done
        if context["mastery_score"] >= 0.85:
            context["termination_reason"] = "mastery"
        elif context["round_count"] >= context.get("max_rounds", 10):
            context["termination_reason"] = "max_rounds"

        # Build session transcript
        self._update_transcript(context)

        return context

    def _parse_question(self, context: dict) -> dict:
        """Parse question agent output (QUESTION: ... / HINT: ...)."""
        output_obj = context.get("_agent_output", {})
        output_text = output_obj.get("content", "") if isinstance(output_obj, dict) else str(output_obj)

        self._debug_print("QUESTION_GENERATOR_RAW", output_text)

        question = ""
        hint = ""

        # Try structured format first
        for line in output_text.split("\n"):
            line_stripped = line.strip()
            if line_stripped.upper().startswith("QUESTION:"):
                question = line_stripped[9:].strip()
            elif line_stripped.upper().startswith("HINT:"):
                hint = line_stripped[5:].strip()

        # Fallback: if no QUESTION: prefix found, use regex to find question marks
        if not question:
            # Look for a sentence ending with ?
            match = re.search(r'([^.!?\n]*\?)', output_text)
            if match:
                question = match.group(1).strip()
            else:
                # Last fallback: use the whole output as the question
                question = output_text.strip().split('\n')[0] if output_text.strip() else "What do you think about this topic?"

        context["question"] = question
        context["follow_up_prompt"] = hint

        self._debug_print("PARSED_QUESTION", {"question": question, "hint": hint})
        return context

    def _parse_evaluation(self, context: dict) -> dict:
        """Parse evaluation agent output (plain text format)."""
        output_obj = context.get("_agent_output", {})
        output_text = output_obj.get("content", "") if isinstance(output_obj, dict) else str(output_obj)

        self._debug_print("EVALUATION_RAW", output_text)

        context["evaluation_score"] = 0.5
        context["evaluation_depth"] = "partial"
        context["evaluation_gaps"] = []
        context["evaluation_strengths"] = []

        for line in output_text.split("\n"):
            line = line.strip()
            key = line.split(":")[0].upper() if ":" in line else ""
            value = line.split(":", 1)[1].strip() if ":" in line else ""

            if key == "SCORE":
                try:
                    context["evaluation_score"] = float(value.split("/")[0])
                except ValueError:
                    pass
            elif key == "DEPTH":
                if value.lower() in ["surface", "partial", "deep"]:
                    context["evaluation_depth"] = value.lower()
            elif key == "GAPS":
                context["evaluation_gaps"] = [g.strip() for g in value.split(",") if g.strip() and g.strip().lower() not in ["none", "n/a"]]
            elif key == "STRENGTHS":
                context["evaluation_strengths"] = [s.strip() for s in value.split(",") if s.strip() and s.strip().lower() not in ["none", "n/a"]]

        self._debug_print("PARSED_EVALUATION", {
            "score": context["evaluation_score"],
            "depth": context["evaluation_depth"],
            "gaps": context["evaluation_gaps"],
            "strengths": context["evaluation_strengths"]
        })

        return context

    def _parse_feedback(self, context: dict) -> dict:
        """Parse feedback agent output (plain text)."""
        output_obj = context.get("_agent_output", {})
        output_text = output_obj.get("content", "") if isinstance(output_obj, dict) else str(output_obj)

        self._debug_print("FEEDBACK_RAW", output_text)

        context["feedback"] = output_text.strip()
        context["feedback_type"] = "hint"

        # Print feedback to user
        if context["feedback"]:
            print(f"\nFeedback: {context['feedback']}")

        return context

    def _update_transcript(self, context: dict) -> None:
        """Build formatted session transcript."""
        lines = []

        # Header
        topic = context.get("topic", "Unknown Topic")
        lines.append(f"# Socratic Learning Session: {topic}")
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("")

        # Rounds
        question_history = context.get("question_history", [])
        response_history = context.get("response_history", [])
        evaluation_history = context.get("evaluation_history", [])

        for i, question in enumerate(question_history):
            round_num = i + 1
            lines.append(f"## Round {round_num}")
            lines.append(f"**Question:** {question}")
            if i < len(response_history):
                lines.append(f"**Response:** {response_history[i]}")
            if i < len(evaluation_history):
                eval_data = evaluation_history[i]
                lines.append(
                    f"**Score:** {eval_data.get('score', 0.0):.2f}/1.0"
                )
                lines.append(f"**Depth:** {eval_data.get('depth', 'unknown')}")
            lines.append("")

        # Summary
        mastery = context.get("mastery_score", 0.0)
        identified_gaps = context.get("identified_gaps", [])
        strengths = context.get("strengths", [])

        lines.append("## Summary")
        lines.append(f"**Final Mastery Score:** {mastery:.2f}/1.0")
        lines.append(
            f"**Identified Gaps:** {', '.join(identified_gaps) if identified_gaps else 'None'}"
        )
        lines.append(
            f"**Strengths:** {', '.join(strengths) if strengths else 'None'}"
        )
        round_count = context.get("round_count", 0)
        max_rounds = context.get("max_rounds", 10)
        lines.append(f"**Rounds:** {round_count}/{max_rounds}")

        context["session_transcript"] = "\n".join(lines)
