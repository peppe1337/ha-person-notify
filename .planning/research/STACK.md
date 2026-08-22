# Stack Research

**Domain:** Home Assistant HACS Custom Integration Template with Lovelace Frontend
**Researched:** 2026-02-19
**Confidence:** HIGH (HA backend), MEDIUM (Copier tooling), MEDIUM (LitElement resolution)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Home Assistant | 2025.7+ minimum | Target runtime platform | `async_register_static_paths` (non-blocking static file registration) was added in 2024.6 and `hass.http.register_static_path` was removed in 2025.7. All three child projects require this API. Pinning to 2025.7+ eliminates the old deprecated path and avoids dual-path maintenance. |
| Python | 3.12+ | Backend integration language | HA's bundled interpreter. No installation step — write to its constraints. Use `from __future__ import annotations` and `type MyEntry = ConfigEntry[MyCoordinator]` (PEP 695 style) for typed entries. |
| LitElement | HA-bundled (Lit 2.x / 3.x) | Lovelace card base class | HA ships LitElement internally. Access via `Object.getPrototypeOf(customElements.get("hui-masonry-view"))` — no CDN, no npm, no build step. Zero runtime dependency management. Cards self-register in the same JS file. |
| Copier | 9.11.3 (latest stable, Jan 2026) | Template engine for project generation and `copier update` inheritance | Copier handles Jinja2 variable substitution across file contents AND file/directory names. It supports `copier update` which allows propagating template fixes to child projects via git merge. Cookiecutter has no update mechanism. Yeoman is JS-ecosystem. Copier is the standard for Python/HA project templates. |

### HA Backend Libraries (HA-Bundled Only)

| Library | Source | Purpose | Notes |
|---------|--------|---------|-------|
| `homeassistant.helpers.aiohttp_client.async_get_clientsession` | HA core | HTTP session for all API calls | Returns the shared HA aiohttp ClientSession. Never create `aiohttp.ClientSession()` directly — HA won't manage its lifecycle and logs deprecation warnings. Use `async_create_clientsession` only when cookies or separate connection pools are required. |
| `homeassistant.helpers.update_coordinator.DataUpdateCoordinator` | HA core | Periodic data polling with shared state | The canonical polling pattern for HA integrations. Integrates with `CoordinatorEntity` for auto-refresh and error propagation. Multiple coordinators can run independently with different intervals. |
| `homeassistant.config_entries.ConfigFlow` / `OptionsFlow` | HA core | UI-driven integration setup and reconfiguration | `ConfigFlow` handles initial setup; `OptionsFlow` handles post-setup changes (host, port, API key). Both required for community-quality integrations. Missing `OptionsFlow` means users must remove-and-readd to change settings, losing entity history. |
| `homeassistant.components.http.StaticPathConfig` | HA core | Dataclass for static path registration | Imported from `homeassistant.components.http`. Used with `await hass.http.async_register_static_paths([StaticPathConfig(url, path, cache)])`. |
| `homeassistant.helpers.device_registry.DeviceInfo` + `DeviceEntryType.SERVICE` | HA core | Device grouping in HA UI | Groups all integration entities under one device card. `DeviceEntryType.SERVICE` is the correct type for software services with no physical hardware. Import `DeviceEntryType` from `homeassistant.components.device_registry`. |
| `homeassistant.core.SupportsResponse` | HA core | Service call return values | `SupportsResponse.ONLY` for pure-response services (no side effects displayed). `SupportsResponse.OPTIONAL` for services that can optionally return data. Introduced in HA 2023.7, stable and available in 2025.7+. |
| `voluptuous` | HA-bundled | Config/service schema validation | HA's standard schema library. Used in `ConfigFlow` data schemas and service schemas. Do not import standalone voluptuous from pip — use HA's bundled version. |
| `homeassistant.components.websocket_api` | HA core | WebSocket command registration | Used for `@websocket_api.websocket_command` decorator pattern. Allows frontend cards to communicate with backend via the existing HA WebSocket connection rather than making separate HTTP API calls. |

### Development / CI Tools

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| `pytest-homeassistant-custom-component` | Latest (updated daily) | Test fixtures mirroring HA core test infrastructure | Provides `hass`, `config_entry`, `mock_config_entry` fixtures. Requires `enable_custom_integrations` fixture. Updated daily to track HA releases — pin to a version range matching the minimum HA version. |
| `pytest-asyncio` | Latest | Async test execution | Required by pytest-homeassistant-custom-component. Configure `asyncio_mode = auto` in `pytest.ini` or `pyproject.toml`. |
| `hassfest` (via `home-assistant/actions/hassfest@master`) | GitHub Action | Validates manifest.json, strings.json, config flow structure | The canonical validation tool for HA custom integrations. Catches missing fields, incorrect types, bad translation keys before HACS submission. Use `@master` per official docs. |
| `hacs/action@main` | GitHub Action | Validates HACS repository structure | Checks hacs.json, repository naming, README presence, and category-specific requirements. Required for HACS default repository inclusion. |
| `softprops/action-gh-release@v2` | GitHub Action | Attaches release zip to GitHub releases | Pairs with the `version` injection step. The standard approach for HACS releases without a separate package registry. |

---

## Key API Patterns (with Versions)

### Static Path Registration (HA 2025.7+)

```python
from homeassistant.components.http import StaticPathConfig

# In async_setup_entry or async_setup:
await hass.http.async_register_static_paths([
    StaticPathConfig(
        "/local/custom_components/my_domain/my_domain-card.js",
        str(Path(__file__).parent / "frontend" / "my_domain-card.js"),
        cache_headers=True,
    )
])
```

**NOT this (removed in 2025.7):**
```python
hass.http.register_static_path(...)  # REMOVED - causes blocking I/O in event loop
```

### Typed ConfigEntry with runtime_data (HA 2024.4+ pattern, quality scale requirement)

```python
type MyDomainConfigEntry = ConfigEntry[MyCoordinator]

async def async_setup_entry(hass: HomeAssistant, entry: MyDomainConfigEntry) -> bool:
    coordinator = MyCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator  # NOT hass.data[DOMAIN][entry.entry_id]
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
```

**Why:** `entry.runtime_data` is the quality-scale-required pattern as of 2024. It is typed via the `ConfigEntry[T]` generic. Avoids `hass.data` dictionary lookups and associated type-safety issues.

### LitElement Resolution (No Build Tools)

```javascript
// Preferred — masonry view always exists, fallback to hui-view
const LitElement = Object.getPrototypeOf(
  customElements.get("hui-masonry-view") ||
  customElements.get("hui-view")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;
```

**Why:** HA ships LitElement internally and exposes it through its registered custom elements. This avoids CDN imports (which add network dependency and break offline installs) and avoids npm/build steps (which break the single-file constraint). The `hui-masonry-view` fallback pattern is the community standard used by well-maintained cards (e.g., mini-graph-card, atomic calendar revive).

### Device Registry (HA 2025.7+)

```python
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.device_registry import DeviceEntryType

# In CoordinatorEntity subclass:
@property
def device_info(self) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
        name=self.coordinator.config_entry.title,
        manufacturer="Custom",
        entry_type=DeviceEntryType.SERVICE,
    )
```

### Config Flow with unique_id (Required for Quality Scale Bronze)

```python
async def async_step_user(self, user_input=None):
    if user_input is not None:
        # Set unique_id to prevent duplicate entries
        await self.async_set_unique_id(user_input[CONF_HOST])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=user_input[CONF_HOST], data=user_input)
```

**Missing from current scaffold** — a missing `unique_id` allows duplicate config entries for the same host.

---

## Copier Template Configuration

### copier.yml Pattern

```yaml
# Template metadata
_min_copier_version: "9.0"
_subdirectory: template   # keep template files separate from copier config files
_answers_file: .copier-answers.yml

# Project variables
project_name:
  type: str
  help: "Human-readable project name (e.g. 'Immich Browser')"

domain:
  type: str
  help: "Integration domain slug (e.g. 'immich_browser')"

# Feature flags for coarse-grained conditionals
use_websocket:
  type: bool
  default: false
  help: "Include WebSocket command handler pattern"

use_multi_coordinator:
  type: bool
  default: false
  help: "Include multi-coordinator pattern"

use_service_response:
  type: bool
  default: false
  help: "Include SupportsResponse service call pattern"

use_multi_step_config:
  type: bool
  default: false
  help: "Include multi-step config flow pattern"
```

### Directory Naming

Copier uses `{{ variable }}` in file/directory names by default. For directories that map to the HA domain name:

```
template/
  custom_components/
    {{ domain }}/           # rendered as e.g. immich_browser/
      __init__.py
      manifest.json
      frontend/
        {{ domain }}-card.js
```

### Whole-File Conditionals (Coarse-Grained)

```
template/
  custom_components/
    {{ domain }}/
      websocket.py.jinja           # always included, reads use_websocket inside
      {% if use_websocket %}websocket_handlers.py{% endif %}.jinja   # excluded entirely
```

**Best practice:** Use whole-file inclusion/exclusion (the `{% if %}` in filename) for optional modules (websocket.py, multi_coordinator.py). Use inline `{% if %}` blocks sparingly and only for short sections like platform registration lists in `__init__.py`.

---

## hacs.json Pattern

```json
{
  "name": "{{ project_name }}",
  "homeassistant": "2025.7",
  "render_readme": true
}
```

**Fields:**
- `name` — required, shown in HACS UI
- `homeassistant` — minimum HA version; set to `"2025.7"` (matches `async_register_static_paths` requirement)
- `render_readme` — renders README.md in HACS UI instead of requiring a separate info.md

**Not needed in hacs.json:** `category` is only needed for non-integration repositories. Integration repos are inferred from their directory structure.

---

## manifest.json Pattern

```json
{
  "domain": "{{ domain }}",
  "name": "{{ project_name }}",
  "codeowners": ["@{{ github_username }}"],
  "config_flow": true,
  "dependencies": ["frontend"],
  "documentation": "https://github.com/{{ github_username }}/{{ repo_name }}",
  "integration_type": "service",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/{{ github_username }}/{{ repo_name }}/issues",
  "requirements": [],
  "version": "0.0.0"
}
```

**Notes:**
- `"dependencies": ["frontend"]` — required when registering Lovelace resources; ensures the frontend component loads before this integration
- `"integration_type": "service"` — correct for software-only integrations with no physical devices
- `"requirements": []` — always empty; this template forbids pip dependencies
- `"version"` — CI workflow overwrites this from the GitHub release tag at release time
- `"iot_class"` — varies per child project: `"local_polling"` for Argos/Immich, `"cloud_polling"` for Requestarr

---

## Test Scaffold

### conftest.py pattern

```python
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield
```

### pytest.ini / pyproject.toml

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Requirements file (tests only)

```
pytest-homeassistant-custom-component
pytest-asyncio
```

No other test dependencies — use HA's bundled mocking utilities from `unittest.mock`.

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `copier update` for child project propagation | Git submodule / subtree | Git merge breaks on domain renames (every filename and import changes). Copier re-renders with correct variable substitution on `copier update`. |
| HA-bundled LitElement via `customElements.get()` | CDN import from unpkg.com | CDN imports fail offline, add latency, can be blocked by CSP. HA already ships LitElement — use what's there. |
| HA-bundled LitElement | npm + rollup/webpack build | Build tools break the single-file constraint and add a separate CI build step. HA community cards (mini-graph-card, button-card) all ship pre-built; this template produces the pre-built file directly. |
| `entry.runtime_data` | `hass.data[DOMAIN][entry.entry_id]` | `hass.data` is untyped, requires manual cleanup in `async_unload_entry`, and is deprecated as the recommended pattern. `runtime_data` is automatically cleaned up and typed. |
| `async_get_clientsession(hass)` | Raw `aiohttp.ClientSession()` | Raw sessions aren't managed by HA's lifecycle — they leak connections and trigger deprecation warnings. The shared session handles connection pooling, verify_ssl, and proper cleanup. |
| `async_register_static_paths` | `hass.http.register_static_path` | The old method did blocking I/O in the async event loop and was removed in HA 2025.7. |
| Whole-file Copier conditionals | Fine-grained `{% if %}` inside every file | Inline conditionals throughout code files make templates unreadable and error-prone. Whole-file conditionals keep each generated file clean and directly readable as Python/JS. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `hass.http.register_static_path()` | Removed in HA 2025.7. Caused blocking I/O in async event loop. | `await hass.http.async_register_static_paths([StaticPathConfig(...)])` |
| `aiohttp.ClientSession()` directly | HA won't manage lifecycle; connection leak risk; logs deprecation errors. | `async_get_clientsession(hass)` |
| `hass.data[DOMAIN]` for coordinator storage | Untyped, manual cleanup required, deprecated as quality-scale pattern. | `entry.runtime_data = coordinator` |
| CDN LitElement imports | Offline failure, CSP blockage, extra network request. | `Object.getPrototypeOf(customElements.get("hui-masonry-view"))` |
| pip dependencies in `requirements` | HA sandboxes custom components; pip-installed packages may conflict with HA's environment or fail to install. | HA-bundled libraries only (aiohttp, voluptuous, homeassistant.*) |
| npm / build toolchain for frontend | Breaks single-file constraint; adds CI complexity for a card that's 200-400 lines of vanilla JS. | Vanilla JS with HA's internal LitElement |
| Missing `unique_id` in config flow | Allows duplicate config entries for the same service endpoint. HACS quality checks flag this. | `await self.async_set_unique_id(...)` + `self._abort_if_unique_id_configured()` |
| Fine-grained Jinja2 throughout code files | Template becomes unreadable; child project developers see `{% if use_websocket %}` noise throughout every file. | Whole-file inclusion via Copier filename conditionals |

---

## Version Compatibility

| Component | Version | Constraint | Notes |
|-----------|---------|------------|-------|
| `async_register_static_paths` | HA 2024.6+ | Minimum HA 2025.7 (old removed) | Available since 2024.6, old `register_static_path` removed in 2025.7. |
| `ConfigEntry.runtime_data` | HA 2024.4+ | Bronze quality scale requirement | Required by hassfest quality_scale validation. |
| `DeviceEntryType.SERVICE` | HA 2022.3+ | Well-established | The string-based `entry_type="service"` was deprecated in 2022.3; use the enum. |
| `SupportsResponse` | HA 2023.7+ | Available in 2025.7+ | Part of the service call response data feature added in 2023.7. |
| `ConfigEntry[T]` generic typing | Python 3.12+ / HA 2024.x | Required for `type MyEntry = ConfigEntry[T]` syntax | PEP 695 TypeVar syntax. HA enforces Python 3.12+. |
| `pytest-homeassistant-custom-component` | Updated daily | Track to HA major version | Pin loosely: `>=2025.7.0`. Updated daily to match HA releases. |
| `copier` | 9.11.3 (Jan 2026) | `_min_copier_version: "9.0"` | v9 introduced loop-based file generation. v9.11.x is current stable. |
| `hacs/action` | `@main` | Always use `@main` | HACS recommends @main for the action. Stable. |
| `home-assistant/actions/hassfest` | `@master` | Always use `@master` | Official recommendation from home-assistant/actions. |

---

## Installation

This is a template — child projects have no `npm install` or `pip install` for runtime dependencies. Development dependencies only.

```bash
# Install Copier (template tooling — runs on developer machine, not in HA)
pip install copier>=9.0

# Create a new child project from this template
copier copy gh:owner/ha-hacs-template ./ha-my-integration

# Update a child project when template changes
cd ha-my-integration
copier update

# Test dependencies only (in child project)
pip install pytest-homeassistant-custom-component pytest-asyncio

# Run tests
pytest tests/
```

---

## Sources

- [Making http path registration async safe with async_register_static_paths — HA Developer Blog 2024-06-18](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/) — MEDIUM confidence (WebSearch verified, official HA dev blog)
- [Use ConfigEntry.runtime_data — HA Integration Quality Scale Rules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data/) — MEDIUM confidence (WebSearch found, official dev docs)
- [inject-websession quality scale rule — HA Developer Docs](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession/) — MEDIUM confidence (WebSearch found)
- [Copier 9.11.3 release — January 23, 2026](https://github.com/copier-org/copier/releases/tag/v9.11.3) — MEDIUM confidence (version confirmed via WebSearch result)
- [Configuring a template — Copier docs](https://copier.readthedocs.io/en/stable/configuring/) — MEDIUM confidence (official docs)
- [pytest-homeassistant-custom-component — PyPI](https://pypi.org/project/pytest-homeassistant-custom-component/) — MEDIUM confidence (WebSearch found, official package)
- [HACS Integrations publish requirements — hacs.xyz](https://www.hacs.xyz/docs/publish/integration/) — MEDIUM confidence (official HACS docs)
- [home-assistant/actions hassfest — GitHub](https://github.com/home-assistant/actions) — MEDIUM confidence (official HA org)
- [Custom card developer docs — HA Developer Docs](https://developers.home-assistant.io/docs/frontend/custom-ui/lovelace-custom-card/) — MEDIUM confidence (official HA dev docs)
- [Integration type annotation pattern — HA Core 2025.1 changelog](https://rc.home-assistant.io/changelogs/core-2025.1) — MEDIUM confidence (WebSearch found)
- Existing scaffold analysis — HIGH confidence (direct code inspection of project files)

---

*Stack research for: HA HACS Integration Template (Copier-based)*
*Researched: 2026-02-19*
