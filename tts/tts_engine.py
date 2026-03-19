"""
Text-to-speech using edge-tts (free, Microsoft Edge backend).

Generates audio as an in-memory WAV then plays it through the BlackHole
virtual audio device so Teams picks it up as microphone input.
"""

import asyncio
import io
import tempfile
import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import edge_tts

from config import TTS_VOICE, TTS_RATE, SAMPLE_RATE, PLAYBACK_DEVICE
from audio.virtual_audio import get_playback_device_index


class TTSEngine:
    def __init__(self, device_name: str = PLAYBACK_DEVICE):
        self._device_name = device_name
        self._device_index: int | None = None

    def _ensure_device(self) -> int:
        if self._device_index is None:
            self._device_index = get_playback_device_index(self._device_name)
        return self._device_index

    async def _synthesize(self, text: str) -> bytes:
        """Run edge-tts synthesis and return raw MP3 bytes."""
        communicate = edge_tts.Communicate(text, voice=TTS_VOICE, rate=TTS_RATE)
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        return buf.getvalue()

    def speak(self, text: str) -> None:
        """Synthesize text and play it through the virtual audio device (blocking)."""
        if not text.strip():
            return

        # Synthesize (edge-tts is async)
        mp3_bytes = asyncio.run(self._synthesize(text))

        # Decode MP3 → numpy array via soundfile (requires libsndfile with MP3 support)
        # Fall back to writing a temp file if in-memory fails
        try:
            audio, sr = sf.read(io.BytesIO(mp3_bytes))
        except Exception:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(mp3_bytes)
                tmp_path = f.name
            try:
                audio, sr = sf.read(tmp_path)
            finally:
                os.unlink(tmp_path)

        # Resample if necessary
        if sr != SAMPLE_RATE:
            import librosa
            audio = librosa.resample(audio.T, orig_sr=sr, target_sr=SAMPLE_RATE).T

        # Ensure float32
        audio = audio.astype(np.float32)
        if audio.ndim == 1:
            audio = audio[:, np.newaxis]

        device_idx = self._ensure_device()
        sd.play(audio, samplerate=SAMPLE_RATE, device=device_idx)
        sd.wait()
