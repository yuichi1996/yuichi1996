"""
Conversation history manager for the Anthropic Messages API.

Maintains a rolling window of the last MAX_CONVERSATION_TURNS turns
so we never exceed context limits.
"""

from dataclasses import dataclass, field
from typing import Literal

from config import MAX_CONVERSATION_TURNS, SYSTEM_PROMPT


@dataclass
class Turn:
    role: Literal["user", "assistant"]
    content: str


class ConversationHistory:
    def __init__(self):
        self._turns: list[Turn] = []

    def add_utterance(self, speaker: str, text: str) -> None:
        """Add a meeting participant's utterance as a user message."""
        self._turns.append(Turn(role="user", content=f"[{speaker}]: {text}"))
        self._trim()

    def add_assistant(self, text: str) -> None:
        """Record Claude's own utterance."""
        self._turns.append(Turn(role="assistant", content=text))
        self._trim()

    def _trim(self) -> None:
        if len(self._turns) > MAX_CONVERSATION_TURNS:
            self._turns = self._turns[-MAX_CONVERSATION_TURNS:]

    def to_messages(self) -> list[dict]:
        """Return messages list suitable for the Anthropic API."""
        return [{"role": t.role, "content": t.content} for t in self._turns]

    def full_transcript(self) -> str:
        """Return all turns as a plain-text transcript."""
        lines = []
        for t in self._turns:
            if t.role == "user":
                lines.append(t.content)
            else:
                lines.append(f"[Claude]: {t.content}")
        return "\n".join(lines)

    def system_prompt(self) -> str:
        return SYSTEM_PROMPT
