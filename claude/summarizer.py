"""
Meeting summarizer: generates a structured summary at the end of a meeting.

Produces:
  - 会議の要約 (meeting summary)
  - 決定事項 (decisions)
  - アクションアイテム (action items with owners/deadlines)
  - 今後のアクション (follow-up actions)
"""

import anthropic

from config import CLAUDE_MODEL, ANTHROPIC_API_KEY
from claude.conversation import ConversationHistory

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SUMMARIZE_SYSTEM = """あなたは会議の議事録を作成するAIアシスタントです。
以下の会議の文字起こしを読み、日本語で構造化されたサマリーを作成してください。

以下の形式で出力してください:

## 会議の要約
（会議全体の概要を3〜5文で）

## 決定事項
- （箇条書き）

## アクションアイテム
| 担当者 | タスク | 期限 |
|--------|--------|------|
| ... | ... | ... |

## 今後のアクション
- （フォローアップ・次のステップ）
"""


def generate_summary(history: ConversationHistory) -> str:
    """
    Generate a structured meeting summary from the conversation history.

    Returns the summary as a Markdown string.
    """
    transcript = history.full_transcript()
    if not transcript.strip():
        return "（文字起こしデータがありません）"

    try:
        response = _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=_SUMMARIZE_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": f"以下の会議の文字起こしを要約してください:\n\n{transcript}",
                }
            ],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"要約の生成中にエラーが発生しました: {e}"
