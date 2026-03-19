import os

# Anthropic
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"

# Teams
TEAMS_EMAIL = os.environ.get("TEAMS_EMAIL", "")
TEAMS_PASSWORD = os.environ.get("TEAMS_PASSWORD", "")
TEAMS_MEETING_URL = os.environ.get("TEAMS_MEETING_URL", "")
BOT_DISPLAY_NAME = os.environ.get("BOT_DISPLAY_NAME", "Claude AI")

# Audio
SAMPLE_RATE = 16000
CHUNK_DURATION_MS = 30  # VAD chunk size in ms
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)
SILENCE_THRESHOLD_SEC = 1.5  # seconds of silence to mark end of utterance
CAPTURE_DEVICE = os.environ.get("CAPTURE_DEVICE", "BlackHole 2ch")  # macOS: BlackHole virtual audio device
PLAYBACK_DEVICE = os.environ.get("PLAYBACK_DEVICE", "BlackHole 2ch")  # macOS: BlackHole virtual audio device

# STT
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")
WHISPER_LANGUAGE = os.environ.get("WHISPER_LANGUAGE", "ja")  # None = auto detect

# TTS
TTS_VOICE = os.environ.get("TTS_VOICE", "ja-JP-NanamiNeural")
TTS_RATE = os.environ.get("TTS_RATE", "+0%")
TTS_OUTPUT_DIR = "/tmp/tts_output"

# Claude behaviour
MAX_CONVERSATION_TURNS = 30          # keep last N turns in memory
INTERRUPT_COOLDOWN_SEC = 30.0        # min seconds between Claude's utterances
LONG_SILENCE_TRIGGER_SEC = 180.0     # Claude speaks if no one has talked for this long
SYSTEM_PROMPT = """あなたは会議に参加しているAIアシスタント「Claude」です。
- 他の参加者と自然に会話し、議論に有益な意見・提案・補足情報を提供してください。
- 質問には的確に答え、行き詰まっている議論には新しい視点を提示してください。
- 発言は簡潔に（2〜3文程度）まとめてください。
- 会議の終了時には、議論の要約・決定事項・アクションアイテム・今後のアクションを提示します。
"""

# API server
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))
