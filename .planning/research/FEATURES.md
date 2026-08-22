# Feature Research

**Domain:** Home Assistant HACS Custom Integration Template (Copier-based)
**Researched:** 2026-02-19
**Confidence:** HIGH (verified against HA developer docs, HACS docs, quality scale, community sources)

---

## Feature Landscape

This research covers what a high-quality HA HACS integration template must generate. Features are
evaluated from two angles: (1) what HACS reviewers and `hassfest` validation require, and (2) what
the HA Integration Quality Scale (Bronze/Silver/Gold) codifies as community expectations. The
template must capture ALL table-stakes features as generated defaults, and the conditional
differentiators as opt-in Copier-generated files.

---

### Table Stakes (Users Expect These)

Missing any of these = HACS rejection, `hassfest` failure, or user complaint tickets within days of release.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **`manifest.json` with all required fields** | `hassfest` validates: `domain`, `name`, `codeowners`, `config_flow: true`, `documentation`, `issue_tracker`, `version`, `integration_type`, `iot_class`. Missing fields = CI failure. | LOW | `requirements: []` is correct for no-pip-dep integrations. `dependencies: ["frontend"]` required when registering Lovelace resources. |
| **`hacs.json` with `name` and correct `homeassistant` minimum** | HACS validator requires `hacs.json` with at minimum `name`. The `homeassistant` field must match the actual minimum version the code requires. Currently scaffold incorrectly pins `2024.1.0` — must be `2025.7.0` to match `async_register_static_paths` requirement. | LOW | `render_readme: true` is conventional but not required. |
| **Config flow with `unique_id` and `already_configured` abort** | Without `unique_id`, users can add duplicate entries with no way to distinguish them. `hassfest` warns; HACS reviewers reject. The `_abort_if_unique_id_configured()` call prevents duplicates. | MEDIUM | `unique_id` should be stable (host, serial, or derived from config). This is the most common missing feature in rejected HACS submissions. |
| **Connection validation in config flow (`test-before-configure`)** | HA Quality Scale Bronze rule: test the connection before creating the entry. Users expect "cannot connect" errors during setup, not after. Returning a bare `async_create_entry` without any validation is an antipattern visible to reviewers. | MEDIUM | Scaffold has a TODO comment but no implementation. The template must generate a working `_async_validate_connection()` stub that raises `CannotConnect` and `InvalidAuth`. |
| **Options flow for reconfiguration** | Users need to change host/API key after setup without removing the integration (losing entity history). `OptionsFlowWithReload` is the current preferred subclass — it auto-reloads the integration when options change. Community integrations without options flow are frequently asked "how do I change the host?" in issues. | MEDIUM | Silver tier Quality Scale rule. Missing in current scaffold. |
| **`ConfigEntry.runtime_data` instead of `hass.data[DOMAIN]`** | `hass.data[DOMAIN][entry.entry_id]` is the old pattern. As of 2024/2025 the HA team has migrated all core integrations to `ConfigEntry.runtime_data` with a typed generic `type MyConfigEntry = ConfigEntry[MyData]`. Blueprint and reviewer feedback now flags the old pattern. | LOW | Current scaffold uses `hass.data` — this is the #1 pattern update needed. |
| **Device registry entry with `DeviceEntryType.SERVICE`** | Service-based integrations (no physical hardware) must use `DeviceEntryType.SERVICE`. Without a device entry, entities appear unassociated in the UI and diagnostic tools don't work properly. This is a Bronze Quality Scale requirement ("The integration creates devices"). | MEDIUM | Entirely missing from current scaffold. `device_info` must be set on every entity. |
| **`_attr_has_entity_name = True` on all entities** | Required for entity naming to follow HA conventions. Without it, entity names don't respect the device name prefix, causing confusing naming in the UI. Bronze Quality Scale requirement. | LOW | Current scaffold has this correct on `TemplateSensor`. |
| **`unique_id` on every entity (via `_attr_unique_id`)** | Without unique IDs, entities cannot be customized (renamed, disabled) in the UI. HA emits a warning. Pattern: `f"{entry.entry_id}_{sensor_key}"`. | LOW | Current scaffold correctly sets `_attr_unique_id`. |
| **`DataUpdateCoordinator` for all polling** | Required any time multiple entities share the same data source. Prevents N API calls per entity per update. Bronze Quality Scale: "appropriate-polling". | MEDIUM | Current scaffold implements this correctly as a base. |
| **`async_config_entry_first_refresh()` on startup** | Coordinators must call `async_config_entry_first_refresh()` (not plain `async_refresh()`). The former raises `ConfigEntryNotReady` on failure, which HA handles gracefully with retry backoff. The latter silently fails. | LOW | Current scaffold does this correctly. |
| **`async_unload_entry` that fully cleans up** | Integrations that don't unload cleanly fail the `config-entry-unloading` Silver Quality Scale rule and leave dangling state when the user reloads. Must call `async_unload_platforms` and clean up `runtime_data`. | LOW | Current scaffold calls `async_unload_platforms` but cleans up `hass.data` not `runtime_data`. Needs updating. |
| **`async_register_static_paths` with `StaticPathConfig`** | `hass.http.register_static_path()` was removed in HA 2025.7. All integrations must use `await hass.http.async_register_static_paths([StaticPathConfig(...)])`. This is the blocking bug in the current scaffold. Verified: multiple HACS issues cite this deprecation. | LOW | `StaticPathConfig` imported from `homeassistant.components.http`. This is confirmed HIGH confidence from HA blog post 2024-06-18. |
| **`async_get_clientsession(hass)` for HTTP client** | Creating raw `aiohttp.ClientSession()` bypasses HA's lifecycle management, causing resource leaks when the integration unloads. Platinum Quality Scale rule: "inject-websession". HACS reviewers flag this. | LOW | Current scaffold has TODO comment but uses raw session. Template must generate correct pattern. |
| **Strings and translations (`strings.json` + `translations/en.json`)** | All config flow step titles, field labels, and error messages must be in `strings.json` and mirrored to `translations/en.json`. Without this, the config UI shows raw key names. Required for HACS distribution. | LOW | Current scaffold has basic strings. Must include options flow strings when options flow is generated. |
| **CI: `hassfest` validation on every push** | HACS's own CI runs `hassfest`. If the template-generated integration fails hassfest, it will never pass HACS default repository review. | LOW | Current scaffold has this in `.github/workflows/validate.yml`. Correct. |
| **CI: `hacs/action` validation on every push** | Validates the HACS-specific requirements (hacs.json, file structure, releases). | LOW | Current scaffold has this. Correct. |
| **Release workflow with version packaging** | HACS requires at least one GitHub release to be submitted to the default repository. The release must contain a properly structured zip or the integration files must be in the right location. | MEDIUM | Current scaffold has `release.yml`. Must verify it injects version and produces correct zip. |
| **Lovelace card registered to `window.customCards`** | For the card to appear in the card picker, it must push to `window.customCards` with `type`, `name`, and `description`. Without this, users must type the card type manually — a major UX gap. | LOW | Current scaffold does this correctly. |
| **Card editor with `getConfigElement()` and `config-changed` event** | The visual card editor in the dashboard requires `static getConfigElement()` returning the editor element, and the editor must dispatch `config-changed` events with `bubbles: true, composed: true`. Without this the card has no UI editor. | MEDIUM | Current scaffold implements this correctly as a pattern. |
| **`getStubConfig()` on card** | Required for the card picker to show a preview without crashing. Returns default config values. | LOW | Current scaffold implements this correctly. |
| **`getCardSize()` on card** | Used by HA dashboard layout engine to allocate grid rows. Without it, cards get default sizing that may be wrong. | LOW | Current scaffold implements this. |
| **pytest test scaffold** | HACS doesn't technically require tests, but Bronze Quality Scale requires "config-flow-test-coverage". Without tests, the integration cannot reach any quality tier, and community PRs are harder to accept. The `pytest-homeassistant-custom-component` package provides all required fixtures. | HIGH | Entirely missing from current scaffold. This is a significant gap. |
| **`README.md` with HACS installation badge and instructions** | Users expect copy-paste HACS installation instructions. The HACS badge + "Add repository" link is standard. Missing this is the most common new user friction point. | LOW | Current scaffold has a minimal README. Template must generate a rich README stub. |

---

### Differentiators (Competitive Advantage)

Features that separate excellent integrations from functional-but-mediocre ones. These are what gets an integration starred and recommended in the community.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **`diagnostics.py` with `async_get_config_entry_diagnostics`** | Allows users to download redacted debug data from the UI for issue reporting. Without this, debugging requires log scraping. Silver+ Quality Scale. Greatly reduces issue report back-and-forth. | MEDIUM | Pattern: import `async_redact_data` from `homeassistant.helpers.redact`, define `TO_REDACT = [CONF_API_KEY]`, return dict with `async_redact_data(entry.data, TO_REDACT)` and coordinator data. |
| **Reauthentication flow (`async_step_reauth`)** | When API credentials expire, HA can show a persistent notification prompting re-auth without requiring the user to remove and re-add the integration. Silver Quality Scale rule. Critical for cloud API integrations. | MEDIUM | `async_step_reauth` and `async_step_reauth_confirm` steps in config flow. Required for Requestarr (cloud API) more than Argos/Immich (local). Template should generate stub. |
| **Reconfigure flow (`async_step_reconfigure`)** | Allows changing connection details (host, port) without removing the integration. Distinct from options flow (which handles optional settings) and reauth (which handles credentials). HA 2024+ pattern. | MEDIUM | Use `self._get_reconfigure_entry()` and `async_set_unique_id` with `_abort_if_unique_id_mismatch()`. The PROJECT.md lists "options flow" but reconfigure is the better pattern for setup-time data changes. |
| **Typed `ConfigEntry` with dataclass `runtime_data`** | `type MyIntegrationConfigEntry = ConfigEntry[MyIntegrationData]` with a `@dataclass MyIntegrationData` gives full type safety across all files. Means mypy/pyright catches coordinator/client mismatches at development time, not runtime. | LOW | Modern HA pattern since 2024. Blueprint uses this. Significant DX improvement for child project developers. |
| **WebSocket command registration (conditional)** | Exposes integration data to the frontend without polling by adding HA WebSocket commands callable from Lovelace JS. Pattern: `@websocket_api.websocket_command(...)` decorator + `@websocket_api.async_response` + `websocket_api.async_register_command(hass, handler)` in `async_setup`. | HIGH | Needed by Immich Browser and Requestarr. Conditional file generation. Requires `websocket_api` in `dependencies` in `manifest.json`. |
| **Service call with `SupportsResponse` (conditional)** | Registers an HA service action that returns data. Allows automations to call the integration and use the response. Pattern: `hass.services.async_register(DOMAIN, SERVICE_NAME, handler, schema=..., supports_response=SupportsResponse.ONLY)`. Must be in `async_setup` not `async_setup_entry`. | HIGH | Needed by Argos Translate (ONLY) and Requestarr (OPTIONAL). Conditional file generation. |
| **Multi-step config flow (conditional)** | For integrations connecting to multiple services (e.g., Requestarr: TMDB + Radarr + Sonarr + Lidarr), a single-step config form is inadequate. Multi-step means `async_step_service_a` → `async_step_service_b` etc., storing partial data in `self._data`. | HIGH | Needed by Requestarr only. Conditional whole-file generation. The template must make this a clean swap vs single-step, not additive complexity. |
| **Multiple coordinators (conditional)** | Some integrations need independent poll intervals for different data types (e.g., Immich: stats at 5min, albums at 10min). Pattern: both coordinators stored in `runtime_data`, entities picking the right coordinator. | HIGH | Needed by Immich Browser only. Conditional generation. `runtime_data` dataclass holds both coordinator references. |
| **`parallel_updates = 0` or explicit value on platforms** | Silver Quality Scale rule. Must either set `PARALLEL_UPDATES = 0` (coordinator-based, no per-entity updates) or an explicit integer (N entities updated concurrently). Without it, HA uses a default that may cause issues. | LOW | Simple one-liner per platform file. Often missed. |
| **LitElement theme integration via CSS variables** | Cards using `var(--primary-color)`, `var(--primary-text-color)`, `var(--card-background-color)` etc. automatically adapt to user's HA theme (light/dark mode, custom themes). Hardcoded colors break in dark mode. | LOW | Current scaffold uses CSS variables correctly. Must be preserved and extended in base card class. |
| **Loading and error states in the card** | Cards that render nothing or crash when the coordinator hasn't loaded yet (or has an error) create a confusing UX. Proper pattern: show spinner during initial load, show error message if coordinator failed, render content when data is ready. | MEDIUM | Current scaffold renders empty on missing state. Base card class should standardize this pattern. |
| **`quality_scale.yaml` in integration root** | Tracks which Quality Scale rules are implemented and which are exempted with reasons. Not required by HACS, but signals maturity and makes review faster. Reviewers for default repository inclusion look for this. | LOW | One YAML file. Low cost, high signal. Template should generate a pre-filled version. |
| **`services.yaml` for service action documentation** | Describes service call parameters so they appear in the HA developer tools UI with descriptions and selectors. Without it, service calls are invisible in the UI. Required when using `SupportsResponse`. | MEDIUM | Conditional — only generated when service calls are included. Must match service registration in `__init__.py`. |
| **Lovelace resource auto-registration via HA URL** | Rather than requiring users to manually add the JS resource in the Lovelace resources panel, the integration serves the card at a predictable `/custom_components/{domain}/frontend/{domain}-card.js` URL and registers it. | LOW | Already in the template concept. The key is using the correct `async_register_static_paths` API. |

---

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem like good ideas but create maintenance burden, HACS rejection, or HA ecosystem friction.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Fine-grained Jinja2 `{% if %}` blocks inside Python files** | Seems like it makes the template more flexible (one file, all variants). | Destroys Python syntax highlighting, makes the template unreadable, causes subtle Jinja/Python indentation conflicts, and makes testing the template itself very hard. Copier renders the template — reviewers read the rendered output, not the template. | Whole-file conditionals: generate `websocket.py` or don't. Use minimal section-level blocks ONLY in `__init__.py` for import/registration lines. |
| **Build tooling for the Lovelace card (webpack, rollup, TypeScript)** | TypeScript gives type safety; bundlers enable module imports and tree shaking. | HACS custom integrations must be single-file JS with no build step or they require a separate build CI and bundled file. Users cannot read or modify the source. HA itself loads LitElement from the existing Lovelace bundle — no npm needed. | Vanilla JS with extracted LitElement reference (`customElements.get("hui-masonry-view")`). Single file, no build. |
| **pip dependencies in `requirements`** | Makes the integration self-contained with a dedicated library. | HACS integrations with pip deps require HA to download them on install, creating version conflicts with HA's bundled packages and causing install failures on constrained systems. All three child projects can be built with `aiohttp` (bundled in HA). | Use `async_get_clientsession(hass)` which provides the HA-managed aiohttp session. Zero pip deps. |
| **`async_setup` in addition to `async_setup_entry`** | Needed for global setup, service registration in old HA patterns. | `async_setup` is the legacy entry point for YAML-configured integrations. Config-flow integrations only use `async_setup_entry`. Service registration should happen in `async_setup_entry` or via `hass.services.async_register` inside `async_setup_entry`. Adding `async_setup` confuses the flow. | Register services inside `async_setup_entry`. For services that should only register once (not per entry), use `hass.data` flag guard or `hass.services.has_service` check. |
| **Storing coordinator/client in `hass.data[DOMAIN]`** | It works and was the documented pattern until 2024. | HA has fully migrated to `ConfigEntry.runtime_data`. The old pattern generates deprecation warnings in 2025+, fails type checking, and requires careful cleanup in `async_unload_entry`. Community reviewers now flag this. | Use `entry.runtime_data = MyData(coordinator=..., client=...)` with a typed `ConfigEntry` generic. |
| **Lovelace resource registration via `lovelace` component API** | Seems like the "right" way to register resources programmatically. | The `lovelace` component approach (`hass.components.lovelace`) requires the Lovelace component to be loaded, is undocumented for custom use, and generates deprecation warnings. HACS itself moved away from this. | Serve the card JS via `async_register_static_paths` at a known URL. Document the URL in the README so users can add it manually if needed. HACS itself adds resources for HACS-managed cards automatically. |
| **Entity platform setup in `__init__.py`** | Keeps all code in one place. | Violates HA's platform discovery pattern. Entities must be in their platform files (`sensor.py`, `binary_sensor.py`, etc.) and set up via `async_forward_entry_setups`. This is a hassfest validation requirement. | Always forward platform setup: `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)`. |
| **Multiple HACS categories (integration + plugin in same repo)** | Seems efficient — one repo, both the integration and the card. | HACS treats integration and plugin (Lovelace card) as separate categories. A repo can only be in one category. Mixing them causes HACS validation failures. | Bundle the card JS file inside the `custom_components/{domain}/frontend/` directory. It gets served via `async_register_static_paths`, not as a separate HACS plugin entry. This is what the template architecture already does. |
| **Global/shared state between config entries** | For multi-account setups, sharing cached data across entries seems efficient. | Creates hard-to-debug race conditions, makes reload unreliable, and violates HA's config entry isolation model. Each config entry must be fully independent. | Each entry creates its own coordinator and client. If caching is needed, scope it to `entry.runtime_data`. |

---

## Feature Dependencies

```
[manifest.json] ──required by──> [hassfest CI]
[manifest.json: config_flow: true] ──enables──> [Config Flow]
[manifest.json: dependencies: ["frontend"]] ──required for──> [async_register_static_paths]

[Config Flow]
    └──requires──> [unique_id in config flow]
                       └──enables──> [already_configured abort]
                       └──enables──> [Options Flow]
                       └──enables──> [Reauthentication Flow]
                       └──enables──> [Reconfigure Flow]

[Options Flow] ──requires──> [Config Flow]
[Options Flow] ──uses──> [strings.json options section]

[DataUpdateCoordinator]
    └──requires──> [async_get_clientsession(hass) in coordinator]
    └──enables──> [CoordinatorEntity base]
                      └──requires──> [Device Registry entry]
                      └──requires──> [unique_id per entity]

[ConfigEntry.runtime_data] ──replaces──> [hass.data[DOMAIN]]
[ConfigEntry.runtime_data] ──enables type-safety──> [typed ConfigEntry generic]

[WebSocket Commands (conditional)]
    └──requires──> [manifest.json: dependencies includes "websocket_api" or "http"]
    └──requires──> [async_setup_entry: websocket_api.async_register_command]
    └──enables──> [Frontend card calling ws commands]

[Service Calls with SupportsResponse (conditional)]
    └──requires──> [services.yaml]
    └──requires──> [async_setup_entry: hass.services.async_register]
    └──enables──> [Frontend or automation calling service and reading response]

[Multiple Coordinators (conditional)]
    └──requires──> [DataUpdateCoordinator base]
    └──requires──> [runtime_data dataclass with multiple coordinator fields]

[Multi-step Config Flow (conditional)]
    └──replaces──> [single-step Config Flow]
    └──requires──> [self._data dict for inter-step storage]

[Diagnostics]
    └──requires──> [runtime_data accessible in diagnostics.py]
    └──requires──> [async_redact_data for sensitive field redaction]

[pytest test scaffold]
    └──requires──> [pytest-homeassistant-custom-component]
    └──covers──> [Config Flow tests]
    └──covers──> [Coordinator mock tests]
    └──covers (conditional)──> [Options Flow tests]

[Lovelace Card]
    └──requires──> [async_register_static_paths in __init__.py]
    └──requires──> [manifest.json: dependencies: ["frontend"]]
    └──requires──> [window.customCards registration]
    └──includes──> [Card Editor with config-changed event]
    └──includes──> [getStubConfig()]
    └──includes──> [getCardSize()]
    └──includes──> [Theme CSS variables]
```

### Dependency Notes

- **`unique_id` in config flow requires careful key choice:** For service integrations without a serial number, use a stable derived value like `f"{host}:{port}"`. This must be set via `await self.async_set_unique_id(unique_id)` before `async_create_entry`.
- **`runtime_data` requires typed generic:** `type MyConfigEntry = ConfigEntry[MyData]` must be defined in a central module (often `__init__.py` or a new `models.py`) and imported by every file that accesses `entry.runtime_data`.
- **WebSocket commands conflict with service calls for same operation:** Don't expose the same operation as both a WS command and a service call — pick the right pattern. WS commands are for frontend-to-backend; service calls are for automation-to-integration.
- **Multi-step config flow is a whole-file replacement:** The single-step `config_flow.py` and multi-step `config_flow.py` are mutually exclusive. Copier conditional (`_copier_conf.operations.exclude`) must generate only one.
- **Diagnostics requires coordinator data be serializable:** The coordinator's `data` attribute must be JSON-serializable or must be explicitly serialized before inclusion in diagnostics output.

---

## MVP Definition

This is a template, not a user-facing product. "MVP" here means: the minimum the template must generate for a child project to pass HACS validation and Quality Scale Bronze, while being immediately usable by the child project developer.

### Launch With (Template v1)

The template's first complete version must generate all of the following without modification:

- [ ] `manifest.json` with all required fields, correct `homeassistant: 2025.7.0` minimum — **HACS blocker if missing**
- [ ] `hacs.json` with correct fields — **HACS blocker if missing**
- [ ] Config flow with `unique_id`, `already_configured` abort, and `CannotConnect`/`InvalidAuth` validation stubs — **Quality Scale Bronze**
- [ ] Options flow using `OptionsFlowWithReload` — **Quality Scale Silver, user expectation**
- [ ] `ConfigEntry.runtime_data` with typed generic dataclass — **modern pattern, replaces hass.data**
- [ ] Device registry entry with `DeviceEntryType.SERVICE` on every entity — **Quality Scale Bronze**
- [ ] `DataUpdateCoordinator` with `async_get_clientsession(hass)` — **resource correctness**
- [ ] `async_register_static_paths` with `StaticPathConfig` — **HA 2025.7 compatibility blocker**
- [ ] Lovelace card with editor, `window.customCards`, theme CSS variables, loading/error states — **user experience**
- [ ] `strings.json` + `translations/en.json` for config flow AND options flow — **UI correctness**
- [ ] `parallel_updates = 0` on all platform files — **Quality Scale Silver**
- [ ] `pytest` test scaffold: `conftest.py`, `test_config_flow.py`, `test_coordinator.py` — **Quality Scale Bronze**
- [ ] CI: hassfest + hacs/action validation on every push — **HACS submission requirement**
- [ ] Release workflow producing correct version-tagged zip — **HACS distribution requirement**
- [ ] `README.md` stub with HACS installation badge and instructions — **user expectation**

### Add After Validation (Template v1.x)

- [ ] `diagnostics.py` with `async_redact_data` — high value, low complexity, add soon
- [ ] `quality_scale.yaml` tracking Quality Scale rule compliance — signals maturity
- [ ] `services.yaml` schema (conditional with service calls) — required for SupportsResponse UI
- [ ] Reconfigure flow stub — cleaner alternative to options flow for connection details

### Future Consideration (Template v2+)

- [ ] Reauthentication flow (`async_step_reauth`) — needed for cloud APIs, defer until Requestarr is being built
- [ ] Device diagnostics (in addition to config entry diagnostics) — Gold Quality Scale, significant extra work
- [ ] Automatic discovery (zeroconf/mDNS/SSDP) — none of the three child projects need this
- [ ] String translations beyond English — defer until integrations are stable; community can contribute

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| `async_register_static_paths` fix | HIGH (HACS broken without it) | LOW | P1 |
| `unique_id` in config flow | HIGH (duplicate prevention) | LOW | P1 |
| `ConfigEntry.runtime_data` pattern | HIGH (modern, type-safe) | LOW | P1 |
| Connection validation in config flow | HIGH (UX + quality scale) | MEDIUM | P1 |
| Device registry with `DeviceEntryType.SERVICE` | HIGH (entity grouping, diagnostics) | MEDIUM | P1 |
| Options flow (`OptionsFlowWithReload`) | HIGH (user reconfiguration) | MEDIUM | P1 |
| pytest test scaffold | HIGH (quality scale, CI) | HIGH | P1 |
| `async_get_clientsession(hass)` | HIGH (resource safety) | LOW | P1 |
| Loading/error states in card | MEDIUM (UX polish) | MEDIUM | P1 |
| `diagnostics.py` | MEDIUM (debugging, quality scale) | MEDIUM | P2 |
| `parallel_updates = 0` | MEDIUM (correctness) | LOW | P2 |
| `quality_scale.yaml` | LOW (signaling) | LOW | P2 |
| WebSocket commands (conditional) | HIGH (Immich, Requestarr) | HIGH | P1 (conditional) |
| Service calls with SupportsResponse (conditional) | HIGH (Argos, Requestarr) | HIGH | P1 (conditional) |
| Multi-step config flow (conditional) | HIGH (Requestarr) | HIGH | P1 (conditional) |
| Multiple coordinators (conditional) | HIGH (Immich) | MEDIUM | P1 (conditional) |
| Reauthentication flow | MEDIUM (cloud APIs) | MEDIUM | P2 |
| Reconfigure flow | MEDIUM (UX) | MEDIUM | P2 |

**Priority key:**
- P1: Must have for template v1 launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

"Competitors" here are reference implementations — the integrations/blueprints that set community expectations.

| Feature | ludeeus/integration_blueprint | jpawlowski/hacs.integration_blueprint | Our Template |
|---------|-------------------------------|----------------------------------------|--------------|
| Config flow with unique_id | Yes | Yes | Yes (fix needed) |
| Options flow | Yes | Yes | Yes (add) |
| ConfigEntry.runtime_data | Yes (2024 update) | Yes | No — must migrate |
| Device registry | Yes | Yes | No — must add |
| async_get_clientsession | Yes | Yes | No — must add |
| async_register_static_paths | N/A (no frontend) | N/A | Must fix |
| Lovelace card | No | No | Yes (differentiator) |
| pytest scaffold | Yes | Yes | No — must add |
| Diagnostics | Yes | Yes | No — must add |
| Copier/template engine | No (use-as-is) | No (use-as-is) | Yes (differentiator) |
| Conditional patterns (WS, services, multi-step) | No | No | Yes (differentiator) |
| Typed ConfigEntry generic | Yes | Yes | No — must add |

**Assessment:** The ludeeus blueprint is the industry reference for integration structure. Our template lags in modern patterns (`runtime_data`, device registry, test scaffold) but exceeds it in scope (Lovelace card, Copier conditionals). Catching up on lagging items is the core work.

---

## Sources

- [HACS Integration Requirements](https://www.hacs.xyz/docs/publish/integration/) — HACS validator rules (MEDIUM confidence, WebSearch verified)
- [HA Integration Quality Scale Rules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/) — Bronze/Silver/Gold tier rules (HIGH confidence, official docs)
- [Store runtime data inside the config entry — HA Developer Blog 2024-04-30](https://developers.home-assistant.io/blog/2024/04/30/store-runtime-data-inside-config-entry/) — `runtime_data` pattern (HIGH confidence)
- [async_register_static_paths — HA Developer Blog 2024-06-18](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/) — static path API migration (HIGH confidence)
- [Config flow handler — HA Developer Docs](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) — unique_id, abort, reconfigure, reauth patterns (HIGH confidence)
- [Options flow — HA Developer Docs](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/) — OptionsFlowWithReload (HIGH confidence)
- [Integration diagnostics — HA Developer Docs](https://developers.home-assistant.io/docs/core/integration_diagnostics/) — async_get_config_entry_diagnostics pattern (HIGH confidence)
- [Extending the WebSocket API — HA Developer Docs](https://developers.home-assistant.io/docs/frontend/extending/websocket-api/) — WebSocket command registration (HIGH confidence)
- [Integration service actions — HA Developer Docs](https://developers.home-assistant.io/docs/dev_101_services/) — SupportsResponse pattern (HIGH confidence)
- [Custom card — HA Developer Docs](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/) — LitElement card requirements (HIGH confidence)
- [ludeeus/integration_blueprint](https://github.com/ludeeus/integration_blueprint) — reference implementation (MEDIUM confidence, structure inferred from WebSearch)
- [jpawlowski/hacs.integration_blueprint](https://github.com/jpawlowski/hacs.integration_blueprint) — modern reference (MEDIUM confidence)
- [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) — testing fixtures (MEDIUM confidence)
- [hacs/integration issues #3828, #3868](https://github.com/hacs/integration/issues/3828) — register_static_path deprecation evidence (HIGH confidence)

---
*Feature research for: HA HACS Integration Template (Copier-based)*
*Researched: 2026-02-19*
