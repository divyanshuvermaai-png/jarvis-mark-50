# J.A.R.V.I.S. WhatsApp Agent — Permissions & Capability Governance

J.A.R.V.I.S. provides granular, per-capability authorization controls over WhatsApp operations. Users can grant or revoke specific abilities at any time without restarting the system.

---

## 1. Capability Authorizations

| Capability | Setting Key | Default | Description |
| :--- | :--- | :--- | :--- |
| **Read Messages** | `read_messages` | `true` | Allows J.A.R.V.I.S. to read messages from the visible desktop UI. |
| **Send Messages** | `send_messages` | `true` | Permits composing and dispatching text messages to contacts. |
| **Voice Calls** | `call` | `true` | Authorizes initiating native WhatsApp audio calls. |
| **Video Calls** | `video_call` | `true` | Authorizes initiating native WhatsApp video calls. |
| **Summarization** | `summarize` | `true` | Enables AI activity summarization and unread digest generation. |

If a capability is revoked, any attempt by voice or UI to execute that action immediately halts with an informative explanation:
> *"Permission 'send_messages' for WhatsApp is currently disabled in J.A.R.V.I.S. settings."*

---

## 2. Configuration Storage

Permissions are persisted in JSON format at:
```
~/.jarvis_system/whatsapp_permissions.json
```

### Example Configuration:
```json
{
  "permissions": {
    "read_messages": true,
    "send_messages": true,
    "call": true,
    "video_call": true,
    "summarize": true
  },
  "privacy_mode": "STRICT_LOCAL",
  "proactive_enabled": false
}
```

---

## 3. Managing Permissions

### Option A: Via HUD Comms Hub
1. Open the HUD (`index.html`) in your browser.
2. Click **COMMS** or press the Tactical Link button.
3. Select the **GOVERNANCE & PERMISSIONS** tab.
4. Toggle individual capabilities and click **SAVE PERMISSIONS**.

### Option B: Via REST API
```bash
# Get current permissions
curl http://127.0.0.1:5001/api/whatsapp/permissions

# Revoke video calls and sending messages
curl -X POST http://127.0.0.1:5001/api/whatsapp/permissions \
  -H "Content-Type: application/json" \
  -d '{"permissions": {"video_call": false, "send_messages": false}}'
```

### Option C: Via Python Code
```python
from agents.whatsapp import whatsapp_agent

# Revoke permission
whatsapp_agent.permissions.set_permission("video_call", False)

# Check permission
allowed, reason = whatsapp_agent.permissions.is_allowed("video_call")
print(allowed)  # False
```
