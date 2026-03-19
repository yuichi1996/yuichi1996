"""
Microsoft Teams web client automation using Playwright.

Joins a Teams meeting as a named guest or with an account,
then manages mute/unmute for Claude's audio injection.
"""

import asyncio
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from config import TEAMS_EMAIL, TEAMS_PASSWORD, TEAMS_MEETING_URL, BOT_DISPLAY_NAME
from bot.audio_controller import AudioController


class TeamsBot:
    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self.audio: AudioController | None = None

    async def start(self, meeting_url: str = TEAMS_MEETING_URL) -> None:
        """Launch Chromium and join the Teams meeting."""
        self._playwright = await async_playwright().start()

        # --use-fake-ui-for-media-stream: auto-grant mic/camera permissions
        # --use-fake-device-for-media-stream: use system default audio devices
        self._browser = await self._playwright.chromium.launch(
            headless=False,  # Set True for fully headless; False is easier to debug
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        self._context = await self._browser.new_context(
            permissions=["microphone", "camera"],
        )
        self._page = await self._context.new_page()
        self.audio = AudioController(self._page)

        if TEAMS_EMAIL and TEAMS_PASSWORD:
            await self._login()

        await self._join_meeting(meeting_url)

    async def _login(self) -> None:
        """Sign in with Microsoft account."""
        page = self._page
        await page.goto("https://teams.microsoft.com")
        await page.wait_for_load_state("networkidle")

        try:
            await page.fill('[data-report-id="signInName"]', TEAMS_EMAIL, timeout=10000)
            await page.click('[type="submit"]')
            await page.fill('[name="passwd"]', TEAMS_PASSWORD, timeout=10000)
            await page.click('[type="submit"]')
            # Handle "Stay signed in?" prompt
            await page.click('[id="idBtn_Back"]', timeout=5000)
        except Exception as e:
            print(f"[TeamsBot] Login step skipped or failed: {e}")

        await page.wait_for_load_state("networkidle")

    async def _join_meeting(self, meeting_url: str) -> None:
        """Navigate to the meeting URL and join as guest or authenticated user."""
        page = self._page
        await page.goto(meeting_url)
        await page.wait_for_load_state("networkidle")

        # If prompted for display name (guest join)
        try:
            name_input = page.locator('[placeholder="Type your name"]')
            await name_input.fill(BOT_DISPLAY_NAME, timeout=5000)
        except Exception:
            pass

        # Click "Join now" / "参加する" button
        for selector in [
            '[data-tid="prejoin-join-button"]',
            'button:has-text("Join now")',
            'button:has-text("参加する")',
        ]:
            try:
                await page.click(selector, timeout=5000)
                break
            except Exception:
                continue

        # Wait for the in-meeting UI to appear
        await page.wait_for_selector('[data-tid="toggle-mute"]', timeout=30000)

        # Start muted
        await self.audio.ensure_muted()
        print(f"[TeamsBot] Joined meeting as '{BOT_DISPLAY_NAME}'")

    async def send_chat_message(self, text: str) -> None:
        """Post a message to the Teams meeting chat."""
        page = self._page
        try:
            # Open chat panel if not already open
            chat_btn = page.locator('[data-tid="chat-button"]')
            if await chat_btn.is_visible(timeout=3000):
                await chat_btn.click()

            chat_input = page.locator('[data-tid="meetingChatEntryPoint"] [contenteditable="true"]')
            await chat_input.fill(text, timeout=5000)
            await page.keyboard.press("Enter")
        except Exception as e:
            print(f"[TeamsBot] Failed to send chat message: {e}")

    async def leave_meeting(self) -> None:
        """Click the leave button."""
        page = self._page
        for selector in [
            '[data-tid="hangup-button"]',
            'button:has-text("Leave")',
            'button:has-text("退出")',
        ]:
            try:
                await page.click(selector, timeout=3000)
                break
            except Exception:
                continue

    async def stop(self) -> None:
        """Clean up browser resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
