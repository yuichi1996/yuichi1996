"""
Entry point for the Teams Claude bot.

Orchestrates:
  - Audio capture + VAD + STT pipeline (background thread)
  - Interrupt evaluation + TTS playback (triggered after each utterance)
  - FastAPI control server (background thread)
  - Teams web automation via Playwright
"""

import asyncio
import signal
import threading
import time

import uvicorn

import config
from audio.capture import AudioCapture
from audio.vad import SileroVAD
from audio.transcriber import Transcriber
from audio.virtual_audio import print_setup_guide
from bot.teams_bot import TeamsBot
from claude.conversation import ConversationHistory
from claude.interrupt_agent import InterruptAgent
from claude.summarizer import generate_summary
from tts.tts_engine import TTSEngine
from api.control_api import app as fastapi_app, set_bot


class MeetingClaude:
    def __init__(self):
        self._history = ConversationHistory()
        self._interrupt = InterruptAgent(self._history)
        self._tts = TTSEngine()
        self._transcriber = Transcriber()
        self._vad = SileroVAD()
        self._teams = TeamsBot()
        self._capture = AudioCapture()

        self.in_meeting = False
        self._running = False
        self._audio_thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public API (used by control_api.py)
    # ------------------------------------------------------------------

    async def join(self, meeting_url: str = config.TEAMS_MEETING_URL) -> None:
        await self._teams.start(meeting_url)
        self.in_meeting = True
        self._running = True
        self._audio_thread = threading.Thread(target=self._audio_loop, daemon=True)
        self._audio_thread.start()
        print("[MeetingClaude] Audio pipeline started.")

    async def leave(self) -> str:
        self._running = False
        await self._teams.leave_meeting()
        self.in_meeting = False

        # Flush any remaining buffered audio
        remaining = self._vad.flush()
        if remaining is not None:
            text = self._transcriber.transcribe(remaining)
            if text:
                self._history.add_utterance("参加者", text)

        summary = generate_summary(self._history)

        # Post summary to Teams chat
        await self._teams.send_chat_message("📋 **会議サマリー**\n\n" + summary)
        print("\n=== 会議サマリー ===\n" + summary)

        await self._teams.stop()
        self._capture.stop()
        return summary

    async def speak(self, message: str) -> None:
        """Manually trigger Claude to speak."""
        if not message.strip():
            return
        audio_ctrl = self._teams.audio
        if audio_ctrl:
            await audio_ctrl.ensure_unmuted()
        self._tts.speak(message)
        if audio_ctrl:
            await audio_ctrl.ensure_muted()
        self._history.add_assistant(message)

    def get_transcript(self) -> str:
        return self._history.full_transcript()

    # ------------------------------------------------------------------
    # Internal audio pipeline (runs in background thread)
    # ------------------------------------------------------------------

    def _audio_loop(self) -> None:
        self._capture.start()
        print("[MeetingClaude] Listening...")
        while self._running:
            chunk = self._capture.read_chunk(timeout=0.5)
            if chunk is None:
                continue

            utterance = self._vad.process_chunk(chunk)
            if utterance is None:
                continue

            # Transcribe
            text = self._transcriber.transcribe(utterance)
            if not text:
                continue

            print(f"[STT] {text}")
            self._history.add_utterance("参加者", text)
            self._interrupt.record_utterance()

            # Evaluate whether Claude should respond
            should_speak, message = self._interrupt.evaluate()
            if should_speak and message:
                # Run speak coroutine from this sync thread
                asyncio.run_coroutine_threadsafe(
                    self.speak(message),
                    self._event_loop,
                ).result(timeout=30)

        self._capture.stop()

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> None:
        self._event_loop = asyncio.new_event_loop()

        # Start FastAPI in a background thread
        def _run_api():
            uvicorn.run(
                fastapi_app,
                host=config.API_HOST,
                port=config.API_PORT,
                log_level="warning",
            )

        api_thread = threading.Thread(target=_run_api, daemon=True)
        api_thread.start()
        print(f"[MeetingClaude] API server running at http://{config.API_HOST}:{config.API_PORT}")

        set_bot(self)

        # Join meeting if URL provided via environment
        if config.TEAMS_MEETING_URL:
            self._event_loop.run_until_complete(self.join(config.TEAMS_MEETING_URL))

        try:
            self._event_loop.run_forever()
        except KeyboardInterrupt:
            print("\n[MeetingClaude] Shutting down...")
            if self.in_meeting:
                self._event_loop.run_until_complete(self.leave())
        finally:
            self._event_loop.close()


if __name__ == "__main__":
    print_setup_guide()
    bot = MeetingClaude()
    bot.run()
