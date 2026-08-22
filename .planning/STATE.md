# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** Every shared integration pattern is decided and implemented once, so child projects inherit correct, modern, community-quality code
**Current focus:** v1.1.1 patch shipped. Fixed deprecated static path API flagged by external review.

## Current Position

Phase: v1.1.1 complete
Status: Fixed deprecated `hass.http.async_register_static_paths` → standalone `async_register_static_paths(hass, ...)` (HA 2024.7+). Propagated to all child projects.
Last activity: 2026-02-23 — v1.1.1 static path fix applied to template and all copies.

Progress: v1.0 [██████████] 100% SHIPPED
Progress: v1.1 [██████████] 100% SHIPPED
Progress: v1.1.1 [██████████] 100% SHIPPED

## v1.1 Changes Summary

### Bug Fixes
- Options flow validates connection before saving (previously saved blindly)
- Options flow reloads integration after config update (previously coordinator kept old config)
- Config flow preserves user input on error via add_suggested_values_to_schema
- API _request() replaces raise_for_status() with explicit HTTP status checks (ServerError vs CannotConnectError)
- API client skips auth headers when no API key configured

### Improvements
- CONF_API_KEY changed from vol.Required to vol.Optional with empty default
- SSL/HTTPS support via CONF_USE_SSL in config flow, options flow, API client, coordinator
- Service handler demonstrates coordinator lookup from config entries
- SupportsResponse.ONLY for query-style services (was OPTIONAL)
- Binary sensor platform for service connectivity status

### New Templates
- binary_sensor.py.jinja — connectivity binary sensor
- test_sensor.py.jinja — sensor value, unique_id, and binary sensor tests
- test_services.py.jinja — service call and missing entry tests (conditional on use_services)

### Updated Templates
- conftest.py.jinja — added mock_config_entry shared fixture
- test_config_flow.py.jinja — options flow validation/error test + reload verification
- strings.json.jinja / en.json.jinja — options error strings and SSL field labels

## v1.1.1 Changes Summary

### Bug Fix
- `__init__.py.jinja`: Replace deprecated `hass.http.async_register_static_paths(...)` with standalone `async_register_static_paths(hass, ...)` from `homeassistant.components.http` (required for HA 2024.7+, old method removed in HA 2025.7)

### External Review Findings (qwencode on ha-requestarr)
- **Static path API** — REAL. Fixed in template and all child projects.
- **Session management (aiohttp.ClientSession leak)** — FALSE POSITIVE. Template already uses `async_get_clientsession(hass)` correctly in coordinator and config_flow. Qwen pattern-matched the pitfall without verifying code paths.
- **Manifest iot_class** — Already correct. No fix needed.

### Propagation
- ha-requestarr: copier update (`--vcs-ref HEAD`)
- ha-argos-translate: manual edit (too diverged for copier update)
- ha-immich-browser: copier update (also picked up other template improvements)

## Accumulated Context

### Decisions

Full decision log in PROJECT.md Key Decisions table (21 decisions with outcomes).

### Pending Todos

None.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-23
Stopped at: v1.1.1 static path fix committed and pushed to all repos.
Resume action: Start next child project or plan v2 features.
