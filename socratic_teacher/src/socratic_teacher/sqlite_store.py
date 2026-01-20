"""SQLite-backed storage for Socratic teacher sessions.

Schema:
- sessions: Main session metadata
- session_rounds: Individual Q&A rounds for checkpoint/resume
- topics: Topic tree storage (subject -> topics hierarchy)
- topic_progress: User progress per topic for auto-difficulty
"""

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SessionRound:
    """A single round of Q&A in a session."""
    round_num: int
    question: str
    response: str
    score: float
    depth: str
    gaps: List[str]
    strengths: List[str]
    critique: str = ""  # Verbose scorer output
    timestamp: str = ""


@dataclass
class Session:
    """Complete session data."""
    session_id: str
    topic: str
    subject: str  # Parent subject for topic tree
    learner_level: int
    task_type: str  # 'procedural' or 'conceptual'
    status: str  # 'active', 'completed', 'suspended'
    mastery_score: float
    rounds: List[SessionRound] = field(default_factory=list)
    identified_gaps: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    rubric: str = ""  # Generated rubric for evaluation
    termination_reason: str = ""
    created_at: str = ""
    updated_at: str = ""
    context_snapshot: Dict[str, Any] = field(default_factory=dict)  # For resume


@dataclass
class Topic:
    """A topic in the topic tree."""
    topic_id: str
    subject: str
    name: str
    parent_topic_id: Optional[str]
    description: str
    difficulty: int  # 1-5
    prerequisites: List[str] = field(default_factory=list)
    task_type: str = "conceptual"  # 'procedural' or 'conceptual'


@dataclass
class TopicProgress:
    """User progress on a specific topic."""
    topic_id: str
    sessions_completed: int
    best_mastery_score: float
    avg_mastery_score: float
    total_rounds: int
    last_session_id: str
    last_practiced: str


class SQLiteSessionStore:
    """SQLite storage backend for sessions, topics, and progress."""

    def __init__(self, db_path: str = ".socratic_teacher.db"):
        self.db_path = Path(db_path)
        self._init_db()

    @contextmanager
    def _connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connection() as conn:
            conn.executescript("""
                -- Sessions table: main session metadata
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    subject TEXT DEFAULT '',
                    learner_level INTEGER DEFAULT 1,
                    task_type TEXT DEFAULT 'conceptual',
                    status TEXT DEFAULT 'active',
                    mastery_score REAL DEFAULT 0.0,
                    identified_gaps TEXT DEFAULT '[]',
                    strengths TEXT DEFAULT '[]',
                    rubric TEXT DEFAULT '',
                    termination_reason TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    context_snapshot TEXT DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_topic ON sessions(topic);
                CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
                CREATE INDEX IF NOT EXISTS idx_sessions_subject ON sessions(subject);

                -- Session rounds: individual Q&A for checkpoint/resume
                CREATE TABLE IF NOT EXISTS session_rounds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    round_num INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    response TEXT DEFAULT '',
                    score REAL DEFAULT 0.0,
                    depth TEXT DEFAULT 'partial',
                    gaps TEXT DEFAULT '[]',
                    strengths TEXT DEFAULT '[]',
                    critique TEXT DEFAULT '',
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    UNIQUE(session_id, round_num)
                );

                CREATE INDEX IF NOT EXISTS idx_rounds_session ON session_rounds(session_id);

                -- Topics table: topic tree hierarchy
                CREATE TABLE IF NOT EXISTS topics (
                    topic_id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    name TEXT NOT NULL,
                    parent_topic_id TEXT,
                    description TEXT DEFAULT '',
                    difficulty INTEGER DEFAULT 1,
                    prerequisites TEXT DEFAULT '[]',
                    task_type TEXT DEFAULT 'conceptual',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (parent_topic_id) REFERENCES topics(topic_id)
                );

                CREATE INDEX IF NOT EXISTS idx_topics_subject ON topics(subject);
                CREATE INDEX IF NOT EXISTS idx_topics_parent ON topics(parent_topic_id);

                -- Topic progress: user progress per topic
                CREATE TABLE IF NOT EXISTS topic_progress (
                    topic_id TEXT PRIMARY KEY,
                    sessions_completed INTEGER DEFAULT 0,
                    best_mastery_score REAL DEFAULT 0.0,
                    avg_mastery_score REAL DEFAULT 0.0,
                    total_rounds INTEGER DEFAULT 0,
                    last_session_id TEXT DEFAULT '',
                    last_practiced TEXT DEFAULT '',
                    FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
                );
            """)

    # ==================== SESSION METHODS ====================

    def create_session(self, session: Session) -> str:
        """Create a new session."""
        now = datetime.now().isoformat()
        session.created_at = now
        session.updated_at = now

        with self._connection() as conn:
            conn.execute("""
                INSERT INTO sessions (
                    session_id, topic, subject, learner_level, task_type,
                    status, mastery_score, identified_gaps, strengths,
                    rubric, termination_reason, created_at, updated_at,
                    context_snapshot
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id, session.topic, session.subject,
                session.learner_level, session.task_type, session.status,
                session.mastery_score, json.dumps(session.identified_gaps),
                json.dumps(session.strengths), session.rubric,
                session.termination_reason, session.created_at,
                session.updated_at, json.dumps(session.context_snapshot)
            ))
        return session.session_id

    def update_session(self, session: Session) -> None:
        """Update an existing session."""
        session.updated_at = datetime.now().isoformat()

        with self._connection() as conn:
            conn.execute("""
                UPDATE sessions SET
                    status = ?, mastery_score = ?, identified_gaps = ?,
                    strengths = ?, rubric = ?, termination_reason = ?,
                    updated_at = ?, context_snapshot = ?
                WHERE session_id = ?
            """, (
                session.status, session.mastery_score,
                json.dumps(session.identified_gaps), json.dumps(session.strengths),
                session.rubric, session.termination_reason, session.updated_at,
                json.dumps(session.context_snapshot), session.session_id
            ))

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID with all rounds."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()

            if not row:
                return None

            # Get rounds
            rounds_rows = conn.execute(
                "SELECT * FROM session_rounds WHERE session_id = ? ORDER BY round_num",
                (session_id,)
            ).fetchall()

            rounds = [
                SessionRound(
                    round_num=r["round_num"],
                    question=r["question"],
                    response=r["response"],
                    score=r["score"],
                    depth=r["depth"],
                    gaps=json.loads(r["gaps"]),
                    strengths=json.loads(r["strengths"]),
                    critique=r["critique"],
                    timestamp=r["timestamp"]
                )
                for r in rounds_rows
            ]

            return Session(
                session_id=row["session_id"],
                topic=row["topic"],
                subject=row["subject"],
                learner_level=row["learner_level"],
                task_type=row["task_type"],
                status=row["status"],
                mastery_score=row["mastery_score"],
                rounds=rounds,
                identified_gaps=json.loads(row["identified_gaps"]),
                strengths=json.loads(row["strengths"]),
                rubric=row["rubric"],
                termination_reason=row["termination_reason"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                context_snapshot=json.loads(row["context_snapshot"])
            )

    def list_sessions(
        self,
        topic: Optional[str] = None,
        subject: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Session]:
        """List sessions with optional filtering."""
        with self._connection() as conn:
            query = "SELECT * FROM sessions WHERE 1=1"
            params = []

            if topic:
                query += " AND topic = ?"
                params.append(topic)
            if subject:
                query += " AND subject = ?"
                params.append(subject)
            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            sessions = []
            for row in rows:
                sessions.append(Session(
                    session_id=row["session_id"],
                    topic=row["topic"],
                    subject=row["subject"],
                    learner_level=row["learner_level"],
                    task_type=row["task_type"],
                    status=row["status"],
                    mastery_score=row["mastery_score"],
                    identified_gaps=json.loads(row["identified_gaps"]),
                    strengths=json.loads(row["strengths"]),
                    rubric=row["rubric"],
                    termination_reason=row["termination_reason"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    context_snapshot=json.loads(row["context_snapshot"])
                ))
            return sessions

    def get_latest_session(self, topic: str) -> Optional[Session]:
        """Get the most recent session for a topic."""
        sessions = self.list_sessions(topic=topic, limit=1)
        return sessions[0] if sessions else None

    def get_active_session(self, topic: str) -> Optional[Session]:
        """Get active/suspended session for resume."""
        with self._connection() as conn:
            row = conn.execute("""
                SELECT * FROM sessions
                WHERE topic = ? AND status IN ('active', 'suspended')
                ORDER BY updated_at DESC LIMIT 1
            """, (topic,)).fetchone()

            if row:
                return self.get_session(row["session_id"])
        return None

    # ==================== ROUND METHODS ====================

    def add_round(self, session_id: str, round_data: SessionRound) -> None:
        """Add a round to a session (checkpoint)."""
        round_data.timestamp = datetime.now().isoformat()

        with self._connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO session_rounds (
                    session_id, round_num, question, response, score,
                    depth, gaps, strengths, critique, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, round_data.round_num, round_data.question,
                round_data.response, round_data.score, round_data.depth,
                json.dumps(round_data.gaps), json.dumps(round_data.strengths),
                round_data.critique, round_data.timestamp
            ))

    def get_rounds(self, session_id: str) -> List[SessionRound]:
        """Get all rounds for a session."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM session_rounds WHERE session_id = ? ORDER BY round_num",
                (session_id,)
            ).fetchall()

            return [
                SessionRound(
                    round_num=r["round_num"],
                    question=r["question"],
                    response=r["response"],
                    score=r["score"],
                    depth=r["depth"],
                    gaps=json.loads(r["gaps"]),
                    strengths=json.loads(r["strengths"]),
                    critique=r["critique"],
                    timestamp=r["timestamp"]
                )
                for r in rows
            ]

    # ==================== TOPIC METHODS ====================

    def create_topic(self, topic: Topic) -> str:
        """Create a new topic."""
        with self._connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO topics (
                    topic_id, subject, name, parent_topic_id, description,
                    difficulty, prerequisites, task_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                topic.topic_id, topic.subject, topic.name, topic.parent_topic_id,
                topic.description, topic.difficulty, json.dumps(topic.prerequisites),
                topic.task_type, datetime.now().isoformat()
            ))
        return topic.topic_id

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        """Get a topic by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM topics WHERE topic_id = ?",
                (topic_id,)
            ).fetchone()

            if not row:
                return None

            return Topic(
                topic_id=row["topic_id"],
                subject=row["subject"],
                name=row["name"],
                parent_topic_id=row["parent_topic_id"],
                description=row["description"],
                difficulty=row["difficulty"],
                prerequisites=json.loads(row["prerequisites"]),
                task_type=row["task_type"]
            )

    def get_topic_tree(self, subject: str) -> List[Topic]:
        """Get all topics for a subject."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM topics WHERE subject = ? ORDER BY difficulty, name",
                (subject,)
            ).fetchall()

            return [
                Topic(
                    topic_id=r["topic_id"],
                    subject=r["subject"],
                    name=r["name"],
                    parent_topic_id=r["parent_topic_id"],
                    description=r["description"],
                    difficulty=r["difficulty"],
                    prerequisites=json.loads(r["prerequisites"]),
                    task_type=r["task_type"]
                )
                for r in rows
            ]

    def has_topic_tree(self, subject: str) -> bool:
        """Check if a topic tree exists for a subject."""
        with self._connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM topics WHERE subject = ?",
                (subject,)
            ).fetchone()[0]
            return count > 0

    def find_topic_by_name(self, subject: str, name: str) -> Optional[Topic]:
        """Find a topic by name within a subject."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM topics WHERE subject = ? AND name = ?",
                (subject, name)
            ).fetchone()

            if row:
                return Topic(
                    topic_id=row["topic_id"],
                    subject=row["subject"],
                    name=row["name"],
                    parent_topic_id=row["parent_topic_id"],
                    description=row["description"],
                    difficulty=row["difficulty"],
                    prerequisites=json.loads(row["prerequisites"]),
                    task_type=row["task_type"]
                )
        return None

    # ==================== PROGRESS METHODS ====================

    def update_progress(self, session: Session) -> None:
        """Update progress after a session completes."""
        topic_id = f"{session.subject}:{session.topic}"

        with self._connection() as conn:
            # Get existing progress
            row = conn.execute(
                "SELECT * FROM topic_progress WHERE topic_id = ?",
                (topic_id,)
            ).fetchone()

            if row:
                # Update existing
                sessions_completed = row["sessions_completed"] + 1
                total_rounds = row["total_rounds"] + len(session.rounds)
                best_score = max(row["best_mastery_score"], session.mastery_score)
                # Recalculate average
                old_total = row["avg_mastery_score"] * row["sessions_completed"]
                avg_score = (old_total + session.mastery_score) / sessions_completed

                conn.execute("""
                    UPDATE topic_progress SET
                        sessions_completed = ?,
                        best_mastery_score = ?,
                        avg_mastery_score = ?,
                        total_rounds = ?,
                        last_session_id = ?,
                        last_practiced = ?
                    WHERE topic_id = ?
                """, (
                    sessions_completed, best_score, avg_score, total_rounds,
                    session.session_id, datetime.now().isoformat(), topic_id
                ))
            else:
                # Create new
                conn.execute("""
                    INSERT INTO topic_progress (
                        topic_id, sessions_completed, best_mastery_score,
                        avg_mastery_score, total_rounds, last_session_id,
                        last_practiced
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    topic_id, 1, session.mastery_score, session.mastery_score,
                    len(session.rounds), session.session_id,
                    datetime.now().isoformat()
                ))

    def get_progress(self, topic_id: str) -> Optional[TopicProgress]:
        """Get progress for a topic."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM topic_progress WHERE topic_id = ?",
                (topic_id,)
            ).fetchone()

            if not row:
                return None

            return TopicProgress(
                topic_id=row["topic_id"],
                sessions_completed=row["sessions_completed"],
                best_mastery_score=row["best_mastery_score"],
                avg_mastery_score=row["avg_mastery_score"],
                total_rounds=row["total_rounds"],
                last_session_id=row["last_session_id"],
                last_practiced=row["last_practiced"]
            )

    def get_recommended_difficulty(self, subject: str) -> int:
        """Get recommended difficulty based on user's progress in a subject."""
        with self._connection() as conn:
            # Get all progress for topics in this subject
            rows = conn.execute("""
                SELECT tp.*, t.difficulty
                FROM topic_progress tp
                JOIN topics t ON tp.topic_id = t.topic_id
                WHERE t.subject = ?
                ORDER BY tp.last_practiced DESC
                LIMIT 10
            """, (subject,)).fetchall()

            if not rows:
                return 1  # Start at beginner

            # Calculate weighted average based on recent mastery
            total_weight = 0
            weighted_sum = 0
            for i, row in enumerate(rows):
                weight = 1.0 / (i + 1)  # More recent = higher weight
                mastery = row["avg_mastery_score"]
                difficulty = row["difficulty"]

                # If mastery > 0.8, suggest next difficulty
                suggested = difficulty + 1 if mastery > 0.8 else difficulty
                suggested = max(1, min(5, suggested))

                weighted_sum += suggested * weight
                total_weight += weight

            return round(weighted_sum / total_weight) if total_weight > 0 else 1

    # ==================== CHECKPOINT/RESUME ====================

    def checkpoint_session(self, session: Session) -> None:
        """Save a full checkpoint of session state for resume."""
        session.status = "suspended"
        self.update_session(session)

    def resume_session(self, session_id: str) -> Optional[Session]:
        """Resume a suspended session."""
        session = self.get_session(session_id)
        if session and session.status == "suspended":
            session.status = "active"
            self.update_session(session)
            return session
        return session

    # ==================== LEGACY COMPAT ====================

    def save(self, session_data: Dict) -> None:
        """Legacy JSONL-compatible save method."""
        session_id = session_data.get("session_id", "")

        # Check if session exists
        existing = self.get_session(session_id)
        if existing:
            # Update
            existing.mastery_score = session_data.get("final_mastery_score", existing.mastery_score)
            existing.termination_reason = session_data.get("termination_reason", existing.termination_reason)
            existing.identified_gaps = session_data.get("identified_gaps", existing.identified_gaps)
            existing.strengths = session_data.get("strengths", existing.strengths)
            existing.status = "completed" if existing.termination_reason else "active"
            self.update_session(existing)
        else:
            # Create new
            session = Session(
                session_id=session_id,
                topic=session_data.get("topic", ""),
                subject=session_data.get("subject", ""),
                learner_level=session_data.get("learner_level", 1),
                task_type=session_data.get("task_type", "conceptual"),
                status="completed" if session_data.get("termination_reason") else "active",
                mastery_score=session_data.get("final_mastery_score", 0.0),
                identified_gaps=session_data.get("identified_gaps", []),
                strengths=session_data.get("strengths", []),
                termination_reason=session_data.get("termination_reason", "")
            )
            self.create_session(session)

    def get(self, session_id: str) -> Optional[Dict]:
        """Legacy JSONL-compatible get method."""
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "topic": session.topic,
            "timestamp": session.created_at,
            "final_mastery_score": session.mastery_score,
            "rounds_completed": len(session.rounds),
            "termination_reason": session.termination_reason,
            "identified_gaps": session.identified_gaps,
            "strengths": session.strengths,
            "first_question": session.rounds[0].question if session.rounds else ""
        }

    def list(self, topic: Optional[str] = None) -> List[Dict]:
        """Legacy JSONL-compatible list method."""
        sessions = self.list_sessions(topic=topic)
        return [
            {
                "session_id": s.session_id,
                "topic": s.topic,
                "timestamp": s.created_at,
                "final_mastery_score": s.mastery_score,
                "rounds_completed": len(s.rounds) if hasattr(s, 'rounds') else 0,
                "termination_reason": s.termination_reason,
                "identified_gaps": s.identified_gaps,
                "strengths": s.strengths,
                "first_question": ""
            }
            for s in sessions
        ]

    def get_latest(self, topic: str) -> Optional[Dict]:
        """Legacy JSONL-compatible get_latest method."""
        session = self.get_latest_session(topic)
        return self.get(session.session_id) if session else None
