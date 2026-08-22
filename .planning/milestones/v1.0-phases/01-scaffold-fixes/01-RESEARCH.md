# Phase 1: Scaffold Fixes - Research

**Researched:** 2026-02-19
**Domain:** Home Assistant integration APIs — static path registration, HTTP session management, config entry patterns, options flow, config flow unique_id
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCAF-01 | Generated integration uses `async_register_static_paths` with `StaticPathConfig` for frontend JS registration | Verified: import from `homeassistant.components.http`, exact signature documented (see Code Examples). Old method removed in HA 2025.7. |
| SCAF-02 | Generated integration uses `async_get_clientsession(hass)` for all HTTP requests (no raw `aiohttp.ClientSession`) | Verified: import from `homeassistant.helpers.aiohttp_client`. Shared session, HA-managed lifecycle, no cleanup needed. |
| SCAF-03 | Config flow calls `async_set_unique_id` and `_abort_if_unique_id_configured` to prevent duplicate entries | Verified: call sequence documented (set unique_id first, then abort check). Must happen before `async_create_entry`. |
| SCAF-04 | Generated integration stores coordinator in `ConfigEntry.runtime_data` with typed generic dataclass (not `hass.data[DOMAIN]`) | Verified: `type MyConfigEntry = ConfigEntry[MyData]` pattern from official HA blog 2024-04-30. Auto-cleanup on unload. |
| SCAF-05 | Config flow includes connection validation stub that raises `CannotConnect` and `InvalidAuth` | Verified: standard scaffold pattern; errors map to `strings.json` error keys `cannot_connect` and `invalid_auth`. Strings already exist in scaffold. |
| SCAF-06 | Options flow uses `OptionsFlow` base class (not `self.config_entry = config_entry` in `__init__`) | Verified: `OptionsFlow` base provides `self.config_entry` automatically. Manual assignment breaks in HA 2025.12. `async_get_options_flow` must return `OptionsFlowHandler()` with no arguments. |
| SCAF-07 | Static path registration is in domain-level setup (not per-entry) to prevent duplicate registration errors | Verified: community developer guide explicitly states registration MUST be in `async_setup`, not `async_setup_entry`. Guard against duplicate calls needed. |
| SCAF-08 | `async_unload_entry` properly cleans up via `async_unload_platforms` (no manual `hass.data` cleanup needed with `runtime_data`) | Verified: with `runtime_data`, no manual dict cleanup needed. `async_unload_platforms` is still required for platform teardown. |
</phase_requirements>

---

## Summary

Phase 1 is a correctness-only phase: five breaking defects in the existing scaffold must be fixed before any feature work is meaningful. The most critical is `hass.http.register_static_path()`, which was removed in HA 2025.7 — the project's minimum target version — meaning the frontend card does not load at all on any supported HA version. This is not a deprecation warning; it is a hard failure. All five defects are independently verified against official HA developer documentation and/or real GitHub issues.

The research confirms that every fix has a single correct implementation with no meaningful design choices: use `async_register_static_paths` (not the old method), put static path registration in `async_setup` (not `async_setup_entry`), use `async_get_clientsession(hass)` (not `aiohttp.ClientSession()`), use `entry.runtime_data` (not `hass.data[DOMAIN]`), call `async_set_unique_id` before `async_create_entry`, and use `OptionsFlow` as the base class with no `__init__` config_entry assignment. No alternatives should be considered for any of these: they are each the single correct pattern as of HA 2025.7+.

An important finding from a community developer guide is that the static path URL prefix should be integration-specific (e.g., `/hacs_template/`) rather than `/hacsfiles/`. The `/hacsfiles/` prefix is owned and managed by the HACS integration itself for cards it downloads — registering under `/hacsfiles/` from within a custom integration is incorrect. The current scaffold uses `/hacsfiles/`, which should change to `/hacs_template/`. Additionally, the `hacs.json` minimum version is incorrectly set to `"2024.1.0"` and must be updated to `"2025.7.0"` to match the actual API requirement.

**Primary recommendation:** Apply all five API fixes as direct edits to the existing scaffold Python files (`__init__.py`, `config_flow.py`, `sensor.py`). Add `async_setup` function for static path registration, split coordinator storage to `runtime_data`, add the options flow class, and add `async_get_clientsession` import in coordinator. Each change is a targeted 3-15 line edit; no new files are needed.

---

## Standard Stack

### Core (all HA-bundled, no pip installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `homeassistant.components.http.StaticPathConfig` | HA 2024.6+ (required 2025.7+) | Dataclass for static path registration arguments | The only supported API for registering static paths; old sync method removed in 2025.7 |
| `homeassistant.helpers.aiohttp_client.async_get_clientsession` | All HA versions | Get HA-managed shared aiohttp session | HA manages lifecycle; prevents unclosed session warnings and file descriptor leaks |
| `homeassistant.config_entries.ConfigEntry` | HA 2024.4+ generic support | Typed config entry with `runtime_data` | `entry.runtime_data` replaces `hass.data[DOMAIN]`; typed via `ConfigEntry[T]` generic |
| `homeassistant.config_entries.OptionsFlow` | HA 2025.1+ (old breaks 2025.12) | Base class for options flow handler | Provides `self.config_entry` automatically; manual `__init__` assignment is deprecated |
| `homeassistant.config_entries.ConfigFlow` | Stable | Config flow base class | Required; unchanged — only `async_set_unique_id` call and options flow registration are new |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `homeassistant.helpers.update_coordinator.DataUpdateCoordinator` | Stable | Polling coordinator base | Already used in scaffold; unchanged |
| `homeassistant.helpers.device_registry.DeviceEntryType` | HA 2022.3+ | Device type enum for service integrations | Phase 3 concern — not in scope for Phase 1 |
| `voluptuous` | HA-bundled | Config flow schema validation | Already used in scaffold; unchanged |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `async_get_clientsession(hass)` | `async_create_clientsession(hass)` | Only use `async_create_clientsession` when cookies are required; not needed for API key auth |
| `entry.runtime_data` | `hass.data[DOMAIN]` | `hass.data` still works but is now a quality-scale anti-pattern; generates reviewer feedback at Bronze/Silver |
| `OptionsFlow` base class | `OptionsFlowWithConfigEntry` | `OptionsFlowWithConfigEntry` is kept for backward compatibility only; new code must use `OptionsFlow` |

**No pip installs required.** All libraries are bundled in Home Assistant.

---

## Architecture Patterns

### Current vs. Required File Changes

```
custom_components/hacs_template/
├── __init__.py          # CHANGE: add async_setup(), move static path reg there,
│                        #         switch to entry.runtime_data, remove hass.data cleanup
├── config_flow.py       # CHANGE: add async_set_unique_id, _abort_if_unique_id_configured,
│                        #         uncomment validation stub (CannotConnect/InvalidAuth),
│                        #         add OptionsFlowHandler class using OptionsFlow base
├── coordinator.py       # CHANGE: add async_get_clientsession import/usage in stub comment
│                        #         (actual API client placeholder ready for Phase 3)
├── sensor.py            # CHANGE: switch hass.data[DOMAIN] lookup to entry.runtime_data
├── const.py             # CHANGE: update FRONTEND_SCRIPT_URL prefix from /hacsfiles/ to
│                        #         /hacs_template/
├── strings.json         # VERIFY: already has cannot_connect, invalid_auth, already_configured
│                        #         ADD: options flow section for Phase 1 options flow
├── translations/en.json # SAME as strings.json
└── manifest.json        # NO CHANGE needed for Phase 1 (already has dependencies: ["frontend"])
hacs.json                # CHANGE: homeassistant from "2024.1.0" to "2025.7.0"
```

### Pattern 1: Static Path Registration in `async_setup`

**What:** Register the frontend JS file as a static HTTP path at the domain level (once per HA start), not per config entry.
**When to use:** Always — only `async_setup` is called once per domain load; `async_setup_entry` is called once per config entry, causing "path already registered" errors when a second entry is created.

```python
# Source: https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/
# Source: https://community.home-assistant.io/t/developer-guide-embedded-lovelace-card-in-a-home-assistant-integration/974909
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

URL_BASE = f"/{DOMAIN}"  # e.g. /hacs_template

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the domain-level resources (called once per domain load)."""
    frontend_path = Path(__file__).parent / "frontend"
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                f"{URL_BASE}/{DOMAIN}-card.js",
                str(frontend_path / f"{DOMAIN}-card.js"),
                cache_headers=True,
            )
        ])
    except RuntimeError:
        # Path already registered (e.g., integration reloaded)
        _LOGGER.debug("Static path already registered for %s", DOMAIN)
    return True
```

### Pattern 2: `runtime_data` with Typed ConfigEntry

**What:** Store coordinator on `entry.runtime_data` via a typed dataclass alias instead of `hass.data[DOMAIN]`.
**When to use:** Always for Phase 1; this is the modern HA pattern since HA 2024.4.

```python
# Source: https://developers.home-assistant.io/blog/2024/04/30/store-runtime-data-inside-config-entry/
from dataclasses import dataclass
from homeassistant.config_entries import ConfigEntry
from .coordinator import TemplateCoordinator

@dataclass
class HacsTemplateData:
    coordinator: TemplateCoordinator

type HacsTemplateConfigEntry = ConfigEntry[HacsTemplateData]

async def async_setup_entry(hass: HomeAssistant, entry: HacsTemplateConfigEntry) -> bool:
    """Set up HACS Template from a config entry."""
    coordinator = TemplateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = HacsTemplateData(coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: HacsTemplateConfigEntry) -> bool:
    """Unload a config entry."""
    # No manual hass.data cleanup — runtime_data is auto-cleaned on unload
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```

### Pattern 3: Config Flow with `unique_id` and Connection Validation

**What:** Set a unique_id before creating the entry, abort on duplicate, and validate connection before entry creation.
**When to use:** Always — required for Quality Scale Bronze and HACS reviewer approval.

```python
# Source: https://github.com/home-assistant/developers.home-assistant/blob/master/docs/config_entries_config_flow_handler.md
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
import voluptuous as vol

class CannotConnect(Exception):
    """Error to indicate we cannot connect."""

class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""

async def _async_validate_connection(user_input: dict) -> None:
    """Validate the connection. Raise CannotConnect or InvalidAuth on failure."""
    # TODO: Replace with actual connection test
    # session = async_get_clientsession(hass)
    # client = MyApiClient(user_input[CONF_HOST], session)
    # await client.async_test_connection()
    pass

class TemplateConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            )
            self._abort_if_unique_id_configured()

            try:
                await _async_validate_connection(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler()
```

### Pattern 4: Options Flow with `OptionsFlow` Base Class

**What:** Options flow that uses `OptionsFlow` as its base class (not `OptionsFlowWithConfigEntry` and not a manual `self.config_entry` assignment).
**When to use:** Always — manual `self.config_entry = config_entry` assignment breaks in HA 2025.12.

```python
# Source: https://developers.home-assistant.io/blog/2024/11/12/options-flow/
from homeassistant.config_entries import OptionsFlow, ConfigFlowResult

class OptionsFlowHandler(OptionsFlow):
    """Handle options flow for HACS Template."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        # self.config_entry is provided automatically by OptionsFlow base class
        # Do NOT do: self.config_entry = config_entry in __init__
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_HOST,
                        default=self.config_entry.data.get(CONF_HOST, ""),
                    ): str,
                }
            ),
        )
```

### Pattern 5: `async_get_clientsession` in Coordinator

**What:** Use HA's shared aiohttp session instead of constructing a raw `aiohttp.ClientSession()`.
**When to use:** Always — prevents "Unclosed client session" warnings on every reload.

```python
# Source: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession/
from homeassistant.helpers.aiohttp_client import async_get_clientsession

class TemplateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(...)
        session = async_get_clientsession(hass)
        # TODO: Pass session to your API client
        # self.client = MyApiClient(
        #     host=entry.data[CONF_HOST],
        #     session=session,
        # )
```

### Pattern 6: Platform Access via `entry.runtime_data`

**What:** Platforms access the coordinator through `entry.runtime_data`, not `hass.data[DOMAIN]`.
**When to use:** Always — this is the typed, auto-cleaned pattern.

```python
# In sensor.py — replaces hass.data[DOMAIN][entry.entry_id]
async def async_setup_entry(
    hass: HomeAssistant,
    entry: HacsTemplateConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities([TemplateSensor(coordinator, entry, "status")])
```

### Anti-Patterns to Avoid

- **`hass.http.register_static_path()`:** Removed in HA 2025.7. Use `async_register_static_paths` with a list of `StaticPathConfig`.
- **Static path registration in `async_setup_entry`:** Causes "path already registered" RuntimeError when a second config entry is created. Always use `async_setup`.
- **`hass.data[DOMAIN][entry.entry_id] = coordinator`:** Untyped, requires manual cleanup, quality-scale anti-pattern. Use `entry.runtime_data`.
- **`hass.data[DOMAIN].pop(entry.entry_id)` in `async_unload_entry`:** Not needed with `runtime_data`; HA cleans it up automatically.
- **`self.config_entry = config_entry` in `OptionsFlowHandler.__init__`:** Logs deprecation warning now, breaks entirely in HA 2025.12.
- **`OptionsFlowHandler(config_entry)` in `async_get_options_flow`:** Must be `OptionsFlowHandler()` with no arguments when using the new `OptionsFlow` base class.
- **`aiohttp.ClientSession()` directly:** HA does not manage its lifecycle; causes resource leaks and "Unclosed client session" log warnings.
- **Using `/hacsfiles/` as static path URL prefix:** `/hacsfiles/` is HACS-owned namespace for cards HACS downloads. Use an integration-specific prefix like `/{DOMAIN}/`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP session management | Custom session factory, custom close logic | `async_get_clientsession(hass)` | HA manages connection pooling, SSL verification, and lifecycle across reloads |
| Static path URL collision detection | Custom registry check | Try/except `RuntimeError` around `async_register_static_paths` | HA raises `RuntimeError` on duplicate path registration; simple guard is sufficient |
| Duplicate config entry prevention | Manual check of existing entries | `async_set_unique_id` + `_abort_if_unique_id_configured()` | HA's built-in mechanism handles all edge cases including reconfigure flows |
| Config entry data cleanup on unload | Manual `hass.data` dict management | `entry.runtime_data` | HA automatically clears `runtime_data` when the config entry unloads |
| Options flow config entry access | Storing config_entry reference in `__init__` | `OptionsFlow` base class `self.config_entry` property | The base class provides it; manual storage is the deprecated pattern |

**Key insight:** Every one of these is a case where the HA framework has a first-party solution. Custom solutions in these areas cause the specific deprecation warnings and runtime errors that Phase 1 exists to fix.

---

## Common Pitfalls

### Pitfall 1: `register_static_path` Is Completely Removed (Not Just Deprecated)

**What goes wrong:** Calling `hass.http.register_static_path()` on HA 2025.7+ causes an `AttributeError` — the method does not exist. The integration fails to load entirely; no card renders.
**Why it happens:** The old method was synchronous (blocking I/O in async event loop). HA removed it rather than keeping a shim.
**How to avoid:** Use `await hass.http.async_register_static_paths([StaticPathConfig(...)])`. Note the plural method name and the list argument.
**Warning signs:** Integration fails to load on HA 2025.7+; log shows `AttributeError: 'HomeAssistantHTTP' object has no attribute 'register_static_path'`.

### Pitfall 2: Static Path Registration Per-Entry Causes "Already Registered" Error

**What goes wrong:** If `async_register_static_paths` is called inside `async_setup_entry`, and a user creates a second config entry (or reloads), HA raises `RuntimeError: Path already registered`.
**Why it happens:** `async_setup_entry` is called once per config entry. `async_setup` is called once per domain load.
**How to avoid:** Move static path registration to `async_setup`. Wrap the call in `try/except RuntimeError` as an additional guard for edge cases (e.g., integration reloaded outside of normal entry lifecycle).
**Warning signs:** Second config entry creation fails with `RuntimeError`; HA log shows "Path already registered".

### Pitfall 3: Options Flow `self.config_entry` Assignment Silently Works Now, Breaks in 2025.12

**What goes wrong:** Using the old `OptionsFlowHandler(config_entry)` signature and `self.config_entry = config_entry` in `__init__` currently logs a deprecation warning. After HA 2025.12, the attribute assignment is blocked and the options flow will fail to open.
**Why it happens:** HA added the `config_entry` property to the `OptionsFlow` base class in 2025.1, making the manual `__init__` pattern obsolete.
**How to avoid:** Subclass `OptionsFlow` (not `OptionsFlowWithConfigEntry`). Return `OptionsFlowHandler()` with no arguments from `async_get_options_flow`. Do not define `__init__` in the handler class.
**Warning signs:** Log message: `"custom integration 'hacs_template' sets option flow config_entry explicitly, which is deprecated"`.

### Pitfall 4: Missing `unique_id` Is Invisible Until User Adds Integration Twice

**What goes wrong:** Without `unique_id`, there is no check preventing a second config entry for the same host. The user can add the same integration twice. Entity ID collisions and double polling follow.
**Why it happens:** `async_create_entry` succeeds without a `unique_id` — HA does not enforce it.
**How to avoid:** Call `await self.async_set_unique_id(unique_key)` before `async_create_entry`, then immediately call `self._abort_if_unique_id_configured()`. The unique key for this scaffold should be `f"{host}:{port}"`.
**Warning signs:** No `async_set_unique_id` call in `config_flow.py`; integration appears twice in HA Integrations UI after two setups.

### Pitfall 5: `hass.data` Cleanup Left in `async_unload_entry` After Migrating to `runtime_data`

**What goes wrong:** If `hass.data[DOMAIN].pop(entry.entry_id)` is left in `async_unload_entry` after switching to `runtime_data`, it will throw `KeyError` because the key was never set in `hass.data`.
**Why it happens:** Partial migration — `async_setup_entry` changed to use `runtime_data` but `async_unload_entry` cleanup code not removed.
**How to avoid:** When migrating to `runtime_data`, remove all `hass.data[DOMAIN]` cleanup from `async_unload_entry`. The only remaining call should be `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)`.
**Warning signs:** `KeyError` in `async_unload_entry` log when reloading; `hass.data[DOMAIN]` dict never populated but code tries to remove from it.

### Pitfall 6: Wrong URL Prefix (`/hacsfiles/`) for Integration-Bundled Card

**What goes wrong:** Using `/hacsfiles/` as the URL prefix for a card bundled inside `custom_components/` conflicts with the HACS integration's namespace. HACS manages the `/hacsfiles/` URL prefix for cards it downloads.
**Why it happens:** The `/hacsfiles/` prefix is the HACS convention for HACS-managed external cards. Internally-bundled cards should use a domain-specific prefix.
**How to avoid:** Use `f"/{DOMAIN}/"` (e.g., `/hacs_template/`) as the URL base. The current scaffold's `FRONTEND_SCRIPT_URL = f"/hacsfiles/{DOMAIN}/{DOMAIN}-card.js"` must change to `f"/{DOMAIN}/{DOMAIN}-card.js"`.
**Warning signs:** URL conflicts in browser console; HACS integration interfering with card resource.

---

## Code Examples

Verified patterns from official sources:

### Complete `async_setup` with Static Path Registration

```python
# Source: https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/
# Source: https://community.home-assistant.io/t/developer-guide-embedded-lovelace-card-in-a-home-assistant-integration/974909
from pathlib import Path
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

URL_BASE = f"/{DOMAIN}"

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up HACS Template domain (runs once per domain load, not per entry)."""
    frontend_path = Path(__file__).parent / "frontend"
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                f"{URL_BASE}/{DOMAIN}-card.js",
                str(frontend_path / f"{DOMAIN}-card.js"),
                cache_headers=True,
            )
        ])
    except RuntimeError:
        _LOGGER.debug("Static path already registered for %s", DOMAIN)
    return True
```

### Complete `async_setup_entry` and `async_unload_entry` with `runtime_data`

```python
# Source: https://developers.home-assistant.io/blog/2024/04/30/store-runtime-data-inside-config-entry/
from dataclasses import dataclass
from homeassistant.config_entries import ConfigEntry

@dataclass
class HacsTemplateData:
    coordinator: TemplateCoordinator

type HacsTemplateConfigEntry = ConfigEntry[HacsTemplateData]

async def async_setup_entry(hass: HomeAssistant, entry: HacsTemplateConfigEntry) -> bool:
    coordinator = TemplateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = HacsTemplateData(coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: HacsTemplateConfigEntry) -> bool:
    # runtime_data is cleaned up automatically — no hass.data manipulation needed
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```

### Config Flow with `unique_id`, Connection Validation, and Options Flow Registration

```python
# Source: https://github.com/home-assistant/developers.home-assistant/blob/master/docs/config_entries_config_flow_handler.md
# Source: https://developers.home-assistant.io/blog/2024/11/12/options-flow/
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

class CannotConnect(Exception):
    """Error to indicate we cannot connect."""

class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""

async def _async_validate_connection(user_input: dict) -> None:
    """Validate the connection. Stub raises nothing; child projects implement real logic."""
    pass  # TODO: raise CannotConnect or InvalidAuth on failure

class TemplateConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            )
            self._abort_if_unique_id_configured()

            try:
                await _async_validate_connection(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        return OptionsFlowHandler()


class OptionsFlowHandler(OptionsFlow):
    """Handle options flow. OptionsFlow base provides self.config_entry automatically."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_HOST,
                        default=self.config_entry.data.get(CONF_HOST, ""),
                    ): str,
                    vol.Optional(
                        CONF_PORT,
                        default=self.config_entry.data.get(CONF_PORT, DEFAULT_PORT),
                    ): int,
                }
            ),
        )
```

### `async_get_clientsession` in Coordinator

```python
# Source: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession/
from homeassistant.helpers.aiohttp_client import async_get_clientsession

class TemplateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
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
        # TODO: Initialize your API client here using the managed session
        # self.client = MyApiClient(
        #     host=entry.data[CONF_HOST],
        #     port=entry.data[CONF_PORT],
        #     session=session,
        # )
```

### `sensor.py` Using `entry.runtime_data`

```python
# Replaces hass.data[DOMAIN][entry.entry_id] lookup
async def async_setup_entry(
    hass: HomeAssistant,
    entry: HacsTemplateConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities = [TemplateSensor(coordinator, entry, "status")]
    async_add_entities(entities)
```

### `strings.json` with Options Flow Section Added

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Connect to Service",
        "description": "Enter the connection details for your service.",
        "data": {
          "host": "Host",
          "port": "Port"
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
          "port": "Port"
        }
      }
    }
  }
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `hass.http.register_static_path(url, path, cache)` | `await hass.http.async_register_static_paths([StaticPathConfig(url, path, cache)])` | Deprecated 2024.6, removed 2025.7 | Hard failure on HA 2025.7+ — integration does not load |
| `hass.data[DOMAIN][entry.entry_id] = coordinator` | `entry.runtime_data = MyData(coordinator=coordinator)` | Pattern introduced 2024.4 | Quality Scale anti-pattern; untyped; requires manual cleanup |
| `OptionsFlowHandler.__init__(self, config_entry)` | `class OptionsFlowHandler(OptionsFlow):` — no `__init__`, no manual assignment | Deprecated 2025.1, breaks 2025.12 | Deprecation warning now; `AttributeError` after 2025.12 |
| No `async_set_unique_id` in config flow | `await self.async_set_unique_id(...)` + `self._abort_if_unique_id_configured()` | Long-standing requirement, never implemented in scaffold | Allows duplicate entries; HACS reviewer rejection |
| `aiohttp.ClientSession()` raw construction | `async_get_clientsession(hass)` | Long-standing HA recommendation | Resource leak; "Unclosed client session" warnings |
| Static path in `async_setup_entry` | Static path in `async_setup` | Best practice, enforced by community guide | RuntimeError on second config entry creation |
| `/hacsfiles/{DOMAIN}/` URL prefix | `/{DOMAIN}/` or integration-specific prefix | HACS convention vs. integration convention | Namespace conflict with HACS-managed cards |

**Deprecated/outdated in this scaffold:**
- `hass.http.register_static_path()`: Removed in 2025.7 — replace immediately
- `hass.data[DOMAIN]` storage: Quality Scale anti-pattern — replace with `runtime_data`
- `OptionsFlowWithConfigEntry` (if used): Deprecated — use `OptionsFlow`
- Static path registration in `async_setup_entry`: Anti-pattern — move to `async_setup`
- `/hacsfiles/` prefix for bundled card: HACS namespace — use `/{DOMAIN}/`

---

## Open Questions

1. **Options flow URL in strings.json — does Phase 1 need options data fields beyond host/port?**
   - What we know: The scaffold only has `CONF_HOST` and `CONF_PORT` in config flow. Options flow for Phase 1 should reconfigure the same fields.
   - What's unclear: Whether the Phase 3 work will change the options flow schema significantly enough that Phase 1 options flow is a throwaway.
   - Recommendation: Implement a minimal options flow that mirrors the config flow (host + port). Phase 3 can extend it. The options flow class structure (using `OptionsFlow` base) is what matters for correctness; the schema fields are cosmetic.

2. **`HacsTemplateData` dataclass — single coordinator field sufficient for Phase 1?**
   - What we know: Phase 1 has only one coordinator. Phase 3 adds API client. The dataclass shape may change.
   - What's unclear: Whether to put the API client in `runtime_data` now (as a placeholder `None`) or only the coordinator.
   - Recommendation: For Phase 1, use `HacsTemplateData(coordinator=coordinator)` with only the coordinator. Phase 3 will expand the dataclass. The typed alias pattern ensures the planner can update the shape cleanly.

3. **`hacs.json` `homeassistant` field format — "2025.7.0" or "2025.7"?**
   - What we know: The current value is `"2024.1.0"`. STACK.md notes `"homeassistant": "2025.7"` (without patch) as the correct format for `hacs.json`, while `manifest.json` uses `"2025.7.0"`.
   - What's unclear: Whether HACS validator accepts `"2025.7"` or requires `"2025.7.0"` in `hacs.json`.
   - Recommendation: Use `"2025.7.0"` in both `hacs.json` and `manifest.json` for consistency. If HACS rejects the patch version, it can be trimmed, but `"2025.7.0"` is the safer choice given both files already exist.

---

## Sources

### Primary (HIGH confidence)

- [HA Developer Blog: async_register_static_paths migration (2024-06-18)](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/) — `StaticPathConfig` import, constructor params, `async_register_static_paths` signature
- [HA Developer Blog: runtime_data pattern (2024-04-30)](https://developers.home-assistant.io/blog/2024/04/30/store-runtime-data-inside-config-entry/) — `ConfigEntry[T]` generic, `entry.runtime_data`, auto-cleanup on unload
- [HA Developer Blog: options flow update (2024-11-12)](https://developers.home-assistant.io/blog/2024/11/12/options-flow/) — `OptionsFlow` base class, `async_get_options_flow` pattern, 2025.12 breaking change
- [HA Config Flow Handler docs](https://github.com/home-assistant/developers.home-assistant/blob/master/docs/config_entries_config_flow_handler.md) — `async_set_unique_id`, `_abort_if_unique_id_configured`, `CannotConnect`/`InvalidAuth` pattern
- [HA inject-websession IQS rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession/) — `async_get_clientsession` vs `async_create_clientsession`

### Secondary (MEDIUM confidence)

- [Community Developer Guide: Embedded Lovelace Card](https://community.home-assistant.io/t/developer-guide-embedded-lovelace-card-in-a-home-assistant-integration/974909) — confirmed `async_setup` (not `async_setup_entry`) requirement, integration-specific URL prefix, `RuntimeError` guard pattern
- [hacs/integration issue #3828](https://github.com/hacs/integration/issues/3828) — real-world evidence of `register_static_path` deprecation impact on HACS itself
- [hacs/integration issue #4314](https://github.com/hacs/integration/issues/4314) — real-world evidence of options flow `config_entry` assignment breaking at HA 2025.1

### Tertiary (LOW confidence)

- None — all findings have at least one official or verified community source.

---

## Metadata

**Confidence breakdown:**
- SCAF-01 (static path): HIGH — official HA dev blog, exact API signature verified
- SCAF-02 (aiohttp session): HIGH — official IQS rule, import path verified
- SCAF-03 (unique_id): HIGH — official config flow handler docs, call sequence verified
- SCAF-04 (runtime_data): HIGH — official HA dev blog, dataclass pattern verified
- SCAF-05 (connection validation): HIGH — standard scaffold pattern, strings already present
- SCAF-06 (options flow): HIGH — official HA dev blog, breaking change timeline confirmed
- SCAF-07 (async_setup placement): HIGH — community developer guide explicitly states requirement; corroborated by HA architecture (async_setup called once per domain)
- SCAF-08 (unload cleanup): HIGH — official runtime_data blog post explicitly states no manual cleanup needed
- URL prefix question: MEDIUM — community guide addresses it; no official HA doc found specifying the correct prefix for bundled cards

**Research date:** 2026-02-19
**Valid until:** 2026-09-19 (180 days — patterns are stable HA API; only a new major HA deprecation would invalidate)
