# Jarvis Voice Briefing

A voice agent that calls field sales reps before meetings and briefs them on the customer.

## Quick Start

```bash
# 1. Install dependencies
pip install vapi-python  # or: pip install retell-sdk
pip install fastapi uvicorn

# 2. Set environment variables
export VAPI_API_KEY=your_key
export VAPI_PHONE_NUMBER_ID=your_phone_id
export REP_PHONE_NUMBER=+15551234567  # Your phone for testing

# 3. Make a test call
python call.py --phone "+15551234567" --customer mock_data/linda.json
```

## Files

```
jarvis/
├── mock_data/
│   └── linda.json          # Mock customer context
├── prompts.py              # Briefing system + user prompts
├── call.py                 # Make voice call (Vapi or Retell)
├── commands.py             # Log commands from calls
├── trigger.py              # Check calendar, trigger calls
├── webhook.py              # Receive call completion webhooks
├── jarvis_commands.jsonl   # Logged commands (output)
└── README.md               # This file
```

## Usage

### Manual Call (Prototype)

```bash
# Call yourself with Linda's briefing
python call.py --phone "+15551234567" --customer mock_data/linda.json

# Use Retell instead of Vapi
python call.py --phone "+15551234567" --customer mock_data/linda.json --provider retell
```

### Calendar Trigger

```bash
# Check calendar once (dry run)
python trigger.py trigger --dry-run

# Check calendar once (real)
python trigger.py trigger

# Run as daemon (checks every 60s)
python trigger.py daemon --interval 60

# Direct call bypassing calendar
python trigger.py call --phone "+15551234567" --customer mock_data/linda.json
```

### Command Logging

```bash
# List pending commands
python commands.py list

# Test command extraction from transcript
python commands.py test

# Mark command as done
python commands.py done "2026-01-27T09:15:00.000000"
```

### Webhook Server

```bash
# Start webhook server
python webhook.py
# Or: uvicorn webhook:app --port 8000

# Test health
curl http://localhost:8000/health
```

## Environment Variables

### Vapi (Default)

```bash
VAPI_API_KEY=your_api_key
VAPI_PHONE_NUMBER_ID=your_phone_number_id
VAPI_WEBHOOK_SECRET=optional_webhook_secret
```

### Retell (HIPAA Compliant)

```bash
RETELL_API_KEY=your_api_key
RETELL_PHONE_NUMBER=+1234567890
RETELL_AGENT_ID=your_agent_id
RETELL_WEBHOOK_SECRET=optional_webhook_secret
```

### General

```bash
VOICE_PROVIDER=vapi  # or retell
REP_PHONE_NUMBER=+15551234567  # For testing
WEBHOOK_PORT=8000
```

## Briefing Structure

Jarvis delivers a 2-3 minute briefing:

1. **Hook (10s)**: "You're meeting [Name], [Title] at [Company] in [time]."
2. **The One Thing (20s)**: Most critical item they need to know
3. **Deal Status (20s)**: Amount, stage, how long stuck, next step
4. **History (30s)**: Last meeting, promises made, objections raised
5. **Personal (15s)**: Rapport details - family, hobbies mentioned
6. **Intel (20s)**: Competitors, decision makers, recent news
7. **Approach (20s)**: What to do in this meeting
8. **Ask (10s)**: "Any questions before you go in?"

## Commands

The rep can give commands during the call:

- "Remind me to [X] after the meeting"
- "Schedule [X]"
- "Note that [X]"
- "What was [specific detail]?"
- "Should I [strategy question]?"

Commands are logged to `jarvis_commands.jsonl` for later processing.

## Testing

1. **Phone rings**: Run `python call.py --phone YOUR_PHONE --customer mock_data/linda.json`
2. **Interrupt Jarvis**: Ask "What did we quote them?" mid-briefing
3. **Give command**: Say "Remind me to send the case study"
4. **Check logs**: Run `python commands.py list`

## Production Setup

1. **Calendar Integration**: Implement `get_calendar_events_google()` or `get_calendar_events_outlook()` in trigger.py
2. **CRM Integration**: Implement `get_customer_context_from_crm()` in trigger.py
3. **Webhook**: Deploy webhook.py and configure in Vapi/Retell dashboard
4. **Daemon**: Run `python trigger.py daemon` as a service

## Architecture

```
Calendar → Trigger → Voice Call → Rep Answers → Briefing → Commands
                                      ↓                       ↓
                                   Jarvis               jarvis_commands.jsonl
                                      ↓                       ↓
                                  Questions              August/CRM
```

Jarvis fills the BEFORE gap. August handles During + After.
