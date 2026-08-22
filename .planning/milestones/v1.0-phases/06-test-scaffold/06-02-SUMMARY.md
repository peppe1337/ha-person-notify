---
phase: 06-test-scaffold
plan: 02
subsystem: testing
tags: [pytest, pytest-homeassistant-custom-component, config-flow, coordinator, copier, jinja2, unittest.mock]

# Dependency graph
requires:
  - phase: 06-test-scaffold
    plan: 01
    provides: "conftest.py.jinja with mock_setup_entry and auto_enable_custom_integrations fixtures"
  - phase: 03-backend-core
    provides: "config_flow.py.jinja with CannotConnect exception and _async_validate_connection function; coordinator.py.jinja with TemplateCoordinator class"

provides:
  - "template/tests/test_config_flow.py.jinja: 4 config flow test cases (successful setup, CannotConnect, duplicate abort, options flow)"
  - "template/tests/test_coordinator.py.jinja: 2 coordinator test cases (successful refresh, UpdateFailed error translation)"

affects:
  - 06-03 (test_websocket.py conditional template follows same mock pattern)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "patch where called (not defined): custom_components.[[ project_domain ]].config_flow._async_validate_connection — not api.ApiClient.async_test_connection"
    - "patch where called (not defined): custom_components.[[ project_domain ]].coordinator.ApiClient.async_get_data — not api.ApiClient.async_get_data"
    - "options flow test: hass.config_entries.options.async_init(entry.entry_id) — not hass.config_entries.flow.async_init"
    - "options flow assertion: entry.data[CONF_API_KEY] (not entry.options) — per Phase 3-03 decision to store options in entry.data"

key-files:
  created:
    - template/tests/test_config_flow.py.jinja
    - template/tests/test_coordinator.py.jinja
  modified: []

key-decisions:
  - "Patch target for config flow: custom_components.[[ project_domain ]].config_flow._async_validate_connection — where the function is called, not where ApiClient is defined (Pitfall 2 from research)"
  - "Patch target for coordinator: custom_components.[[ project_domain ]].coordinator.ApiClient.async_get_data — coordinator module is where ApiClient is imported and used"
  - "Options flow test asserts entry.data[CONF_API_KEY] (not entry.options) — consistent with Phase 3-03 decision that options flow writes to entry.data via async_update_entry"
  - "TemplateCoordinator is a hardcoded class name (not a Copier variable) — imported directly in test template"

patterns-established:
  - "Pattern: mock_setup_entry fixture consumed via parameter in test_form only (test functions that don't need it don't request it)"
  - "Pattern: async_block_till_done() called after async_configure in CREATE_ENTRY flow — required for mock_setup_entry assertion to register"
  - "Pattern: pytest.raises(UpdateFailed) inside the patch context manager — coordinator is created inside patch so mock is active at construction time"

requirements-completed: [TEST-02, TEST-03]

# Metrics
duration: 1min
completed: 2026-02-20
---

# Phase 6 Plan 02: Config Flow and Coordinator Test Templates Summary

**Config flow tests (4 cases: successful setup, CannotConnect error, duplicate abort, options flow) and coordinator tests (2 cases: successful refresh, UpdateFailed error translation) as always-on Copier-rendered test templates**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-02-20T15:52:13Z
- **Completed:** 2026-02-20T15:53:10Z
- **Tasks:** 2
- **Files modified:** 2 (all created)

## Accomplishments

- Created `template/tests/test_config_flow.py.jinja` with 4 test cases covering the complete config flow: successful setup creating a config entry, CannotConnect error displayed to user, duplicate abort when same host:port already configured, and options flow updating entry.data
- Created `template/tests/test_coordinator.py.jinja` with 2 test cases: successful data refresh from mocked ApiClient returning `{"sensor_value": 42, "status": "ok"}`, and failed refresh asserting CannotConnectError is translated to UpdateFailed
- Both files use `[[ ]]` Copier delimiters exclusively — no `{{ }}` Jinja2 syntax — eliminating brace collision with the `_envops` custom delimiter configuration

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test_config_flow.py.jinja with 4 test cases** - `e7cd7d9` (feat)
2. **Task 2: Create test_coordinator.py.jinja with refresh tests** - `6a1ed79` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `template/tests/test_config_flow.py.jinja` - 4 config flow tests: successful setup (uses mock_setup_entry fixture), CannotConnect error, duplicate abort via MockConfigEntry unique_id, and options flow via hass.config_entries.options
- `template/tests/test_coordinator.py.jinja` - 2 coordinator tests: mocked ApiClient.async_get_data returning mock_data, and CannotConnectError side_effect asserting pytest.raises(UpdateFailed)

## Decisions Made

- Patch target `config_flow._async_validate_connection` (where called) rather than `api.ApiClient.async_test_connection` (where defined) — standard Python mock principle; patching the wrong location results in the real function being called
- Patch target `coordinator.ApiClient.async_get_data` (where called in coordinator module) — same principle applied to coordinator tests
- `entry.data[CONF_API_KEY]` asserted (not `entry.options`) in options flow test — consistent with Phase 3-03 design decision that OptionsFlowHandler writes to entry.data via `async_update_entry`, not the separate options store
- `TemplateCoordinator` used as hardcoded class name in test template — it is the actual class name in coordinator.py.jinja, not a user-configurable Copier variable

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- TEST-02 (config flow test coverage) and TEST-03 (coordinator test coverage) requirements satisfied
- Plan 06-03 can now create `[% if use_websocket %]test_websocket.py[% endif %].jinja` using the same MockConfigEntry and patch patterns established here
- All always-on test templates complete; remaining plan covers conditional (optional) test templates

---
*Phase: 06-test-scaffold*
*Completed: 2026-02-20*
