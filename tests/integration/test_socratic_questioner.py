import asyncio

import pytest
from flatagents.baseagent import AgentResponse

from socratic_teacher.main import run


@pytest.mark.integration
def test_socratic_questioner_integration(tmp_path, monkeypatch):
    question_text = "What makes a system distributed?"
    hint_text = "Think about nodes and coordination."

    monkeypatch.setattr(
        "builtins.input",
        lambda *args, **kwargs: "Multiple computers working together.",
    )

    async def fake_call(self, tool_provider=None, messages=None, **input_data):
        if self.agent_name == "question_generator":
            return AgentResponse(content=f"QUESTION: {question_text}\nHINT: {hint_text}")
        if self.agent_name == "response_evaluator":
            return AgentResponse(
                content="SCORE: 0.9\nDEPTH: deep\nGAPS: consistency\nSTRENGTHS: scalability"
            )
        if self.agent_name == "feedback_provider":
            return AgentResponse(content="Good. Now consider consistency trade-offs.")
        raise AssertionError(f"Unexpected agent: {self.agent_name}")

    monkeypatch.setattr("flatagents.flatagent.FlatAgent.call", fake_call)

    result = asyncio.run(
        run(
            topic="distributed systems",
            level=2,
            max_rounds=1,
            working_dir=str(tmp_path),
            cwd=str(tmp_path),
        )
    )

    assert result["learning_transcript"] == [question_text]
    assert result["rounds_completed"] == 1
    assert result["termination_reason"] in ("mastery", "max_rounds")

    session_files = list(tmp_path.glob("socratic_session_*.md"))
    assert session_files
    assert question_text in session_files[0].read_text()
