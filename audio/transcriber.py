"""
Speech-to-text transcription using faster-whisper.

Runs the Whisper model locally (no API cost).
Supports Japanese and English (auto-detect or explicit lang setting).
"""

import numpy as np
from faster_whisper import WhisperModel

from config import WHISPER_MODEL, WHISPER_LANGUAGE, SAMPLE_RATE


class Transcriber:
    def __init__(self):
        # device="cpu" works everywhere; use "cuda" if GPU is available
        self._model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribe audio array (float32, mono, SAMPLE_RATE).

        Returns the transcribed text, or empty string if nothing detected.
        """
        segments, _info = self._model.transcribe(
            audio,
            language=WHISPER_LANGUAGE or None,
            beam_size=5,
            vad_filter=False,  # VAD already applied upstream
        )
        parts = [seg.text.strip() for seg in segments]
        return " ".join(parts).strip()
