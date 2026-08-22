---
phase: 05-conditional-patterns
plan: 02
subsystem: ha-integration-template
tags: [home-assistant, copier, jinja2, config-flow, coordinator, multi-step-flow]

# Dependency graph
requires:
  - phase: 05-conditional-patterns
    provides: Research for multi-step config flow (Option C decision), secondary coordinator pattern, conditional Jinja2 block strategy

provides:
  - config_flow.py.jinja with [% if use_multi_step_config_flow %] blocks rendering single-step or two-step config flow
  - coordinator_secondary.py.jinja with TemplateSecondaryCoordinator (300s independent poll interval, own ApiClient)
  - const.py.jinja with DEFAULT_SECONDARY_SCAN_INTERVAL = 300
  - strings.json.jinja and translations/en.json.jinja with conditional credentials step for multi-step flow
  - Dead config_flow_multi_step.py stub deleted

affects: [05-03-__init__.py-conditional-wiring, any plan testing copier smoke output for multi-step or secondary coordinator flags]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "[% if use_multi_step_config_flow %] / [% else %] / [% endif %] blocks inline in single .jinja file to produce alternate class body"
    - "Multi-step flow: __init__ with self._data dict, async_step_user collects host/port + chains, async_step_credentials collects api_key + sets unique_id + validates"
    - "unique_id and _abort_if_unique_id_configured in LAST step only (after all data collected)"
    - "Secondary coordinator: own ApiClient instance to avoid shared state race conditions"
    - "DEFAULT_SECONDARY_SCAN_INTERVAL always present in const.py (harmless if unused, avoids conditional const imports)"

key-files:
  created: []
  modified:
    - "template/custom_components/[[ project_domain ]]/config_flow.py.jinja"
    - "template/custom_components/[[ project_domain ]]/[% if use_secondary_coordinator %]coordinator_secondary.py[% endif %].jinja"
    - "template/custom_components/[[ project_domain ]]/const.py.jinja"
    - "template/custom_components/[[ project_domain ]]/strings.json.jinja"
    - "template/custom_components/[[ project_domain ]]/translations/en.json.jinja"
  deleted:
    - "template/custom_components/[[ project_domain ]]/[% if use_multi_step_config_flow %]config_flow_multi_step.py[% endif %].jinja"

key-decisions:
  - "Option C confirmed: multi-step flow inlined in config_flow.py.jinja via [% if %] blocks — single-step [% else %] branch is byte-for-byte identical to pre-edit output"
  - "unique_id set in async_step_credentials (last step) not async_step_user (first step) — anti-pattern from research"
  - "coordinator_secondary creates its own ApiClient (not shared with primary) to avoid concurrent refresh race conditions"
  - "DEFAULT_SECONDARY_SCAN_INTERVAL = 300 always included in const.py (unconditional) — harmless if unused, avoids conditional import complexity"
  - "Dead config_flow_multi_step.py stub deleted — HA only discovers config_flow.py; the stub was unreachable"

patterns-established:
  - "Inline conditional Jinja2 blocks ([% if %]/[% else %]/[% endif %]) inside existing .jinja files to produce alternate implementations"
  - "Leading-comma JSON convention: conditional block contains ,\"key\": {...} so false-branch preserves valid JSON without trailing commas"
  - "Multi-step config flow accumulates data in self._data dict across steps"

requirements-completed: [COND-03, COND-04]

# Metrics
duration: 1min
completed: 2026-02-20
---

# Phase 05 Plan 02: Multi-Step Config Flow and Secondary Coordinator Summary

**Multi-step config flow inlined in config_flow.py.jinja via [% if %] blocks, dead stub deleted, and TemplateSecondaryCoordinator with 300s independent poll interval and own ApiClient implemented**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-02-20T05:24:41Z
- **Completed:** 2026-02-20T05:26:00Z
- **Tasks:** 2
- **Files modified:** 5 modified, 1 deleted

## Accomplishments

- config_flow.py.jinja now conditionally renders either single-step (default) or two-step (host/port then api_key) config flow using [% if use_multi_step_config_flow %] blocks — single-step branch is identical to pre-edit output (no regression)
- Dead [% if use_multi_step_config_flow %]config_flow_multi_step.py[% endif %].jinja stub deleted (HA only discovers config_flow.py; stub was unreachable)
- coordinator_secondary.py.jinja replaced from stub to working TemplateSecondaryCoordinator with 300s update_interval and its own ApiClient
- strings.json.jinja and translations/en.json.jinja updated with conditional credentials step and api_key placement
- const.py.jinja extended with DEFAULT_SECONDARY_SCAN_INTERVAL = 300

## Task Commits

Each task was committed atomically:

1. **Task 1: Inline multi-step config flow into config_flow.py.jinja and update translations** - `b487fb2` (feat)
2. **Task 2: Implement secondary coordinator and add const** - `50ca11c` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `template/custom_components/[[ project_domain ]]/config_flow.py.jinja` - Added [% if use_multi_step_config_flow %] conditional blocks for schema definitions and class body methods (two-step vs single-step flow)
- `template/custom_components/[[ project_domain ]]/strings.json.jinja` - Conditional api_key in user step data; conditional credentials step with api_key
- `template/custom_components/[[ project_domain ]]/translations/en.json.jinja` - Identical conditional changes matching strings.json.jinja
- `template/custom_components/[[ project_domain ]]/[% if use_secondary_coordinator %]coordinator_secondary.py[% endif %].jinja` - Full TemplateSecondaryCoordinator implementation (was stub)
- `template/custom_components/[[ project_domain ]]/const.py.jinja` - Added DEFAULT_SECONDARY_SCAN_INTERVAL = 300
- `template/custom_components/[[ project_domain ]]/[% if use_multi_step_config_flow %]config_flow_multi_step.py[% endif %].jinja` - DELETED (dead code)

## Decisions Made

- **Option C for multi-step flow:** Single config_flow.py.jinja with [% if %] blocks is the correct approach — eliminates the unreachable stub file and keeps HA's config_flow.py discovery working
- **unique_id placement:** async_set_unique_id and _abort_if_unique_id_configured called in async_step_credentials (last step), not async_step_user — all data must be collected before uniqueness check
- **Independent ApiClient per coordinator:** Each coordinator owns its ApiClient instance to prevent race conditions during concurrent refreshes
- **Unconditional DEFAULT_SECONDARY_SCAN_INTERVAL:** Constant always present in const.py regardless of use_secondary_coordinator flag — simpler than conditional import, harmless if unused
- **Leading-comma JSON conditional pattern:** Conditional block in strings.json includes leading comma inside the [% if %] block (,"credentials": {...}) so the JSON remains valid when flag is false

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- config_flow.py.jinja and coordinator_secondary.py.jinja ready for wiring into __init__.py.jinja
- Phase 05 plan 03 (__init__.py conditional wiring for use_secondary_coordinator and use_multi_step_config_flow) can now proceed — both modules export their expected entry points (TemplateSecondaryCoordinator)
- COND-03 and COND-04 requirements satisfied

---
*Phase: 05-conditional-patterns*
*Completed: 2026-02-20*

## Self-Check: PASSED

All files found, stub confirmed deleted, commits b487fb2 and 50ca11c verified in git log.
