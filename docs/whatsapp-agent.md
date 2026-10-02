# J.A.R.V.I.S. Advanced WhatsApp Agent Subsystem

The **WhatsApp Agent** transforms WhatsApp on macOS Apple Silicon into an autonomous, voice-native communication organ of J.A.R.V.I.S. Rather than relying on external web scrapers or unauthorized reverse-engineered APIs, it operates securely through the user's **already-installed and logged-in WhatsApp Desktop macOS application (Catalyst)**, or in a safe, fully-isolated simulation mock engine.

---

## 1. System Architecture

```
J.A.R.V.I.S. HUD / Remote / Voice / CLI
               │
               ▼
┌────────────────────────────────────────────────────────┐
│           WhatsAppAgent (agents/whatsapp/agent.py)     │
├────────────────────────────────────────────────────────┤
│  • Natural Language & Voice Command Understanding      │
│  • Multi-Turn Pronoun & Action Memory                  │
│  • Zero-Mistake Contact Resolution                     │
│  • Sensitive Content Pre-Dispatch Auditing             │
│  • Local-First Privacy Summarization (Apple Silicon)   │
│  • Per-Capability Permissions & Policy Enforcement     │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
      [Simulation Mode]           [Production Mode]
               │                          │
               ▼                          ▼
┌───────────────────────────┐  ┌───────────────────────────────────┐
│     WhatsAppMockEngine    │  │     WhatsAppDesktopController     │
│   (agents/whatsapp/       │  │   (agents/whatsapp/               │
│    mock_engine.py)        │  │    desktop_controller.py)         │
├───────────────────────────┤  ├───────────────────────────────────┤
│ • In-memory simulated     │  │ Layer 1: Semantic AX (JXA / UI)   │
│   contacts & unreads      │  │ Layer 2: AppKit Pasteboard + URL  │
│ • Synthetic chat history  │  │ Layer 3: Native Keyboard Keystroke│
│ • Safe test execution     │  │ Layer 4: Graceful Fail & Recovery │
└───────────────────────────┘  └─────────────────┬─────────────────┘
                                                 │
                                                 ▼
                                ┌───────────────────────────────────┐
                                │   WhatsApp Desktop (macOS Catalyst│
                                └───────────────────────────────────┘
```

---

## 2. Core Subsystems

| Module | File | Role |
| :--- | :--- | :--- |
| **Agent Coordinator** | `agents/whatsapp/agent.py` | Central `BaseAgent` subclass exposing standard high-level API methods, natural language parsing, and multi-turn workflows. |
| **Contact Resolver** | `agents/whatsapp/contact_resolver.py` | Fuzzy Levenshtein matching, phonetic Soundex indexing, nickname translation (`Mom`, `Dad`, `Bro`, `Sis`), phone number bypass, and ambiguity detection. |
| **Context Memory** | `agents/whatsapp/context_memory.py` | Multi-turn conversational memory tracking pronouns (`him`, `her`, `them`, `the person who messaged me`) and action continuity (`the same message`). |
| **Message Composer** | `agents/whatsapp/message_composer.py` | Intent-based greeting composition ("Say hello", "Wish happy birthday") and sensitive content detection (passwords, OTPs, credit cards). |
| **Local Summarizer** | `agents/whatsapp/summarizer.py` | Local-first message summarizer with context compression, urgency categorization (`URGENT`, `IMPORTANT`, `NORMAL`, `LOW_PRIORITY`), and deduplication. |
| **Activity Monitor** | `agents/whatsapp/activity_monitor.py` | Background unread watcher and delta tracker ("What's new since I left?") publishing to `core.events.event_bus`. |
| **Permission Manager**| `agents/whatsapp/permission_manager.py`| Persistent JSON permissions (`read_messages`, `send_messages`, `call`, `video_call`, `summarize`) and privacy policies. |
| **Desktop Controller**| `agents/whatsapp/desktop_controller.py`| Multi-layered macOS Catalyst desktop automation via JXA, AppKit pasteboard, and keyboard events with privacy redaction. |
| **Simulation Engine** | `agents/whatsapp/mock_engine.py` | 100% offline simulation environment allowing comprehensive testing without opening real WhatsApp or sending external messages. |
| **Health Check** | `agents/whatsapp/health_check.py` | System diagnostics auditing app installation, running process, and macOS Accessibility permissions. |

---

## 3. Natural Language & Voice Commands

The agent parses and executes conversational commands across all voice, chat, HUD, and CLI surfaces:

1. **"What's happening on WhatsApp?" / "What are my WhatsApp updates?"**
   - Returns a structured executive briefing of unread messages and urgent senders.
2. **"Who messaged me?" / "Who contacted me today?"**
   - Extracts unique senders who sent messages recently.
3. **"What did Rahul say?" / "Summarize Rahul's messages"**
   - Fetches and locally summarizes recent messages exchanged with Rahul.
4. **"Say hello to Rahul"**
   - Resolves Rahul, composes a friendly greeting ("Hello Rahul! Hope you are having a wonderful day."), and dispatches.
5. **"Tell Rahul I'll call him later"**
   - Sends the exact conversational text to the resolved contact.
6. **"Call Rahul on WhatsApp"**
   - Resolves Rahul and initiates a native WhatsApp voice call (`Cmd + Shift + A`).
7. **"Video call Mom"**
   - Maps `Mom` to family contact, verifies video call capability, and triggers a video call (`Cmd + Shift + V`).
8. **"Open my WhatsApp"**
   - Activates and brings the WhatsApp Desktop application to the front.
9. **"What's new since I left?"**
   - Analyzes recent activity against the previous baseline snapshot and reports newly received messages.
10. **"Reply to him saying I'll be there in 10 minutes"**
    - Resolves pronoun `him` to the last active conversational contact from context memory and transmits.

---

## 4. REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/whatsapp/activity` | `GET` | Returns JSON object containing unread counts, recent senders, pending replies, and activity summary. |
| `/api/whatsapp/summarize` | `GET` / `POST` | Summarizes recent activity or specific contact conversation (`{"contact": "Rahul"}`). |
| `/api/whatsapp/permissions`| `GET` / `POST` | Gets or updates per-capability authorizations and privacy mode. |
| `/api/whatsapp/health` | `GET` | Performs diagnostic health check of WhatsApp Desktop and system permissions. |
| `/api/whatsapp/mock` | `GET` / `POST` | Inspects or toggles offline simulation mode (`{"mock": true/false}`). |

---

## 5. EventBus Integration

WhatsApp Agent publishes real-time structured events to `core.events.event_bus`:

* `whatsapp.message.received`: Dispatched when a new incoming message is observed.
* `whatsapp.unread.changed`: Dispatched when total unread count changes.
* `whatsapp.call.started`: Dispatched upon initiating an audio or video call.
* `whatsapp.call.ended`: Dispatched when a call completes.
* `whatsapp.action.failed`: Dispatched when an action fails or permission is denied.
