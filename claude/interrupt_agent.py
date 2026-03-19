"""
Interrupt agent: decides whether Claude should speak and generates the response.

Sends the current conversation history to Claude with a structured prompt
asking it to return JSON: {"should_speak": bool, "message": str}.
"""

import json
import time
import anthropic

from config import CLAUDE_MODEL, ANTHROPIC_API_KEY, INTERRUPT_COOLDOWN_SEC, LONG_SILENCE_TRIGGER_SEC
from claude.conversation import ConversationHistory

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_INTERRUPT_SYSTEM = """あなたは会議に参加しているAIアシスタント「Claude」です。
以下の会議の会話を読み、あなたが今発言すべきかどうかを判断してください。

発言すべき状況:
- 参加者から質問が向けられた
- 議論が行き詰まっている / 同じ話が繰り返されている
- 重要な情報・視点を補足できる
- 長時間（3分以上）誰も発言していない

発言すべきでない状況:
- 議論が活発に進んでいる
- 直前にあなたが発言した（クールダウン中）
- 発言しても議論に価値を加えられない

必ず以下のJSON形式のみで返答してください（他のテキストは含めない）:
{"should_speak": true, "message": "発言内容（2〜3文）"}
または
{"should_speak": false, "message": ""}
"""


class InterruptAgent:
    def __init__(self, history: ConversationHistory):
        self._history = history
        self._last_spoke_at: float = 0.0
        self._last_utterance_at: float = time.monotonic()

    def record_utterance(self) -> None:
        """Call this whenever any participant speaks."""
        self._last_utterance_at = time.monotonic()

    def evaluate(self, force: bool = False) -> tuple[bool, str]:
        """
        Ask Claude whether to speak.

        Returns (should_speak, message).
        If force=True, skip cooldown check.
        """
        now = time.monotonic()

        # Respect cooldown between Claude's own utterances
        if not force and (now - self._last_spoke_at) < INTERRUPT_COOLDOWN_SEC:
            return False, ""

        messages = self._history.to_messages()
        if not messages:
            # Nothing to respond to yet
            silence_sec = now - self._last_utterance_at
            if silence_sec < LONG_SILENCE_TRIGGER_SEC:
                return False, ""

        try:
            response = _client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=256,
                system=_INTERRUPT_SYSTEM,
                messages=messages or [{"role": "user", "content": "会議が始まりました。挨拶をしてください。"}],
            )
            raw = response.content[0].text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            should_speak: bool = bool(data.get("should_speak", False))
            message: str = data.get("message", "").strip()
        except Exception as e:
            print(f"[InterruptAgent] Error: {e}")
            return False, ""

        if should_speak and message:
            self._last_spoke_at = now
            self._history.add_assistant(message)
        return should_speak, message
