---
phase: 05-conditional-patterns
plan: 03
subsystem: integration-template
tags: [home-assistant, copier, jinja2, conditional-wiring, websocket_api, services, coordinator]

# Dependency graph
requires:
  - phase: 05-conditional-patterns
    provides: websocket.py.jinja (async_setup_websocket), services.py.jinja (async_register_services), coordinator_secondary.py.jinja (TemplateSecondaryCoordinator) — all ready for __init__.py wiring

provides:
  - __init__.py.jinja with conditional imports for websocket, services, secondary coordinator
  - __init__.py.jinja with conditional async_setup calls (domain-level, prevents duplicate registration)
  - __init__.py.jinja with conditional secondary coordinator init and runtime_data assignment in async_setup_entry
  - Data dataclass conditionally including coordinator_secondary field
  - End-to-end copier smoke test validation (all-OFF and all-ON)

affects: [any child project generated from this template, Phase 6 and beyond]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Conditional imports after coordinator import — [% if flag %]from .module import fn[% endif %] pattern"
    - "Domain-level setup (websocket, services) in async_setup not async_setup_entry — prevents duplicate registration on second config entry"
    - "Per-entry setup (secondary coordinator) in async_setup_entry — each entry gets its own secondary coordinator instance"
    - "Conditional dataclass field using [% if %] block inside dataclass body"
    - "if/else runtime_data assignment — [% if use_secondary_coordinator %] expanded form [% else %] compact form [% endif %]"

key-files:
  created: []
  modified:
    - "template/custom_components/[[ project_domain ]]/__init__.py.jinja"

key-decisions:
  - "WebSocket and services called in async_setup (not async_setup_entry) — prevents duplicate handler registration when multiple config entries exist"
  - "Secondary coordinator initialized in async_setup_entry — each config entry owns its own secondary coordinator lifecycle"
  - "runtime_data uses if/else branch so all-ON case passes coordinator_secondary=coordinator_secondary to the Data constructor"
  - "Dataclass field [% if use_secondary_coordinator %] block added — field only declared when secondary coordinator exists, preventing type errors"

patterns-established:
  - "Pattern: __init__.py.jinja is a wiring file only — imports and one-line function calls; all logic stays in conditional modules"
  - "Pattern: [% if %] blocks for conditional imports grouped immediately after unconditional imports"
  - "Pattern: smoke tests with all-OFF and all-ON flags validate template correctness end-to-end"

requirements-completed: [COND-05]

# Metrics
duration: 2min
completed: 2026-02-20
---

# Phase 5 Plan 03: __init__.py Conditional Wiring Summary

**WebSocket, services, and secondary coordinator wired into __init__.py.jinja via minimal [% if %] blocks, with end-to-end copier smoke tests (all-OFF and all-ON) confirming complete Phase 5 template correctness**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-20T05:30:04Z
- **Completed:** 2026-02-20T05:31:48Z
- **Tasks:** 2 (Task 1: implementation; Task 2: verification only)
- **Files modified:** 1

## Accomplishments

- Added 8 conditional [% if %] blocks to __init__.py.jinja: 3 imports (websocket, services, secondary coordinator), 1 dataclass field, 2 async_setup calls, 1 secondary coordinator init, 1 if/else runtime_data assignment
- Validated all-features-OFF: no conditional files generated, __init__.py contains no references to websocket/services/secondary, single-step config flow, manifest dependencies = ["frontend"], all Python and JSON parse
- Validated all-features-ON: all conditional files generated (websocket.py, services.py, services.yaml, coordinator_secondary.py), __init__.py contains all three identifiers, multi-step config flow active, manifest dependencies = ["frontend", "websocket_api"], strings/translations have credentials step, all Python and JSON parse, no Jinja2 artifacts

## Task Commits

Each task was committed atomically:

1. **Task 1: Add conditional import and wiring blocks to __init__.py.jinja** - `c7d7477` (feat)
2. **Task 2: Copier smoke test — all features ON and all features OFF** - verification only, no files modified

## Files Created/Modified

- `template/custom_components/[[ project_domain ]]/__init__.py.jinja` - Added 8 conditional [% if %] blocks for websocket imports, services imports, secondary coordinator imports, dataclass field, async_setup calls, async_setup_entry init and runtime_data assignment

## Decisions Made

- Placed websocket and services calls in `async_setup` (domain-level, called once) not `async_setup_entry` (per-entry) — prevents duplicate handler registration per Research Pitfall 2 and Pitfall 3
- Two separate `[% if use_secondary_coordinator %]` blocks in `async_setup_entry`: one for the init+first_refresh, one for the runtime_data if/else — kept them separate for clarity
- Dataclass `coordinator_secondary` field inside `[% if %]` block so the field is only declared when the secondary coordinator feature is enabled

## Deviations from Plan

None - plan executed exactly as written. The verify step counted 7 [% if %] blocks but the action described 8 operations (including the dataclass field); implementation includes all 8 as described in the action steps.

## Issues Encountered

- `copier` command not on PATH — located at `/home/dab/mediaparser-venv/bin/copier` and used full path (consistent with prior phases).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 5 complete: all four conditional feature sets (COND-01 through COND-06) satisfied
- Generated integrations from this template are correct for all flag combinations
- Child projects can now inherit: conditional WebSocket handler, conditional service actions, optional multi-step config flow, optional secondary coordinator
- Phase 6 can proceed with COND-05 (this plan) satisfied

---
*Phase: 05-conditional-patterns*
*Completed: 2026-02-20*

## Self-Check: PASSED

All files found, all commits verified, both smoke tests (all-OFF and all-ON) passed all checks.
