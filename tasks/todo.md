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

- [x] 7. Refined Operator Investigation Flow (Explore Card Direct Chat & Review Grouping)
  - [x] Card click in Explore immediately launches investigation chat for that detection object (`investigateCard(this)` -> `startConversationForEvent(eventId)`).
  - [x] Hover button (`.card-details-btn`) preserved on card thumbnail for opening metadata modal.
  - [x] Replaced standalone "Security Assistant" branding with subtle "Threads" toolbar button and "Investigation" drawer title.
  - [x] Grouped Review timeline view by tracked object identity `(class_name, track_id, camera_id)` matching Explore.
  - [x] Each object in Review shows summary card, horizontal detection history strip, and "Investigate" button linked to Explore chat.
  - [x] Provided backwards-compatible `events` along with `tracked_objects` in `ReviewView` context.
  - [x] 8. Clean Architectural Separation of Explore and Review
  - [x] **Explore**: Full-page ChatGPT-style investigation workspace (`templates/nvr/explore.html`). Centered around conversation/threads sidebar, active investigation title, attached event context banner with detach ability, rich chat message stream with evidence rendering, starter prompt suggestions, and quick query pills.
  - [x] **Review**: Object / Event Exploration and Discovery Workspace (`templates/nvr/review.html` + `ReviewView` in `nvr/views.py`). Hosts the full multi-parameter search (keyword/description, class, camera, datetime range), object categories horizontal strips, metadata inspection modal, and direct "Investigate" button on every detection card linking into Explore with that event context.
  - [x] Navigation sidebar in `base_nvr.html` updated with dedicated icons and labels reflecting Review as Object & Event Discovery and Explore as Investigation Workspace.
  - [x] Tests in `nvr/tests.py` updated to verify Review search filtering and Explore workspace rendering. Full test suite passes (26/26 tests, 0 failures).

## ACTIVE TASKS: Targeted UI/UX & Pipeline Refinements

- [ ] 1. Completely Remove Face Recognition / Attendance
  - [ ] Remove from navigation sidebar in `base_nvr.html` and delete `templates/nvr/face_recognition.html`.
  - [ ] Remove `FaceRecognitionView` and `FaceStreamView` from `nvr/views.py` and `nvr/urls.py`.
  - [ ] Remove `face_recognition_frame_generator` from `nvr/streaming.py`.
  - [ ] Remove `FaceReference` and `AttendanceRecord` models from `nvr/models.py`, `nvr/admin.py`, and `nvr/assistant/tools.py`.
  - [ ] Remove `has_face_recognition` from `accounts/models.py`, `accounts/admin.py`, and `service_face_recognition` from `core/models.py`.
  - [ ] Create and run migrations (`makemigrations`, `migrate`).
  - [ ] Clean up tests in `nvr/tests.py`, `accounts/tests.py`, and `core/tests.py`.

- [x] 2. Review Tab: Reduce Whitespace & Make Entire Card Clickable
  - [x] Streamline vertical space in `templates/nvr/review.html` between search/filter section and detection groups (16px search-to-filter gap, 28px filter-to-results gap verified via browser subagent).
  - [x] Make entire detection card clickable (`openDetailModalFromEl`) with proper cursor and hover affordance.
  - [x] Remove the small info icon button.
  - [x] Ensure "Investigate" button uses `event.stopPropagation()` to avoid conflicting modal opening.

- [ ] 3. Explore Tab: Fix Page Scrolling (ChatGPT Fixed-Viewport Layout)
  - [ ] Ensure Explore viewport remains fixed within application shell (`height: 100%; overflow: hidden;`).
  - [ ] Sidebar thread list has independent scroll (`overflow-y: auto`).
  - [ ] Messages stream has independent scroll (`overflow-y: auto`).
  - [ ] Composer input remains permanently pinned at the bottom.
  - [ ] Main app sidebar and header do not shift when scrolling messages.

- [ ] 4. Delete Investigation Thread (Backend & UI with Confirmation)
  - [ ] Add `DELETE` method to `AssistantConversationDetailApiView` and `delete_conversation` in `AssistantService`.
  - [ ] Ensure cascade deletes `ChatMessage` records without touching `DetectionEvent` or evidence.
  - [ ] Add delete button and confirmation modal in Explore UI.
  - [ ] Automatically select another thread or show welcome state upon deletion.

- [ ] 5 & 6. Restricted-Zone Alert with Sound & Full Alert -> Review -> Explore Flow
  - [ ] Add `/nvr/api/alerts/latest/` endpoint querying recent intrusion `DetectionEvent`s.
  - [ ] Implement browser notification layer with Web Audio API chime and toast banner.
  - [ ] Visual alert includes direct links to Review and Explore for the same detection event.
  - [ ] Handle browser audio autoplay permission gracefully with un-mute indicator.
  - [ ] Guarantee real-time detection pipeline remains non-blocking and decoupled.

- [ ] 7. Increase Explore Chat Typography
  - [ ] Increase font sizes for user and assistant messages, context banner, and thread items.
  - [ ] Maintain proportional headings and buttons matching SemanticEdge design system.

- [ ] 8. Comprehensive Verification
  - [ ] Run full automated test suite (`./.venv/bin/python manage.py test`).
  - [ ] Verify Django system checks (`manage.py check`).

## Review

New clean architecture:

  Camera -> YOLO -> ByteTrack -> trajectory/event logic -> DetectionEvent -> Alert
                                                                               |
                                                              nvr/assistant/service.py
                                                              (AlertConversation + ChatMessage)
                                                                               |
                                                              nvr/assistant/tools.py (controlled queries)
                                                                               |
                                                              nvr/assistant/llm.py (RuleBased / Gemini)
                                                                               |
                                 +---------------------------------------------+---------------------------------------------+
                                 |                                                                                           |
                       REVIEW WORKSPACE                                                             EXPLORE WORKSPACE
              (Object / Event Discovery Grid)                                              (Full-Page ChatGPT Workspace)
                 - Multi-parameter search & filters                                           - Thread list sidebar
                 - Categories strips (Person, Car, etc.)                                      - Message stream with evidence cards
                 - Detection metadata modal                                                   - Context banner with event binding
                 - "Investigate" -> opens in Explore                                          - Starter prompts & quick query chips

Key files created/modified:
- [nvr/assistant/](file:///Users/ms.vivekranjan/VIVEK/CODE/PROJECTS/YOLO_Project/SemanticEdgev2/semanticedge/nvr/assistant/) — tools.py, nlp.py, service.py, llm.py
- [nvr/models.py](file:///Users/ms.vivekranjan/VIVEK/CODE/PROJECTS/YOLO_Project/SemanticEdgev2/semanticedge/nvr/models.py) — AlertConversation, ChatMessage (removed TelegramSession, TelegramFeedback)
- [nvr/views.py](file:///Users/ms.vivekranjan/VIVEK/CODE/PROJECTS/YOLO_Project/SemanticEdgev2/semanticedge/nvr/views.py) — 4 new assistant API views, ReviewView grouped by tracked object identity
- [nvr/urls.py](file:///Users/ms.vivekranjan/VIVEK/CODE/PROJECTS/YOLO_Project/SemanticEdgev2/semanticedge/nvr/urls.py) — 4 new assistant API routes
- [nvr/streaming.py](file:///Users/ms.vivekranjan/VIVEK/CODE/PROJECTS/YOLO_Project/SemanticEdgev2/semanticedge/nvr/streaming.py) — Telegram calls removed
- [templates/nvr/explore.html](file:///Users/ms.vivekranjan/VIVEK/CODE/PROJECTS/YOLO_Project/SemanticEdgev2/semanticedge/templates/nvr/explore.html) — Direct card-to-investigation chat, Threads toggle, details modal hover trigger
- [templates/nvr/review.html](file:///Users/ms.vivekranjan/VIVEK/CODE/PROJECTS/YOLO_Project/SemanticEdgev2/semanticedge/templates/nvr/review.html) — Grouped tracked object view with detection timeline strips and Investigate actions
- [templates/nvr/settings.html](file:///Users/ms.vivekranjan/VIVEK/CODE/PROJECTS/YOLO_Project/SemanticEdgev2/semanticedge/templates/nvr/settings.html) — Assistant diagnostics card (replaced Telegram card)
- [nvr/tests.py](file:///Users/ms.vivekranjan/VIVEK/CODE/PROJECTS/YOLO_Project/SemanticEdgev2/semanticedge/nvr/tests.py) — Comprehensive integration & unit tests
- Migrations: `0006_remove_telegramsession_user_alertconversation_and_more.py`
- Removed: `nvr/management/commands/run_openclaw_bot.py`
