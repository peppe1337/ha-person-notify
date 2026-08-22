# Project Research Summary

**Project:** HA HACS Integration Template (Copier-based)
**Domain:** Home Assistant custom integration template with Lovelace frontend
**Researched:** 2026-02-19
**Confidence:** HIGH

## Executive Summary

This project is a Copier template that generates community-quality Home Assistant custom integrations with bundled Lovelace cards, distributed via HACS. The key insight from research is that the existing scaffold has five breaking defects — all inherited by the three child projects (ha-argos-translate, ha-immich-browser, ha-requestarr) — that must be fixed before any new features are layered on. The most critical is `hass.http.register_static_path()`, which was removed in HA 2025.7 (the project's minimum target version), meaning the card does not load at all on any supported HA version. Fixing these regressions is not optional polish; it is the entire point of Phase 1.

The recommended approach is to build in strict dependency order: fix all deprecated HA API usage first (Phase 1), then establish correct Copier template scaffolding (Phase 2), then build the backend core and frontend card as parallel concerns (Phases 3-4), then add conditional patterns and the test scaffold (Phases 5-6), and finally wire up CI/CD (Phase 7). Each phase must be smoke-tested against a real `copier copy` run before the next begins, because Copier template rendering errors (Jinja2/Python brace collisions) are silent until render time. The ludeeus/integration_blueprint is the community reference for integration structure; the template currently lags it on modern patterns but will exceed it in scope once Copier conditionals and the Lovelace card base class are complete.

The primary risk is the Copier Jinja2/Python brace collision pitfall — every Python file with `{}` syntax (dict literals, f-strings, type hints) will be corrupted unless wrapped in `{% raw %}...{% endraw %}` blocks. This must be the first Copier-specific decision locked in, before any Python source files are written as template files. The secondary risk is HA API churn: the options flow `self.config_entry` assignment pattern breaks in HA 2025.12, and the static path registration changed in 2025.7. Research has identified all known breakages; no unknown deprecations are expected for the 2025.7+ target window.

## Key Findings

### Recommended Stack

The stack is almost entirely determined by HA's bundled runtime — there are no external dependencies to choose. Python 3.12+ is HA's interpreter; aiohttp, voluptuous, and homeassistant.* are the only libraries available; LitElement is extracted from HA's already-loaded Lovelace elements via `Object.getPrototypeOf(customElements.get("hui-masonry-view"))` with no CDN or npm involved. The only genuine tooling decision is **Copier 9.11.3** as the template engine, which research confirms is the correct choice over Cookiecutter (no update mechanism) or Yeoman (JS ecosystem). Copier's `copier update` capability — which performs a 3-way merge to propagate template fixes to child projects — is the entire architectural justification for this template existing.

**Core technologies:**
- **Python 3.12+**: HA's bundled interpreter — no installation, write to its constraints, use PEP 695 type alias syntax
- **Copier 9.11.3**: Template engine — the only tool supporting `copier update` propagation via 3-way git merge
- **LitElement (HA-bundled)**: Card base class — extracted at runtime from `customElements.get("hui-masonry-view")`, zero network dependency
- **HA 2025.7+**: Minimum runtime — dictated by `async_register_static_paths` requirement; pins all three child projects to a clean API surface

**Key HA-bundled APIs (versions matter):**
- `async_register_static_paths` + `StaticPathConfig` (HA 2024.6+, old method removed 2025.7)
- `ConfigEntry.runtime_data` typed generic (HA 2024.4+, replaces `hass.data[DOMAIN]`)
- `OptionsFlow` base providing `self.config_entry` automatically (HA 2025.1+, old `__init__` assignment breaks 2025.12)
- `async_get_clientsession(hass)` (stable, always correct for shared HTTP sessions)
- `DeviceEntryType.SERVICE` from `homeassistant.components.device_registry` (stable since 2022.3)

### Expected Features

Research distinguishes three categories: HACS blockers (fail CI immediately), Quality Scale requirements (determine Bronze/Silver/Gold tier), and user experience differentiators. The current scaffold fails on multiple HACS blockers.

**Must have — HACS blockers (template broken without these):**
- `manifest.json` with all required fields including `homeassistant: "2025.7"` minimum — CI fails otherwise
- `async_register_static_paths` with `StaticPathConfig` — card does not load on HA 2025.7+
- `unique_id` + `_abort_if_unique_id_configured()` in config flow — duplicate entries, HACS reviewer rejection
- Connection validation stub in config flow (`CannotConnect`/`InvalidAuth`) — Quality Scale Bronze blocker
- `hacs.json` with correct `homeassistant` field — HACS validator rejects wrong version format
- `pytest` test scaffold — required for Quality Scale Bronze `config-flow-test-coverage` rule

**Must have — Quality Scale Bronze/Silver (community expectations):**
- `ConfigEntry.runtime_data` with typed dataclass (replaces `hass.data`, modern pattern since 2024)
- Device registry entry with `DeviceEntryType.SERVICE` on every entity
- Options flow using `OptionsFlow` base class (NOT `OptionsFlowHandler.__init__` assignment)
- `async_get_clientsession(hass)` in API client base — prevents connection leaks
- `parallel_updates = 0` on all platform files
- Strings/translations for config and options flows
- Lovelace card with `window.customCards` registration, editor, `getStubConfig()`, `getCardSize()`, theme CSS variables, loading/error states

**Should have — differentiators beyond ludeeus/blueprint:**
- `diagnostics.py` with `async_redact_data` (Silver+ Quality Scale, greatly reduces issue triage)
- `quality_scale.yaml` tracking compliance (signals maturity to reviewers)
- Copier conditional patterns: WebSocket commands, SupportsResponse services, multi-coordinator, multi-step config flow

**Defer to v1.x/v2+:**
- Reauthentication flow (`async_step_reauth`) — needed for Requestarr, defer until that child project starts
- Reconfigure flow (`async_step_reconfigure`) — clean alternative to options flow, low priority
- Translations beyond English — community contribution after integrations stabilize

### Architecture Approach

The architecture has two distinct structures that must not be conflated: the Copier template repo (contains Jinja2 syntax, Copier configuration, conditional filename logic) and the generated integration (plain Python/JS that child project developers read and extend). The guiding principle is that child projects extend base classes, not edit generated boilerplate — meaning the LitElement base card is subclassed, and the generic API client is subclassed, with project-specific code living outside Copier-managed files. Whole-file conditional generation (generate `websocket.py` or not) is strongly preferred over scattered inline `{% if %}` blocks inside code files, with the exception of `__init__.py` where minimal import and call-site blocks are acceptable.

**Major components (in generated integration):**

1. `__init__.py` — Entry setup/teardown, frontend registration (must be in `async_setup`, not `async_setup_entry` to avoid duplicate path registration on second entry), coordinator init, platform forwarding
2. `config_flow.py` — Config flow (single-step default, multi-step conditional) + options flow, `unique_id` management, connection validation stub
3. `coordinator.py` — `DataUpdateCoordinator` subclass using `async_get_clientsession`, stores data for all entities; optional `coordinator_secondary.py` for independent poll intervals
4. `api_client.py` — Generic HTTP base class: session, auth (API key header), timeout, error handling; child projects subclass with specific endpoints
5. `sensor.py` — `CoordinatorEntity` subclass: `device_info`, `_attr_unique_id`, `_attr_has_entity_name = True`
6. `frontend/{domain}-card.js` — Single-file LitElement card with borrowed prototype, editor, `window.customCards`, CSS custom properties
7. Conditional: `websocket.py`, `services.py`/`services.yaml`, `coordinator_secondary.py`
8. `tests/` — `conftest.py` with `enable_custom_integrations`, `test_config_flow.py`, `test_coordinator.py`, conditional test files

**Critical data flow:** Config flow → `async_setup_entry` → coordinator in `entry.runtime_data` → `CoordinatorEntity` sensors → HA state machine → LitElement card reads `hass.states`. WebSocket commands (optional) bypass the state machine for transient card-to-backend calls.

### Critical Pitfalls

1. **`register_static_path()` removed in HA 2025.7** — Replace with `await hass.http.async_register_static_paths([StaticPathConfig(...)])`. Move registration to `async_setup` (not `async_setup_entry`) to prevent "already registered" on second config entry. This is the highest-severity defect in the current scaffold.

2. **Copier Jinja2/Python brace collision** — Every Python `.jinja` template file must wrap its source in `{% raw %}...{% endraw %}`. Without this, dict literals `{"key": "val"}`, f-strings `f"{var}"`, and type hints `dict[str, Any]` are silently corrupted or cause `TemplateSyntaxError`. Establish the escaping strategy before writing any template Python files.

3. **Options flow `self.config_entry` assignment breaks in HA 2025.12** — Use `OptionsFlow` base class (which provides `self.config_entry` automatically). Do NOT assign it in `__init__`. The `async_get_options_flow` classmethod must be a `@staticmethod @callback` returning `OptionsFlowHandler()` with no arguments.

4. **Missing `unique_id` in config flow** — Without `await self.async_set_unique_id(...)` + `self._abort_if_unique_id_configured()`, users can create duplicate config entries. This is the most common reason HACS reviewer rejection happens on first submission.

5. **Raw `aiohttp.ClientSession()` leaks connections** — HA does not manage sessions created outside its helpers. Use `async_get_clientsession(hass)` in the API client base class. Leads to "Unclosed client session" warnings on every reload and eventual file descriptor exhaustion.

## Implications for Roadmap

Research establishes a clear dependency chain. Phase ordering is determined by three constraints: (1) broken HA APIs must be fixed before any frontend work is meaningful, (2) Copier escaping strategy must be locked in before any `.jinja` files are written, and (3) conditional patterns depend on the always-on core being stable. The architecture's build order in ARCHITECTURE.md maps directly to the suggested phases below.

### Phase 1: Fix Deprecated HA API Usage

**Rationale:** All five breaking defects (static path registration, raw aiohttp session, missing unique_id, hass.data storage, options flow pattern) must be fixed before child projects can use the template. These are not "improvements" — the card literally does not load on HA 2025.7+ without the static path fix. This phase has no new features; it is exclusively correctness.
**Delivers:** A working scaffold where all generated code passes `hassfest`, uses modern HA patterns, and loads cleanly on HA 2025.7+
**Addresses:** `async_register_static_paths`, `async_get_clientsession`, `unique_id` in config flow, `entry.runtime_data`, `OptionsFlow` base class pattern
**Avoids:** Static path removal breakage (Pitfall 1), connection leaks (Pitfall 2), duplicate entries (Pitfall 3), hass.data tech debt (Pitfall 4), options flow 2025.12 breakage (Pitfall 5)
**Research flag:** Well-documented patterns, no research needed — all API signatures confirmed

### Phase 2: Copier Template Scaffolding

**Rationale:** The Copier configuration (`copier.yml` questions, directory naming, `.jinja` escaping strategy, conditional file inclusion mechanics) must be established before any Python source files are committed as template files. A retroactive escaping fix after 20+ `.jinja` files exist is a painful, error-prone migration.
**Delivers:** Working `copier copy` and `copier update` lifecycle; correct `_{{ domain }}_/` directory naming; `{% raw %}` escaping strategy documented and applied; first smoke test of a generated child project
**Addresses:** `copier.yml` with all questions, Jinja2/Python brace collision strategy, `.copier-answers.yml` documentation
**Avoids:** Copier Jinja2/Python brace collision (Pitfall 6), wrong directory delimiter (Pitfall 7), `.copier-answers.yml` misuse (Pitfall 8)
**Research flag:** Well-documented in Copier official docs; no additional research needed

### Phase 3: Backend Core (Always-On Patterns)

**Rationale:** The backend core (api_client, config_flow, coordinator, `__init__`, sensor, device registry, strings) is the foundation that all conditional patterns extend. The conditional files (Phase 5) touch `__init__.py` imports — finalizing the core before adding conditionals avoids rework.
**Delivers:** Fully functional generated integration with single-step config flow, single coordinator, sensor entity, device registry, options flow, and all HACS-required metadata files
**Addresses:** `api_client.py` base class, `config_flow.py` with unique_id and connection validation, `coordinator.py`, typed `ConfigEntry` generic dataclass, `sensor.py` with `device_info`, `strings.json`/`translations/en.json`, `manifest.json`, `hacs.json`, `README.md` stub
**Avoids:** Missing device registry (HACS quality complaint), missing options flow (user friction), missing connection validation (Quality Scale Bronze failure)
**Research flag:** Well-documented patterns; backend patterns are HIGH confidence from official HA docs

### Phase 4: Frontend Card Base Class

**Rationale:** The LitElement card depends on Phase 1's `async_register_static_paths` being correct (registration must work before card can load) but is otherwise independent of backend conditionals. Building it after Phase 3 means the card can immediately read real coordinator-provided entity states.
**Delivers:** Single-file `{domain}-card.js` with LitElement prototype extraction, card editor, `window.customCards` registration, theme CSS variables, loading/error states, `ha-card` wrapper, `getStubConfig()`, `getCardSize()`
**Addresses:** All Lovelace card table-stakes features
**Avoids:** Missing `window.customCards` registration, hardcoded colors, shadow DOM theme isolation, missing `ha-card` wrapper, broken card editor `config-changed` event
**Research flag:** Well-documented in HA developer docs; LitElement extraction pattern is community standard — no research needed

### Phase 5: Conditional Patterns

**Rationale:** Optional modules (WebSocket commands, SupportsResponse services, multi-coordinator, multi-step config flow) depend on the always-on core being stable because they add imports and call sites to `__init__.py`. Each conditional pattern is independent of the others and can be implemented in any order within this phase.
**Delivers:** Four Copier-conditional file sets: `websocket.py` (for Immich Browser, Requestarr), `services.py`+`services.yaml` (for Argos Translate, Requestarr), `coordinator_secondary.py` (for Immich Browser), multi-step `config_flow.py` variant (for Requestarr)
**Addresses:** All P1 conditional features from FEATURES.md
**Avoids:** Service registration inside `async_setup_entry` instead of `async_setup` (Pitfall from ARCHITECTURE.md anti-patterns)
**Research flag:** Well-documented patterns; each conditional is independently verified against official docs

### Phase 6: Test Scaffold

**Rationale:** Tests depend on the always-on core being final (config flow and coordinator must be stable before writing tests for them) and on the conditional patterns being finalized (conditional test files mirror conditional modules). Building tests after Phases 3-5 also validates that the generated code is actually testable.
**Delivers:** `conftest.py` with `enable_custom_integrations`, `test_config_flow.py`, `test_coordinator.py`, conditional test files for optional modules; `pytest.ini` / `pyproject.toml` with `asyncio_mode = auto`
**Addresses:** Quality Scale Bronze `config-flow-test-coverage` requirement; makes child project CI viable
**Avoids:** No test structure (the single largest gap in the current scaffold vs. ludeeus blueprint)
**Research flag:** Well-documented with `pytest-homeassistant-custom-component` library; standard fixtures confirmed

### Phase 7: CI/CD and HACS Distribution

**Rationale:** CI validates the generated output — it cannot be set up meaningfully until the generated output exists. The release workflow produces the HACS-distribution zip, which is only useful once the integration is functionally complete.
**Delivers:** `.github/workflows/validate.yml` (hassfest + hacs/action), `.github/workflows/release.yml` (tag-based, manifest version injection, zip artifact), correct `hacs.json` minimum version format
**Addresses:** All HACS submission requirements; CI runs on every push to catch regressions
**Avoids:** HACS validation failures (hacs.json wrong version format), hassfest manifest key order failures, missing release artifact
**Research flag:** Well-documented; `hacs/action@main` and `home-assistant/actions/hassfest@master` version pinning confirmed

### Phase 8: Differentiators

**Rationale:** After the template generates a HACS-quality Bronze/Silver integration, high-value additions that signal maturity and reduce issue triage burden can be added without timeline pressure.
**Delivers:** `diagnostics.py` with `async_redact_data`, `quality_scale.yaml` tracking rule compliance
**Addresses:** P2 features from FEATURES.md prioritization matrix
**Research flag:** Standard patterns; diagnostics API confirmed in official HA docs

### Phase Ordering Rationale

- **Phases 1-2 are non-negotiable prerequisites.** Phase 1 fixes broken code; Phase 2 establishes the template render pipeline. Both must complete before any template file contains Python source.
- **Phase 3 before Phase 4** because the card's static path registration (`__init__.py`) must be correct before the card loads; also, the card can read real entity states only after the coordinator exists.
- **Phase 3 before Phase 5** because conditional patterns add to `__init__.py` — a stable core prevents rework.
- **Phase 5 before Phase 6** because conditional test files mirror conditional source files.
- **Phase 7 last** because CI validates the final output; wiring it up before the output exists generates only noise.
- **Phase 8 is independent** and can be done in any order after Phase 3.

### Research Flags

Phases likely needing `/gsd:research-phase` during planning:
- **None identified.** All patterns are confirmed from official HA developer documentation, official Copier documentation, and real GitHub issues. Research confidence is HIGH across all areas.

Phases with well-established patterns (no research needed):
- **All phases** — patterns are stable, official-source-verified, and directly code-applicable. The main implementation risk is execution discipline (running `copier copy` smoke tests between phases), not research gaps.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | HA runtime is fixed; Copier 9.11.3 version confirmed; LitElement extraction pattern community-verified |
| Features | HIGH | All table-stakes features verified against official HA Quality Scale docs and hassfest rules; competitor analysis confirms gaps |
| Architecture | HIGH | Official HA docs for all component patterns; Copier docs for template mechanics; ARCHITECTURE.md build order validated against real dependency graph |
| Pitfalls | HIGH | All 8 critical pitfalls traced to official HA dev blog posts or real GitHub issues (hacs/integration #3828, #4314); deprecation timelines confirmed |

**Overall confidence: HIGH**

### Gaps to Address

- **LitElement version (Lit 2.x vs 3.x):** HA ships LitElement internally, but the exact version (2.x or 3.x) may vary by HA release. The extraction pattern `Object.getPrototypeOf(customElements.get("hui-masonry-view"))` works regardless of version, but API differences (if any) need verification at first smoke-test against a live HA instance. Mitigation: confirm which Lit version HA 2025.7 ships during Phase 4.

- **Static path URL convention (`/local/` vs `/hacsfiles/`):** ARCHITECTURE.md and STACK.md use slightly different URL prefixes for the registered static path. `/hacsfiles/` is the HACS convention for card JS files; `/local/custom_components/` is the integration convention. Confirm the correct prefix for a Lovelace resource registered from within the integration (not from HACS) during Phase 1.

- **`copier update` merge behavior on `__init__.py`:** When conditional patterns are added/removed via `copier update`, the 3-way merge on `__init__.py` (which has inline `{% if %}` blocks) may produce unexpected diffs. This is a practical risk to verify during Phase 5 smoke testing, not a blocking research gap.

## Sources

### Primary (HIGH confidence)
- [HA Developer Blog: async_register_static_paths migration (2024-06-18)](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/) — static path API, StaticPathConfig signature
- [HA Developer Blog: runtime_data pattern (2024-04-30)](https://developers.home-assistant.io/blog/2024/04/30/store-runtime-data-inside-config-entry/) — ConfigEntry.runtime_data pattern
- [HA Developer Blog: options flow update (2024-11-12)](https://developers.home-assistant.io/blog/2024/11/12/options-flow/) — OptionsFlow base class, 2025.12 breaking change
- [HA Integration Quality Scale Rules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/) — Bronze/Silver/Gold requirements
- [HA Config Flow Handler docs](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) — unique_id, abort, reconfigure patterns
- [HA Options Flow Handler docs](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/) — OptionsFlowWithReload
- [HA Integration Diagnostics docs](https://developers.home-assistant.io/docs/core/integration_diagnostics/) — async_get_config_entry_diagnostics
- [HA WebSocket API docs](https://developers.home-assistant.io/docs/frontend/extending/websocket-api/) — websocket_command decorator, async_register_command
- [HA Service Actions docs](https://developers.home-assistant.io/docs/dev_101_services/) — SupportsResponse pattern
- [HA Custom Card docs](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/) — LitElement card requirements
- [Copier Docs: Creating a Template](https://copier.readthedocs.io/en/stable/creating/) — Jinja2 mechanics, directory naming
- [Copier Docs: Configuring a Template](https://copier.readthedocs.io/en/stable/configuring/) — copier.yml structure, _templates_suffix
- [HACS Integration Publishing Requirements](https://www.hacs.xyz/docs/publish/integration/) — hacs.json fields, validation rules
- [hacs/integration issue #3828](https://github.com/hacs/integration/issues/3828) — real-world register_static_path deprecation breakage
- [hacs/integration issue #4314](https://github.com/hacs/integration/issues/4314) — real-world options flow config_entry breakage at HA 2025.1

### Secondary (MEDIUM confidence)
- [ludeeus/integration_blueprint](https://github.com/ludeeus/integration_blueprint) — community reference for integration structure (structure inferred from WebSearch)
- [jpawlowski/hacs.integration_blueprint](https://github.com/jpawlowski/hacs.integration_blueprint) — modern 2025-aligned reference (structure inferred)
- [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) — test fixture library
- Copier 9.11.3 release notes (January 2026) — version confirmation
- Existing scaffold analysis — direct code inspection of current project files

---
*Research completed: 2026-02-19*
*Ready for roadmap: yes*
