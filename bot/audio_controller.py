"""
Microphone mute/unmute control for the Teams web client via Playwright.

Teams web UI has a mute button in the call controls bar.
We toggle it programmatically so Claude only "speaks" when the TTS is playing.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page


class AudioController:
    # CSS selectors for Teams web (may need updating if Teams UI changes)
    _MIC_BUTTON_SELECTOR = '[data-tid="toggle-mute"]'

    def __init__(self, page: "Page"):
        self._page = page
        self._muted = True  # Bot starts muted

    async def ensure_muted(self) -> None:
        """Mute the microphone (safe to call even if already muted)."""
        if not self._muted:
            await self._toggle()
            self._muted = True

    async def ensure_unmuted(self) -> None:
        """Unmute the microphone before TTS playback."""
        if self._muted:
            await self._toggle()
            self._muted = False

    async def _toggle(self) -> None:
        try:
            btn = self._page.locator(self._MIC_BUTTON_SELECTOR)
            await btn.click(timeout=5000)
        except Exception as e:
            print(f"[AudioController] Failed to toggle mic: {e}")
