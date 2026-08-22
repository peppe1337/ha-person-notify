---
phase: 06-test-scaffold
plan: 03
subsystem: testing
tags: [pytest, pytest-homeassistant-custom-component, websocket, copier, jinja2, conditional-filename, unittest.mock]

# Dependency graph
requires:
  - phase: 06-test-scaffold
    plan: 02
    provides: "test_config_flow.py.jinja and test_coordinator.py.jinja with established MockConfigEntry and patch patterns"
  - phase: 05-conditional-patterns
    plan: 01
    provides: "websocket.py.jinja with coordinator.ApiClient.async_get_data as the mock patch target"

provides:
  - "template/tests/[% if use_websocket %]test_websocket.py[% endif %].jinja: conditional WebSocket command test (generated only when use_websocket=true)"

affects:
  - "Phase 7 if any: all Phase 6 test templates complete, no further test scaffold work planned"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Conditional test filename pattern: [% if use_websocket %]test_websocket.py[% endif %].jinja — same pattern as source conditional files in Phase 5"
    - "hass_ws_client fixture from pytest-homeassistant-custom-component for WebSocket command testing"
    - "Full integration setup in WebSocket test: async_setup(entry.entry_id) + async_block_till_done() before ws_client connection"
    - "patch coordinator.ApiClient.async_get_data (where used) prevents real API calls during async_setup"

key-files:
  created:
    - template/tests/[% if use_websocket %]test_websocket.py[% endif %].jinja
  modified: []

key-decisions:
  - "Conditional test filename uses [% if use_websocket %]test_websocket.py[% endif %].jinja — identical pattern to Phase 5 source conditionals; entire base+extension inside [% if %] block"
  - "WebSocket test performs full integration setup (async_setup + async_block_till_done) before ws_client — WebSocket handlers are registered in async_setup and need live integration context"
  - "Patch target: custom_components.[[ project_domain ]].coordinator.ApiClient.async_get_data — consistent with test_coordinator.py.jinja patch target (where called in coordinator module)"

patterns-established:
  - "Pattern: conditional feature tests mirror conditional source modules — test_websocket.py appears iff websocket.py appears"
  - "Pattern: f-string for WS command type in test: f\"{DOMAIN}/get_data\" — matches WS_TYPE_GET_DATA constant definition in websocket.py"

requirements-completed: [TEST-04]

# Metrics
duration: 1min
completed: 2026-02-20
---

# Phase 6 Plan 03: Conditional WebSocket Test Template Summary

**Conditional test_websocket.py.jinja using [% if use_websocket %] filename pattern, with copier smoke tests confirming file inclusion (all-ON) and exclusion (all-OFF)**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-02-20T15:55:30Z
- **Completed:** 2026-02-20T15:56:51Z
- **Tasks:** 2
- **Files modified:** 1 (created)

## Accomplishments

- Created `template/tests/[% if use_websocket %]test_websocket.py[% endif %].jinja` with a single `test_websocket_get_data` test case that performs full integration setup, connects via `hass_ws_client`, sends `{DOMAIN}/get_data` command, and asserts the coordinator data is returned
- Copier smoke test all-OFF (use_websocket=false): 9 checks all pass — 6 test files present, test_websocket.py correctly absent, domain variables substituted in conftest.py and test_config_flow.py
- Copier smoke test all-ON (use_websocket=true): 8 checks all pass — test_websocket.py present and domain variable `test_integration` substituted in patch target and import paths; no Jinja2 artifacts in any test files

## Task Commits

Each task was committed atomically:

1. **Task 1: Create conditional test_websocket.py.jinja** - `aac19a3` (feat)
2. **Task 2: Copier smoke test validation** - No file changes; validation-only task confirmed via smoke tests

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `template/tests/[% if use_websocket %]test_websocket.py[% endif %].jinja` — Conditional WebSocket test: `test_websocket_get_data` uses `hass_ws_client` fixture, patches `coordinator.ApiClient.async_get_data`, runs full integration setup, sends WS command, asserts `result["success"]` and `result["result"]`

## Decisions Made

- Conditional filename `[% if use_websocket %]test_websocket.py[% endif %].jinja` follows identical pattern to Phase 5 source conditional files — entire `test_websocket.py` base+extension inside `[% if %]` block so false renders to empty string and copier skips the file
- Full integration setup required in WebSocket test: `async_setup(entry.entry_id)` + `async_block_till_done()` — WebSocket handlers are registered in `async_setup` via `async_setup_websocket(hass)`, not in `async_setup_entry`, so the WS client connection must happen after full setup
- Patch target `coordinator.ApiClient.async_get_data` prevents real API calls during setup and seeds `coordinator.data` with mock return value `{"sensor_value": 42}` which the WebSocket handler then returns to the client

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- TEST-04 (WebSocket test coverage) requirement satisfied
- Phase 6 (Test Scaffold) is now complete: TEST-01 through TEST-05 all satisfied
- All 3 plans of Phase 6 complete: pyproject.toml + conftest (06-01), test_config_flow + test_coordinator (06-02), test_websocket conditional (06-03)
- Phase 7 planning can begin (if applicable); the complete test scaffold is ready for use in child projects

---
*Phase: 06-test-scaffold*
*Completed: 2026-02-20*
