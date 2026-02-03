"""InterviewBridge: asyncio queue pair connecting comprehension agent to voice agent."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

END_SENTINEL = "__END_INTERVIEW__"

_active_bridges: dict[str, "InterviewBridge"] = {}


@dataclass
class InterviewBridge:
    """Two-way async bridge between comprehension logic and voice agent.

    Comprehension side calls push_question() and awaits the answer.
    Voice agent side calls get_next_question() and submit_answer().
    """

    room_name: str
    question_queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)
    answer_queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)
    _ended: bool = field(default=False, init=False)

    async def push_question(self, question: str, timeout: float = 120.0) -> str:
        """Called by comprehension agent. Pushes question, awaits founder's answer."""
        if self._ended:
            raise RuntimeError("Interview has ended")
        await self.question_queue.put(question)
        return await asyncio.wait_for(self.answer_queue.get(), timeout=timeout)

    async def get_next_question(self, timeout: float = 300.0) -> str:
        """Called by voice agent. Blocks until next question arrives."""
        return await asyncio.wait_for(self.question_queue.get(), timeout=timeout)

    async def submit_answer(self, answer: str) -> None:
        """Called by voice agent after STT transcription."""
        await self.answer_queue.put(answer)

    def signal_end(self) -> None:
        """Signal that the interview is over."""
        self._ended = True
        self.question_queue.put_nowait(END_SENTINEL)


def create_bridge(room_name: str) -> InterviewBridge:
    """Create and register a bridge for a room."""
    bridge = InterviewBridge(room_name=room_name)
    _active_bridges[room_name] = bridge
    return bridge


def get_bridge(room_name: str) -> InterviewBridge | None:
    """Get bridge for a room, or None."""
    return _active_bridges.get(room_name)


def remove_bridge(room_name: str) -> None:
    """Remove bridge when interview is done."""
    _active_bridges.pop(room_name, None)
