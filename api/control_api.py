"""
FastAPI control endpoints for the Teams Claude bot.

Allows external control of the bot (join, leave, manual speak, transcript).
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

if TYPE_CHECKING:
    from main import MeetingClaude

app = FastAPI(title="Teams Claude Bot API")

# Set by main.py after bot is created
_bot: "MeetingClaude | None" = None


def set_bot(bot: "MeetingClaude") -> None:
    global _bot
    _bot = bot


class JoinRequest(BaseModel):
    meeting_url: str


class SpeakRequest(BaseModel):
    message: str


@app.post("/join")
async def join(req: JoinRequest):
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    await _bot.join(req.meeting_url)
    return {"status": "joined", "meeting_url": req.meeting_url}


@app.post("/leave")
async def leave():
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    summary = await _bot.leave()
    return {"status": "left", "summary": summary}


@app.post("/speak")
async def speak(req: SpeakRequest):
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    await _bot.speak(req.message)
    return {"status": "spoken", "message": req.message}


@app.get("/transcript")
async def transcript():
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    return {"transcript": _bot.get_transcript()}


@app.get("/status")
async def status():
    if _bot is None:
        return {"status": "not_initialized"}
    return {"status": "running", "in_meeting": _bot.in_meeting}
