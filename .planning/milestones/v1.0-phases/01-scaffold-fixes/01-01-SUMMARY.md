---
phase: 01-scaffold-fixes
plan: 01
subsystem: integration-core
tags: [home-assistant, hacs, static-path, runtime-data, aiohttp, coordinator]

# Dependency graph
requires: []
provides:
  - async_setup with StaticPathConfig static path registration (domain-level, not per-entry)
  - HacsTemplateData dataclass storing coordinator in entry.runtime_data
  - HacsTemplateConfigEntry type alias for typed config entry access
  - coordinator.py using HA-managed HTTP session via async_get_clientsession
  - sensor.py accessing coordinator via entry.runtime_data.coordinator
  - Correct frontend URL prefix (/{DOMAIN}/ not /hacsfiles/)
  - hacs.json requiring HA 2025.7.0 minimum
affects: [02-copier-template, all phases using coordinator or sensor patterns]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "async_setup for domain-level setup (static paths); async_setup_entry for per-entry setup"
    - "entry.runtime_data = HacsTemplateData(coordinator=...) instead of hass.data[DOMAIN]"
    - "async_get_clientsession(hass) for HA-managed HTTP sessions in coordinator"
    - "HacsTemplateConfigEntry type alias for typed runtime_data access across platform files"
    - "async_unload_entry: only async_unload_platforms, no manual data cleanup needed"

key-files:
  created: []
  modified:
    - custom_components/hacs_template/__init__.py
    - custom_components/hacs_template/coordinator.py
    - custom_components/hacs_template/sensor.py
    - custom_components/hacs_template/const.py
    - hacs.json

key-decisions:
  - "Static path registration in async_setup (not async_setup_entry) to prevent duplicate registration on reload"
  - "entry.runtime_data over hass.data[DOMAIN] — HA-recommended pattern, auto-cleaned on unload"
  - "async_get_clientsession(hass) over raw aiohttp.ClientSession — HA manages lifecycle"
  - "Frontend URL uses /{DOMAIN}/ prefix; /hacsfiles/ is HACS-owned namespace for downloaded cards"
  - "hacs.json homeassistant 2025.7.0 — minimum required for async_register_static_paths API"

patterns-established:
  - "async_setup: register domain-level resources (static paths, services) once"
  - "HacsTemplateData: typed dataclass on runtime_data replaces hass.data dict"
  - "Type alias pattern: type HacsTemplateConfigEntry = ConfigEntry[HacsTemplateData]"

requirements-completed: [SCAF-01, SCAF-02, SCAF-04, SCAF-07, SCAF-08]

# Metrics
duration: 1min
completed: 2026-02-19
---

# Phase 1 Plan 01: Scaffold Fixes — Integration Core Summary

**HA 2025.7+ compatible integration core: async_register_static_paths + StaticPathConfig, entry.runtime_data pattern, and HA-managed HTTP session replacing all deprecated and removed APIs**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-19T19:51:49Z
- **Completed:** 2026-02-19T19:53:08Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Replaced removed `register_static_path` sync API with `async_register_static_paths` + `StaticPathConfig` in a new `async_setup` function (domain-level, not per-entry)
- Migrated `async_setup_entry` from `hass.data[DOMAIN]` anti-pattern to `entry.runtime_data` using a `HacsTemplateData` dataclass and `HacsTemplateConfigEntry` type alias
- Simplified `async_unload_entry` to a single `async_unload_platforms` call — runtime_data is auto-cleaned
- Added `async_get_clientsession(hass)` to coordinator to replace raw aiohttp session usage
- Fixed FRONTEND_SCRIPT_URL from `/hacsfiles/` to `/{DOMAIN}/` prefix and bumped hacs.json minimum HA to 2025.7.0

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix __init__.py, const.py, hacs.json** - `e91ace6` (feat)
2. **Task 2: Fix coordinator.py and sensor.py** - `fd7077f` (feat)

**Plan metadata:** (see docs commit below)

## Files Created/Modified

- `custom_components/hacs_template/__init__.py` - Full rewrite: async_setup + StaticPathConfig, HacsTemplateData dataclass, HacsTemplateConfigEntry type alias, runtime_data pattern, clean unload
- `custom_components/hacs_template/coordinator.py` - Added async_get_clientsession import and usage; updated TODO to guide session handoff to API client
- `custom_components/hacs_template/sensor.py` - Uses HacsTemplateConfigEntry and entry.runtime_data.coordinator; removed hass.data usage and now-unnecessary DOMAIN/ConfigEntry imports
- `custom_components/hacs_template/const.py` - Fixed FRONTEND_SCRIPT_URL prefix from /hacsfiles/ to /{DOMAIN}/
- `hacs.json` - Bumped homeassistant minimum from 2024.1.0 to 2025.7.0

## Decisions Made

- Static path registration belongs in `async_setup` so it runs once at domain load, not once per config entry (prevents RuntimeError "path already registered" on second entry or reload)
- `entry.runtime_data` is the current HA-recommended pattern; `hass.data[DOMAIN]` is an anti-pattern that requires manual cleanup
- `async_unload_entry` no longer needs a conditional or hass.data cleanup — `runtime_data` is auto-cleaned when the entry is unloaded
- Frontend URL prefix `/{DOMAIN}/` is correct for integration-bundled cards; `/hacsfiles/` is the HACS-owned namespace for cards HACS itself downloads

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Integration core is fully corrected for HA 2025.7+ compatibility
- Plan 01-02 (config flow fixes) is independent (disjoint file set) and can run in parallel or sequentially
- Phase 2 (Copier template) can reference these corrected patterns for all generated files

## Self-Check: PASSED

All files verified present and all commits verified in git history:
- `custom_components/hacs_template/__init__.py` — FOUND
- `custom_components/hacs_template/coordinator.py` — FOUND
- `custom_components/hacs_template/sensor.py` — FOUND
- `custom_components/hacs_template/const.py` — FOUND
- `hacs.json` — FOUND
- `.planning/phases/01-scaffold-fixes/01-01-SUMMARY.md` — FOUND
- Commit `e91ace6` (Task 1) — FOUND
- Commit `fd7077f` (Task 2) — FOUND
- Commit `90916b5` (metadata) — FOUND
