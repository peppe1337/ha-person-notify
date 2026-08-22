# Milestones

## v1.0 MVP (Shipped: 2026-02-20)

**Phases:** 1-7 (17 plans) | **Commits:** 92 | **Template:** 25 files, 331 LOC
**Timeline:** 2 days (2026-02-19 to 2026-02-20)
**Git range:** 0de3a18..4a73338

**Delivered:** A Copier-powered template that generates HACS-quality Home Assistant integrations with modern APIs, conditional patterns, test scaffold, and CI/CD — passing hassfest and HACS validation out of the box.

**Key accomplishments:**
1. Fixed all deprecated HA API usage (static paths, clientsession, runtime_data) for HA 2025.7+ compatibility
2. Established Copier template pipeline with custom Jinja2 delimiters solving Python/Jinja2 brace collision
3. Built complete backend core: ApiClient, DataUpdateCoordinator, config/options flow, sensor, device registry
4. Created LitElement frontend card with editor, theme integration, loading/error states, and card picker registration
5. Implemented four conditional file patterns (WebSocket, services, multi-coordinator, multi-step config) via Copier conditionals
6. Added pytest test scaffold with HA fixtures, config flow, coordinator, and conditional test files
7. Created CI/CD pipeline with hassfest + HACS validation, verified passing on live GitHub Actions

**Known Gaps (resolved in v1.1):**
- ~~Missing test_services.py conditional template~~ — added in v1.1
- CICD-02 (release workflow) deferred to per-project setup by user decision
- Multi-step config flow test adaptation (v2 candidate)

**Archives:** milestones/v1.0-ROADMAP.md, milestones/v1.0-REQUIREMENTS.md, milestones/v1.0-MILESTONE-AUDIT.md

---

## v1.1 Fixes (Shipped: 2026-02-23)

**Template:** 28 files (3 new, 11 modified) | **Timeline:** 1 session
**Source:** Lessons learned from ha-argos-translate v1.0 + v1.1 field testing

**Delivered:** Bug fixes, quality improvements, and new platform/test templates backported from real-world usage of the template in ha-argos-translate.

**Bug fixes:**
1. Options flow validates connection before saving (previously saved blindly, breaking coordinator)
2. Options flow reloads integration after config update (previously coordinator kept stale credentials)
3. Config flow preserves user input on validation error (previously all fields cleared)
4. API `_request()` replaces `raise_for_status()` with explicit HTTP status checks — new `ServerError` class distinguishes reachable-but-rejected from unreachable
5. API client no longer sends empty `Authorization: Bearer ""` header when no API key

**Improvements:**
6. `CONF_API_KEY` changed from `vol.Required` to `vol.Optional` with empty default
7. SSL/HTTPS toggle via `CONF_USE_SSL` in config flow, options flow, API client, coordinator
8. Service handler demonstrates proper coordinator lookup from config entries with `ServiceValidationError`
9. `SupportsResponse.ONLY` for query-style services (was `OPTIONAL`)
10. Binary sensor platform for service connectivity (based on `coordinator.last_update_success`)

**New templates:**
11. `binary_sensor.py.jinja` — connectivity binary sensor entity
12. `test_sensor.py.jinja` — sensor value, unique_id, binary sensor online tests
13. `test_services.py.jinja` — service call and missing entry error tests (conditional on `use_services`)

---
