# J.A.R.V.I.S. WhatsApp Agent — Testing & Simulation Guide

To enable fast, deterministic, and 100% safe verification without opening real desktop windows or transmitting messages to real contacts, the WhatsApp Agent includes an offline **Mock Engine**.

---

## 1. Mock Simulation Architecture

When simulation mode is active:
- **Zero GUI Interference**: WhatsApp Desktop is never launched, activated, or focused.
- **Zero Real Transmissions**: No messages or calls are placed over the network.
- **Realistic Synthetic Fixtures**: Pre-populated with representative contacts, realistic chat history, questions, and unread counts.

### Default Simulated Contacts:

| Name | Role | Unread Messages | Sample Last Message |
| :--- | :--- | :--- | :--- |
| **Rahul Sharma** | Colleague | 2 | *"Are you coming to the tech sync today at 4 PM?"* |
| **Mom** | Family | 1 | *"Don't forget to eat lunch!"* |
| **Ankit** | Friend | 0 | *"Sent the design documents over email."* |
| **Priya** | Team Lead | 3 | *"Urgent: Need the security audit report before 5 PM."* |

---

## 2. Enabling Simulation Mode

### Method 1: Environment Variable
Set `WHATSAPP_MOCK_MODE=true` prior to launching J.A.R.V.I.S.:
```bash
export WHATSAPP_MOCK_MODE=true
./jarvis
```

### Method 2: In Code / Unit Tests
```python
from agents.whatsapp import whatsapp_agent

# Enable simulation
whatsapp_agent.set_mock_mode(True)

# Run operations safely
result = whatsapp_agent.send_message("Rahul", "I'll be there soon!")
assert result.success is True
```

### Method 3: Via HUD UI
1. Open HUD Tactical Link modal.
2. Select **GOVERNANCE & PERMISSIONS**.
3. Toggle the **MOCK SIMULATION ENGINE** button to **SIMULATION: ON**.

---

## 3. Running Automated Tests

Run the dedicated WhatsApp Agent test suite:
```bash
/Users/divyanshu/Documents/anti2/.venv/bin/python -m unittest tests/test_whatsapp_agent.py
```

Run the entire project test suite:
```bash
/Users/divyanshu/Documents/anti2/.venv/bin/python -m unittest discover -s tests
```

---

## 4. Acceptance Test Scenarios Covered

The test suite validates all 10 core acceptance workflows:
1. `test_acceptance_1_activity_summary`: "What's happening on WhatsApp?"
2. `test_acceptance_2_who_messaged_me`: "Who messaged me?"
3. `test_acceptance_3_summarize_contact`: "What did Rahul say?"
4. `test_acceptance_4_say_hello`: "Say hello to Rahul"
5. `test_acceptance_5_tell_contact`: "Tell Rahul I'll call him later"
6. `test_acceptance_6_voice_call`: "Call Rahul on WhatsApp"
7. `test_acceptance_7_video_call`: "Video call Mom"
8. `test_acceptance_8_open_whatsapp`: "Open my WhatsApp"
9. `test_acceptance_9_delta_since_left`: "What's new since I left?"
10. `test_acceptance_10_pronoun_reply`: "Reply to him saying I'll do it"
