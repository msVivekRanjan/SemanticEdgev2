# Lessons Learned & Operational Guidelines

## Pattern: Operator Workflow Integration (Explore → Direct Investigation Chat → Review)

### Context & Mistake
- When designing the Assistant UI, it was initially built as a standalone "Security Assistant" auxiliary tool on Explore requiring extra clicks (or opening a generic drawer) instead of making the Explore cards directly open the investigation chat.
- Review view was originally treating events as a flat list, whereas Explore groups events by tracked object identity `(class, track_id, camera)`. The operator expects identical grouping and mental models across both Explore and Review.

### Rules to Prevent Recurrence
1. **Direct Action Over Intermediate Layers**:
   - In search/explore interfaces, when an operator clicks on an item to investigate, take them directly into the context-bound conversation/investigation workflow without interstitial confirmation modals.
   - Retain secondary inspectors (like metadata modal) as discrete hover/secondary controls (`.card-details-btn`).

2. **Consistent Identity Models Across Tabs**:
   - Maintain identical grouping keys between Explore and Review (`(class_name, track_id, camera_id)`).
   - Review timelines should display chronological detection strips grouped by physical tracked object rather than isolated flat cards.

3. **Context Backwards-Compatibility**:
   - When refactoring template context from flat lists (e.g. `events`) to grouped hierarchies (`tracked_objects`), preserve convenience flat lists in context (`context["events"]`) to maintain backwards compatibility with existing test assertions and downstream components.

## Pattern: Clean Separation of Functional Workspaces (Explore vs Review)

### Context & Mistake
- Conflating object discovery (search, filter, category grids) with conversational investigation in the same tab led to a cluttered hybrid UI with side drawers.
- Explore must be dedicated exclusively as the full-page ChatGPT-style investigation workspace (threads list + message stream + context banner + input).
- Review must host the object discovery and historical search workspace (class/camera/datetime filters, categories gallery, detection detail modal), with prominent "Investigate" actions directing into Explore.

### Rules to Prevent Recurrence
1. **Never Layer Chat Drawers Over Exploration Grids**:
   - If an assistant/chat experience is central to operator investigations, give it a dedicated full-page workspace centered on threads and message flow.
2. **Review Owns Discovery, Explore Owns Investigation**:
   - Discovery tasks (filtering by time, class, camera, keyword) belong in Review.
   - Deep-dive reasoning, evidence generation, and multi-turn queries belong in Explore.
   - Deep-link between the two seamlessly using URL parameters (`?event_id=...&investigate=1` and `/nvr/review/?event_id=...`).

