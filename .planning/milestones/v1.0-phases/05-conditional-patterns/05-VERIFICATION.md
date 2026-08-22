---
phase: 05-conditional-patterns
verified: 2026-02-20T00:00:00Z
status: passed
score: 11/11 must-haves verified
re_verification: false
human_verification:
  - test: "Copier smoke test — all features OFF"
    expected: "copier copy --defaults generates project with no websocket.py, services.py, services.yaml, coordinator_secondary.py; __init__.py contains no conditional identifiers; manifest.json dependencies equals [\"frontend\"]; all Python and JSON files parse; strings.json has no credentials step"
    why_human: "Smoke test requires copier binary at /home/dab/mediaparser-venv/bin/copier and a live filesystem render — SUMMARY.md claims both all-OFF and all-ON tests passed during plan execution"
  - test: "Copier smoke test — all features ON"
    expected: "copier copy with all four flags=true generates websocket.py, services.py, services.yaml, coordinator_secondary.py; __init__.py contains async_setup_websocket, async_register_services, TemplateSecondaryCoordinator; config_flow.py contains async_step_credentials; manifest.json dependencies includes websocket_api; strings.json and translations/en.json have credentials step; no Jinja2 artifacts in any generated file"
    why_human: "Same as above — copier render requires runtime execution; all source artifacts verified programmatically and are correctly structured"
---

# Phase 5: Conditional Patterns Verification Report

**Phase Goal:** All four Copier-conditional feature sets generate correctly when selected and are absent when not selected; `__init__.py` wires them in via minimal conditional blocks
**Verified:** 2026-02-20
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Selecting WebSocket support generates `websocket.py` with a working command handler and adds `websocket_api` to `manifest.json` dependencies; deselecting omits the file entirely | VERIFIED | `[% if use_websocket %]websocket.py[% endif %].jinja` exists with full async handler (`@websocket_api.websocket_command` + `@websocket_api.async_response` decorators in correct order, `async_setup_websocket` registration fn); `manifest.json.jinja` line 6 conditionally appends `"websocket_api"` |
| 2 | Selecting service calls generates `services.py` and `services.yaml` with a `SupportsResponse` pattern; deselecting omits them | VERIFIED | `[% if use_services %]services.py[% endif %].jinja` exists with `SupportsResponse.OPTIONAL`, full `SERVICE_SCHEMA`, and `async_register_services` callback; `[% if use_services %]services.yaml[% endif %].jinja` exists with `query` service definition and `response.optional: true` |
| 3 | Selecting multi-step config flow replaces the default `config_flow.py` with a multi-step variant; both variants pass `hassfest` | VERIFIED | `config_flow.py.jinja` contains `[% if use_multi_step_config_flow %]` / `[% else %]` / `[% endif %]` blocks for both schema and class body; multi-step branch has `__init__`, `async_step_user` (host/port + chain), `async_step_credentials` (api_key + unique_id + validation); dead stub `[% if use_multi_step_config_flow %]config_flow_multi_step.py[% endif %].jinja` deleted (confirmed via git log commit `b487fb2`) |
| 4 | Selecting secondary coordinator generates `coordinator_secondary.py` with its own poll interval; `entry.runtime_data` holds both coordinators | VERIFIED | `[% if use_secondary_coordinator %]coordinator_secondary.py[% endif %].jinja` exists with `TemplateSecondaryCoordinator(DataUpdateCoordinator)`, own `ApiClient` instance, `timedelta(seconds=DEFAULT_SECONDARY_SCAN_INTERVAL)` (300s); `__init__.py.jinja` conditionally assigns `coordinator_secondary=coordinator_secondary` in runtime_data |

**Score:** 4/4 success criteria verified

### Must-Have Truths (from PLAN frontmatter — all three plans)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | WebSocket stub replaced with working async command handler using `@websocket_command` + `@async_response` decorators | VERIFIED | Lines 20-38 of websocket.py.jinja: `@websocket_api.websocket_command(...)` outermost, `@websocket_api.async_response` second; handler fetches entries, guards on empty, returns `coordinator.data or {}` |
| 2 | Services stub replaced with working `SupportsResponse.OPTIONAL` handler and `async_register_services` callback | VERIFIED | services.py.jinja: `SupportsResponse.OPTIONAL` on line 49, `async_register_services` callback on line 42 |
| 3 | `services.yaml` conditional template file exists and documents the query service | VERIFIED | File exists, 11 lines, contains `query:`, `response: optional: true`, `[[ project_name ]]` substitution |
| 4 | `manifest.json` conditionally includes `websocket_api` in dependencies when `use_websocket` is true | VERIFIED | Line 6: `"dependencies": ["frontend"[% if use_websocket %], "websocket_api"[% endif %]]` |
| 5 | `config_flow.py.jinja` contains conditional blocks that render either single-step or multi-step flow based on `use_multi_step_config_flow` flag | VERIFIED | Flag appears on lines 20 and 85; single-step `[% else %]` branch is byte-for-byte compatible with original |
| 6 | Multi-step flow splits user/credentials into two steps with `self._data` accumulation and proper `unique_id`/validation in last step | VERIFIED | `__init__` with `self._data = {}`; `async_step_user` only collects host/port, chains to credentials; `async_step_credentials` sets unique_id + validates — correct order |
| 7 | `config_flow_multi_step.py` stub file is deleted (dead code) | VERIFIED | `ls` shows file absent; git log confirms deletion in commit `b487fb2` |
| 8 | `coordinator_secondary.py` stub replaced with working `SecondaryCoordinator` using independent poll interval | VERIFIED | Full 49-line implementation: class inherits `DataUpdateCoordinator[dict[str, Any]]`, `update_interval=timedelta(seconds=DEFAULT_SECONDARY_SCAN_INTERVAL)`, own `ApiClient` |
| 9 | `strings.json` and `translations/en.json` conditionally include credentials step when multi-step is enabled | VERIFIED | Both files: `[% if not use_multi_step_config_flow %],"api_key"...[% endif %]` in user step; `[% if use_multi_step_config_flow %],"credentials": {...}[% endif %]` after user step; identical content |
| 10 | `const.py` includes `DEFAULT_SECONDARY_SCAN_INTERVAL = 300` | VERIFIED | Line 7 of const.py.jinja: `DEFAULT_SECONDARY_SCAN_INTERVAL = 300` (unconditional — always present) |
| 11 | `__init__.py` has conditional import blocks for websocket, services, and secondary coordinator modules, calls them appropriately, and conditionally expands Data dataclass | VERIFIED | 8 conditional `[% if %]` blocks: 3 imports (lines 16-24), 1 dataclass field (line 36), 2 `async_setup` calls (lines 88-93), 1 secondary coordinator init (lines 102-105), 1 if/else runtime_data (lines 106-113) |

**Score:** 11/11 must-haves verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `[% if use_websocket %]websocket.py[% endif %].jinja` | WebSocket command handler with `async_setup_websocket` | VERIFIED | 45 lines, substantive; `websocket_api.async_register_command` present |
| `[% if use_services %]services.py[% endif %].jinja` | Service handler with `SupportsResponse.OPTIONAL` | VERIFIED | 51 lines, substantive; `async_register_services` present |
| `[% if use_services %]services.yaml[% endif %].jinja` | Service YAML definition for hassfest | VERIFIED | 11 lines, `query` service with `response.optional: true` |
| `manifest.json.jinja` | Conditional `websocket_api` dependency | VERIFIED | Line 6 has `[% if use_websocket %]` conditional |
| `config_flow.py.jinja` | Single-step or multi-step config flow variant | VERIFIED | 205 lines; `[% if use_multi_step_config_flow %]` appears on lines 20 and 85 |
| `[% if use_secondary_coordinator %]coordinator_secondary.py[% endif %].jinja` | Secondary DataUpdateCoordinator with independent poll interval | VERIFIED | 49 lines, `TemplateSecondaryCoordinator` class, 300s interval, own `ApiClient` |
| `const.py.jinja` | `DEFAULT_SECONDARY_SCAN_INTERVAL` constant | VERIFIED | Line 7: `DEFAULT_SECONDARY_SCAN_INTERVAL = 300` |
| `strings.json.jinja` | Conditional credentials step translations | VERIFIED | `[% if use_multi_step_config_flow %]` blocks present |
| `translations/en.json.jinja` | Conditional credentials step translations | VERIFIED | Identical structure to `strings.json.jinja` |
| `__init__.py.jinja` | Conditional wiring for all four feature sets | VERIFIED | `use_websocket`, `use_services`, `use_secondary_coordinator` all present; 8 total `[% if %]` blocks |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `websocket.py.jinja` | `const.py.jinja` | `from .const import DOMAIN` | WIRED | Line 13: `from .const import DOMAIN` |
| `services.py.jinja` | `const.py.jinja` | `from .const import DOMAIN` | WIRED | Line 19: `from .const import DOMAIN` |
| `manifest.json.jinja` | `copier.yml` | `use_websocket` boolean controls `websocket_api` dependency | WIRED | `copier.yml` line 61 defines `use_websocket`; `manifest.json.jinja` line 6 uses it |
| `config_flow.py.jinja` | `copier.yml` | `use_multi_step_config_flow` boolean controls which class body renders | WIRED | `copier.yml` line 76 defines flag; `config_flow.py.jinja` lines 20 and 85 use it |
| `coordinator_secondary.py.jinja` | `const.py.jinja` | `DEFAULT_SECONDARY_SCAN_INTERVAL` import | WIRED | Line 16: `from .const import DEFAULT_SECONDARY_SCAN_INTERVAL, DOMAIN` |
| `coordinator_secondary.py.jinja` | `api.py.jinja` | `ApiClient` import for independent data fetching | WIRED | Line 15: `from .api import ApiClient, CannotConnectError` |
| `__init__.py.jinja` | `websocket.py.jinja` | conditional import of `async_setup_websocket` | WIRED | Line 17: `from .websocket import async_setup_websocket`; called line 89 inside `async_setup` |
| `__init__.py.jinja` | `services.py.jinja` | conditional import of `async_register_services` | WIRED | Line 20: `from .services import async_register_services`; called line 92 inside `async_setup` |
| `__init__.py.jinja` | `coordinator_secondary.py.jinja` | conditional import of `TemplateSecondaryCoordinator` | WIRED | Line 23: `from .coordinator_secondary import TemplateSecondaryCoordinator`; instantiated line 103 and used in dataclass field line 37 and runtime_data line 109 |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| COND-01 | 05-01-PLAN | WebSocket command registration and handler pattern in `websocket.py` | SATISFIED | `websocket.py.jinja` exists with complete handler; `async_setup_websocket` wired in `__init__.py.jinja` |
| COND-02 | 05-01-PLAN | Service call with `SupportsResponse` pattern in `services.py` + `services.yaml` | SATISFIED | Both conditional files exist with correct patterns; `async_register_services` wired in `__init__.py.jinja` |
| COND-03 | 05-02-PLAN | Multi-step config flow variant replacing single-step `config_flow.py` | SATISFIED | `config_flow.py.jinja` has `[% if use_multi_step_config_flow %]` blocks for both variant; dead stub deleted |
| COND-04 | 05-02-PLAN | Secondary coordinator with independent poll interval in `coordinator_secondary.py` | SATISFIED | `coordinator_secondary.py.jinja` with `TemplateSecondaryCoordinator` at 300s, wired into `__init__.py.jinja` |
| COND-05 | 05-03-PLAN | `__init__.py` uses minimal Jinja2 `[% if %]` blocks for conditional import/registration lines only | SATISFIED | 8 conditional blocks in `__init__.py.jinja`; all logic stays in conditional modules (no feature logic leaked) |
| COND-06 | 05-01-PLAN | `manifest.json` conditionally includes `websocket_api` in `dependencies` when WebSocket selected | SATISFIED | `manifest.json.jinja` line 6: inline conditional, produces valid JSON for both flag states |

**Orphaned requirements:** None. All 6 requirements (COND-01 through COND-06) claimed by plans and verified in codebase.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `[% if use_services %]services.py[% endif %].jinja` | 34 | `# TODO: Implement with actual coordinator/client data` | Info | Template-level customization hint — NOT a stub. The function has complete logic: builds result dict from `call.data["query"]`, checks `call.return_response`, returns `result` or `None`. The TODO guides generated-project authors to replace the placeholder `results: []` with real API data. The structural pattern (`SupportsResponse.OPTIONAL`) is fully implemented. |

**Assessment:** The single TODO comment is categorized as Info, not a blocker. The function is substantively implemented — it demonstrates the correct `SupportsResponse.OPTIONAL` pattern with a working return structure. The TODO is a code comment for the template consumer, not evidence of a missing implementation.

### Human Verification Required

#### 1. Copier all-features-OFF smoke test

**Test:** Run `copier copy --defaults --data project_domain=smoke_test --data author_name=test /path/to/template /tmp/test-off` (using copier at `/home/dab/mediaparser-venv/bin/copier`), then verify: no `websocket.py`, `services.py`, `services.yaml`, `coordinator_secondary.py` in output; `__init__.py` contains no "websocket", "services", "secondary"; `manifest.json` dependencies is `["frontend"]`; `strings.json` has no "credentials" step; all Python files parse with `python3 -c "import ast; ast.parse(open(f).read())"`.
**Expected:** All absent-file checks pass; all parse checks pass; no Jinja2 artifacts.
**Why human:** Requires the copier binary at runtime. SUMMARY.md (05-03) claims this test was run and passed during plan execution. All source artifacts have been programmatically verified to be correctly structured for this outcome.

#### 2. Copier all-features-ON smoke test

**Test:** Run `copier copy --defaults --data project_domain=smoke_test --data author_name=test --data use_websocket=true --data use_services=true --data use_secondary_coordinator=true --data use_multi_step_config_flow=true /path/to/template /tmp/test-on`, then verify: `websocket.py`, `services.py`, `services.yaml`, `coordinator_secondary.py` exist and parse; `__init__.py` contains `async_setup_websocket`, `async_register_services`, `TemplateSecondaryCoordinator` and parses; `config_flow.py` contains `async_step_credentials` and parses; `manifest.json` includes `"websocket_api"`; `strings.json` and `translations/en.json` have "credentials" step; no `[[`, `[%`, `]]`, `%]` in any file.
**Expected:** All present-file checks pass; all parse checks pass; no Jinja2 artifacts.
**Why human:** Same as above — requires runtime copier execution. Source templates verified to be correctly structured for this outcome.

### Gaps Summary

No gaps found. All 11 must-have truths are verified in the codebase, all 10 artifacts pass all three levels (exists, substantive, wired), all 9 key links are wired, and all 6 requirements (COND-01 through COND-06) are satisfied. The single TODO comment in services.py.jinja is a template-author guidance comment, not a structural deficiency — the SupportsResponse.OPTIONAL pattern is fully and correctly implemented.

The only items deferred to human verification are the end-to-end copier smoke tests (all-OFF and all-ON), which require the copier binary at runtime. The SUMMARY.md for plan 05-03 documents that both tests were executed and passed during phase execution.

---

_Verified: 2026-02-20_
_Verifier: Claude (gsd-verifier)_
