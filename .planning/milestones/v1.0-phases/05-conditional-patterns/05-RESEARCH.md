# Phase 5: Conditional Patterns - Research

**Researched:** 2026-02-20
**Domain:** Home Assistant integration conditional patterns — WebSocket API, service actions, multi-step config flow, secondary coordinator
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| COND-01 | WebSocket command registration and handler pattern in `websocket.py` (conditional, for Immich/Requestarr) | WebSocket decorator + async_register_command pattern confirmed from HA core source; dependency on `websocket_api` in manifest confirmed |
| COND-02 | Service call with `SupportsResponse` pattern in `services.py` + `services.yaml` (conditional, for Argos/Requestarr) | SupportsResponse.OPTIONAL pattern confirmed from official docs; `services.yaml` format confirmed; registration in `async_setup` confirmed |
| COND-03 | Multi-step config flow variant replacing single-step `config_flow.py` (conditional, for Requestarr) | Multi-step chaining via `self._data` and step method returns confirmed; hassfest requires `ConfigFlow` subclass with `VERSION` |
| COND-04 | Secondary coordinator with independent poll interval in `coordinator_secondary.py` (conditional, for Immich) | Two-coordinator dataclass pattern confirmed; each called with `async_config_entry_first_refresh()`; both stored in runtime_data |
| COND-05 | `__init__.py` uses minimal Jinja2 `[% if %]` blocks for conditional import/registration lines only | Project uses `[% %]` envops globally; conditional blocks in .jinja files follow the same pattern as copier.yml |
| COND-06 | `manifest.json` conditionally includes `websocket_api` in `dependencies` when WebSocket pattern is selected | Pattern confirmed from HA core integrations (zwave_js, HACS) using "websocket_api" in manifest dependencies |
</phase_requirements>

---

## Summary

Phase 5 implements four conditional feature sets — each gated by a Copier boolean flag — that are already scaffolded as stub `.jinja` files from Phase 2. The stubs have comment-only bodies (`# TODO: Implement...`). This phase replaces each stub with working, community-quality implementation code.

The four patterns are technically independent of each other but share one cross-cutting concern: `__init__.py` must conditionally import and wire in each feature using `[% if flag %]...[% endif %]` blocks. Additionally, `manifest.json` needs a conditional block for `websocket_api`. The multi-step config flow has a structural complication: it must coexist with the always-present single-step `config_flow.py` since both exist in the template (one or the other is rendered at copy time), so the multi-step file is already named `config_flow_multi_step.py` — but in the generated project it renders as... that same name. This means the multi-step flow needs its own class that HA can discover, OR the stub name pattern must be rethought (see Architecture Patterns).

`services.yaml` is the one entirely missing template file — it has no stub at all and needs to be created (plus its conditional filename wrapper).

**Primary recommendation:** Implement all four conditional modules fully in one wave (they are independent files), with `__init__.py` and `manifest.json` changes as the final coordination step. The multi-step config flow naming/discovery problem requires a decision before implementation.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `homeassistant.components.websocket_api` | HA bundled | WebSocket command registration | HA-native; no third-party dep needed |
| `homeassistant.core.ServiceCall`, `SupportsResponse`, `ServiceResponse` | HA bundled | Service with response data | HA-native; introduced HA 2023.7 |
| `homeassistant.helpers.update_coordinator.DataUpdateCoordinator` | HA bundled | Secondary coordinator | Same class, different `update_interval` |
| `homeassistant.config_entries.ConfigFlow` | HA bundled | Multi-step config flow | Same base class, additional `async_step_*` methods |
| `voluptuous` | HA bundled | Schema validation for WebSocket commands and services | Standard HA validation library |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `homeassistant.helpers.config_validation` (cv) | HA bundled | Field validators in service schemas | Always paired with voluptuous |
| `homeassistant.core.callback` | HA bundled | Marking sync WebSocket handlers | Required when not using `@async_response` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `SupportsResponse.OPTIONAL` | `SupportsResponse.ONLY` | OPTIONAL allows the service to work without returning data (automation-friendly); ONLY forces a return value every call |
| Separate `coordinator_secondary.py` file | Subclass in `coordinator.py` | Separate file is cleaner for Copier conditional; avoids modifying always-present coordinator.py |
| Multi-step flow in a renamed file | Inline steps in existing `config_flow.py` using conditional Jinja2 | Copier conditional file approach is already established (Phase 2 decision) |

---

## Architecture Patterns

### Recommended Project Structure (Phase 5 additions)

```
template/custom_components/[[ project_domain ]]/
├── __init__.py.jinja                              # Updated with conditional blocks
├── manifest.json.jinja                            # Updated with conditional websocket_api dep
├── [% if use_websocket %]websocket.py[% endif %].jinja          # Fills in stub
├── [% if use_services %]services.py[% endif %].jinja            # Fills in stub
├── [% if use_services %]services.yaml[% endif %].jinja          # NEW - no stub exists yet
├── [% if use_secondary_coordinator %]coordinator_secondary.py[% endif %].jinja  # Fills in stub
└── [% if use_multi_step_config_flow %]config_flow_multi_step.py[% endif %].jinja  # Fills in stub
```

### Pattern 1: WebSocket Command Handler (COND-01)

**What:** Register one or more typed WebSocket commands using the `@websocket_api.websocket_command` decorator and `websocket_api.async_register_command()`.

**When to use:** When the integration needs to push data or respond to frontend-initiated queries over the WebSocket connection (e.g., Immich photo library browsing, Requestarr queue status).

**Decorator order (critical):** `@websocket_command` must be outermost; `@async_response` next (if async); `@callback` innermost (if sync).

**Example (async handler):**
```python
# Source: HA core homeassistant/components/hassio/websocket_api.py pattern
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

WS_TYPE_GET_DATA = f"{DOMAIN}/get_data"


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_GET_DATA,
    }
)
@websocket_api.async_response
async def websocket_get_data(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle get_data WebSocket command."""
    from .coordinator import TemplateCoordinator  # noqa: PLC0415

    # Access coordinator from any loaded config entry's runtime_data
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "No config entries")
        return

    coordinator: TemplateCoordinator = entries[0].runtime_data.coordinator
    connection.send_result(msg["id"], coordinator.data or {})


@callback
def async_setup_websocket(hass: HomeAssistant) -> None:
    """Register WebSocket commands."""
    websocket_api.async_register_command(hass, websocket_get_data)
```

**Registration in `__init__.py` (via conditional block):**
```python
# [% if use_websocket %]
from .websocket import async_setup_websocket
# [% endif %]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    ...
    # [% if use_websocket %]
    async_setup_websocket(hass)
    # [% endif %]
    return True
```

**manifest.json dependency (COND-06):**
```json
"dependencies": ["frontend"[% if use_websocket %], "websocket_api"[% endif %]]
```

### Pattern 2: Service with SupportsResponse (COND-02)

**What:** Register a custom action (service) in `async_setup` that optionally returns structured response data. Document it in `services.yaml`.

**Key rule:** Service registration goes in `async_setup`, NOT `async_setup_entry`. (Official HA docs, developers.home-assistant.io/docs/dev_101_services/).

**Python (`services.py`):**
```python
# Source: developers.home-assistant.io/docs/dev_101_services/
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_QUERY = "query"

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("query"): cv.string,
    }
)


async def _async_handle_query(call: ServiceCall) -> ServiceResponse:
    """Handle the query service call."""
    # TODO: Implement with actual coordinator/client data
    result: dict[str, Any] = {"query": call.data["query"], "results": []}
    if call.return_response:
        return result
    return None


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register integration service actions."""
    hass.services.async_register(
        DOMAIN,
        SERVICE_QUERY,
        _async_handle_query,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
```

**services.yaml (must also be conditionally generated):**
```yaml
# Source: developers.home-assistant.io/docs/dev_101_services/ format
query:
  description: "Query the [[ project_name ]] service and optionally return results."
  fields:
    query:
      required: true
      description: "The query string to send."
      example: "search term"
      selector:
        text:
  response:
    optional: true
```

**Registration in `__init__.py`:**
```python
# [% if use_services %]
from .services import async_register_services
# [% endif %]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    ...
    # [% if use_services %]
    async_register_services(hass)
    # [% endif %]
    return True
```

**CRITICAL — services.yaml conditional filename:** This file does not currently exist as a stub. It needs a new template file with the Copier conditional filename pattern:
```
[% if use_services %]services.yaml[% endif %].jinja
```

### Pattern 3: Multi-Step Config Flow (COND-03)

**What:** A config flow that splits user input across two sequential steps (e.g., step 1: host/port, step 2: API key/auth).

**Critical architectural decision (unresolved):** The stub is named `config_flow_multi_step.py` and is generated alongside `config_flow.py`. Both exist in the generated project simultaneously. This is a problem because HA discovers the config flow by importing `config_flow.py` and looking for a `ConfigFlow` subclass — it does NOT look in `config_flow_multi_step.py`. The multi-step file as currently named is unreachable by HA.

**Three options:**

| Option | Approach | Tradeoff |
|--------|---------|---------|
| A | Make multi-step flow a REPLACEMENT of `config_flow.py` via Copier exclusion pattern | Clean, but requires Copier to exclude `config_flow.py` when `use_multi_step_config_flow=true`; Copier supports `_exclude` in answers but not per-file conditionals on the destination name |
| B | Keep `config_flow_multi_step.py` and have `config_flow.py` conditionally import and re-export its class | `config_flow.py.jinja` needs a `[% if use_multi_step_config_flow %]` block; works but the single-step and multi-step versions live in the same `config_flow.py.jinja` file |
| C | Single `config_flow.py.jinja` with Jinja2 conditional blocks rendering either single-step or multi-step class body | Eliminates the separate stub file entirely; cleanest solution; the `config_flow_multi_step.py` conditional file becomes dead code and can be removed |

**Recommendation: Option C** — use a single `config_flow.py.jinja` with `[% if use_multi_step_config_flow %]` blocks. This is consistent with how `__init__.py.jinja` handles conditional content. The separate `config_flow_multi_step.py` stub file (currently unused) should be deleted.

**Multi-step pattern (steps chain via return value):**
```python
# Source: developers.home-assistant.io/docs/config_entries_config_flow_handler/
class TemplateConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: Host and port."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_credentials()
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: API key."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            await self.async_set_unique_id(
                f"{self._data[CONF_HOST]}:{self._data[CONF_PORT]}"
            )
            self._abort_if_unique_id_configured()
            try:
                await _async_validate_connection(self.hass, self._data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(
                    title=self._data[CONF_HOST],
                    data=self._data,
                )
        return self.async_show_form(
            step_id="credentials",
            data_schema=STEP_CREDENTIALS_SCHEMA,
            errors=errors,
        )
```

**hassfest requirements:** The `ConfigFlow` subclass must extend `homeassistant.config_entries.ConfigFlow`, pass `domain=DOMAIN`, and declare `VERSION = 1`. Both single-step and multi-step variants satisfy hassfest identically. The `strings.json` / `translations/en.json` must include step entries for `credentials` step if added.

### Pattern 4: Secondary Coordinator (COND-04)

**What:** A second `DataUpdateCoordinator` subclass in `coordinator_secondary.py` with its own `update_interval`. Both coordinators stored in the `runtime_data` dataclass.

**Dataclass expansion in `__init__.py`:**
```python
# [% if use_secondary_coordinator %]
from .coordinator_secondary import TemplateSecondaryCoordinator
# [% endif %]

@dataclass
class [[ PascalDomain ]]Data:
    coordinator: TemplateCoordinator
# [% if use_secondary_coordinator %]
    coordinator_secondary: TemplateSecondaryCoordinator
# [% endif %]
```

**async_setup_entry expansion:**
```python
async def async_setup_entry(hass, entry):
    coordinator = TemplateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
# [% if use_secondary_coordinator %]
    coordinator_secondary = TemplateSecondaryCoordinator(hass, entry)
    await coordinator_secondary.async_config_entry_first_refresh()
# [% endif %]
    entry.runtime_data = [[ PascalDomain ]]Data(
        coordinator=coordinator,
# [% if use_secondary_coordinator %]
        coordinator_secondary=coordinator_secondary,
# [% endif %]
    )
    ...
```

**coordinator_secondary.py pattern:**
```python
# Source: homeassistant.helpers.update_coordinator pattern, same as coordinator.py
from datetime import timedelta

DEFAULT_SECONDARY_SCAN_INTERVAL = 300  # 5 minutes — longer than primary

class TemplateSecondaryCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Secondary coordinator for slower-changing data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_secondary",
            update_interval=timedelta(seconds=DEFAULT_SECONDARY_SCAN_INTERVAL),
        )
        # Reuse the ApiClient from the primary coordinator if entry has runtime_data
        # OR initialize its own client
        session = async_get_clientsession(hass)
        self.client = ApiClient(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            api_key=entry.data[CONF_API_KEY],
            session=session,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_get_data()
        except CannotConnectError as err:
            raise UpdateFailed(f"Secondary coordinator error: {err}") from err
```

**Note:** `_async_setup` (added HA 2024.8) can be used for one-time initialization in the secondary coordinator, but it is not required for this pattern.

### Pattern 5: Conditional Jinja2 Blocks in `__init__.py.jinja`

**What:** Minimal `[% if flag %]...[% endif %]` blocks that add imports and wiring calls for each conditional feature.

**Anti-pattern to avoid:** Putting feature implementation inside `__init__.py`. Keep `__init__.py` as a wiring file only — imports and function calls. All logic lives in the conditional module.

**Example structure of final `__init__.py.jinja` conditional sections:**
```python
# Conditional imports at top of file
[% if use_websocket %]
from .websocket import async_setup_websocket
[% endif %]
[% if use_services %]
from .services import async_register_services
[% endif %]
[% if use_secondary_coordinator %]
from .coordinator_secondary import TemplateSecondaryCoordinator
[% endif %]

# In async_setup():
[% if use_websocket %]
    async_setup_websocket(hass)
[% endif %]
[% if use_services %]
    async_register_services(hass)
[% endif %]
```

### Anti-Patterns to Avoid

- **Registering services in `async_setup_entry`:** HA docs are explicit — services go in `async_setup` (domain-level, not per-entry). Services registered per-entry get duplicated if two config entries exist.
- **Missing `@async_response` decorator on async WebSocket handlers:** Without it, `await` inside the handler silently fails or raises. Decorator order matters: `@websocket_command` outermost, `@async_response` middle, handler function innermost.
- **Multi-step flow unique_id set in wrong step:** `async_set_unique_id` must be called before `_abort_if_unique_id_configured`. For multi-step flows, both calls go in the LAST step (after all data is collected), not the first.
- **Forgetting strings.json step entries for multi-step flow:** hassfest checks that every `step_id` in the flow has a corresponding entry in `strings.json` and `translations/en.json`. Adding `async_step_credentials` requires `"credentials"` step in strings.
- **Sharing client initialization between coordinators without coordination:** If both coordinators use the same API client object, concurrent refreshes may cause race conditions. Safest pattern: each coordinator constructs its own `ApiClient` from `entry.data`.
- **`services.yaml` missing when `SupportsResponse` is registered:** HA/hassfest warns (may become error) when a service has no `services.yaml` description.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WebSocket message routing | Custom HTTP handler | `websocket_api.async_register_command` + `@websocket_command` | HA handles auth, connection lifecycle, error framing |
| Response schema for services | Custom response envelope | Return a plain `dict` from handler; document in `services.yaml` | HA serializes to JSON automatically; `ServiceResponse = dict[str, Any]` |
| Multi-step data accumulation | `hass.data[DOMAIN]` temporary storage | `self._data` instance variable on flow class | Flow instance persists across steps; `hass.data` is inappropriate for ephemeral flow state |
| Coordinator refresh sequencing | Manual `asyncio.gather` | `async_config_entry_first_refresh()` on each coordinator | HA handles error propagation and config entry failure correctly |

---

## Common Pitfalls

### Pitfall 1: Multi-step config flow file naming — unreachable class

**What goes wrong:** `config_flow_multi_step.py` is generated alongside `config_flow.py`. HA only loads `config_flow.py` and looks for a `ConfigFlow` subclass there. The multi-step class is never discovered.

**Why it happens:** Phase 2 decision chose separate conditional files, but did not account for HA's hardcoded `config_flow.py` discovery mechanism.

**How to avoid:** Use Option C — single `config_flow.py.jinja` with `[% if use_multi_step_config_flow %]` blocks that swap the class body. Remove the dead `config_flow_multi_step.py` conditional file.

**Warning signs:** Copier renders both files; `config_flow_multi_step.py` is present in generated project but HA never imports it.

### Pitfall 2: Services registered per-entry instead of per-domain

**What goes wrong:** If `async_register_services` is called in `async_setup_entry`, each config entry registers a duplicate service. The second registration overwrites the first silently or raises a `ServiceAlreadyRegistered` error.

**Why it happens:** Template pattern calls both setup functions; developer places service registration in the wrong location.

**How to avoid:** Services are ONLY registered in `async_setup` (domain-level, called once). Use a `hass.data` guard or `async_register_service` idempotency check if needed.

### Pitfall 3: Missing `websocket_api` in manifest dependencies

**What goes wrong:** WebSocket command registration succeeds at runtime but HA cannot guarantee `websocket_api` is loaded before the integration tries to register commands.

**Why it happens:** `manifest.json` `dependencies` controls load order. Without it, timing-dependent failures occur.

**How to avoid:** COND-06 requires conditional `"websocket_api"` in manifest `dependencies` whenever `use_websocket=true`.

### Pitfall 4: Multi-step flow strings.json missing new step

**What goes wrong:** hassfest validation fails with missing translation key. HA UI shows blank form labels.

**Why it happens:** Adding `async_step_credentials` requires `"step": {"credentials": {...}}` in `strings.json` and `translations/en.json`.

**How to avoid:** Any new `async_step_<name>` method requires a matching entry in both translation files. Phase 5 must update these files conditionally (or always include the credentials step keys).

### Pitfall 5: `services.yaml` missing entirely

**What goes wrong:** No `services.yaml` stub exists. Phase 5 must CREATE a new conditional template file from scratch, not just fill in a stub.

**Why it happens:** Phase 2 created stubs for Python files (websocket.py, services.py, coordinator_secondary.py, config_flow_multi_step.py) but did not create a stub for `services.yaml`.

**How to avoid:** Create `[% if use_services %]services.yaml[% endif %].jinja` as part of this phase.

### Pitfall 6: Copier Jinja2 delimiter collision in services.yaml

**What goes wrong:** `services.yaml` is a plain YAML file — no Python braces. But Copier renders it as a Jinja2 template (`.jinja` suffix). If the YAML content uses `{{` or `}}` for any reason, it will collide with Jinja2.

**Why it happens:** YAML itself rarely uses braces, but this is worth noting.

**How to avoid:** The project's custom `_envops` uses `[[ ]]` and `[% %]` globally, so standard Jinja2 `{{ }}` is NOT active. `services.yaml.jinja` can safely contain `[[project_name]]` substitutions; no collision risk.

---

## Code Examples

Verified patterns from official sources:

### WebSocket handler with async_response

```python
# Source: HA core homeassistant/components/hassio/websocket_api.py
@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_domain/my_command",
        vol.Optional("param"): cv.string,
    }
)
@websocket_api.async_response
async def websocket_my_command(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle my_command WebSocket message."""
    try:
        result = await some_async_operation()
        connection.send_result(msg["id"], result)
    except SomeError as err:
        connection.send_error(msg["id"], websocket_api.ERR_UNKNOWN_ERROR, str(err))
```

### Service with SupportsResponse.OPTIONAL

```python
# Source: developers.home-assistant.io/docs/dev_101_services/
async def _async_handle_query(call: ServiceCall) -> ServiceResponse:
    result = {"data": []}  # populate from coordinator
    if call.return_response:
        return result
    return None

hass.services.async_register(
    DOMAIN,
    "query",
    _async_handle_query,
    schema=SERVICE_SCHEMA,
    supports_response=SupportsResponse.OPTIONAL,
)
```

### Multi-step flow step chaining with data accumulation

```python
# Source: developers.home-assistant.io/docs/config_entries_config_flow_handler/
async def async_step_user(self, user_input=None):
    if user_input is not None:
        self._data.update(user_input)
        return await self.async_step_credentials()  # chain to next step
    return self.async_show_form(step_id="user", data_schema=SCHEMA_1)

async def async_step_credentials(self, user_input=None):
    if user_input is not None:
        self._data.update(user_input)
        # validate, set unique_id, create entry
        return self.async_create_entry(title=..., data=self._data)
    return self.async_show_form(step_id="credentials", data_schema=SCHEMA_2)
```

### Secondary coordinator initialization in async_setup_entry

```python
# Source: HA DataUpdateCoordinator pattern (coordinator.py template as reference)
coordinator = TemplateCoordinator(hass, entry)
await coordinator.async_config_entry_first_refresh()

coordinator_secondary = TemplateSecondaryCoordinator(hass, entry)
await coordinator_secondary.async_config_entry_first_refresh()

entry.runtime_data = MyIntegrationData(
    coordinator=coordinator,
    coordinator_secondary=coordinator_secondary,
)
```

### manifest.json conditional websocket_api dependency

```json
{
  "dependencies": ["frontend"[% if use_websocket %], "websocket_api"[% endif %]]
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Services registered in `async_setup_entry` | Services registered in `async_setup` | Enforced HA 2024+ | Prevents duplicate registration |
| `hass.data[DOMAIN]` for coordinator | `entry.runtime_data` dataclass | HA 2024.4+ | Auto-cleanup on unload |
| `hass.services.register()` (sync) | `hass.services.async_register()` | Long-standing | Required for async integrations |
| No response data from services | `SupportsResponse` + `ServiceResponse` | HA 2023.7 | Enables script response variables |
| Single coordinator assumed | Typed dataclass holding N coordinators | HA best practice 2024+ | Multiple poll intervals per integration |
| Separate `config_flow_multi_step.py` as extra file | Single `config_flow.py.jinja` with conditional blocks | Phase 5 decision | Only HA-discoverable location is `config_flow.py` |

**Deprecated/outdated:**
- `hass.services.register()` (sync): Use `hass.services.async_register()` instead.
- `hass.data[DOMAIN][entry.entry_id]` coordinator storage: Use `entry.runtime_data` instead.

---

## Open Questions

1. **Multi-step flow — remove `config_flow_multi_step.py` stub or repurpose?**
   - What we know: The stub file renders as `config_flow_multi_step.py` in the generated project, which HA never loads.
   - What's unclear: Whether to delete the stub file and inline the multi-step variant into `config_flow.py.jinja`, or adopt another strategy.
   - Recommendation: Option C (inline conditional blocks in `config_flow.py.jinja`); delete `[% if use_multi_step_config_flow %]config_flow_multi_step.py[% endif %].jinja`. This is a PLANNING DECISION — confirm before writing the plan.

2. **strings.json multi-step credentials step — always-include or conditional?**
   - What we know: If `async_step_credentials` only exists when `use_multi_step_config_flow=true`, the translations need to be conditional too.
   - What's unclear: Whether `[% if use_multi_step_config_flow %]` can be used inside JSON template files (it can — they're `.jinja` files too).
   - Recommendation: Use `[% if use_multi_step_config_flow %]` blocks inside `strings.json.jinja` to conditionally include the `credentials` step entry.

3. **Secondary coordinator — shared ApiClient vs. independent?**
   - What we know: Two coordinators both constructing `ApiClient` from the same `entry.data` is safe but redundant.
   - What's unclear: Whether the template should show the cleaner shared-client pattern.
   - Recommendation: Independent `ApiClient` per coordinator (simpler, avoids shared state); note this as a TODO for child project authors who want to optimize.

4. **`DEFAULT_SECONDARY_SCAN_INTERVAL` — where to define?**
   - What we know: It should live in `const.py` alongside `DEFAULT_SCAN_INTERVAL`, conditional on presence of secondary coordinator.
   - Recommendation: Always include `DEFAULT_SECONDARY_SCAN_INTERVAL = 300` in `const.py.jinja` (harmless if unused, avoids conditional const imports).

---

## Sources

### Primary (HIGH confidence)

- `github.com/home-assistant/core/blob/dev/homeassistant/components/hassio/websocket_api.py` — async WebSocket handler with `@websocket_command`, `@async_response`, function signature, `connection.send_result`, registration call
- `github.com/home-assistant/core/blob/dev/homeassistant/components/config/device_registry.py` — sync WebSocket handler pattern, `@callback` decorator usage, `async_register_command` call
- `developers.home-assistant.io/docs/dev_101_services/` — `SupportsResponse.OPTIONAL` vs `ONLY`, `ServiceCall.return_response`, `async_register` in `async_setup`, `services.yaml` format
- `developers.home-assistant.io/docs/config_entries_config_flow_handler/` — multi-step flow `async_step_*` chaining, `self._data` instance variable, `VERSION` + `MINOR_VERSION` requirements
- `developers.home-assistant.io/blog/2024/08/05/coordinator_async_setup/` — `_async_setup` method in `DataUpdateCoordinator` (HA 2024.8)
- `github.com/home-assistant/core/blob/dev/homeassistant/components/zwave_js/manifest.json` — confirms `websocket_api` in manifest dependencies

### Secondary (MEDIUM confidence)

- WebSearch: `websocket_api` confirmed as manifest dependency from zwave_js and HACS integration examples
- WebSearch: `SupportsResponse` introduced HA 2023.7 (from release blog)
- jnsgr.uk/2024/10/writing-a-home-assistant-integration/ — multiple coordinators stored as list in `entry.runtime_data` (validates two-coordinator pattern)

### Tertiary (LOW confidence)

- None flagged — all key claims have HIGH or MEDIUM confirmation.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all patterns from HA core source or official docs
- Architecture: HIGH — WebSocket, services, secondary coordinator patterns confirmed; multi-step flow naming issue identified from direct inspection of project file structure
- Pitfalls: HIGH — most from direct code inspection; multi-step naming pitfall confirmed by reading HA's discovery mechanism

**Research date:** 2026-02-20
**Valid until:** 2026-04-20 (stable HA APIs; WebSocket decorator pattern unchanged since HA 2022+; SupportsResponse since HA 2023.7)
