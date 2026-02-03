"""E2E test: comprehension agent interface + voice bridge (mock STT/TTS).

Proves that ask_founder=bridge.push_question is a valid interface
without modifying comprehension.py.
"""

import asyncio
import pytest

from voice.bridge import InterviewBridge, END_SENTINEL


@pytest.mark.asyncio
async def test_ask_founder_interface():
    """Simulate comprehension agent using bridge.push_question as ask_founder callback."""
    bridge = InterviewBridge(room_name="e2e-test")

    # Canned answers simulating founder responses (what STT would produce)
    canned_answers = {
        "Who is your ideal customer?": "Field sales reps at mid-market companies",
        "What's their biggest pain point?": "They waste 2 hours a day on manual CRM data entry",
    }

    async def mock_voice_agent():
        """Simulates the voice agent: gets questions, submits canned answers."""
        while True:
            question = await bridge.get_next_question(timeout=10)
            if question == END_SENTINEL:
                break
            answer = canned_answers.get(question, "I'm not sure about that")
            await asyncio.sleep(0.05)  # Simulate STT latency
            await bridge.submit_answer(answer)

    async def mock_comprehension_agent(ask_founder):
        """Simulates ComprehensionAgent using the ask_founder callback."""
        answers = []
        for question in canned_answers.keys():
            answer = await ask_founder(question)
            answers.append({"question": question, "answer": answer})
        return answers

    # Start voice agent simulation
    voice_task = asyncio.create_task(mock_voice_agent())

    # Run comprehension with bridge as the ask_founder callback
    results = await mock_comprehension_agent(ask_founder=bridge.push_question)

    # Signal end and wait for voice agent to finish
    bridge.signal_end()
    await voice_task

    # Verify results
    assert len(results) == 2
    assert results[0]["answer"] == "Field sales reps at mid-market companies"
    assert results[1]["answer"] == "They waste 2 hours a day on manual CRM data entry"


@pytest.mark.asyncio
async def test_ask_founder_with_timeout():
    """Verify timeout behavior when founder doesn't respond."""
    bridge = InterviewBridge(room_name="timeout-test")

    # No voice agent listening — should timeout
    with pytest.raises(asyncio.TimeoutError):
        await bridge.push_question("Anyone there?", timeout=0.1)


@pytest.mark.asyncio
async def test_interview_flow_with_end_signal():
    """Full flow: questions → answers → end signal → graceful shutdown."""
    bridge = InterviewBridge(room_name="flow-test")
    events = []

    async def voice_agent():
        while True:
            q = await bridge.get_next_question(timeout=5)
            if q == END_SENTINEL:
                events.append("end_received")
                break
            events.append(f"heard:{q}")
            await bridge.submit_answer(f"answer to {q}")
            events.append("answered")

    async def comprehension():
        a1 = await bridge.push_question("Q1", timeout=5)
        events.append(f"got:{a1}")
        a2 = await bridge.push_question("Q2", timeout=5)
        events.append(f"got:{a2}")
        bridge.signal_end()

    voice_task = asyncio.create_task(voice_agent())
    await comprehension()
    await voice_task

    assert events == [
        "heard:Q1",
        "answered",
        "got:answer to Q1",
        "heard:Q2",
        "answered",
        "got:answer to Q2",
        "end_received",
    ]
