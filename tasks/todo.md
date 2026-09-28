# Task: Architectural Migration to Internal SemanticEdge Assistant Service & Explore/Review Unification

## COMPLETED

- [x] 1. Extract & Migrate OpenClaw Logic into Controlled NVR Assistant Tools
  - [x] Extracted snapshot resolution, event retrieval, track history, camera telemetry, monitoring zones, and detection statistics from `nvr/openclaw.py` into `nvr/assistant/tools.py`.
  - [x] Preserved NLP intent parsing from `OpenClawNLPEngine` into `nvr/assistant/nlp.py` (rule-based provider).
  - [x] Removed `send_telegram_alert()` calls from `nvr/streaming.py` — detection/tracking loop is fully decoupled from LLM/assistant.

- [x] 2. Implement Internal Assistant Service Layer & LLM Abstraction
  - [x] Created `AlertConversation` and `ChatMessage` models in `nvr/models.py` with migration `0006_remove_telegramsession_user_alertconversation_and_more.py`.
  - [x] Created `nvr/assistant/llm.py` with provider abstraction (`BaseLLMProvider`, `RuleBasedNVRProvider`, `GeminiLLMProvider`).
  - [x] Created `nvr/assistant/service.py` (`AssistantService`) orchestrating conversation context, controlled tools, and LLM providers.
  - [x] LLM never accesses raw SQL — all queries route through typed, controlled tool functions in `nvr/assistant/tools.py`.

- [x] 3. Expose Assistant API & Conversation Endpoints
  - [x] Created API views in `nvr/views.py`: `AssistantConversationApiView`, `AssistantConversationDetailApiView`, `AssistantMessageApiView`, `AssistantDiagnosticsApiView`.
  - [x] Wired URLs in `nvr/urls.py` at `/nvr/api/assistant/conversations/`, `/nvr/api/assistant/conversations/<id>/`, `/nvr/api/assistant/conversations/<id>/messages/`, `/nvr/api/assistant/diagnostics/`.
  - [x] Replaced Telegram diagnostic card in `settings.html` with Assistant Status & Diagnostics card.
  - [x] Removed `nvr/management/commands/run_openclaw_bot.py`.

- [x] 4. Unify Explore and Review Semantic Flow
  - [x] `ReviewView` supports `track_id` and `event_id` query parameters for deep investigation from Explore.
  - [x] Added "Investigate with Assistant" and "View in Review timeline" / "Inspect in Review" actions on Explore object cards and detail modal.
  - [x] Review timeline supports jumping into assistant context via Explore links.

- [x] 5. Implement Explore Assistant Chat UI
  - [x] Built interactive, dockable drawer Assistant Chat panel in `templates/nvr/explore.html` with real-time conversation loading, message posting, active alert context display, and evidence rendering.
  - [x] Clicking any detection/object in Explore binds it as the current investigation context.
  - [x] Snapshot evidence, camera details, and Review navigation links render directly inside chat messages.

- [x] 6. Testing, Verification, and Documentation
  - [x] Updated `nvr/tests.py` — removed Telegram-specific bot tests, added comprehensive tests for `AssistantService`, controlled tools, `AlertConversation`, `ChatMessage`, API endpoints, and Explore-Review links.
  - [x] Full test suite passes: 35 tests, 0 failures.
  - [x] Django system check: 0 issues.
  - [x] Database migrations applied cleanly.

## Review

New pipeline architecture:

  Camera -> YOLO -> ByteTrack -> trajectory/event logic -> DetectionEvent -> Alert
                                                                               |
                                                              nvr/assistant/service.py
                                                              (AlertConversation + ChatMessage)
                                                                               |
                                                              nvr/assistant/tools.py (controlled queries)
                                                                               |
                                                              nvr/assistant/llm.py (RuleBased / Gemini)
                                                                               |
                                                              Explore UI: Assistant Drawer Chat Panel

Key files created/modified:
- nvr/assistant/__init__.py, tools.py, nlp.py, service.py, llm.py
- nvr/models.py -- AlertConversation, ChatMessage (removed TelegramSession, TelegramFeedback)
- nvr/views.py -- 4 new assistant API views
- nvr/urls.py -- 4 new assistant API routes
- nvr/streaming.py -- Telegram calls removed
- templates/nvr/explore.html -- Assistant drawer, Investigate action, View in Review links
- templates/nvr/settings.html -- Assistant diagnostics card (replaced Telegram card)
- nvr/tests.py -- 9 new assistant/integration tests
- Migrations: 0006_remove_telegramsession_user_alertconversation_and_more.py
- nvr/management/commands/run_openclaw_bot.py -- DELETED
