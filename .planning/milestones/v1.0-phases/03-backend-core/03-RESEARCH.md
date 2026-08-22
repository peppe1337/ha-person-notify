# Phase 3: Backend Core - Research

**Researched:** 2026-02-19
**Domain:** Home Assistant integration APIs — DataUpdateCoordinator, ConfigEntry.runtime_data typed generics, CoordinatorEntity, DeviceEntryType, config/options flow, ApiClient, manifest, translations
**Confidence:** HIGH (HA developer docs verified; HA core source verified; hacs.xyz docs verified)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BACK-01 | Generic `ApiClient` base class with configurable auth (header/body/query), timeout, and error handling | HA docs: `async_get_clientsession(hass)` provides managed session; `aiohttp.ClientError` + `aiohttp.ClientTimeout` are the standard error/timeout types; CannotConnect/InvalidAuth exceptions are the HA convention |
| BACK-02 | `DataUpdateCoordinator` subclass using API client from `runtime_data`, with configurable `update_interval` | Verified: `DataUpdateCoordinator[T]` is a typed generic; coordinator stores client in `__init__`; `_async_update_data` raises `UpdateFailed`; `config_entry: ConfigEntry` class attribute gives access to runtime_data |
| BACK-03 | Typed `ConfigEntry` generic defined as `type MyConfigEntry = ConfigEntry[MyData]` with dataclass `runtime_data` | Verified: `type MyConfigEntry = ConfigEntry[MyData]` is the current HA pattern (Python 3.12+ `type` statement); dataclass holds coordinator(s); planner uses this from existing __init__.py.jinja |
| BACK-04 | Sensor platform with `CoordinatorEntity` base, `_attr_has_entity_name = True`, `_attr_unique_id`, and example sensor | Verified: `CoordinatorEntity[MyCoordinator]` + `SensorEntity` MRO; `_attr_has_entity_name = True` required; `_attr_unique_id = f"{entry.entry_id}_{key}"` pattern; existing sensor.py.jinja already partially implements this |
| BACK-05 | Device registry integration with `DeviceEntryType.SERVICE` on every entity via `device_info` property | Verified: `DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, entry_type=DeviceEntryType.SERVICE, name=...)` is the pattern for service integrations (WAQI, OTP, GitHub, 17Track all use this) |
| BACK-06 | Options flow for reconfiguring host/port/API key after initial setup without removing integration | Verified: `OptionsFlowWithReload` (HA 2025.8+) is preferred over `OptionsFlow` when connection details change; `OptionsFlow` base is acceptable; `OptionsFlowHandler()` constructor takes NO arguments; `self.config_entry` injected by base class |
| BACK-07 | `manifest.json` with all required fields, `homeassistant: "2025.7.0"`, `dependencies: ["frontend"]`, `integration_type: "service"` | Verified: manifest has no "homeassistant" minimum version field — that goes in `hacs.json` only; `issue_tracker` (not `issue_tracker_url`) is the correct field name |
| BACK-08 | `hacs.json` with correct `name` and `homeassistant` minimum version | Verified: `hacs.json` supports `name` (required) and `homeassistant` (optional, minimum HA version string); existing template has both |
| BACK-09 | `strings.json` and `translations/en.json` covering config flow, options flow, and error messages | Verified: both files must have identical key structure; `strings.json` is HA-primary, `translations/en.json` is the English runtime file; both must be present for config flow labels to render |
| BACK-10 | `parallel_updates = 0` set on all platform files (sensor.py and any conditional platforms) | Verified: variable is `PARALLEL_UPDATES` (uppercase, module-level); value is `0` for coordinator-based read-only platforms; applies to sensor.py; conditional platforms (Phase 5) should also get it |
</phase_requirements>

---

## Summary

Phase 3 builds on an already-working Copier template scaffold (Phase 2). The existing `.jinja` files have partial implementations of most BACK requirements — specifically, the coordinator, config flow, sensor, and manifest patterns are roughed in. The phase's work is NOT starting from scratch but filling specific gaps in these existing templates to make the generated integration fully functional.

The eight existing template files in `template/custom_components/[[ project_domain ]]/` already implement: `runtime_data` typed ConfigEntry generic (BACK-03 done), `DataUpdateCoordinator` subclass with `async_get_clientsession` (BACK-02 partial), `CoordinatorEntity` + `SensorEntity` inheritance (BACK-04 partial), `CannotConnect`/`InvalidAuth` exceptions (BACK-01 partial), and `OptionsFlowHandler(OptionsFlow)` with no-`__init__` pattern (BACK-06 partial). What is MISSING: `ApiClient` class (BACK-01 — not yet in any template file), `DeviceInfo`/`DeviceEntryType.SERVICE` on entities (BACK-05 — not in sensor.py.jinja), `PARALLEL_UPDATES = 0` (BACK-10 — not in sensor.py.jinja), `CONF_API_KEY` wired into config/options flow forms and strings.json (BACK-06 gap), and `hacs.json` not imported into sensor (BACK-08 already done in template/).

The key architectural pattern for HA 2025.7+ integrations: `type XxxConfigEntry = ConfigEntry[XxxData]` (Python 3.12 `type` alias statement), `@dataclass class XxxData`, coordinator stored in `entry.runtime_data`, `PARALLEL_UPDATES = 0` at platform module level, `DeviceInfo(entry_type=DeviceEntryType.SERVICE)` in every entity's `_attr_device_info`, and `OptionsFlowWithReload` for connection-detail options flows.

**Primary recommendation:** Add `api.py.jinja` (ApiClient template), add `DeviceInfo` + `PARALLEL_UPDATES = 0` to `sensor.py.jinja`, wire `CONF_API_KEY` through config/options flow and strings.json, and switch `OptionsFlowHandler` to `OptionsFlowWithReload`. All other patterns are already structurally correct in the existing templates.

---

## Standard Stack

### Core (HA built-ins — no extra dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `homeassistant.helpers.update_coordinator.DataUpdateCoordinator` | HA 2025.7+ | Coordinated periodic data fetching | HA's official pattern for polling integrations; prevents N entities each polling independently |
| `homeassistant.helpers.update_coordinator.CoordinatorEntity` | HA 2025.7+ | Entity base class that subscribes to coordinator updates | Provides `available`, `should_poll`, `async_update`, `async_added_to_hass` automatically |
| `homeassistant.config_entries.ConfigEntry` | HA 2025.7+ | Typed via `type XxxConfigEntry = ConfigEntry[XxxData]` | Official HA 2025 pattern; replaces `hass.data[DOMAIN]` |
| `homeassistant.helpers.aiohttp_client.async_get_clientsession` | HA 2025.7+ | HTTP session for API calls | HA manages session lifecycle; do NOT create `aiohttp.ClientSession` directly |
| `homeassistant.helpers.device_registry.DeviceInfo` | HA 2025.7+ | Device entry creation via entity's `device_info` property | Automatic device registry integration |
| `homeassistant.helpers.device_registry.DeviceEntryType` | HA 2025.7+ | `DeviceEntryType.SERVICE` for cloud/service integrations | Correct entry_type for non-physical-hardware integrations |
| `homeassistant.config_entries.OptionsFlowWithReload` | HA 2025.8+ | Options flow that auto-reloads integration on save | Eliminates need for `entry.add_update_listener()` when options change |
| `homeassistant.helpers.update_coordinator.UpdateFailed` | HA 2025.7+ | Exception raised in `_async_update_data` on failure | Standard error type; triggers retry logic in coordinator |
| `aiohttp.ClientError` | bundled with HA | Catch-all for HTTP connection failures | Maps to `CannotConnect` in config flow validation |
| `aiohttp.ClientTimeout` | bundled with HA | Request timeout configuration | Per-request or session-level timeout control |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `homeassistant.const.CONF_HOST` | any | Standard key for host config | Use instead of custom "host" string |
| `homeassistant.const.CONF_PORT` | any | Standard key for port config | Use instead of custom "port" string |
| `homeassistant.const.CONF_API_KEY` | any | Standard key for API key config | Use instead of custom "api_key" string — but note: `const.py.jinja` defines `CONF_API_KEY = "api_key"` locally; remove local def and import from `homeassistant.const` |
| `homeassistant.components.sensor.SensorEntity` | any | Sensor entity base class | All sensor entities |
| `homeassistant.config_entries.ConfigFlow` | any | Config flow base class | First-time integration setup |
| `homeassistant.config_entries.OptionsFlow` | any | Options flow base class (manual reload) | If NOT on HA 2025.8+ |
| `voluptuous` | bundled with HA | Form schema validation | All config/options flow data schemas |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `OptionsFlowWithReload` | `OptionsFlow` + `entry.add_update_listener()` | `OptionsFlowWithReload` eliminates boilerplate; requires HA 2025.8+ minimum; template already targets 2025.7.0 minimum — this is a decision the planner must make |
| `CONF_API_KEY` from `homeassistant.const` | Local `CONF_API_KEY = "api_key"` in const.py | HA standard keys reduce string errors; local definition already works but duplicates HA's constant |
| `DeviceInfo` in entity `__init__` | `device_info` as a `@property` | Setting `_attr_device_info` in `__init__` is the modern pattern (avoids re-instantiation on every state write) |

**Installation:** No additional packages. All dependencies are HA built-ins.

---

## Architecture Patterns

### What Already Exists in Templates vs What Needs Adding

**ALREADY IMPLEMENTED (do NOT re-implement):**
- `__init__.py.jinja`: typed ConfigEntry generic, `XxxData` dataclass, `async_setup_entry` with `runtime_data`, `async_unload_entry` (BACK-03 complete)
- `coordinator.py.jinja`: `DataUpdateCoordinator` subclass, `async_get_clientsession`, `_async_update_data` stub (BACK-02 partial — needs ApiClient wiring)
- `config_flow.py.jinja`: `CannotConnect`/`InvalidAuth`, `async_set_unique_id`, `_abort_if_unique_id_configured`, `OptionsFlowHandler(OptionsFlow)` with no `__init__` (BACK-06 partial — needs CONF_API_KEY field)
- `sensor.py.jinja`: `CoordinatorEntity[TemplateCoordinator]` + `SensorEntity`, `_attr_has_entity_name = True`, `_attr_unique_id` (BACK-04 partial)
- `manifest.json.jinja`: all 10 hassfest-required fields present (BACK-07 complete)
- `hacs.json.jinja` (in `template/` root): `name` and `homeassistant` fields (BACK-08 complete)
- `strings.json.jinja` + `translations/en.json.jinja`: config and options flow keys (BACK-09 partial — needs `api_key` field labels)

**NEEDS TO BE ADDED:**
1. `api.py.jinja` — new file: `ApiClient` base class (BACK-01)
2. `sensor.py.jinja` — add `PARALLEL_UPDATES = 0` and `device_info` via `DeviceInfo(entry_type=DeviceEntryType.SERVICE)` (BACK-05, BACK-10)
3. `config_flow.py.jinja` — add `CONF_API_KEY` field to both config and options flow schemas; wire `CONF_API_KEY` into `_async_validate_connection` stub (BACK-06 completion)
4. `strings.json.jinja` + `translations/en.json.jinja` — add `api_key` label to both config and options `data` sections (BACK-09 completion)
5. `coordinator.py.jinja` — update comment to reference `ApiClient` and show how to initialize from `entry.data` (BACK-02 completion)

### Recommended Project Structure (Generated Output)

```
custom_components/my_integration/
├── __init__.py              # setup/unload, XxxData dataclass, XxxConfigEntry type
├── api.py                   # ApiClient base class with auth/timeout/error handling
├── config_flow.py           # ConfigFlow + OptionsFlowHandler (or OptionsFlowWithReload)
├── const.py                 # DOMAIN, CONF_HOST, CONF_PORT, CONF_API_KEY, DEFAULT_PORT, etc.
├── coordinator.py           # DataUpdateCoordinator subclass using ApiClient
├── manifest.json            # all hassfest fields; integration_type="service"
├── sensor.py                # PARALLEL_UPDATES=0; CoordinatorEntity+SensorEntity
├── strings.json             # config/options flow labels + error keys
└── translations/
    └── en.json              # identical structure to strings.json
```

### Pattern 1: Typed ConfigEntry Generic (BACK-03)

**Already implemented in `__init__.py.jinja`. Shown here for reference.**

```python
# Source: HA quality scale docs (runtime-data rule)
# template/custom_components/[[ project_domain ]]/__init__.py.jinja

from __future__ import annotations
from dataclasses import dataclass
from homeassistant.config_entries import ConfigEntry

from .coordinator import TemplateCoordinator

@dataclass
class [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]Data:
    """Data for the [[ project_name ]] integration."""
    coordinator: TemplateCoordinator

type [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]ConfigEntry = ConfigEntry[
    [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]Data
]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]ConfigEntry,
) -> bool:
    coordinator = TemplateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]Data(coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
```

**Key:** `type` keyword (Python 3.12) creates a `TypeAlias` — HA 2025+ supports this. The dataclass wraps coordinator(s).

### Pattern 2: ApiClient Base Class (BACK-01) — NEW FILE

**This is the main new file needed: `api.py.jinja`.**

```python
# Source: HA api_lib_auth docs + aiohttp docs
# template/custom_components/[[ project_domain ]]/api.py.jinja

"""API client for [[ project_name ]]."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import CONF_API_KEY, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class CannotConnectError(Exception):
    """Exception raised when connection to service fails."""


class InvalidAuthError(Exception):
    """Exception raised when authentication fails."""


class ApiClient:
    """Generic API client for [[ project_name ]].

    Supports header-based auth (Authorization: Bearer <key>).
    Override `_get_auth_headers` for query/body auth variants.
    """

    def __init__(
        self,
        host: str,
        port: int,
        api_key: str,
        session: aiohttp.ClientSession,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the API client."""
        self._base_url = f"http://{host}:{port}"
        self._api_key = api_key
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    def _get_auth_headers(self) -> dict[str, str]:
        """Return authentication headers.

        Override to use query param or body auth instead.
        """
        return {"Authorization": f"Bearer {self._api_key}"}

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request.

        Raises CannotConnectError on connection failure.
        Raises InvalidAuthError on 401/403.
        """
        url = f"{self._base_url}{endpoint}"
        headers = self._get_auth_headers()
        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                timeout=self._timeout,
                **kwargs,
            ) as response:
                if response.status in (401, 403):
                    raise InvalidAuthError(
                        f"Authentication failed: {response.status}"
                    )
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientConnectionError as err:
            raise CannotConnectError(f"Cannot connect to {url}: {err}") from err
        except aiohttp.ClientError as err:
            raise CannotConnectError(f"Request failed: {err}") from err
        except asyncio.TimeoutError as err:
            raise CannotConnectError(f"Request timed out: {err}") from err

    async def async_test_connection(self) -> bool:
        """Test connection and authentication.

        Called from config flow validation.
        Returns True on success.
        Raises CannotConnectError or InvalidAuthError on failure.
        """
        # TODO: Replace with an actual lightweight endpoint
        await self._request("GET", "/health")
        return True

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch main data payload.

        TODO: Replace with actual endpoint for your service.
        """
        return await self._request("GET", "/api/data")
```

**Notes for planner:**
- `DEFAULT_TIMEOUT` needs to be added to `const.py.jinja` (e.g., `DEFAULT_TIMEOUT = 30`)
- Config flow creates ApiClient to test connection; coordinator creates it for ongoing fetching
- `CannotConnectError`/`InvalidAuthError` in `api.py` are DIFFERENT from `CannotConnect`/`InvalidAuth` in `config_flow.py` — the config flow catches api.py exceptions and re-raises its own; keep them separate or consolidate (see Pitfall 4)

### Pattern 3: Coordinator with ApiClient (BACK-02)

**Updates to `coordinator.py.jinja`:**

```python
# Source: HA fetching_data docs + GitHub/WAQI integration patterns
# Key change: instantiate ApiClient in __init__, use it in _async_update_data

from .api import ApiClient
from .const import CONF_API_KEY, DEFAULT_SCAN_INTERVAL, DOMAIN

class TemplateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data fetching from the service."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.config_entry = entry
        session = async_get_clientsession(hass)
        self.client = ApiClient(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            api_key=entry.data[CONF_API_KEY],
            session=session,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the service."""
        try:
            return await self.client.async_get_data()
        except CannotConnectError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
```

**Key:** import `CONF_HOST`, `CONF_PORT` from `homeassistant.const`; import `CONF_API_KEY` from `.const`; the coordinator stores the client and the config entry.

### Pattern 4: Sensor with device_info and PARALLEL_UPDATES (BACK-04, BACK-05, BACK-10)

**Updates to `sensor.py.jinja`:**

```python
# Source: WAQI sensor.py, GitHub sensor.py, OTP sensor.py (HA core)
# Three additions: PARALLEL_UPDATES, device_info, DeviceEntryType import

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

PARALLEL_UPDATES = 0  # coordinator centralizes updates; no per-entity semaphore needed


class TemplateSensor(CoordinatorEntity[TemplateCoordinator], SensorEntity):
    """Representation of a Template sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TemplateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_name = sensor_type.replace("_", " ").title()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=entry.title,
            manufacturer="[[ project_name ]]",
        )
```

**Key points:**
- `PARALLEL_UPDATES = 0` is module-level, BEFORE class definition
- `_attr_device_info` set in `__init__` (not as `@property`) — modern HA pattern
- `identifiers={(DOMAIN, entry.entry_id)}` — ties device to this config entry
- `DeviceEntryType.SERVICE` — marks it as a service, not physical hardware
- `entry.title` comes from `async_create_entry(title=user_input[CONF_HOST], data=...)` in config flow

### Pattern 5: Config Flow with CONF_API_KEY (BACK-06 completion)

**Updates to `config_flow.py.jinja`:**

```python
# Source: HA config_flow docs + prior decisions (SCAF-03, SCAF-05, SCAF-06 satisfied)
# Additions: CONF_API_KEY field in schema, OptionsFlowWithReload (if targeting 2025.8+)

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_API_KEY

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_API_KEY): str,
    }
)

# In OptionsFlowHandler — option: OptionsFlow or OptionsFlowWithReload
# OptionsFlowWithReload requires HA 2025.8+; template targets 2025.7.0 minimum
# Decision for planner: use OptionsFlow for maximum compatibility OR
# update hacs.json minimum to 2025.8.0 and use OptionsFlowWithReload
class OptionsFlowHandler(OptionsFlow):  # or OptionsFlowWithReload
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_HOST, default=self.config_entry.data.get(CONF_HOST, "")): str,
                vol.Optional(CONF_PORT, default=self.config_entry.data.get(CONF_PORT, DEFAULT_PORT)): int,
                vol.Optional(CONF_API_KEY, default=self.config_entry.data.get(CONF_API_KEY, "")): str,
            }),
        )
```

**Key:** `CONF_API_KEY` is imported from `homeassistant.const` (standard HA constant). The local `CONF_API_KEY = "api_key"` in `const.py.jinja` should be removed and replaced with the import from `homeassistant.const`.

### Pattern 6: Strings and Translations (BACK-09 completion)

**Updates to `strings.json.jinja` and `translations/en.json.jinja` — add `api_key` field:**

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Connect to Service",
        "description": "Enter the connection details for your service.",
        "data": {
          "host": "Host",
          "port": "Port",
          "api_key": "API Key"
        }
      }
    },
    "error": {
      "cannot_connect": "Failed to connect",
      "invalid_auth": "Invalid authentication",
      "unknown": "Unexpected error"
    },
    "abort": {
      "already_configured": "Service is already configured"
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Update Service Settings",
        "data": {
          "host": "Host",
          "port": "Port",
          "api_key": "API Key"
        }
      }
    }
  }
}
```

**Key:** `strings.json` and `translations/en.json` MUST be identical in structure. Both files must exist. hassfest validates key alignment between them.

### Pattern 7: Manifest Clarification (BACK-07)

**The manifest.json `homeassistant` minimum version does NOT exist as a manifest field.** It only exists in `hacs.json`. The manifest template is already correct. The requirement "homeassistant: 2025.7.0" in BACK-07 refers to the `hacs.json` minimum version, NOT a manifest field.

**Current manifest.json.jinja is already correct:**
```json
{
  "domain": "[[ project_domain ]]",
  "name": "[[ project_name ]]",
  "codeowners": ["@[[ author_name ]]"],
  "config_flow": true,
  "dependencies": ["frontend"],
  "documentation": "[[ documentation_url ]]",
  "integration_type": "[[ integration_type ]]",
  "iot_class": "[[ iot_class ]]",
  "issue_tracker": "[[ issue_tracker_url ]]",
  "requirements": [],
  "version": "[[ version ]]"
}
```

Note: Field is `issue_tracker` (not `issue_tracker_url`). Template correctly uses `issue_tracker_url` as the Copier VARIABLE name but outputs `"issue_tracker"` as the JSON KEY. This is correct.

**Current hacs.json.jinja is already correct:**
```json
{
  "name": "[[ project_name ]]",
  "homeassistant": "2025.7.0",
  "render_readme": true
}
```

### Anti-Patterns to Avoid

- **`CONF_API_KEY = "api_key"` in const.py:** HA ships `CONF_API_KEY` in `homeassistant.const`. Don't shadow it with a local constant. Import from HA instead.
- **Creating `aiohttp.ClientSession` directly:** Always use `async_get_clientsession(hass)`. HA manages the session lifecycle; creating your own means it won't be properly closed.
- **`device_info` as `@property` re-instantiating `DeviceInfo` on every state write:** Set `_attr_device_info` once in `__init__`. HA reads `_attr_device_info` directly without calling a property.
- **`OptionsFlowHandler.__init__(self, config_entry):`** Do NOT define `__init__` or assign `self.config_entry` manually. The `OptionsFlow` base class injects `config_entry` automatically. (This is SCAF-06, already fixed in template — do not regress.)
- **`async_get_options_flow` passing `config_entry` to constructor:** `return OptionsFlowHandler(config_entry)` is wrong. Must be `return OptionsFlowHandler()`. (Already correct in template — do not regress.)
- **`raise UpdateFailed` from non-coordinator code:** Only `_async_update_data` should raise `UpdateFailed`. Other code raises `CannotConnectError` or `InvalidAuthError`.
- **Setting `PARALLEL_UPDATES` to 1 for coordinator-based sensors:** Use `0` — coordinator already serializes all entity data through a single API call.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP session management | `aiohttp.ClientSession()` directly | `async_get_clientsession(hass)` | HA closes sessions on shutdown; raw sessions leak on integration reload |
| Device registration | `device_registry.async_get_or_create(...)` calls | `_attr_device_info` on entity | HA reads `device_info` automatically when entity has `unique_id` and is loaded via config entry |
| Periodic polling | Custom `asyncio.sleep` loop | `DataUpdateCoordinator` with `update_interval` | Coordinator handles startup failure (ConfigEntryNotReady), retry backoff, and log spam prevention |
| Options change listener | `entry.add_update_listener(async_reload_entry)` | `OptionsFlowWithReload` (2025.8+) | Built-in reload; no extra wiring required |
| Unique ID duplicate detection | Custom config entry iteration | `async_set_unique_id` + `_abort_if_unique_id_configured` | HA handles abort flow and shows correct UI message automatically |
| Parallel update control | Custom asyncio.Semaphore | `PARALLEL_UPDATES = 0` | HA's integration loader reads this constant and manages the semaphore |

**Key insight:** For service-type integrations (cloud API, network service), almost all infrastructure concerns are handled by HA's coordinator/config-entry/device-registry system. The integration author writes business logic only.

---

## Common Pitfalls

### Pitfall 1: CONF_API_KEY Import Conflict

**What goes wrong:** `const.py.jinja` currently defines `CONF_API_KEY = "api_key"`. When `config_flow.py.jinja` imports both from `homeassistant.const` AND from `.const`, there will be a name collision.
**Why it happens:** The local definition predates the decision to use `homeassistant.const` imports.
**How to avoid:** Remove `CONF_API_KEY = "api_key"` from `const.py.jinja`. Import `CONF_API_KEY` from `homeassistant.const` in `config_flow.py.jinja` and `coordinator.py.jinja` directly.
**Warning signs:** Import errors in generated project; type checkers flagging redefined name.

### Pitfall 2: DeviceInfo.identifiers Must Be a Frozenset of Tuples

**What goes wrong:** Passing `identifiers={(DOMAIN, entry.entry_id)}` works correctly (Python set of tuples). Passing `identifiers={DOMAIN: entry.entry_id}` (dict) causes a type error.
**Why it happens:** `DeviceInfo.identifiers` type is `set[tuple[str, str]]`, not `dict`.
**How to avoid:** Always use `identifiers={(DOMAIN, some_unique_string)}` — set containing one tuple.
**Warning signs:** HA logs `TypeError: unhashable type: 'dict'`; device does not appear in registry.

### Pitfall 3: Missing PARALLEL_UPDATES in Generated platform files

**What goes wrong:** hassfest quality scale validation fails with "parallel-updates rule not satisfied." HA 2025.1+ added this as a quality scale check.
**Why it happens:** Old template pattern didn't include `PARALLEL_UPDATES`.
**How to avoid:** Add `PARALLEL_UPDATES = 0` as the FIRST non-import line in `sensor.py.jinja` and any future platform files (binary_sensor.py, etc.).
**Warning signs:** `quality_scale` CI check fails; HA logs a warning on platform load.

### Pitfall 4: CannotConnect vs CannotConnectError Name Collision

**What goes wrong:** `api.py` defines `CannotConnectError` and `InvalidAuthError`; `config_flow.py` defines `CannotConnect` and `InvalidAuth` (the HA convention). If they get mixed up, except clauses catch the wrong type.
**Why it happens:** HA examples show `CannotConnect`/`InvalidAuth` in config flow; the API client needs its own exception hierarchy that config flow catches and re-raises.
**How to avoid:** Use clear naming separation. Config flow `_async_validate_connection` calls `ApiClient.async_test_connection()`, catches `CannotConnectError`/`InvalidAuthError`, and re-raises `CannotConnect`/`InvalidAuth`. Alternatively, import from `api.py` into config flow and eliminate duplicates.
**Warning signs:** `except CannotConnect` never triggers because api.py raises `CannotConnectError`; connection errors fall through to the generic `except Exception` handler.

### Pitfall 5: Options Flow Updating entry.data vs entry.options

**What goes wrong:** Options flow `async_create_entry(data=user_input)` stores in `entry.options`, not `entry.data`. Coordinator reads from `entry.data`. After options change, coordinator still uses old host/port/API key.
**Why it happens:** HA splits config into permanent `data` (from initial config flow) and mutable `options` (from options flow). They are separate dicts.
**How to avoid:** Coordinator `__init__` should merge `entry.data | entry.options` when reading connection parameters. OR: options flow should call `hass.config_entries.async_update_entry(entry, data=user_input)` to update `entry.data` instead of using options. `OptionsFlowWithReload` auto-reloads, so the coordinator re-reads `entry.data` on reload — IF options flow updates `entry.data` via `async_update_and_abort`.
**Warning signs:** Changing host in options flow has no effect until manual reload; entity history lost because unique_id derived from old host.

### Pitfall 6: async_config_entry_first_refresh vs async_refresh

**What goes wrong:** Using `await coordinator.async_refresh()` in `async_setup_entry` instead of `await coordinator.async_config_entry_first_refresh()`. The first method does not raise `ConfigEntryNotReady` on failure.
**Why it happens:** Both methods exist; `async_refresh` is for subsequent updates.
**How to avoid:** Always use `async_config_entry_first_refresh()` in `async_setup_entry`. It raises `ConfigEntryNotReady` if the first data fetch fails, which HA uses to schedule a retry.
**Warning signs:** Integration shows as loaded even when API is unreachable; no automatic retry on startup failure.

### Pitfall 7: strings.json / translations/en.json Structural Mismatch

**What goes wrong:** hassfest fails with translation key mismatch error.
**Why it happens:** Developer adds field to one file but not the other.
**How to avoid:** Keep `strings.json.jinja` and `translations/en.json.jinja` byte-for-byte identical in key structure. They serve different roles (HA uses `strings.json` as canonical; `en.json` is the English locale file) but must have the same keys.
**Warning signs:** `hassfest` CI fails; config flow labels don't render in HA UI.

---

## Code Examples

Verified patterns from official sources and HA core integrations:

### ApiClient Class (api.py.jinja — new file)

```python
# Source: HA api_lib_auth docs + aiohttp docs + pattern from config flow validation stubs
"""API client for [[ project_name ]]."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30  # seconds


class CannotConnectError(Exception):
    """Cannot connect to service."""


class InvalidAuthError(Exception):
    """Invalid authentication credentials."""


class ApiClient:
    """API client for [[ project_name ]]."""

    def __init__(
        self,
        host: str,
        port: int,
        api_key: str,
        session: aiohttp.ClientSession,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self._base_url = f"http://{host}:{port}"
        self._api_key = api_key
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self._base_url}{endpoint}"
        try:
            async with self._session.request(
                method, url,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
                **kwargs,
            ) as response:
                if response.status in (401, 403):
                    raise InvalidAuthError(f"Auth failed: {response.status}")
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientConnectionError as err:
            raise CannotConnectError(f"Cannot connect: {err}") from err
        except aiohttp.ClientError as err:
            raise CannotConnectError(f"Request error: {err}") from err
        except asyncio.TimeoutError as err:
            raise CannotConnectError(f"Timeout: {err}") from err

    async def async_test_connection(self) -> bool:
        """Test connection. Raises CannotConnectError or InvalidAuthError."""
        # TODO: Replace /health with your actual endpoint
        await self._request("GET", "/health")
        return True

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch data. TODO: Replace with your actual endpoint."""
        return await self._request("GET", "/api/data")
```

### Config Flow Connection Validation

```python
# Source: config_flow.py.jinja (existing) + api.py integration
from .api import ApiClient, CannotConnectError, InvalidAuthError
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_API_KEY

async def _async_validate_connection(hass: HomeAssistant, user_input: dict) -> None:
    """Validate connection to service. Raises CannotConnect or InvalidAuth."""
    session = async_get_clientsession(hass)
    client = ApiClient(
        host=user_input[CONF_HOST],
        port=user_input[CONF_PORT],
        api_key=user_input[CONF_API_KEY],
        session=session,
    )
    try:
        await client.async_test_connection()
    except CannotConnectError as err:
        raise CannotConnect from err
    except InvalidAuthError as err:
        raise InvalidAuth from err
```

### Sensor with device_info and PARALLEL_UPDATES

```python
# Source: WAQI sensor.py (github.com/home-assistant/core), HA quality scale docs
"""Sensor platform for [[ project_name ]]."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

PARALLEL_UPDATES = 0  # coordinator centralizes all updates


class TemplateSensor(CoordinatorEntity[TemplateCoordinator], SensorEntity):
    """Representation of a [[ project_name ]] sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, sensor_type: str) -> None:
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_name = sensor_type.replace("_", " ").title()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=entry.title,
            manufacturer="[[ project_name ]]",
        )
```

### DataUpdateCoordinator with ApiClient

```python
# Source: HA fetching_data docs; WAQI coordinator pattern
class TemplateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.config_entry = entry
        self.client = ApiClient(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            api_key=entry.data[CONF_API_KEY],
            session=async_get_clientsession(hass),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_get_data()
        except CannotConnectError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `hass.data[DOMAIN][entry.entry_id]` for runtime data | `entry.runtime_data` with typed generic | HA 2024.x | Automatic cleanup on unload; type safety; no manual cleanup in `async_unload_entry` |
| `OptionsFlow.__init__(self, config_entry)` | `OptionsFlow` base injects `config_entry` | HA 2024.x | Do NOT define `__init__` or pass `config_entry` to constructor |
| `entry.add_update_listener(async_reload_entry)` | `OptionsFlowWithReload` | HA 2025.8 | Eliminates boilerplate reload listener |
| `PARALLEL_UPDATES` undeclared | `PARALLEL_UPDATES = 0` explicit | HA 2025.1 (quality scale) | Required for quality scale compliance; hassfest warns if missing |
| Manual `device_registry.async_get_or_create()` calls | `_attr_device_info` on entity | HA 2020+ | HA reads `device_info` automatically when entity has `unique_id` and is loaded via config entry |
| String-based `entry_type="service"` | `DeviceEntryType.SERVICE` enum | HA 2022.3 | String form deprecated since 2022.3; enum required since then |

**Deprecated/outdated:**
- `hass.data[DOMAIN]` for coordinator storage: replaced by `entry.runtime_data`
- `entry_type="service"` (string): replaced by `DeviceEntryType.SERVICE`
- Manual `add_update_listener` for reload: replaced by `OptionsFlowWithReload`
- `PARALLEL_UPDATES` undeclared: now required for quality scale

---

## Open Questions

1. **OptionsFlow vs OptionsFlowWithReload for connection-detail options**
   - What we know: `OptionsFlowWithReload` auto-reloads after options save (HA 2025.8+); template minimum is 2025.7.0; reload causes coordinator re-init which re-reads `entry.data`
   - What's unclear: Should options flow update `entry.data` or `entry.options`? If options, coordinator must merge `entry.data | entry.options` on every init. If data, use `async_update_and_abort` pattern from reconfigure flow.
   - Recommendation: Use `OptionsFlowWithReload` AND update `entry.data` via `hass.config_entries.async_update_entry(entry, data={**entry.data, **user_input})` before returning `async_create_entry`. This preserves entity history (same unique_id). Planner should make this call.

2. **ApiClient exception hierarchy: one vs two layers**
   - What we know: Config flow has `CannotConnect`/`InvalidAuth` exceptions; API client needs its own exceptions. Two-layer adds indirection.
   - What's unclear: Should `api.py` define its own exceptions (CannotConnectError, InvalidAuthError) and config flow re-raises, OR should api.py import and raise the config-flow exceptions directly?
   - Recommendation: Keep separate. `api.py` exceptions are reusable without importing from config_flow. Config flow translates them. This is the pattern used in HA core integrations.

3. **`OptionsFlowWithReload` import path**
   - What we know: `from homeassistant.config_entries import OptionsFlowWithReload` — added HA 2025.8
   - What's unclear: Whether bumping the `hacs.json` minimum from 2025.7.0 to 2025.8.0 is acceptable for this template
   - Recommendation: The planner must decide. Safe choice: use `OptionsFlow` to match the 2025.7.0 minimum. Ambitious choice: bump minimum to 2025.8.0 and use `OptionsFlowWithReload`. Given template already targets 2025.7.0 for `async_register_static_paths`, bumping to 2025.8.0 is a very minor change.

4. **`_async_validate_connection` needs `hass` parameter**
   - What we know: Current `config_flow.py.jinja` has `async def _async_validate_connection(user_input: dict)` — no `hass` parameter. Creating `ApiClient` requires `async_get_clientsession(hass)`.
   - What's unclear: Best way to pass `hass` — module-level function with `hass` param, or method on `TemplateConfigFlow`?
   - Recommendation: Make it a `staticmethod` or free function with `hass` as first parameter: `async def _async_validate_connection(hass, user_input)`. Config flow calls `await _async_validate_connection(self.hass, user_input)`.

---

## Sources

### Primary (HIGH confidence)

- [HA Developer Docs — Fetching data](https://developers.home-assistant.io/docs/integration_fetching_data/) — `DataUpdateCoordinator`, `CoordinatorEntity`, `UpdateFailed`, `async_config_entry_first_refresh`
- [HA Developer Docs — runtime-data quality rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data/) — `type XxxConfigEntry = ConfigEntry[XxxData]` pattern, `entry.runtime_data` usage
- [HA Developer Docs — parallel-updates quality rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/parallel-updates/) — `PARALLEL_UPDATES = 0` for coordinator-based read-only platforms
- [HA Developer Docs — Device Registry](https://developers.home-assistant.io/docs/device_registry_index/) — `DeviceInfo`, `DeviceEntryType.SERVICE`, `identifiers` type `set[tuple[str, str]]`
- [HA Developer Docs — Options Flow](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/) — `OptionsFlow`, `OptionsFlowWithReload`, `self.config_entry` injection, `async_get_options_flow` signature
- [HA Developer Docs — Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) — `async_set_unique_id`, `_abort_if_unique_id_configured`, `ConfigFlowResult`
- [HA Developer Docs — Integration Manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/) — `issue_tracker` field name, all required manifest fields, no `homeassistant` minimum-version field in manifest
- [HACS Docs — hacs.json format](https://www.hacs.xyz/docs/publish/start/) — `name` (required), `homeassistant` (optional min version), `render_readme`
- [HA Developer Docs — API Library Auth](https://developers.home-assistant.io/docs/api_lib_auth/) — `AbstractAuth` pattern, `ClientSession` usage
- [HA Developer Docs — Backend localization](https://developers.home-assistant.io/docs/internationalization/core/) — `strings.json` complete format with config/options/error/abort keys
- [HA Core: WAQI sensor.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/waqi/sensor.py) — `DeviceEntryType.SERVICE`, `device_info` in `__init__`, `CoordinatorEntity[T]`
- [HA Core: GitHub sensor.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/github/sensor.py) — typed `GithubConfigEntry`, `DeviceEntryType.SERVICE`, `_attr_device_info`
- [HA Core: OTP sensor.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/otp/sensor.py) — `DeviceEntryType.SERVICE` pattern for service integrations
- [HA Core: update_coordinator.py](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py) — `DataUpdateCoordinator[_DataT]` generic class definition
- [HA Core: Bring coordinator.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/bring/coordinator.py) — `type BringConfigEntry = ConfigEntry[BringCoordinators]` dataclass pattern

### Secondary (MEDIUM confidence)

- [OptionsFlowWithReload adoption — HA 2025.8 search results](https://www.home-assistant.io/changelogs/core-2025.8/) — `OptionsFlowWithReload` added HA 2025.8; adopted across multiple integrations; confirmed by multiple community sources
- [17Track sensor.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/seventeentrack/sensor.py) — `DeviceEntryType.SERVICE` with `CoordinatorEntity` pattern for cloud service integrations
- [Waze Travel Time sensor.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/waze_travel_time/sensor.py) — `DeviceInfo` with `entry_type=DeviceEntryType.SERVICE` and `identifiers={(DOMAIN, DOMAIN)}`

### Tertiary (LOW confidence)

- WebSearch findings about `OptionsFlowWithReload` being added in 2025.8 — consistent across multiple search results but not a single primary source document; treat as community consensus pending changelog verification.

---

## Metadata

**Confidence breakdown:**
- Standard stack (HA APIs): HIGH — official HA developer docs
- DataUpdateCoordinator/CoordinatorEntity: HIGH — official docs + HA core source
- typed ConfigEntry pattern: HIGH — official quality scale rule doc
- PARALLEL_UPDATES = 0: HIGH — official quality scale rule doc
- DeviceEntryType.SERVICE: HIGH — official device registry doc + multiple HA core examples
- OptionsFlow/OptionsFlowWithReload: HIGH/MEDIUM — options flow doc (HIGH); 2025.8 cutoff (MEDIUM, pending changelog verify)
- ApiClient pattern: MEDIUM — HA api_lib_auth docs describe abstract pattern; implementation adapted from standard aiohttp patterns
- strings.json/translations structure: HIGH — official backend localization docs
- manifest field names: HIGH — official manifest docs
- hacs.json fields: HIGH — hacs.xyz official docs

**Research date:** 2026-02-19
**Valid until:** 2026-08-19 (180 days — HA APIs are stable within a major version series; only a HA breaking change would invalidate)
