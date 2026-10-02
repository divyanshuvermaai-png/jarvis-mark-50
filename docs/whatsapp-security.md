# J.A.R.V.I.S. WhatsApp Agent — Security & Privacy Architecture

The WhatsApp subsystem is architected under a **Zero-Trust, Local-First Privacy Model**. Private personal conversations and messages are never treated as arbitrary text streams and are safeguarded by strict boundary controls.

---

## 1. Local-First Privacy Modes

Configuration is managed via `WhatsAppPrivacyMode` in `~/.jarvis_system/whatsapp_permissions.json`:

| Mode | Behavior |
| :--- | :--- |
| `STRICT_LOCAL` *(Default)* | **100% on-device processing**. Conversation history, contact names, and message bodies are processed solely on Apple Silicon via extractive heuristic engines or local MLX Gemma models. **Zero bytes of message text are ever transmitted to any cloud AI service.** |
| `LOCAL_PREFERRED` | Prefers local on-device models. If unavailable, falls back to secure local rule-based heuristics without external network egress. |
| `CLOUD_ALLOWED` | Opt-in mode allowing external AI models to summarize messages only after user explicitly configures cloud access. |

---

## 2. Sensitive Content Pre-Dispatch Gate

Before any outgoing text message is dispatched, it passes through `MessageComposer.audit_message()`:

```
Outgoing Message
       │
       ▼
┌───────────────────────────────────────┐
│     MessageComposer Security Gate     │
├───────────────────────────────────────┤
│ • Credit / Debit Card Numbers         │
│ • Bank Account / Routing Digits       │
│ • Passwords / Secret API Keys         │
│ • One-Time Passcodes (OTP) / PINs     │
│ • Legal Commitments / Binding Promises│
└───────────────────┬───────────────────┘
                    │
           Sensitive Content Found?
          ┌─────────┴─────────┐
         YES                  NO
          │                    │
          ▼                    ▼
┌─────────────────────┐  ┌───────────────┐
│ Pause & Require     │  │ Immediate     │
│ Explicit User       │  │ Transmission  │
│ Confirmation        │  └───────────────┘
└─────────────────────┘
```

When sensitive content is detected, the agent returns an `ActionResult(requires_confirmation=True)` with a clear explanation:
> *"Safety Check: Message contains financial account information or credentials. Do you confirm sending this message to Rahul?"*

Routine conversational messages and standard greetings bypass confirmation for seamless hands-free productivity.

---

## 3. Privacy-Safe Logging & Redaction

J.A.R.V.I.S. enforces strict log scrubbing:
- **No Plaintext Message Bodies in Logs**: Log outputs never record raw conversation bodies. Logging records only lengths, truncated hashes, and action outcomes (`"Dispatched message (len: 24) to Rahul"`).
- **Redacted Exceptions**: If an error occurs during AppleScript or JXA execution, message text is stripped from the stack trace before writing to disk.

---

## 4. Ambiguity Protection (Zero-Mistake Dispatch)

To avoid sending a private message to the wrong recipient:
- If a contact query returns multiple candidates with identical or near-identical match scores (e.g., "Rahul Sharma" and "Rahul Verma" for query "Rahul"), the agent **never guesses**.
- Dispatch is paused and the agent prompts:
  > *"I found multiple contacts matching 'Rahul': Rahul Sharma, Rahul Verma. Which one do you mean?"*

---

## 5. macOS Sandbox & Accessibility Boundaries

The agent interacts with WhatsApp exclusively via standard macOS Accessibility APIs (`System Events`, `AXUIElement`) and deep-link schemes (`whatsapp://send`). It does **not**:
- Read internal WhatsApp SQLite databases or encryption keys.
- Inject third-party dylibs into WhatsApp processes.
- Interfere with WhatsApp end-to-end encryption.
- Implement any financial or payment transactions (WhatsApp Pay is strictly omitted).
