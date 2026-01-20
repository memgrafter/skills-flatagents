"""Hooks for Socratic teacher machine with SQLite persistence and split-brain scoring."""

import json
import os
import re
import sys
from datetime import datetime
from flatagents import MachineHooks
from socratic_teacher.sqlite_store import (
    SQLiteSessionStore,
    Session,
    SessionRound,
    Topic,
)

# Turn off litellm logging
os.environ["LITELLM_LOG"] = "ERROR"


class SocraticTeacherHooks(MachineHooks):
    """Hooks for Socratic teacher machine custom actions."""

    def __init__(self):
        super().__init__()
        self.debug = os.environ.get("SOCRATIC_DEBUG", "0") == "1"
        self._store = None

    def _get_store(self, context: dict) -> SQLiteSessionStore:
        """Get or create SQLite store."""
        if self._store is None:
            working_dir = context.get("working_dir", ".")
            db_path = f"{working_dir}/.socratic_teacher.db"
            self._store = SQLiteSessionStore(db_path)
        return self._store

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
        actions = {
            # Session management
            "check_for_resume": self._check_for_resume,
            "restore_session_state": self._restore_session_state,
            "show_resume_info": self._show_resume_info,
            # Topic tree
            "check_topic_tree": self._check_topic_tree,
            "parse_topic_tree": self._parse_topic_tree,
            "use_default_topic": self._use_default_topic,
            "select_topic": self._select_topic,
            "check_auto_difficulty": self._check_auto_difficulty,
            # Rubric
            "skip_rubric": self._skip_rubric,
            "show_session_info": self._show_session_info,
            # Main loop
            "collect_learner_response": self._collect_learner_response,
            "parse_question": self._parse_question,
            "parse_extraction": self._parse_extraction,
            "fallback_evaluation": self._fallback_evaluation,
            "parse_feedback": self._parse_feedback,
            # Checkpoint & mastery
            "checkpoint_round": self._checkpoint_round,
            "update_understanding_model": self._update_understanding_model,
            # Termination
            "handle_user_quit": self._handle_user_quit,
            "complete_session": self._complete_session,
            # Legacy
            "init_session": self._init_session,
            "show_past_sessions": self._show_past_sessions,
            "parse_evaluation": self._parse_evaluation,
        }

        handler = actions.get(action)
        if handler:
            return handler(context)
        return context

    # ==================== SESSION MANAGEMENT ====================

    def _check_for_resume(self, context: dict) -> dict:
        """Check if there's a suspended session to resume."""
        store = self._get_store(context)
        topic = context.get("topic", "")
        subject = context.get("subject", "") or topic

        # Generate session ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_slug = topic.replace(" ", "_").replace("/", "-")[:50]
        context["session_id"] = f"socratic_{topic_slug}_{timestamp}"

        # Check for active/suspended sessions
        active_session = store.get_active_session(topic)

        if active_session and active_session.status == "suspended":
            print(f"\n{'='*70}")
            print(f"Found suspended session for '{topic}'")
            print(f"  Progress: {active_session.mastery_score:.1%} mastery, {len(active_session.rounds)} rounds")
            print(f"  Last activity: {active_session.updated_at}")
            print(f"{'='*70}")
            print("\nResume this session? [Y/n]: ", end="", flush=True)

            try:
                response = input().strip().lower()
                if response in ("", "y", "yes"):
                    context["resuming_session"] = True
                    context["session_id"] = active_session.session_id
                    self._debug_print("RESUME_SESSION", active_session.session_id)
            except EOFError:
                pass

        return context

    def _restore_session_state(self, context: dict) -> dict:
        """Restore session state from SQLite."""
        store = self._get_store(context)
        session = store.get_session(context["session_id"])

        if not session:
            context["resuming_session"] = False
            return context

        # Restore context from snapshot
        snapshot = session.context_snapshot or {}
        for key, value in snapshot.items():
            if key not in ("_input", "_agent_output", "_extractor_output"):
                context[key] = value

        # Restore from session object
        context["topic"] = session.topic
        context["subject"] = session.subject
        context["learner_level"] = session.learner_level
        context["task_type"] = session.task_type
        context["mastery_score"] = session.mastery_score
        context["identified_gaps"] = session.identified_gaps
        context["strengths"] = session.strengths
        context["rubric"] = session.rubric
        context["round_count"] = len(session.rounds)

        # Restore history from rounds
        context["question_history"] = [r.question for r in session.rounds]
        context["response_history"] = [r.response for r in session.rounds]
        context["evaluation_history"] = [
            {
                "score": r.score,
                "depth": r.depth,
                "identified_gaps": r.gaps,
                "correct_elements": r.strengths,
            }
            for r in session.rounds
        ]

        if session.rounds:
            context["first_question"] = session.rounds[0].question

        # Mark as active
        session.status = "active"
        store.update_session(session)

        self._debug_print("RESTORED_SESSION", {
            "session_id": session.session_id,
            "rounds": len(session.rounds),
            "mastery": session.mastery_score
        })

        return context

    def _show_resume_info(self, context: dict) -> dict:
        """Show info about resumed session."""
        print(f"\n{'='*70}")
        print(f"Resumed session: {context['topic']}")
        print(f"Progress: {context['mastery_score']:.1%} mastery after {context['round_count']} rounds")
        if context.get("identified_gaps"):
            print(f"Known gaps: {', '.join(context['identified_gaps'][:3])}")
        print(f"{'='*70}\n")
        print("Continuing where you left off...")
        return context

    # ==================== TOPIC TREE ====================

    def _check_topic_tree(self, context: dict) -> dict:
        """Check if topic tree exists for subject."""
        store = self._get_store(context)
        subject = context.get("subject", "") or context.get("topic", "")

        if store.has_topic_tree(subject):
            topics = store.get_topic_tree(subject)
            context["topic_tree"] = [
                {
                    "topic_id": t.topic_id,
                    "name": t.name,
                    "description": t.description,
                    "difficulty": t.difficulty,
                    "task_type": t.task_type,
                    "parent": t.parent_topic_id,
                }
                for t in topics
            ]
            self._debug_print("LOADED_TOPIC_TREE", len(topics))
        else:
            context["topic_tree"] = []

        return context

    def _parse_topic_tree(self, context: dict) -> dict:
        """Parse topic tree from agent output and store in SQLite."""
        output_obj = context.get("_agent_output", {})
        output_text = output_obj.get("content", "") if isinstance(output_obj, dict) else str(output_obj)

        self._debug_print("TOPIC_TREE_RAW", output_text[:500])

        store = self._get_store(context)
        subject = context.get("subject", "") or context.get("topic", "")

        # Try to parse JSON array
        topics = []
        try:
            # Find JSON array in output
            match = re.search(r'\[[\s\S]*\]', output_text)
            if match:
                topics = json.loads(match.group())
        except json.JSONDecodeError:
            self._debug_print("TOPIC_TREE_PARSE_ERROR", "Could not parse JSON")

        if topics:
            # Store topics in SQLite
            for t in topics:
                topic = Topic(
                    topic_id=t.get("topic_id", f"{subject}:{t.get('name', 'unknown')}"),
                    subject=subject,
                    name=t.get("name", "Unknown"),
                    parent_topic_id=t.get("parent_topic_id"),
                    description=t.get("description", ""),
                    difficulty=t.get("difficulty", 1),
                    prerequisites=t.get("prerequisites", []),
                    task_type=t.get("task_type", "conceptual"),
                )
                store.create_topic(topic)

            context["topic_tree"] = topics
            self._debug_print("STORED_TOPIC_TREE", len(topics))
        else:
            context["topic_tree"] = []

        return context

    def _use_default_topic(self, context: dict) -> dict:
        """Use the input topic directly without a tree."""
        topic = context.get("topic", "")
        context["selected_topic"] = {
            "name": topic,
            "task_type": context.get("task_type", "conceptual"),
            "difficulty": context.get("learner_level", 1),
        }
        if not context.get("task_type"):
            context["task_type"] = "conceptual"
        return context

    def _select_topic(self, context: dict) -> dict:
        """Select a topic from the tree or use provided topic."""
        topic = context.get("topic", "")
        topic_tree = context.get("topic_tree", [])

        # If topic already specified, find it in tree or use as-is
        if topic:
            for t in topic_tree:
                if t.get("name", "").lower() == topic.lower():
                    context["selected_topic"] = t
                    context["topic"] = t.get("name", topic)
                    if not context.get("task_type"):
                        context["task_type"] = t.get("task_type", "conceptual")
                    return context

            # Topic not in tree, use as-is
            context["selected_topic"] = {"name": topic}
            if not context.get("task_type"):
                context["task_type"] = "conceptual"
            return context

        # No topic specified - let user select
        if topic_tree:
            print(f"\n{'='*70}")
            print("Available topics:")
            print(f"{'='*70}")

            for i, t in enumerate(topic_tree, 1):
                diff_stars = "*" * t.get("difficulty", 1)
                task_marker = "[P]" if t.get("task_type") == "procedural" else "[C]"
                print(f"  {i}. {t.get('name', 'Unknown')} {task_marker} {diff_stars}")
                if t.get("description"):
                    print(f"     {t['description'][:60]}...")

            print(f"\nSelect topic (1-{len(topic_tree)}): ", end="", flush=True)

            try:
                selection = input().strip()
                idx = int(selection) - 1
                if 0 <= idx < len(topic_tree):
                    selected = topic_tree[idx]
                    context["selected_topic"] = selected
                    context["topic"] = selected.get("name", "")
                    if not context.get("task_type"):
                        context["task_type"] = selected.get("task_type", "conceptual")
            except (ValueError, EOFError):
                # Default to first topic
                if topic_tree:
                    context["selected_topic"] = topic_tree[0]
                    context["topic"] = topic_tree[0].get("name", "")

        return context

    def _check_auto_difficulty(self, context: dict) -> dict:
        """Set difficulty automatically based on history if not specified."""
        if context.get("learner_level", 0) > 0:
            return context  # Already specified

        store = self._get_store(context)
        subject = context.get("subject", "") or context.get("topic", "")

        recommended = store.get_recommended_difficulty(subject)
        context["learner_level"] = recommended

        self._debug_print("AUTO_DIFFICULTY", recommended)
        return context

    # ==================== RUBRIC ====================

    def _skip_rubric(self, context: dict) -> dict:
        """Skip rubric generation (error fallback)."""
        context["rubric"] = ""
        return context

    def _show_session_info(self, context: dict) -> dict:
        """Show session info before starting."""
        store = self._get_store(context)
        topic = context.get("topic", "")
        subject = context.get("subject", "") or topic

        # Show past sessions
        past_sessions = store.list_sessions(topic=topic, limit=5)

        print(f"\n{'='*70}")
        print(f"Subject: {subject}")
        print(f"Topic: {topic}")
        print(f"Type: {context.get('task_type', 'conceptual')}")
        print(f"Difficulty: {'*' * context.get('learner_level', 1)} (Level {context.get('learner_level', 1)}/5)")

        if past_sessions:
            print(f"\nPrevious sessions: {len(past_sessions)}")
            for s in past_sessions[:3]:
                print(f"  - {s.mastery_score:.1%} mastery ({s.termination_reason})")

        print(f"{'='*70}")
        print("\nCommands: /quit to save and exit | Ctrl+D for hard exit")
        print("Starting session...\n")

        # Create session in SQLite
        session = Session(
            session_id=context["session_id"],
            topic=topic,
            subject=subject,
            learner_level=context.get("learner_level", 1),
            task_type=context.get("task_type", "conceptual"),
            status="active",
            mastery_score=0.0,
            rubric=context.get("rubric", ""),
        )
        store.create_session(session)

        return context

    # ==================== MAIN LOOP ====================

    def _collect_learner_response(self, context: dict) -> dict:
        """Collect learner response from stdin."""
        question = context.get("question", "")
        print(f"\nQuestion: {question}")
        if context.get("follow_up_prompt"):
            print(f"Hint: {context['follow_up_prompt']}")
        print("\nYour response (or /quit to save & exit): ", end="", flush=True)

        try:
            response = input().strip()

            # Check for quit command
            if response.lower() in ("/quit", "/q", "/exit"):
                context["user_quit"] = True
                context["learner_response"] = ""
                return context

            if not response:
                print("No response provided. Please try again.")
                return context

            # Add to history
            context.setdefault("question_history", []).append(question)
            context.setdefault("response_history", []).append(response)
            context["learner_response"] = response

        except EOFError:
            context["learner_response"] = ""
            context["user_quit"] = True
            context["termination_reason"] = "input_eof"

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
            match = re.search(r'([^.!?\n]*\?)', output_text)
            if match:
                question = match.group(1).strip()
            else:
                question = output_text.strip().split('\n')[0] if output_text.strip() else "What do you think about this topic?"

        context["question"] = question
        context["follow_up_prompt"] = hint

        if not context.get("first_question"):
            context["first_question"] = question

        self._debug_print("PARSED_QUESTION", {"question": question, "hint": hint})
        return context

    def _parse_extraction(self, context: dict) -> dict:
        """Parse extraction output from JSON extractor machine."""
        extractor_output = context.get("_extractor_output", {})

        self._debug_print("EXTRACTOR_OUTPUT", extractor_output)

        extracted = extractor_output.get("extracted", {})

        # Map extracted values to context
        context["evaluation_score"] = float(extracted.get("score", 0.5))
        context["evaluation_depth"] = extracted.get("depth", "partial")
        context["evaluation_gaps"] = extracted.get("gaps", [])
        context["evaluation_strengths"] = extracted.get("strengths", [])

        # Ensure valid depth
        if context["evaluation_depth"] not in ("surface", "partial", "deep"):
            context["evaluation_depth"] = "partial"

        # Ensure score in range
        context["evaluation_score"] = max(0.0, min(1.0, context["evaluation_score"]))

        self._debug_print("PARSED_EXTRACTION", {
            "score": context["evaluation_score"],
            "depth": context["evaluation_depth"],
            "gaps": context["evaluation_gaps"],
            "strengths": context["evaluation_strengths"]
        })

        return context

    def _fallback_evaluation(self, context: dict) -> dict:
        """Fallback when extraction fails - parse verbose critique directly."""
        critique = context.get("verbose_critique", "")

        self._debug_print("FALLBACK_EVALUATION", "Extraction failed, using heuristics")

        # Default values
        context["evaluation_score"] = 0.5
        context["evaluation_depth"] = "partial"
        context["evaluation_gaps"] = []
        context["evaluation_strengths"] = []

        critique_lower = critique.lower()

        # Heuristic score detection
        if any(w in critique_lower for w in ["excellent", "perfect", "complete", "thorough"]):
            context["evaluation_score"] = 0.9
            context["evaluation_depth"] = "deep"
        elif any(w in critique_lower for w in ["good", "solid", "correct", "right"]):
            context["evaluation_score"] = 0.75
            context["evaluation_depth"] = "partial"
        elif any(w in critique_lower for w in ["partial", "incomplete", "some"]):
            context["evaluation_score"] = 0.5
            context["evaluation_depth"] = "partial"
        elif any(w in critique_lower for w in ["wrong", "incorrect", "missed", "lacking"]):
            context["evaluation_score"] = 0.3
            context["evaluation_depth"] = "surface"

        # Pass/fail detection
        if "pass" in critique_lower and "fail" not in critique_lower:
            context["evaluation_score"] = max(context["evaluation_score"], 0.7)
        elif "fail" in critique_lower:
            context["evaluation_score"] = min(context["evaluation_score"], 0.5)

        return context

    def _parse_feedback(self, context: dict) -> dict:
        """Parse feedback agent output (plain text)."""
        output_obj = context.get("_agent_output", {})
        output_text = output_obj.get("content", "") if isinstance(output_obj, dict) else str(output_obj)

        self._debug_print("FEEDBACK_RAW", output_text)

        context["feedback"] = output_text.strip()
        context["feedback_type"] = "hint"

        if context["feedback"]:
            print(f"\nFeedback: {context['feedback']}")
            print(f"[Score: {context['evaluation_score']:.1%} | Depth: {context['evaluation_depth']}]")

        return context

    # ==================== CHECKPOINT & MASTERY ====================

    def _checkpoint_round(self, context: dict) -> dict:
        """Checkpoint current round to SQLite."""
        store = self._get_store(context)
        session_id = context.get("session_id", "")

        if not session_id:
            return context

        round_data = SessionRound(
            round_num=context.get("round_count", 0) + 1,
            question=context.get("question", ""),
            response=context.get("learner_response", ""),
            score=context.get("evaluation_score", 0.0),
            depth=context.get("evaluation_depth", "partial"),
            gaps=context.get("evaluation_gaps", []),
            strengths=context.get("evaluation_strengths", []),
            critique=context.get("verbose_critique", ""),
        )

        store.add_round(session_id, round_data)

        # Update session with context snapshot
        session = store.get_session(session_id)
        if session:
            # Snapshot context for resume
            snapshot_keys = [
                "topic", "subject", "learner_level", "task_type", "rubric",
                "mastery_score", "identified_gaps", "strengths", "round_count",
                "question_history", "response_history", "evaluation_history",
                "first_question"
            ]
            session.context_snapshot = {k: context.get(k) for k in snapshot_keys}
            session.mastery_score = context.get("mastery_score", 0.0)
            session.identified_gaps = context.get("identified_gaps", [])
            session.strengths = context.get("strengths", [])
            store.update_session(session)

        self._debug_print("CHECKPOINT_ROUND", round_data.round_num)
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

        return context

    # ==================== TERMINATION ====================

    def _handle_user_quit(self, context: dict) -> dict:
        """Handle graceful user quit - save session as suspended."""
        store = self._get_store(context)
        session_id = context.get("session_id", "")

        context["termination_reason"] = "user_quit"

        if session_id:
            session = store.get_session(session_id)
            if session:
                session.status = "suspended"
                session.termination_reason = "user_quit"
                store.update_session(session)

        print(f"\n{'='*70}")
        print("Session saved! You can resume later with the same topic.")
        print(f"Progress: {context.get('mastery_score', 0):.1%} mastery after {context.get('round_count', 0)} rounds")
        print(f"{'='*70}\n")

        self._update_transcript(context)
        return context

    def _complete_session(self, context: dict) -> dict:
        """Complete session - mark as finished and update progress."""
        store = self._get_store(context)
        session_id = context.get("session_id", "")

        if session_id:
            session = store.get_session(session_id)
            if session:
                session.status = "completed"
                session.termination_reason = context.get("termination_reason", "completed")
                session.mastery_score = context.get("mastery_score", 0.0)
                session.identified_gaps = context.get("identified_gaps", [])
                session.strengths = context.get("strengths", [])
                store.update_session(session)

                # Update progress tracking
                store.update_progress(session)

        reason = context.get("termination_reason", "")
        mastery = context.get("mastery_score", 0.0)

        print(f"\n{'='*70}")
        if reason == "mastery":
            print(f"Congratulations! You've achieved mastery ({mastery:.1%})!")
        else:
            print(f"Session complete. Final mastery: {mastery:.1%}")

        if context.get("strengths"):
            print(f"Strengths: {', '.join(context['strengths'][:5])}")
        if context.get("identified_gaps"):
            print(f"Areas to work on: {', '.join(context['identified_gaps'][:5])}")
        print(f"Rounds completed: {context.get('round_count', 0)}")
        print(f"{'='*70}\n")

        self._update_transcript(context)
        return context

    def _update_transcript(self, context: dict) -> None:
        """Build formatted session transcript and wrap in file_writer format."""
        lines = []

        # Header
        topic = context.get("topic", "Unknown Topic")
        subject = context.get("subject", "") or topic
        lines.append(f"# Socratic Learning Session: {topic}")
        lines.append(f"Subject: {subject}")
        lines.append(f"Session ID: {context.get('session_id', 'unknown')}")
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append(f"Task Type: {context.get('task_type', 'conceptual')}")
        lines.append(f"Difficulty: Level {context.get('learner_level', 1)}/5")
        lines.append("")

        # Rubric if present
        if context.get("rubric"):
            lines.append("## Evaluation Rubric")
            lines.append(context["rubric"])
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
                lines.append(f"**Score:** {eval_data.get('score', 0.0):.2f}/1.0")
                lines.append(f"**Depth:** {eval_data.get('depth', 'unknown')}")
                if eval_data.get("identified_gaps"):
                    lines.append(f"**Gaps:** {', '.join(eval_data['identified_gaps'])}")
                if eval_data.get("correct_elements"):
                    lines.append(f"**Strengths:** {', '.join(eval_data['correct_elements'])}")
            lines.append("")

        # Summary
        mastery = context.get("mastery_score", 0.0)
        identified_gaps = context.get("identified_gaps", [])
        strengths = context.get("strengths", [])

        lines.append("## Summary")
        lines.append(f"**Final Mastery Score:** {mastery:.2f}/1.0")
        lines.append(f"**Identified Gaps:** {', '.join(identified_gaps) if identified_gaps else 'None'}")
        lines.append(f"**Strengths:** {', '.join(strengths) if strengths else 'None'}")
        round_count = context.get("round_count", 0)
        max_rounds = context.get("max_rounds", 10)
        lines.append(f"**Rounds:** {round_count}/{max_rounds}")

        termination_reason = context.get("termination_reason", "")
        if termination_reason:
            lines.append(f"**Termination Reason:** {termination_reason}")

        markdown_content = "\n".join(lines)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_slug = topic.replace(" ", "_").replace("/", "-").replace("\\", "-")[:50]
        filename = f"socratic_session_{topic_slug}_{timestamp}.md"

        # Wrap in SEARCH/REPLACE format for file_writer
        context["session_transcript"] = f"""```markdown
{filename}
<<<<<<< SEARCH

=======
{markdown_content}
>>>>>>> REPLACE
```"""

    # ==================== LEGACY METHODS ====================

    def _init_session(self, context: dict) -> dict:
        """Initialize session from input (legacy)."""
        input_data = context.get("_input", {})
        context["topic"] = input_data.get("topic", context.get("topic", ""))
        context["learner_level"] = int(input_data.get("learner_level", context.get("learner_level", 1)))
        context["max_rounds"] = int(input_data.get("max_rounds", context.get("max_rounds", 10)))
        context["working_dir"] = input_data.get("working_dir", context.get("working_dir", "."))
        return context

    def _show_past_sessions(self, context: dict) -> dict:
        """Load and display past sessions for this topic (legacy)."""
        store = self._get_store(context)
        topic = context.get("topic", "")
        past_sessions = store.list_sessions(topic=topic, limit=10)

        if not past_sessions:
            print(f"\n{'='*70}")
            print(f"Topic: {topic}")
            print(f"No previous sessions found. Starting fresh!")
            print(f"{'='*70}\n")
            return context

        print(f"\n{'='*70}")
        print(f"Topic: {topic}")
        print(f"Found {len(past_sessions)} previous session(s):")
        print(f"{'='*70}\n")

        for i, session in enumerate(past_sessions[:5], 1):
            date_str = session.created_at[:16].replace("T", " ") if session.created_at else "unknown"
            mastery = session.mastery_score
            reason = session.termination_reason or "unknown"
            status = session.status

            print(f"Session {i}: {date_str} [{status}]")
            print(f"  Mastery: {mastery:.2f}/1.0 | Ended: {reason}")
            if session.identified_gaps:
                gaps_str = ", ".join(session.identified_gaps[:3])
                print(f"  Gaps: {gaps_str}")
            print()

        print(f"{'='*70}\n")
        return context

    def _parse_evaluation(self, context: dict) -> dict:
        """Parse evaluation agent output (legacy - plain text format)."""
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
                context["evaluation_gaps"] = [
                    g.strip() for g in value.split(",")
                    if g.strip() and g.strip().lower() not in ["none", "n/a"]
                ]
            elif key == "STRENGTHS":
                context["evaluation_strengths"] = [
                    s.strip() for s in value.split(",")
                    if s.strip() and s.strip().lower() not in ["none", "n/a"]
                ]

        self._debug_print("PARSED_EVALUATION", {
            "score": context["evaluation_score"],
            "depth": context["evaluation_depth"],
            "gaps": context["evaluation_gaps"],
            "strengths": context["evaluation_strengths"]
        })

        return context
