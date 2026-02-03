"""Unit tests for InterviewBridge queue mechanism."""

import asyncio
import pytest

from voice.bridge import InterviewBridge, create_bridge, get_bridge, remove_bridge, END_SENTINEL


@pytest.fixture
def bridge():
    return InterviewBridge(room_name="test-room")


@pytest.mark.asyncio
async def test_push_question_and_answer(bridge):
    """Comprehension pushes question, voice agent gets it and submits answer."""

    async def voice_agent_side():
        question = await bridge.get_next_question(timeout=5)
        assert question == "What is your target market?"
        await bridge.submit_answer("Small businesses in retail")

    agent_task = asyncio.create_task(voice_agent_side())
    answer = await bridge.push_question("What is your target market?", timeout=5)

    assert answer == "Small businesses in retail"
    await agent_task


@pytest.mark.asyncio
async def test_multiple_questions(bridge):
    """Multiple question-answer rounds work correctly."""
    questions = [
        "Who is your customer?",
        "What problem do you solve?",
        "How big is the market?",
    ]
    answers_expected = [
        "SMB owners",
        "Inventory management",
        "10B TAM",
    ]

    async def voice_agent_side():
        for expected_q, answer in zip(questions, answers_expected):
            q = await bridge.get_next_question(timeout=5)
            assert q == expected_q
            await bridge.submit_answer(answer)

    agent_task = asyncio.create_task(voice_agent_side())

    for q, expected_a in zip(questions, answers_expected):
        answer = await bridge.push_question(q, timeout=5)
        assert answer == expected_a

    await agent_task


@pytest.mark.asyncio
async def test_signal_end(bridge):
    """signal_end sends the sentinel value."""
    bridge.signal_end()
    question = await bridge.get_next_question(timeout=1)
    assert question == END_SENTINEL


@pytest.mark.asyncio
async def test_push_after_end_raises(bridge):
    """Pushing a question after signal_end raises RuntimeError."""
    bridge.signal_end()
    with pytest.raises(RuntimeError, match="Interview has ended"):
        await bridge.push_question("Should not work")


@pytest.mark.asyncio
async def test_timeout_on_no_answer(bridge):
    """push_question times out if no answer arrives."""
    # Put a question but never answer it
    with pytest.raises(asyncio.TimeoutError):
        await bridge.push_question("Waiting forever", timeout=0.1)


@pytest.mark.asyncio
async def test_global_registry():
    """create_bridge / get_bridge / remove_bridge work."""
    b = create_bridge("room-abc")
    assert get_bridge("room-abc") is b
    assert get_bridge("nonexistent") is None
    remove_bridge("room-abc")
    assert get_bridge("room-abc") is None
