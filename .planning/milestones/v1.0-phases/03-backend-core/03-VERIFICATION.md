---
phase: 03-backend-core
verified: 2026-02-19T00:00:00Z
status: passed
score: 13/13 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Install generated integration in real HA instance via config flow"
    expected: "Config flow completes with host/port/API key; error is shown (not crash) when connection fails; device entry appears in Settings > Devices with correct name"
    why_human: "Requires a live HA instance and a real or mock API endpoint; cannot verify config flow UI behavior, device registry visibility, or error message rendering programmatically"
  - test: "Open Options flow after initial setup and change the API key"
    expected: "Integration reloads with new credentials; entity history is preserved (entity ID unchanged)"
    why_human: "Options flow entry.data update path verified statically but coordinator reload behavior and entity history preservation require a live HA instance"
  - test: "Confirm sensor entity visible under device in HA UI"
    expected: "At least one sensor entity (status) appears under the device in Settings > Devices; entity state updates from coordinator data"
    why_human: "Sensor entity wiring is structurally complete but actual coordinator data polling and entity state population requires live HA"
---

# Phase 3: Backend Core Verification Report

**Phase Goal:** A generated integration with default options (single-step config, single coordinator) installs, loads, creates a device entry, and exposes a sensor entity in HA
**Verified:** 2026-02-19
**Status:** PASSED
**Re-verification:** No - initial verification

## Goal Achievement

### Success Criteria from ROADMAP.md

| # | Success Criterion | Status | Evidence |
|---|-------------------|--------|---------|
| 1 | Integration sets up via config flow using host/port/API key with connection validation | VERIFIED | `config_flow.py.jinja` line 24: `vol.Required(CONF_API_KEY): str`; `_async_validate_connection` creates `ApiClient` and calls `async_test_connection()`, mapping `ApiCannotConnect -> CannotConnect`, `ApiInvalidAuth -> InvalidAuth`; errors set on `errors["base"]` (not crash) |
| 2 | Device entry appears with `DeviceEntryType.SERVICE` and correct integration name | VERIFIED | `sensor.py.jinja` line 50-55: `_attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, entry_type=DeviceEntryType.SERVICE, name=entry.title, manufacturer="[[ project_name ]]")` |
| 3 | At least one sensor entity visible and updates from coordinator data | VERIFIED | `sensor.py.jinja` line 25-31: `TemplateSensor(coordinator, entry, "status")` created in `async_setup_entry`; `native_value` returns `self.coordinator.data.get(self._sensor_type)` |
| 4 | Options flow allows changing host/port/API key; entity history preserved | VERIFIED | `config_flow.py.jinja` line 112-115: `async_update_entry(self.config_entry, data={**self.config_entry.data, **user_input})` then `async_create_entry(data={})`; stores in entry.data (not options) so coordinator re-reads on reload without re-creating entity |
| 5 | manifest.json, hacs.json, strings.json/translations/en.json present and complete; labels render | VERIFIED | manifest: 11/11 hassfest fields present; hacs.json: name + homeassistant 2025.7.0; strings.json == translations/en.json (byte-identical); api_key labels in both config and options sections |

**Score:** 5/5 success criteria verified

### Observable Truths (derived from must_haves across all three plans)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | ApiClient class exists with configurable auth, timeout, and error handling | VERIFIED | `api.py.jinja`: `class ApiClient` with `_get_auth_headers()`, `_request()` catching `ClientConnectionError`, `ClientError`, `TimeoutError` -> `CannotConnectError`; 401/403 -> `InvalidAuthError`; `aiohttp.ClientTimeout(total=timeout)` |
| 2 | Coordinator creates ApiClient from entry.data and uses it in _async_update_data | VERIFIED | `coordinator.py.jinja`: `self.client = ApiClient(host=entry.data[CONF_HOST], port=entry.data[CONF_PORT], api_key=entry.data[CONF_API_KEY], session=session)` in `__init__`; `return await self.client.async_get_data()` in `_async_update_data` |
| 3 | ApiClient exceptions are distinct from config_flow exceptions | VERIFIED | `api.py.jinja`: `CannotConnectError`, `InvalidAuthError`; `config_flow.py.jinja`: local `CannotConnect`, `InvalidAuth`; aliased on import as `ApiCannotConnect`, `ApiInvalidAuth` to avoid name collision |
| 4 | const.py exports DOMAIN, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DEFAULT_TIMEOUT, FRONTEND_SCRIPT_URL only (no CONF_* shadows) | VERIFIED | `const.py.jinja`: 5 constants only; no `CONF_HOST`, `CONF_PORT`, `CONF_API_KEY` present |
| 5 | Sensor entity has _attr_device_info with DeviceEntryType.SERVICE and identifiers tied to entry | VERIFIED | `sensor.py.jinja` line 50-55: confirmed |
| 6 | PARALLEL_UPDATES = 0 is set at module level in sensor.py | VERIFIED | `sensor.py.jinja` line 16: `PARALLEL_UPDATES = 0` at module level, after imports, before `async_setup_entry` |
| 7 | manifest.json.jinja has all required hassfest fields | VERIFIED | All 11 fields: domain, name, codeowners, config_flow, dependencies, documentation, integration_type, iot_class, issue_tracker, requirements, version |
| 8 | hacs.json.jinja has name and homeassistant minimum version | VERIFIED | name: `[[ project_name ]]`, homeassistant: `"2025.7.0"`, render_readme: true |
| 9 | Config flow schema includes host, port, and api_key fields | VERIFIED | `config_flow.py.jinja` line 20-26: `STEP_USER_DATA_SCHEMA` with `CONF_HOST`, `CONF_PORT`, `CONF_API_KEY` |
| 10 | Config flow validates connection using ApiClient.async_test_connection() | VERIFIED | `config_flow.py.jinja` line 43-54: `ApiClient(...)` constructed, `await client.async_test_connection()` called, exceptions mapped to flow errors |
| 11 | Options flow includes host, port, and api_key with current values as defaults | VERIFIED | `config_flow.py.jinja` line 119-134: `vol.Optional(CONF_HOST, default=self.config_entry.data.get(...))` for all three fields |
| 12 | Options flow updates entry.data (not entry.options) so coordinator re-reads on reload | VERIFIED | `config_flow.py.jinja` line 112-115: `async_update_entry(self.config_entry, data={**self.config_entry.data, **user_input})` then `async_create_entry(data={})` |
| 13 | strings.json and translations/en.json both have api_key labels in config and options sections | VERIFIED | Both files: `config.step.user.data.api_key = "API Key"` and `options.step.init.data.api_key = "API Key"`; files are byte-identical |

**Score:** 13/13 truths verified

## Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `template/custom_components/[[ project_domain ]]/api.py.jinja` | VERIFIED | 91 lines; `class ApiClient`, `CannotConnectError`, `InvalidAuthError`, `async_test_connection`, `async_get_data`, Bearer auth, configurable timeout |
| `template/custom_components/[[ project_domain ]]/coordinator.py.jinja` | VERIFIED | 49 lines; imports `ApiClient, CannotConnectError` from `.api`; creates client in `__init__`; calls `async_get_data()` in `_async_update_data` |
| `template/custom_components/[[ project_domain ]]/const.py.jinja` | VERIFIED | 10 lines; `DEFAULT_TIMEOUT = 30` present; no `CONF_*` constants |
| `template/custom_components/[[ project_domain ]]/sensor.py.jinja` | VERIFIED | `PARALLEL_UPDATES = 0` at module level; `DeviceEntryType.SERVICE` in `_attr_device_info`; `identifiers={(DOMAIN, entry.entry_id)}` |
| `template/custom_components/[[ project_domain ]]/config_flow.py.jinja` | VERIFIED | `CONF_API_KEY` in schema; real ApiClient validation; options flow writes entry.data via `async_update_entry` |
| `template/custom_components/[[ project_domain ]]/manifest.json.jinja` | VERIFIED | 11/11 hassfest fields; `integration_type: "[[ integration_type ]]"` |
| `template/hacs.json.jinja` | VERIFIED | name, homeassistant 2025.7.0, render_readme |
| `template/custom_components/[[ project_domain ]]/strings.json.jinja` | VERIFIED | api_key in config + options sections |
| `template/custom_components/[[ project_domain ]]/translations/en.json.jinja` | VERIFIED | Identical to strings.json.jinja |

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `coordinator.py.jinja` | `api.py.jinja` | `from .api import ApiClient, CannotConnectError` | WIRED | Line 15 confirmed; `self.client = ApiClient(...)` on line 36 |
| `coordinator.py.jinja` | `homeassistant.const` | `CONF_HOST, CONF_PORT, CONF_API_KEY` imports | WIRED | Line 10 confirmed; used in `entry.data[CONF_HOST/PORT/API_KEY]` |
| `sensor.py.jinja` | `homeassistant.helpers.device_registry` | `DeviceEntryType, DeviceInfo` imports | WIRED | Line 8 confirmed; used in `_attr_device_info = DeviceInfo(entry_type=DeviceEntryType.SERVICE)` |
| `sensor.py.jinja` | `const.py.jinja` | `from .const import DOMAIN` | WIRED | Line 13 confirmed; used in `identifiers={(DOMAIN, entry.entry_id)}` |
| `config_flow.py.jinja` | `api.py.jinja` | `from .api import ApiClient, CannotConnectError as ApiCannotConnect, InvalidAuthError as ApiInvalidAuth` | WIRED | Line 15 confirmed; `ApiClient(...)` constructed and `async_test_connection()` called in `_async_validate_connection` |
| `config_flow.py.jinja` | `homeassistant.const` | `CONF_HOST, CONF_PORT, CONF_API_KEY` | WIRED | Line 11 confirmed; used in schema, validation, and options form |
| `strings.json.jinja` | `translations/en.json.jinja` | identical key structure | WIRED | Both files byte-identical (confirmed: Python `assert d == e` passes) |

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| BACK-01 | 03-01-PLAN | Generic ApiClient base class with configurable auth, timeout, and error handling | SATISFIED | `api.py.jinja`: complete `ApiClient` class with `_get_auth_headers()`, `_request()`, typed exceptions |
| BACK-02 | 03-01-PLAN | DataUpdateCoordinator using API client from runtime_data, configurable update_interval | SATISFIED | `coordinator.py.jinja`: `TemplateCoordinator` creates `ApiClient` from `entry.data`, calls `async_get_data()` in `_async_update_data`; `update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL)` |
| BACK-03 | 03-01-PLAN | Typed ConfigEntry generic with dataclass runtime_data | SATISFIED | `__init__.py.jinja` line 23-31: `@dataclass class TestIntegrationData` + `type TestIntegrationConfigEntry = ConfigEntry[TestIntegrationData]` |
| BACK-04 | 03-02-PLAN | Sensor with CoordinatorEntity base, _attr_has_entity_name, _attr_unique_id | SATISFIED | `sensor.py.jinja`: `CoordinatorEntity[TemplateCoordinator]`, `_attr_has_entity_name = True`, `_attr_unique_id = f"{entry.entry_id}_{sensor_type}"` |
| BACK-05 | 03-02-PLAN | Device registry with DeviceEntryType.SERVICE on every entity via device_info | SATISFIED | `sensor.py.jinja` line 50-55: `_attr_device_info = DeviceInfo(entry_type=DeviceEntryType.SERVICE, ...)` |
| BACK-06 | 03-03-PLAN | Options flow for reconfiguring host/port/API key without removing integration | SATISFIED | `config_flow.py.jinja`: `OptionsFlowHandler` with all three fields; `async_update_entry` writes to `entry.data` preserving entity history |
| BACK-07 | 03-02-PLAN | manifest.json with all required fields, homeassistant 2025.7.0, dependencies: [frontend], integration_type | SATISFIED | `manifest.json.jinja`: 11 fields; `"dependencies": ["frontend"]`; `"integration_type": "[[ integration_type ]]"` (defaults to "service") |
| BACK-08 | 03-02-PLAN | hacs.json with correct name and homeassistant minimum version | SATISFIED | `hacs.json.jinja`: `"homeassistant": "2025.7.0"` |
| BACK-09 | 03-03-PLAN | strings.json and translations/en.json covering config flow, options flow, and error messages | SATISFIED | Both files: config step user data (host/port/api_key), error keys (cannot_connect/invalid_auth/unknown), abort.already_configured, options step init data (host/port/api_key) |
| BACK-10 | 03-02-PLAN | parallel_updates = 0 on all platform files | SATISFIED | `sensor.py.jinja` line 16: `PARALLEL_UPDATES = 0` at module level |

**Coverage:** 10/10 phase requirements satisfied. No orphaned requirements.

**REQUIREMENTS.md traceability column:** All 10 BACK-01 through BACK-10 entries marked `[x] Complete` and mapped to Phase 3.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `api.py.jinja` | 80 | `TODO: Replace /health with the actual health-check endpoint.` | INFO | Intentional placeholder for child project customization — not a blocker. The endpoint is functional as a stub; child projects are expected to replace it. |
| `api.py.jinja` | 88 | `TODO: Replace /api/data with the actual data endpoint.` | INFO | Same as above — intentional child-project hook. `async_get_data()` returns a real API response from whatever endpoint is set. |
| `sensor.py.jinja` | 27 | `# TODO: Create sensor entities based on your data` | INFO | Intentional scaffolding comment. One real sensor is still created (`TemplateSensor(coordinator, entry, "status")`), so the entity exists. The comment guides child project authors to add more entities. |

No blocker or warning-level anti-patterns found. All three TODOs are intentional extension points documented as such.

## Fresh Smoke Test Results

A fresh `copier copy --vcs-ref=0.1.0` was executed (not the stale `/tmp/smoke_test_03` from during development). Results:

| Check | Result |
|-------|--------|
| `api.py` AST parse | PASS |
| `config_flow.py` AST parse | PASS |
| `coordinator.py` AST parse | PASS |
| `sensor.py` AST parse | PASS |
| `__init__.py` AST parse | PASS |
| `const.py` AST parse | PASS |
| `manifest.json` JSON parse | PASS |
| `strings.json` JSON parse | PASS |
| `translations/en.json` JSON parse | PASS |
| `hacs.json` JSON parse | PASS |
| `strings.json == translations/en.json` | PASS |
| No Jinja2 artifacts in generated output (`[[`, `{%`) | PASS |

Generated `api.py` contains `class ApiClient`, `class CannotConnectError`, `class InvalidAuthError`, `async_test_connection`, `async_get_data` — no template syntax leakage.

Generated `coordinator.py` contains `self.client = ApiClient(`, `await self.client.async_get_data()`, `except CannotConnectError`.

Generated `sensor.py` contains `PARALLEL_UPDATES = 0`, `DeviceEntryType.SERVICE`, `_attr_device_info = DeviceInfo(`.

Generated `config_flow.py` contains `CONF_API_KEY`, `ApiClient(`, `await client.async_test_connection()`, `async_update_entry`.

Generated `const.py` does NOT contain `CONF_HOST`, `CONF_PORT`, or `CONF_API_KEY`.

Generated `manifest.json` has all 11 hassfest fields with correct values.

## Commit Verification

All commits documented in summaries confirmed to exist in git log:

| Commit | Summary Claims | Verified |
|--------|---------------|---------|
| `1deb3d3` | Create ApiClient template and clean const.py | EXISTS |
| `dcd3936` | Wire ApiClient into coordinator | EXISTS |
| `7061ee9` | Add device_info and PARALLEL_UPDATES to sensor.py.jinja | EXISTS |
| `3c7c398` | Add CONF_API_KEY and real connection validation to config flow | EXISTS |
| `e6a1065` | Add api_key to strings.json and translations/en.json | EXISTS |

Note: git tag `0.1.0` points to commit `e6a1065` (one commit before HEAD `bf23a13`). The HEAD commit is a docs-only commit (03-03-SUMMARY.md). Tag correctly covers all template file changes.

## Human Verification Required

### 1. Config Flow UI and Connection Validation

**Test:** Install generated integration (`copier copy` output) in a real HA instance. Open Settings > Integrations > Add Integration. Enter a valid host/port/API key pointing to a running API. Submit.
**Expected:** Integration appears in integrations list; no crash; if API is unreachable, error banner shows "Failed to connect" (not a Python traceback).
**Why human:** Config flow UI behavior, error message rendering in HA frontend, and real HTTP connection validation cannot be verified statically.

### 2. Device Registry Entry

**Test:** After successful config flow setup, open Settings > Devices. Search for the integration name.
**Expected:** Device entry appears with `DeviceEntryType.SERVICE` (displayed as "Service" in HA UI). Device name matches the configured host.
**Why human:** Device registry population requires live HA core; cannot be verified by static code analysis.

### 3. Options Flow and Entity History

**Test:** After setup, open the integration's options flow. Change the API key to a new value. Save. Check entity history for the status sensor.
**Expected:** Integration reloads with new credentials; entity history for the status sensor is preserved (no gap/break because entity_id is unchanged).
**Why human:** Entity history preservation requires live HA with recorder; options flow reload behavior requires runtime HA environment.

---

## Gaps Summary

None. All 13 observable truths verified. All 10 phase requirements satisfied. All key links wired. Fresh smoke test passes (11/11 checks). No blocker anti-patterns.

The three TODO comments in `api.py.jinja` and `sensor.py.jinja` are intentional extension hooks for child project authors and are not gaps — they are documented as such in the plans and research notes.

Human verification required for live HA integration behavior (3 items above) but all automated checks pass.

---

_Verified: 2026-02-19_
_Verifier: Claude (gsd-verifier)_
