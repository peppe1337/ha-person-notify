# HA HACS Integration Template

## What This Is

A Copier-based template that generates community-quality Home Assistant custom integrations with Lovelace frontend cards, distributed via HACS. Running `copier copy` produces a complete, hassfest-passing integration with modern HA APIs (2025.7+), conditional feature patterns, pytest scaffold, and CI/CD — ready for HACS submission. This is the shared foundation for ha-argos-translate, ha-immich-browser, and ha-requestarr.

## Core Value

Every shared integration pattern is decided and implemented once in this template, so child projects inherit correct, modern, community-quality code and can focus purely on their unique functionality.

## Requirements

### Validated

- ✓ Copier template engine with custom Jinja2 delimiters solving Python brace collision — v1.0
- ✓ Coarse-grained Copier conditionals: whole-file inclusion/exclusion for 4 optional patterns — v1.0
- ✓ Generic API client base class with configurable auth, timeout, and error handling — v1.0
- ✓ Full LitElement base card with theme integration, loading/error states, editor, card sizing — v1.0
- ✓ Config flow: single-step default with host/port/API key and connection validation — v1.0
- ✓ Config flow: multi-step conditional for projects needing multiple service connections — v1.0
- ✓ Options flow for reconfiguration without removing the integration — v1.0
- ✓ DataUpdateCoordinator: single-coordinator default pattern — v1.0
- ✓ DataUpdateCoordinator: multi-coordinator conditional with independent intervals — v1.0
- ✓ WebSocket command registration and handler pattern (conditional) — v1.0
- ✓ Service call with SupportsResponse pattern (conditional) — v1.0
- ✓ Device registry integration with DeviceEntryType.SERVICE — v1.0
- ✓ CoordinatorEntity base with entity naming, unique IDs, and device grouping — v1.0
- ✓ Sensor platform with example entities reading from coordinator — v1.0
- ✓ Frontend static path registration via async_register_static_paths (HA 2025.7+) — v1.0
- ✓ LitElement card editor with entity picker and text field patterns — v1.0
- ✓ Strings/translations pattern (strings.json + translations/en.json) — v1.0
- ✓ CI/CD: GitHub Actions for hassfest + HACS validation — v1.0
- ✓ Full pytest test scaffold with HA fixtures, config flow tests, coordinator mocking — v1.0
- ✓ HACS distribution structure (hacs.json, manifest.json, README pattern) — v1.0
- ✓ Minimum HA version 2025.7+ across all generated projects — v1.0

- ✓ Options flow validates connection before saving and reloads integration — v1.1
- ✓ Config flow preserves user input on error via add_suggested_values_to_schema — v1.1
- ✓ API client distinguishes server errors (4xx/5xx) from connection failures via ServerError — v1.1
- ✓ API client skips auth headers when no API key configured — v1.1
- ✓ CONF_API_KEY optional with empty default (not all services require auth) — v1.1
- ✓ SSL/HTTPS support via CONF_USE_SSL in config flow, options flow, API client, and coordinator — v1.1
- ✓ Service handler demonstrates coordinator lookup from config entries with ServiceValidationError — v1.1
- ✓ Service template uses SupportsResponse.ONLY for query-style services — v1.1
- ✓ Binary sensor platform for service connectivity status — v1.1
- ✓ Sensor and binary sensor test template (test_sensor.py.jinja) — v1.1
- ✓ Service call test template (test_services.py.jinja conditional) — v1.1
- ✓ Options flow test covers validation failure and reload behavior — v1.1

### Active

- [ ] CI/CD: Tag-based release workflow with version injection and zip packaging (deferred from v1.0 to per-project setup)
- [ ] Multi-step config flow test adaptation (test_config_flow.py.jinja conditional branches)
- [ ] Diagnostics platform with async_get_config_entry_diagnostics and redaction
- [ ] quality_scale.yaml pre-filled with Bronze/Silver compliance

### Out of Scope

- Project-specific API logic — each child project implements its own API endpoints and data parsing
- Project-specific card UI — each child project builds its own views on top of the base card class
- Project-specific sensors — each child project defines its own entity types and attributes
- Runtime shared library — this is a template, not an importable package; shared code is rendered into each project
- Mobile app / native components — web-based Lovelace cards only
- Build tooling for card (webpack, rollup, TypeScript) — HACS requires single-file JS; HA bundles LitElement
- pip dependencies in requirements — all child projects use HA-bundled aiohttp only
- YAML-based configuration — all integrations are config-flow-only
- Automatic discovery (zeroconf/mDNS/SSDP) — none of the three child projects need it
- Translations beyond English — community contribution after integrations stabilize

## Context

Shipped v1.0 with 25 template files (331 LOC) across 7 phases in 2 days.
Updated to v1.1 with 28 template files — backporting fixes and improvements from ha-argos-translate field testing.
Tech stack: Copier, Jinja2 (custom `[[ ]]` / `[% %]` delimiters), Python 3.12+, LitElement, pytest.
Generated integrations pass both `hassfest` and `hacs/action` validation on GitHub Actions.

### Child Projects

Three integrations share this template as their upstream:

1. **ha-argos-translate** — Local text translation via LibreTranslate. Single-step config, service call with SupportsResponse.ONLY, single coordinator, translation card.
2. **ha-immich-browser** — Immich photo library browsing. Single-step config, WebSocket commands, dual coordinators (stats 5min, albums 10min), photo grid card.
3. **ha-requestarr** — Media request dashboard replacing Jellyseerr. Multi-step config flow, WebSocket + service calls, single coordinator, tabbed search/request card.

## Constraints

- **HA Version**: 2025.7+ minimum — required for async_register_static_paths with StaticPathConfig
- **No pip dependencies**: All integrations use only HA-bundled libraries (aiohttp, voluptuous, LitElement)
- **Single JS file**: Frontend cards must be self-contained in one JavaScript file
- **Copier compatibility**: Template files use custom [[ ]] / [% %] Jinja2 delimiters via _envops
- **HACS compliance**: Directory structure must pass both hassfest and hacs/action validation
- **Python 3.12+**: HA's bundled Python version

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Copier for template inheritance | Git upstream merge breaks on domain renames. Copier handles variable substitution and supports `copier update`. | ✓ Good — clean generation and update pipeline confirmed |
| Custom _envops delimiters [[ ]] / [% %] | Avoids Jinja2/Python brace collision globally. Alternative ({% raw %}) was per-file and error-prone. | ✓ Good — zero brace collision issues across 25 template files |
| Coarse-grained conditionals | Whole-file inclusion/exclusion + minimal __init__.py blocks. Keeps template readable. | ✓ Good — 4 conditional patterns work cleanly |
| HA 2025.7+ minimum | async_register_static_paths requires 2025.7+. Avoids maintaining deprecated code paths. | ✓ Good — no deprecated API usage |
| Generic API client base class | All projects need session management, auth, timeout, error handling. One base serves all three. | ✓ Good — configurable auth pattern works for all child projects |
| entry.runtime_data over hass.data[DOMAIN] | HA-recommended pattern, auto-cleaned on unload, type-safe with generics. | ✓ Good — cleaner code, no manual cleanup |
| async_get_clientsession(hass) | HA manages HTTP session lifecycle. No "Unclosed client session" warnings. | ✓ Good — zero resource leak warnings |
| Static path in async_setup (not async_setup_entry) | Prevents duplicate registration error when multiple config entries exist. | ✓ Good — essential for multi-entry scenarios |
| Options flow writes to entry.data (not entry.options) | Coordinator reads from entry.data; keeps single source of truth. | ✓ Good — reload picks up changes immediately |
| WebSocket/services in async_setup | Prevents duplicate handler registration with multiple config entries. | ✓ Good — handlers registered once globally |
| ha-spinner (not ha-circular-progress) | ha-circular-progress removed in HA frontend 20250326.0. | ✓ Good — future-proof |
| CICD-02 release workflow deferred | Per-project customization needed (version format, zip structure, changelog). Not a template concern. | ✓ Good — correct scoping decision |
| hassfest requires "http" in manifest deps | Even though "frontend" transitively depends on "http", hassfest checks direct imports only. | ✓ Good — caught and fixed in Phase 7 gap closure |
| CONFIG_SCHEMA required for config-entry-only with async_setup | hassfest mandates cv.config_entry_only_config_schema(DOMAIN) when async_setup is defined. | ✓ Good — caught and fixed in Phase 7 gap closure |
| Options flow must validate + reload | Without validation, bad config breaks coordinator silently. Without reload, old credentials persist until HA restart. | ✓ Good — discovered via ha-argos-translate field testing |
| ServerError separate from CannotConnectError | raise_for_status() misclassifies 4xx as connection failure (both are ClientError subclasses). Explicit status checks distinguish reachable-but-rejected from unreachable. | ✓ Good — enables correct coordinator error state management |
| CONF_API_KEY optional by default | Not all services require auth. Required API key blocks setup for open services like LibreTranslate. | ✓ Good — matches real-world usage in ha-argos-translate |
| SSL toggle in config flow | Real-world services may run behind HTTPS. Template hardcoded http:// which blocked HTTPS services. | ✓ Good — runtime toggle covers both protocols |
| Binary sensor for connectivity | Polling integrations need a visible online/offline indicator. CoordinatorEntity + last_update_success is the standard pattern. | ✓ Good — immediate visibility of service health |
| SupportsResponse.ONLY for query services | OPTIONAL implies side-effect + optional response. Query services that always return data should use ONLY to prevent silent data loss when callers forget return_response. | ✓ Good — clearer API contract |

---
*Last updated: 2026-02-23 after v1.1 fixes from ha-argos-translate lessons*
