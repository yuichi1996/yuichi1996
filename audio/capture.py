"""
Continuous audio capture from the BlackHole virtual audio device.

Produces fixed-size numpy chunks (CHUNK_SAMPLES @ SAMPLE_RATE) and puts them
into a queue for downstream VAD processing.
"""

import queue
import threading
import numpy as np
import sounddevice as sd

from config import SAMPLE_RATE, CHUNK_SAMPLES, CAPTURE_DEVICE
from audio.virtual_audio import get_capture_device_index


class AudioCapture:
    def __init__(self, device_name: str = CAPTURE_DEVICE):
        self._device_name = device_name
        self._device_index: int | None = None
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: sd.InputStream | None = None
        self._running = False

    def start(self) -> None:
        self._device_index = get_capture_device_index(self._device_name)
        self._running = True
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=CHUNK_SAMPLES,
            device=self._device_index,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> None:
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        if status:
            print(f"[AudioCapture] {status}")
        # indata shape: (frames, 1) → flatten to 1-D
        self._queue.put(indata[:, 0].copy())

    def read_chunk(self, timeout: float = 1.0) -> np.ndarray | None:
        """Return next audio chunk or None on timeout."""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()
