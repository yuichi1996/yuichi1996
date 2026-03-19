"""
Voice Activity Detection using Silero-VAD.

Accumulates 30 ms audio chunks and emits complete utterance segments
once a configurable silence period has elapsed.
"""

import time
import numpy as np
import torch

from config import SAMPLE_RATE, CHUNK_SAMPLES, SILENCE_THRESHOLD_SEC


class SileroVAD:
    def __init__(self):
        # Load Silero VAD model from torch hub (cached after first download)
        self._model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False,
        )
        self._model.eval()
        self._reset_state()

    def _reset_state(self) -> None:
        self._buffer: list[np.ndarray] = []
        self._in_speech = False
        self._silence_start: float | None = None

    def process_chunk(self, chunk: np.ndarray) -> np.ndarray | None:
        """
        Feed one audio chunk (CHUNK_SAMPLES @ SAMPLE_RATE).

        Returns a complete utterance as a numpy array when a speech segment
        ends (silence >= SILENCE_THRESHOLD_SEC), otherwise returns None.
        """
        tensor = torch.from_numpy(chunk).float()
        with torch.no_grad():
            prob = self._model(tensor, SAMPLE_RATE).item()

        is_speech = prob > 0.5

        if is_speech:
            self._buffer.append(chunk)
            self._in_speech = True
            self._silence_start = None
        elif self._in_speech:
            self._buffer.append(chunk)
            if self._silence_start is None:
                self._silence_start = time.monotonic()
            elif time.monotonic() - self._silence_start >= SILENCE_THRESHOLD_SEC:
                utterance = np.concatenate(self._buffer)
                self._reset_state()
                return utterance

        return None

    def flush(self) -> np.ndarray | None:
        """Return any buffered audio (e.g. at shutdown)."""
        if self._buffer:
            utterance = np.concatenate(self._buffer)
            self._reset_state()
            return utterance
        return None
