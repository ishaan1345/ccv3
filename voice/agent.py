"""LiveKit voice agent worker for founder interviews.

Run standalone: python -m voice.agent dev
"""

from __future__ import annotations

import asyncio
import logging

from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    UserInputTranscribedEvent,
    WorkerOptions,
    cli,
)
from livekit.plugins import cartesia, deepgram, silero, anthropic

from voice.bridge import END_SENTINEL, get_bridge, create_bridge

logger = logging.getLogger("voice.agent")

SYSTEM_PROMPT = """\
You are a friendly interview assistant helping conduct a founder interview.
Your ONLY job is conversational wrapping — greetings, acknowledgments, and transitions.
You do NOT decide what questions to ask. Questions come from the system.
Keep responses under 2 sentences. Be warm but concise.
"""


class InterviewAgent(Agent):
    """Agent that relays questions from the bridge and collects spoken answers."""

    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
        )


async def entrypoint(ctx: JobContext) -> None:
    """Main entrypoint for the voice agent worker."""
    logger.info(f"Voice agent joining room: {ctx.room.name}")

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for a participant to join
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    # Get or create bridge for this room
    bridge = get_bridge(ctx.room.name)
    if bridge is None:
        bridge = create_bridge(ctx.room.name)

    # Build agent and session with v1.3 API
    agent = InterviewAgent()
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3"),
        llm=anthropic.LLM(model="claude-sonnet-4-20250514"),
        tts=cartesia.TTS(model="sonic-2"),
    )

    # start() is async — must be awaited
    await session.start(agent, room=ctx.room)

    # Greet the founder — say() returns SpeechHandle, await wait_for_playout()
    # so we don't start listening for questions before greeting finishes
    greeting = session.say(
        "Hi! Thanks for joining. I'll be asking you a few questions about your business. Ready when you are!"
    )
    await greeting.wait_for_playout()

    # Main interview loop
    while True:
        try:
            question = await bridge.get_next_question(timeout=300)
        except (TimeoutError, asyncio.TimeoutError):
            logger.warning("No question received in 5 minutes, ending")
            handle = session.say("It looks like we're done. Thanks for your time!")
            await handle.wait_for_playout()
            break

        if question == END_SENTINEL:
            handle = session.say(
                "That's all the questions I have. Thanks so much for sharing — this was really helpful!"
            )
            await handle.wait_for_playout()
            break

        # Speak the question and wait for playout to finish before listening
        question_handle = session.say(question)
        await question_handle.wait_for_playout()

        # Now wait for the founder's spoken response via STT
        answer = await _wait_for_speech(session, timeout=60)

        if answer:
            await bridge.submit_answer(answer)
            ack = session.say("Got it, thanks.")
            await ack.wait_for_playout()
        else:
            await bridge.submit_answer("[no response]")
            ack = session.say("No worries, let's move on.")
            await ack.wait_for_playout()

    logger.info("Interview complete")


async def _wait_for_speech(session: AgentSession, timeout: float = 60.0) -> str:
    """Wait for the user to finish speaking and return the transcription."""
    loop = asyncio.get_running_loop()
    result_future: asyncio.Future[str] = loop.create_future()

    def on_user_input(ev: UserInputTranscribedEvent):
        if ev.is_final and not result_future.done():
            result_future.set_result(ev.transcript)

    session.on("user_input_transcribed", on_user_input)

    try:
        return await asyncio.wait_for(result_future, timeout=timeout)
    except (TimeoutError, asyncio.TimeoutError):
        return ""
    finally:
        session.off("user_input_transcribed", on_user_input)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
