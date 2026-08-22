---
phase: 03-backend-core
plan: 01
subsystem: api
tags: [aiohttp, home-assistant, coordinator, jinja2, copier, template]

# Dependency graph
requires:
  - phase: 02-copier-template-scaffolding
    provides: Copier template structure with [[ ]] / [% %] custom delimiters and .jinja suffix files

provides:
  - ApiClient base class template (api.py.jinja) with auth headers, timeout, error handling, test_connection, and get_data
  - CannotConnectError and InvalidAuthError exception classes for backend error discrimination
  - Coordinator wired to ApiClient — creates client from entry.data, calls async_get_data in _async_update_data
  - const.py.jinja cleaned of shadowed CONF_* constants; DEFAULT_TIMEOUT = 30 added

affects:
  - 03-02-PLAN.md (sensor pattern — reads coordinator data)
  - 03-03-PLAN.md (config flow — uses CONF_HOST/CONF_PORT/CONF_API_KEY from homeassistant.const)
  - Any future phase that adds API endpoints (override async_get_data / add methods to ApiClient)

# Tech tracking
tech-stack:
  added: [aiohttp (ClientTimeout, ClientConnectionError, ClientSession usage patterns)]
  patterns:
    - ApiClient as injectable dependency (passed via session, not created internally)
    - CannotConnectError / InvalidAuthError as typed exceptions distinct from config_flow exceptions
    - Coordinator._async_update_data wraps CannotConnectError -> UpdateFailed
    - CONF_* sourced from homeassistant.const only (not shadowed locally in const.py)

key-files:
  created:
    - template/custom_components/[[ project_domain ]]/api.py.jinja
  modified:
    - template/custom_components/[[ project_domain ]]/coordinator.py.jinja
    - template/custom_components/[[ project_domain ]]/const.py.jinja

key-decisions:
  - "CONF_HOST/CONF_PORT/CONF_API_KEY imported from homeassistant.const (not shadowed in const.py) — eliminates import confusion identified in Research Pitfall 1"
  - "ApiClient._get_auth_headers() is overridable — supports Bearer token default but allows query-param or body auth override"
  - "CannotConnectError covers connection, client, and timeout errors — keeps exception surface minimal for coordinator"

patterns-established:
  - "ApiClient pattern: injectable session, configurable timeout, typed exceptions, overridable auth"
  - "Coordinator pattern: creates client in __init__ from entry.data, delegates fetch to client.async_get_data()"
  - "Error translation pattern: CannotConnectError -> UpdateFailed in coordinator, never raw exceptions"

requirements-completed: [BACK-01, BACK-02, BACK-03]

# Metrics
duration: 1min
completed: 2026-02-19
---

# Phase 3 Plan 01: Backend Core - ApiClient and Coordinator Summary

**aiohttp ApiClient base class with Bearer auth, timeout, and typed exceptions wired into HA DataUpdateCoordinator via injectable session pattern**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-02-19T23:47:17Z
- **Completed:** 2026-02-19T23:48:10Z
- **Tasks:** 2
- **Files modified:** 3 (1 created, 2 updated)

## Accomplishments

- Created api.py.jinja with complete ApiClient class — CannotConnectError, InvalidAuthError, Bearer auth headers, configurable aiohttp.ClientTimeout, authenticated _request(), async_test_connection(), async_get_data()
- Cleaned const.py.jinja of shadowed CONF_HOST/CONF_PORT/CONF_API_KEY constants; added DEFAULT_TIMEOUT = 30
- Wired coordinator.py.jinja to ApiClient — imports from homeassistant.const, initializes client from entry.data, translates CannotConnectError to UpdateFailed in _async_update_data

## Task Commits

Each task was committed atomically:

1. **Task 1: Create api.py.jinja and update const.py.jinja** - `1deb3d3` (feat)
2. **Task 2: Wire ApiClient into coordinator.py.jinja** - `dcd3936` (feat)

## Files Created/Modified

- `template/custom_components/[[ project_domain ]]/api.py.jinja` - New ApiClient base class with CannotConnectError, InvalidAuthError, Bearer auth, timeout, _request, async_test_connection, async_get_data
- `template/custom_components/[[ project_domain ]]/const.py.jinja` - Removed CONF_* shadowing; added DEFAULT_TIMEOUT = 30
- `template/custom_components/[[ project_domain ]]/coordinator.py.jinja` - Wired to ApiClient; imports from homeassistant.const; _async_update_data calls async_get_data()

## Decisions Made

- CONF_HOST/CONF_PORT/CONF_API_KEY are imported from `homeassistant.const` only. The local shadows in const.py.jinja caused import confusion (Research Pitfall 1) and have been removed.
- `_get_auth_headers()` is a separate overridable method so child projects can swap Bearer token auth for query-param or request-body auth without subclassing the entire _request().
- Both connection errors and timeouts raise CannotConnectError — single exception type simplifies coordinator error handling.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- ApiClient and Coordinator patterns are complete. Phase 3 Plan 02 (sensor pattern) can read coordinator data via entry.runtime_data.coordinator.
- Phase 3 Plan 03 (config flow) should import CONF_HOST/CONF_PORT/CONF_API_KEY from homeassistant.const (not .const).
- TODO comments in async_test_connection (/health) and async_get_data (/api/data) are intentional placeholders for child project customization.

---
*Phase: 03-backend-core*
*Completed: 2026-02-19*
