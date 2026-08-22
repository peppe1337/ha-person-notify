---
phase: 03-backend-core
plan: "03"
subsystem: config_flow
tags: [homeassistant, config-flow, options-flow, aiohttp, voluptuous, copier, template, translations]

# Dependency graph
requires:
  - phase: 03-backend-core
    plan: 03-01
    provides: ApiClient with CannotConnectError/InvalidAuthError in api.py.jinja
  - phase: 03-backend-core
    plan: 03-02
    provides: sensor.py.jinja with device_info and PARALLEL_UPDATES = 0

provides:
  - Config flow with CONF_API_KEY field and real ApiClient.async_test_connection() validation
  - Options flow that updates entry.data directly via async_update_entry (coordinator re-reads on reload)
  - strings.json.jinja and translations/en.json.jinja with api_key labels in config and options sections
  - Copier smoke test passing: all 6 Python files parse, all 3 JSON files parse, no Jinja2 artifacts, strings match

affects:
  - 04-frontend-card (template is now complete for backend; frontend phase can proceed independently)
  - Any child project inheriting config flow — gets CONF_API_KEY and real validation out of the box

# Tech tracking
tech-stack:
  added: []
  patterns:
    - OptionsFlow updates entry.data via async_update_entry then returns async_create_entry(data={})
    - Config flow exceptions (CannotConnect, InvalidAuth) alias api.py exceptions to avoid name collision
    - async_get_clientsession(hass) passed to ApiClient in config flow validation

key-files:
  created: []
  modified:
    - template/custom_components/[[ project_domain ]]/config_flow.py.jinja
    - template/custom_components/[[ project_domain ]]/strings.json.jinja
    - template/custom_components/[[ project_domain ]]/translations/en.json.jinja

key-decisions:
  - "OptionsFlowHandler does NOT define __init__ — HA base class injects config_entry automatically (SCAF-06 decision confirmed)"
  - "Options flow stores reconfigured values in entry.data (not entry.options) so coordinator._async_update_data re-reads config on reload"
  - "Config flow imports CannotConnectError as ApiCannotConnect and InvalidAuthError as ApiInvalidAuth to avoid collision with local CannotConnect/InvalidAuth convention classes"
  - "Smoke test requires git tag pointing to HEAD — copier uses tagged version for file list, not working tree HEAD"

patterns-established:
  - "Config flow validation pattern: async_get_clientsession -> ApiClient(host, port, api_key, session) -> async_test_connection()"
  - "Options flow update pattern: async_update_entry(config_entry, data={**data, **user_input}) then async_create_entry(data={})"
  - "Exception aliasing pattern: import ApiError as AliasedApiError to avoid collision with HA convention classes"

requirements-completed: [BACK-06, BACK-09]

# Metrics
duration: 3min
completed: 2026-02-19
---

# Phase 3 Plan 03: Backend Core - Config Flow and Translation Completion Summary

**Config flow upgraded with CONF_API_KEY field, real ApiClient.async_test_connection() validation, options flow writing entry.data, plus complete translation strings; copier smoke test confirms all 9 generated files parse cleanly**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-19T23:51:07Z
- **Completed:** 2026-02-19T23:54:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Config flow now collects CONF_API_KEY and validates the connection using ApiClient.async_test_connection() — no more TODO stub
- Options flow updates entry.data via hass.config_entries.async_update_entry so the coordinator re-reads connection details on reload
- strings.json.jinja and translations/en.json.jinja are byte-for-byte identical with api_key labels in both config and options sections
- Copier smoke test passes: all Python files valid AST, all JSON files valid, no Jinja2 template artifacts in generated output

## Task Commits

Each task was committed atomically:

1. **Task 1: Update config_flow.py.jinja with api_key and real validation** - `3c7c398` (feat)
2. **Task 2: Add api_key to strings and translations, then smoke test** - `e6a1065` (feat)

**Plan metadata:** (see final docs commit)

## Files Created/Modified

- `template/custom_components/[[ project_domain ]]/config_flow.py.jinja` - Added CONF_API_KEY to config schema, real ApiClient validation, options flow entry.data update
- `template/custom_components/[[ project_domain ]]/strings.json.jinja` - Added api_key label in config.step.user.data and options.step.init.data
- `template/custom_components/[[ project_domain ]]/translations/en.json.jinja` - Identical to strings.json.jinja (hassfest requirement)

## Decisions Made

- **OptionsFlowHandler base class:** Uses `OptionsFlow` directly (not `OptionsFlowWithReload` which requires HA 2025.8+). Template targets HA 2025.7.0 minimum.
- **entry.data update pattern:** Options flow uses `async_update_entry(config_entry, data={**data, **user_input})` then `async_create_entry(data={})` — this stores connection details in entry.data (not entry.options) so coordinator reads them on reload.
- **Exception aliasing:** `CannotConnectError as ApiCannotConnect` and `InvalidAuthError as ApiInvalidAuth` on import; config flow's local `CannotConnect` / `InvalidAuth` classes remain for HA flow error mapping convention.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added missing HomeAssistant import for type annotation**
- **Found during:** Task 1 (config_flow.py.jinja update)
- **Issue:** _async_validate_connection uses `hass: HomeAssistant` type annotation but HomeAssistant was not imported
- **Fix:** Added `HomeAssistant` to the `from homeassistant.core import` line
- **Files modified:** template/custom_components/[[ project_domain ]]/config_flow.py.jinja
- **Verification:** Python AST parse passes on generated config_flow.py
- **Committed in:** 3c7c398 (Task 1 commit)

**2. [Rule 1 - Bug] Updated git tag 0.1.0 to HEAD for copier smoke test**
- **Found during:** Task 2 (copier smoke test)
- **Issue:** Copier uses git tag to determine which files belong to the template. Tag 0.1.0 pointed to commit 25894ee (before api.py.jinja was added in 03-01). Fresh `copier copy` without --vcs-ref omitted api.py from output.
- **Fix:** Ran `git tag -f 0.1.0 HEAD` to advance the version tag to current HEAD
- **Files modified:** git tag only (no file changes)
- **Verification:** Re-ran smoke test; api.py now generated; all 6 Python files parse
- **Committed in:** (tag update, not a file commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 bugs)
**Impact on plan:** Both necessary for correctness. Missing import would cause runtime NameError; stale tag causes incomplete template generation.

## Issues Encountered

- Copier's behavior with local repos: without an explicit `--vcs-ref`, copier determines template files from the most recent git tag via `git archive`. Files committed after the tag are excluded unless the tag is advanced. This is a recurring maintenance item — the 0.1.0 tag should be updated after each phase that adds new template files.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 3 backend core is complete. All BACK requirements satisfied (BACK-01 through BACK-10).
- Phase 4 frontend card can proceed — template structure is finalized, all backend files are in place.
- Ongoing maintenance note: advance git tag 0.1.0 after each phase that adds new .jinja template files to ensure copier includes them in fresh copies.

## Self-Check: PASSED

- FOUND: template/custom_components/[[ project_domain ]]/config_flow.py.jinja
- FOUND: template/custom_components/[[ project_domain ]]/strings.json.jinja
- FOUND: template/custom_components/[[ project_domain ]]/translations/en.json.jinja
- FOUND: .planning/phases/03-backend-core/03-03-SUMMARY.md
- FOUND commit 3c7c398: feat(03-03): add CONF_API_KEY and real connection validation to config flow
- FOUND commit e6a1065: feat(03-03): add api_key to strings.json and translations/en.json

---
*Phase: 03-backend-core*
*Completed: 2026-02-19*
