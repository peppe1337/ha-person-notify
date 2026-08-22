# Roadmap: HA HACS Integration Template

## Milestones

- ✅ **v1.0 MVP** — Phases 1-7 (shipped 2026-02-20)
- ✅ **v1.1 Fixes** — Backport fixes from ha-argos-translate (shipped 2026-02-23)
- ✅ **v1.1.1 Patch** — Fix deprecated static path API (shipped 2026-02-23)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-7) — SHIPPED 2026-02-20</summary>

- [x] Phase 1: Scaffold Fixes (2/2 plans) — completed 2026-02-19
- [x] Phase 2: Copier Template Scaffolding (3/3 plans) — completed 2026-02-19
- [x] Phase 3: Backend Core (3/3 plans) — completed 2026-02-20
- [x] Phase 4: Frontend Card (1/1 plan) — completed 2026-02-20
- [x] Phase 5: Conditional Patterns (3/3 plans) — completed 2026-02-20
- [x] Phase 6: Test Scaffold (3/3 plans) — completed 2026-02-20
- [x] Phase 7: CI/CD and HACS Distribution (2/2 plans) — completed 2026-02-20

</details>

### v1.1.1 Patch (2026-02-23)

External review (qwencode) flagged deprecated static path API in `__init__.py.jinja`:

- [x] Fix: `hass.http.async_register_static_paths` → standalone `async_register_static_paths(hass, ...)` (HA 2024.7+)
- [x] Propagated to ha-requestarr, ha-argos-translate, ha-immich-browser

Qwencode false positives (no action needed):
- Session management: template already uses `async_get_clientsession(hass)` correctly
- Manifest iot_class: already correct

### v1.1 Fixes (2026-02-23)

Backported from ha-argos-translate field testing. All changes in a single pass:

- [x] Fix: Options flow validates connection before saving
- [x] Fix: Options flow reloads integration after config update
- [x] Fix: Config flow preserves user input on error (add_suggested_values_to_schema)
- [x] Fix: API _request() distinguishes ServerError from CannotConnectError (replaces raise_for_status)
- [x] Fix: API client skips empty auth headers when no API key
- [x] Improvement: CONF_API_KEY optional with empty default
- [x] Improvement: SSL/HTTPS support via CONF_USE_SSL toggle
- [x] Improvement: Service handler demonstrates coordinator lookup pattern
- [x] Improvement: SupportsResponse.ONLY for query-style services
- [x] Addition: Binary sensor platform (connectivity status)
- [x] Addition: test_sensor.py.jinja (sensor + binary sensor tests)
- [x] Addition: test_services.py.jinja (conditional, service + missing entry tests)
- [x] Addition: Options flow validation/error test in test_config_flow.py.jinja
- [x] Addition: Shared mock_config_entry fixture in conftest.py.jinja
- [x] Update: strings.json + en.json with options error strings and SSL field

## Progress

| Phase                          | Milestone | Plans Complete | Status   | Completed  |
| ------------------------------ | --------- | -------------- | -------- | ---------- |
| 1. Scaffold Fixes              | v1.0      | 2/2            | Complete | 2026-02-19 |
| 2. Copier Template Scaffolding | v1.0      | 3/3            | Complete | 2026-02-19 |
| 3. Backend Core                | v1.0      | 3/3            | Complete | 2026-02-20 |
| 4. Frontend Card               | v1.0      | 1/1            | Complete | 2026-02-20 |
| 5. Conditional Patterns        | v1.0      | 3/3            | Complete | 2026-02-20 |
| 6. Test Scaffold               | v1.0      | 3/3            | Complete | 2026-02-20 |
| 7. CI/CD and HACS Distribution | v1.0      | 2/2            | Complete | 2026-02-20 |
| v1.1 Fixes                     | v1.1      | —              | Complete | 2026-02-23 |
| v1.1.1 Patch                   | v1.1.1    | —              | Complete | 2026-02-23 |

---
*Full v1.0 details: milestones/v1.0-ROADMAP.md*
