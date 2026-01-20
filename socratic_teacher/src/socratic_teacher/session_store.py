"""Session metadata storage for Socratic teacher sessions."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Protocol


class SessionStore(Protocol):
    """Protocol for session storage backends (swappable with SQLite later)."""

    def save(self, session: Dict) -> None:
        """Save a session record."""
        ...

    def get(self, session_id: str) -> Optional[Dict]:
        """Retrieve a specific session by ID."""
        ...

    def list(self, topic: Optional[str] = None) -> List[Dict]:
        """List all sessions, optionally filtered by topic."""
        ...

    def get_latest(self, topic: str) -> Optional[Dict]:
        """Get the most recent session for a topic."""
        ...


class JSONLSessionStore:
    """Append-only JSONL file storage for session metadata."""

    def __init__(self, filepath: str = ".socratic_sessions.jsonl"):
        self.filepath = Path(filepath)

    def save(self, session: Dict) -> None:
        """Append session metadata as a single JSON line."""
        # Ensure parent directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(self.filepath, "a") as f:
            f.write(json.dumps(session) + "\n")

    def get(self, session_id: str) -> Optional[Dict]:
        """Find session by ID (linear scan)."""
        if not self.filepath.exists():
            return None

        with open(self.filepath) as f:
            for line in f:
                if line.strip():
                    session = json.loads(line)
                    if session.get("session_id") == session_id:
                        return session
        return None

    def list(self, topic: Optional[str] = None) -> List[Dict]:
        """List all sessions, optionally filtered by topic."""
        if not self.filepath.exists():
            return []

        sessions = []
        with open(self.filepath) as f:
            for line in f:
                if line.strip():
                    session = json.loads(line)
                    if topic is None or session.get("topic") == topic:
                        sessions.append(session)

        # Sort by timestamp descending (most recent first)
        return sorted(sessions, key=lambda s: s.get("timestamp", ""), reverse=True)

    def get_latest(self, topic: str) -> Optional[Dict]:
        """Get the most recent session for a topic."""
        sessions = self.list(topic)
        return sessions[0] if sessions else None
