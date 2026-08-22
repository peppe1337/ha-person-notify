---
phase: 05-conditional-patterns
plan: 01
subsystem: integration-template
tags: [websocket_api, services, SupportsResponse, conditional-templates, copier, home-assistant]

# Dependency graph
requires:
  - phase: 02-copier-template-scaffolding
    provides: conditional filename pattern ([% if flag %]name.py[% endif %].jinja) and _envops [[ ]] / [% %] delimiters
  - phase: 03-backend-core
    provides: const.py DOMAIN constant and coordinator runtime_data structure used by websocket handler

provides:
  - WebSocket command handler template (websocket.py.jinja) with async_setup_websocket registration function
  - Service action handler template (services.py.jinja) with async_register_services callback and SupportsResponse.OPTIONAL
  - services.yaml conditional template for hassfest service documentation
  - manifest.json conditional websocket_api dependency gated by use_websocket flag

affects:
  - 05-02 (or future __init__.py wiring plan): async_setup_websocket and async_register_services are ready to import

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "@websocket_api.websocket_command outermost decorator, @websocket_api.async_response second — decorator order is critical"
    - "Services registered via async_register_services called from async_setup (not async_setup_entry) — prevents duplicate registration"
    - "SupportsResponse.OPTIONAL allows service to work in automations without forced return value"
    - "Conditional YAML template uses same [% if %]filename[% endif %].jinja pattern as Python stubs"
    - "Copier Jinja2 block inside JSON value is valid — produces valid JSON for both true/false flag states"

key-files:
  created:
    - "template/custom_components/[[ project_domain ]]/[% if use_services %]services.yaml[% endif %].jinja"
  modified:
    - "template/custom_components/[[ project_domain ]]/[% if use_websocket %]websocket.py[% endif %].jinja"
    - "template/custom_components/[[ project_domain ]]/[% if use_services %]services.py[% endif %].jinja"
    - "template/custom_components/[[ project_domain ]]/manifest.json.jinja"

key-decisions:
  - "websocket.py imports coordinator type lazily via local import inside handler (noqa: PLC0415) to avoid circular import at module level"
  - "manifest.json uses [% if use_websocket %], 'websocket_api'[% endif %] inline — comma placement inside the conditional block ensures valid JSON when false"
  - "services.yaml created as new conditional file (no Phase 2 stub existed) matching the established [% if %]name.yaml[% endif %].jinja pattern"

patterns-established:
  - "Pattern: async WebSocket handler wraps coordinator access in entries guard — connection.send_error if no config entries"
  - "Pattern: ServiceResponse handler returns None when call.return_response is False — SupportsResponse.OPTIONAL compatibility"
  - "Pattern: Both websocket.py and services.py export a single registration function (async_setup_websocket / async_register_services) for __init__.py wiring"

requirements-completed: [COND-01, COND-02, COND-06]

# Metrics
duration: 1min
completed: 2026-02-20
---

# Phase 5 Plan 01: Conditional Patterns (WebSocket + Services) Summary

**WebSocket command handler with @websocket_command/@async_response decorators and service action handler with SupportsResponse.OPTIONAL, plus conditional manifest websocket_api dependency and new services.yaml template**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-20T05:24:28Z
- **Completed:** 2026-02-20T05:25:29Z
- **Tasks:** 2
- **Files modified:** 4 (3 modified, 1 created)

## Accomplishments

- Replaced websocket.py stub with complete async handler: @websocket_command + @async_response decorators in correct order, coordinator.data lookup via entries[0].runtime_data.coordinator, async_setup_websocket registration callback
- Replaced services.py stub with complete SupportsResponse.OPTIONAL handler: SERVICE_QUERY constant, SERVICE_SCHEMA with vol.Required("query"), _async_handle_query returning dict or None based on call.return_response, async_register_services callback
- Created new services.yaml conditional template (no stub existed) with query service definition, fields, selector, and response.optional: true for hassfest compatibility
- Updated manifest.json.jinja to conditionally include websocket_api in dependencies array using [% if use_websocket %] block, producing valid JSON for both flag states

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement WebSocket command handler and service action handler** - `ed09bcd` (feat)
2. **Task 2: Create services.yaml conditional template and add manifest.json conditional dependency** - `55f3509` (feat)

## Files Created/Modified

- `template/custom_components/[[ project_domain ]]/[% if use_websocket %]websocket.py[% endif %].jinja` - Complete async WebSocket command handler with @websocket_command + @async_response decorators and async_setup_websocket function
- `template/custom_components/[[ project_domain ]]/[% if use_services %]services.py[% endif %].jinja` - Complete service handler with SupportsResponse.OPTIONAL, SERVICE_SCHEMA, and async_register_services callback
- `template/custom_components/[[ project_domain ]]/[% if use_services %]services.yaml[% endif %].jinja` - NEW conditional template for hassfest service documentation with query service definition
- `template/custom_components/[[ project_domain ]]/manifest.json.jinja` - Added conditional websocket_api in dependencies array

## Decisions Made

- Lazy import of coordinator type inside websocket handler function body (not at module top) avoids potential circular import; follows HA core hassio/websocket_api.py pattern
- Manifest conditional uses `, "websocket_api"` inside the [% if %] block so when false it renders `["frontend"]` — valid JSON; when true renders `["frontend", "websocket_api"]` — also valid JSON

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- async_setup_websocket(hass) and async_register_services(hass) are ready for __init__.py.jinja wiring (conditional import and call blocks)
- services.yaml is in place for hassfest validation when use_services=true
- manifest.json websocket_api dependency will load before websocket command registration, preventing timing failures
- COND-01, COND-02, COND-06 satisfied; COND-03 (multi-step config flow) and COND-04 (secondary coordinator) remain for subsequent plans

---
*Phase: 05-conditional-patterns*
*Completed: 2026-02-20*
