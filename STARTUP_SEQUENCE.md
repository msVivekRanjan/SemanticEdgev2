# SemanticEdge & OpenClaw Integration: Startup Sequence & Architecture Guide

## 1. System Architecture Overview

SemanticEdge NVR uses OpenClaw strictly as a **backend NLP intelligence engine**, while the Django management daemon (`run_openclaw_bot`) acts as the **exclusive Telegram update consumer**. This ensures that the generic OpenClaw chatbot never intercepts Telegram messages, prevents HTTP 409 long-polling conflicts, and restricts bot interactions strictly to NVR surveillance operations.

```
┌─────────────────┐
│  Telegram User  │
└────────┬────────┘
         │ (User query: "latest intrusion", "send image for Track ID 5")
         ▼
┌─────────────────────────────────────────────────────────────┐
│ SemanticEdge Bot Poller (`python manage.py run_openclaw_bot`) │
│ [Exclusive Telegram Consumer: calls getUpdates]             │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: [TELEGRAM RECEIVE] Incoming message logged         │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: [OPENCLAW NLP] OpenClawNLPEngine Intent Parsing    │
│  - "latest intrusion"         -> LATEST_INTRUSION           │
│  - "show latest image"        -> LATEST_IMAGE               │
│  - "send image for Track ID 5"-> TRACK_ID (id: 5)           │
│  - "show yesterday's alerts"  -> YESTERDAY_ALERTS           │
│  - General chat (chit-chat)   -> GENERAL_CONVERSATION       │
│                                  (Strictly Rejected)        │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 3 & 4: [SQLITE QUERY] & [DETECTION EVENT]             │
│  Django ORM queries `DetectionEvent` table in SQLite        │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: [SNAPSHOT LOAD] Resolve snapshot image from disk   │
│  Loads JPEG/PNG file from `MEDIA_ROOT`                      │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 6: [TELEGRAM SEND] Dispatches photo + rich metadata   │
│  or explanatory text message back to Telegram               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Root Cause of Previous Interception & Conflict

1. **The Issue**:
   When users messaged the bot on Telegram, they received the default OpenClaw assistant greeting:
   `"Hello! I'm your new assistant..."`
2. **Why It Happened**:
   - The system OpenClaw service (`openclaw gateway --port 18789`) was running via macOS LaunchAgent (`~/Library/LaunchAgents/ai.openclaw.gateway.plist`).
   - In `~/.openclaw/openclaw.json`, `channels.telegram` was enabled using the **exact same bot token**.
   - OpenClaw's internal poller captured incoming Telegram updates before Django could process them and executed its unconfigured workspace birth sequence (`BOOTSTRAP.md`).
   - Furthermore, because Telegram only allows **one** polling consumer at a time, running `run_openclaw_bot` concurrently resulted in update starvation and HTTP 409 conflict errors.
3. **The Solution**:
   - The `telegram` channel has been permanently deleted from OpenClaw gateway configuration (`~/.openclaw/openclaw.json`).
   - OpenClaw gateway runs strictly as a backend service with 0 chat channels.
   - `python manage.py run_openclaw_bot` is now the sole Telegram update consumer.

---

## 3. Exact Multi-Service Startup Sequence

To ensure stable operation with zero conflicts, launch the services in the following order:

### Step 1: OpenClaw Backend Service (Gateway)
OpenClaw runs in the background as a local backend NLP service on port `18789`.

```bash
# Check status to ensure gateway is reachable and NO chat channels are attached
openclaw channels status
```

**Expected output:**
```
Gateway reachable.
- no configured chat channels (run `openclaw channels list --all` to see installable channels)
```

> **Note**: If OpenClaw gateway is running as a LaunchAgent, it is already active. If you need to restart or start it manually:
> ```bash
> launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway
> # Or manual foreground run:
> openclaw gateway --port 18789
> ```

---

### Step 2: Django Web Application Server
Start the Django development server to serve the NVR UI, live camera streams, and REST APIs.

```bash
cd /Users/ms.vivekranjan/VIVEK/CODE/PROJECTS/YOLO_Project/SemanticEdgev2/semanticedge
./.venv/bin/python manage.py runserver 0.0.0.0:8000
```

Verify that the dashboard is accessible at:
[http://localhost:8000/nvr/dashboard/](http://localhost:8000/nvr/dashboard/)

---

### Step 3: SemanticEdge Telegram Polling Daemon
Start the dedicated Telegram polling daemon. This process connects to Telegram, listens for user requests, calls the OpenClaw NLP engine, queries SQLite, and dispatches snapshot evidence.

```bash
cd /Users/ms.vivekranjan/VIVEK/CODE/PROJECTS/YOLO_Project/SemanticEdgev2/semanticedge
./.venv/bin/python -u manage.py run_openclaw_bot
```

**Expected Startup Banner:**
```
═══════════════════════════════════════════════════════════════════
  🛡️ SemanticEdge Telegram Bot Poller Active
  Bot: @Semanticedgebot (Token: ...zTVuJl_o)
  Default Chat ID: 8533970656
  Role: Single Telegram Update Consumer -> OpenClaw Backend NLP
═══════════════════════════════════════════════════════════════════
```

---

## 4. Stage-by-Stage Verification & Logging

Whenever a message is processed by `run_openclaw_bot`, all 6 stages are logged with explicit identifiers:

| Stage | Log Prefix | Description |
|---|---|---|
| **Stage 1** | `[TELEGRAM RECEIVE]` | Logs the incoming user text and sender chat ID. |
| **Stage 2** | `[OPENCLAW NLP]` | Logs the intent parsed by OpenClaw (`latest_intrusion`, `latest_image`, `track_id`, `yesterday_alerts`, or `general_conversation`). |
| **Stage 3** | `[SQLITE QUERY]` | Logs the exact Django ORM query executed against SQLite `DetectionEvent`. |
| **Stage 4** | `[DETECTION EVENT]` | Logs matching event details (ID, Track ID, Camera, Class, Status). |
| **Stage 5** | `[SNAPSHOT LOAD]` | Logs snapshot disk path, existence (`True`/`False`), and file size in bytes. |
| **Stage 6** | `[TELEGRAM SEND]` | Logs response dispatch (`photo` or `text`), destination chat ID, and HTTP status. |

### Sample Log Output for Valid Request:
```
[TELEGRAM RECEIVE] Telegram message received: 'send image for Track ID 5' from chat 8533970656
[OPENCLAW NLP] Intent parsed by OpenClaw: intent='track_id', params={'track_id': 5, 'raw_query': 'send image for Track ID 5'}
[SQLITE QUERY] SQLite query executed: DetectionEvent.objects.filter(track_id=5).order_by('-created_at').first()
[DETECTION EVENT] DetectionEvent found: ID=42, Track=#5, Camera='Main Gate', Class='person', Status='Intrusion: Zone A'
[SNAPSHOT LOAD] Snapshot loaded: path='/Users/.../media/snapshots/cam1/event_42.jpg', exists=True, size=184320 bytes
[TELEGRAM SEND] Telegram response sent: type='photo', destination='8533970656', success=True
```

### Sample Log Output for General Conversation Rejection:
```
[TELEGRAM RECEIVE] Telegram message received: 'how are you today?' from chat 8533970656
[OPENCLAW NLP] Intent parsed by OpenClaw: intent='general_conversation', params={'raw_query': 'how are you today?'}
[SNAPSHOT LOAD] Snapshot loaded: path='None', exists=False, size=0 bytes
[TELEGRAM SEND] Telegram response sent: type='text', destination='8533970656', success=True
```
*User receives a polite message stating that general conversation is disabled and providing the supported surveillance commands.*

---

## 5. Automated Intrusion Alerts & 7-Stage Flow

When an intrusion is detected (either in the Restricted Area stream or on any camera with active monitoring zones), `send_telegram_alert(event)` is executed with end-to-end stage logging:

```
[INTRUSION DETECTED]
        ↓
[DetectionEvent saved]
        ↓
[send_telegram_alert() called]
        ↓
[Telegram payload created]
        ↓
[Telegram API request sent]
        ↓
[Telegram API response received]
        ↓
[Alert delivered successfully]
```

### Sample Log Output for Real-Time Intrusion Alert:
```
[INTRUSION DETECTED] Camera='MacBook' | Zone='North Gate' (ID=1) | Track ID=#777 | Class='person' | Confidence=0.9654
[DetectionEvent saved] Event ID=437 | Track=#777 | Camera='MacBook' | Status='Intrusion: North Gate' | Snapshot='/media/detections/user_1/camera_1/intrusion_1_tid777_person_1788956250.jpg'
[send_telegram_alert() called] Event ID=437 | Track=#777 | Camera='MacBook' | Target Chat ID='1448272968'
[Telegram payload created] Endpoint: POST https://api.telegram.org/bot85339706...Jl_o/sendMessage | Target Chat: 1448272968 | Message Length: 385 chars
[Telegram API request sent] Dispatching POST request to Telegram API (timeout=10s)...
[Telegram API response received] HTTP Status=200 | Response: {"ok":true,"result":{"message_id":131,...}}
[Alert delivered successfully] Telegram Message ID=131 delivered to chat 1448272968 for event 437 (#777)
```

---

## 6. Live "Test Telegram Alert" Button

You can verify the notification pipeline directly from the NVR web interface without waiting for camera movements:

1. Navigate to the **Config** tab in the NVR sidebar ([http://localhost:8000/nvr/settings/](http://localhost:8000/nvr/settings/)).
2. Scroll to the **Telegram Intrusion Alert & OpenClaw Integration** panel.
3. Verify your Target Chat ID (`1448272968`).
4. Click **"Test Telegram Alert"**.
5. The UI will dispatch a sample alert through the identical `send_telegram_alert()` code path and render the HTTP response and Telegram message ID directly on screen.

---

## 7. Verification Commands

Run the full automated test suite to verify all tabs, streaming engines, and Telegram alert integrations:
```bash
./.venv/bin/python manage.py test accounts core nvr
```
All 28 tests will execute and pass cleanly.

