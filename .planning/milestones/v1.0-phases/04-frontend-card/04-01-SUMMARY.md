---
phase: 04-frontend-card
plan: "01"
subsystem: ui
tags: [homeassistant, lovelace, lit-element, custom-card, ha-spinner, ha-alert, copier, template, javascript]

# Dependency graph
requires:
  - phase: 03-backend-core
    provides: __init__.py.jinja with static path registration for frontend card JS
  - phase: 02-copier-template-scaffolding
    provides: _envops [[ ]] delimiters enabling .js.jinja files without Python brace collision

provides:
  - LitElement card template with four render states (loading/ha-spinner, error/ha-alert, no-entity, normal)
  - getGridOptions() for sections view 12-column grid (HA 2024.11+)
  - getStubConfig(hass) that finds a real sensor entity as default
  - customElements.get() duplicate registration guards on both define() calls
  - Lovelace resource auto-registration in __init__.py for storage-mode dashboards
  - Copier smoke test passing: rendered JS and Python both clean

affects:
  - Any child project generated from this template — gets production-ready card immediately
  - Next plan in phase 04 (if any) — card template is now complete

# Tech tracking
tech-stack:
  added: []
  patterns:
    - ha-spinner (not ha-circular-progress) for loading state — correct for HA 2025.4+
    - ha-alert alert-type="error" for entity-not-found state
    - Four-state render() pattern: loading -> no-entity -> error -> normal
    - getGridOptions() returns {rows:3, columns:6, min_rows:2, min_columns:3} for sections view
    - getStubConfig(hass) finds first sensor.* entity; falls back to empty string
    - if (!customElements.get(...)) guards around customElements.define() calls
    - _async_register_lovelace_resource() helper with defensive try/except
    - lovelace.resources.loaded check before async_create_item, event listener fallback

key-files:
  created: []
  modified:
    - template/custom_components/[[ project_domain ]]/frontend/[[ project_domain ]]-card.js.jinja
    - template/custom_components/[[ project_domain ]]/__init__.py.jinja

key-decisions:
  - "ha-spinner used for loading state — ha-circular-progress was removed in frontend 20250326.0 (~HA 2025.4); template targets HA 2025.7+ so ha-spinner is correct"
  - "getGridOptions() added as instance method (not static) per HA developer blog specification"
  - "Lovelace auto-registration wrapped in broad try/except with debug log — community API pattern (not official); fallback to manual is acceptable"
  - "getStubConfig(hass) guards against undefined hass parameter — HA may call it before hass is set in some code paths"
  - "Git tag 0.1.0 advanced to HEAD after modifying template files — copier uses tagged version for file list"

patterns-established:
  - "Four-state render pattern: (!hass||!config)->spinner; (!entityId)->empty; (!stateObj)->error; normal render"
  - "CSS only uses CSS custom properties (var(--...)) — no hex/rgb values anywhere in card styles"
  - ":host { display: block; } replaces ha-card { padding } to avoid double-padding"
  - "Lovelace resource registration pattern: check mode=='storage', check loaded, else listen for lovelace_updated"

requirements-completed: [CARD-01, CARD-02, CARD-03, CARD-04, CARD-05, CARD-06, CARD-07, CARD-08]

# Metrics
duration: 2min
completed: 2026-02-20
---

# Phase 4 Plan 01: Frontend Card - Complete Card Template Summary

**LitElement card template with ha-spinner/ha-alert loading/error states, getGridOptions() sections view support, smart getStubConfig(hass) with sensor entity lookup, duplicate element guards, and Lovelace resource auto-registration for storage-mode dashboards**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-20T01:29:51Z
- **Completed:** 2026-02-20T01:32:27Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Card render() now handles all four states: loading (ha-spinner), no entity configured, entity not found in hass.states (ha-alert error), and normal entity display
- getGridOptions() enables the card in HA 2024.11+ sections view with 12-column grid sizing
- getStubConfig(hass) finds the first real `sensor.*` entity for the card picker preview
- customElements.define() calls guarded against duplicate registration on integration reload
- __init__.py auto-registers the card JS as a Lovelace resource for storage-mode dashboards with a defensive try/except fallback
- Copier smoke test passed all 14 checks: no Jinja artifacts, all features present in rendered output, Python AST valid

## Task Commits

Each task was committed atomically:

1. **Task 1: Enhance card JS template** - `22cf8cf` (feat)
2. **Task 2: Add Lovelace resource auto-registration** - `69b1850` (feat)
3. **Task 3: Copier smoke test + git tag advancement** - (tag update only, no file changes — smoke test is verification, not a file modification)

**Plan metadata:** (see final docs commit)

## Files Created/Modified

- `template/custom_components/[[ project_domain ]]/frontend/[[ project_domain ]]-card.js.jinja` - Added ha-spinner loading state, ha-alert error state, four-state render(), getGridOptions(), getStubConfig(hass) with sensor lookup, duplicate element guards, :host CSS, .loading flex CSS, removed ha-card double-padding rule
- `template/custom_components/[[ project_domain ]]/__init__.py.jinja` - Added _async_register_lovelace_resource() helper and Lovelace resource auto-registration block in async_setup()

## Decisions Made

- **ha-spinner (not ha-circular-progress):** ha-circular-progress was removed in HA frontend 20250326.0 (~HA 2025.4). Template targets HA 2025.7 minimum, so ha-spinner is the correct component.
- **getGridOptions() as instance method:** Per HA developer blog, getGridOptions() must NOT be static — it is called on card instances.
- **Lovelace auto-registration with try/except:** The lovelace.resources API is a community pattern (not official HA API). Broad exception handling ensures the integration loads cleanly even if the API changes; user can add the resource manually.
- **getStubConfig(hass) hass guard:** Added `if (!hass)` guard because HA may call getStubConfig without a hass argument in some card picker code paths.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stale git tag required advancement before smoke test**
- **Found during:** Task 3 (copier smoke test)
- **Issue:** First copier copy with tag still pointing to e6a1065 (Phase 03-03 head) generated the old card JS without the new enhancements. This is the same recurring pattern documented in 03-03 SUMMARY.
- **Fix:** Advanced git tag 0.1.0 to HEAD (69b1850) before re-running smoke test
- **Files modified:** git tag only (no file changes)
- **Verification:** Re-ran copier copy; rendered card JS contained all 11 expected features
- **Committed in:** (tag update, not a file commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - stale git tag)
**Impact on plan:** Tag advancement is a known recurring maintenance step documented in STATE.md decisions. No scope creep.

## Issues Encountered

- Git tag pattern: copier uses the most recent git tag to determine which template files to include. Any phase that adds or modifies template files must advance the tag before running smoke tests. This is now documented as a standing pattern in STATE.md.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 4 Plan 01 is the only plan in Phase 4. The frontend card template is complete.
- All 8 CARD requirements satisfied (CARD-01 through CARD-08).
- Generated card is production-ready: handles all lifecycle states, appears in card picker, renders with HA theme colors, supports masonry and sections views, and auto-registers as a dashboard resource.
- Child projects generated from the template will get a fully functional card out of the box without any additional configuration.

## Self-Check: PASSED

- FOUND: template/custom_components/[[ project_domain ]]/frontend/[[ project_domain ]]-card.js.jinja
- FOUND: template/custom_components/[[ project_domain ]]/__init__.py.jinja
- FOUND: .planning/phases/04-frontend-card/04-01-SUMMARY.md (this file)
- FOUND commit 22cf8cf: feat(04-01): enhance card JS template
- FOUND commit 69b1850: feat(04-01): add Lovelace resource auto-registration

---
*Phase: 04-frontend-card*
*Completed: 2026-02-20*
