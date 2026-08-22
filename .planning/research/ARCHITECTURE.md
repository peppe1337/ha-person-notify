# Architecture Research

**Domain:** Copier-based Home Assistant HACS Integration Template
**Researched:** 2026-02-19
**Confidence:** HIGH (HA patterns from official docs; Copier patterns from official docs + verified community examples)

---

## Two Distinct Architecture Concerns

This project has two separate structures that must not be confused:

1. **Copier Template Structure** — what lives in this repo, the source of truth
2. **Generated Integration Structure** — what Copier renders into child project repos

The template structure contains Jinja2 syntax; the generated structure is plain Python/JS. Building the template means building both simultaneously and verifying the rendered output is correct.

---

## Part 1: Copier Template Structure

### Copier Template Directory Layout

```
ha-hacs-template/                         # Template repo root
├── copier.yml                            # Template configuration + questions
├── hacs.json                             # (non-templated, used by this repo's own HACS listing)
├── .github/
│   └── workflows/
│       ├── release.yml                   # (non-templated CI for this repo)
│       └── validate.yml                  # (non-templated CI for this repo)
├── custom_components/
│   └── _{{ project_domain }}_/           # Copier directory rename: becomes e.g. argos_translate/
│       ├── __init__.py                   # Always generated (setup_entry, unload_entry, frontend reg)
│       ├── manifest.json                 # Always generated (Jinja2 for domain, name, version)
│       ├── const.py                      # Always generated (DOMAIN, CONF_*, defaults)
│       ├── strings.json                  # Always generated
│       ├── config_flow.py                # Always generated (single-step default)
│       ├── coordinator.py                # Always generated (single coordinator default)
│       ├── sensor.py                     # Always generated (CoordinatorEntity example)
│       ├── api_client.py                 # Always generated (generic base class)
│       ├── translations/
│       │   └── en.json                   # Always generated
│       ├── frontend/
│       │   └── {{ project_domain }}-card.js  # Always generated (LitElement base card)
│       │
│       # --- Conditional files (whole-file approach) ---
│       ├── {% if use_websocket %}websocket.py{% endif %}.jinja
│       ├── {% if use_services %}services.py{% endif %}.jinja
│       ├── {% if use_services %}services.yaml{% endif %}.jinja
│       ├── {% if use_multi_coordinator %}coordinator_secondary.py{% endif %}.jinja
│       └── {% if use_multi_step_config %}config_flow_steps.py{% endif %}.jinja  # or inline in config_flow.py
│
├── tests/
│   └── _{{ project_domain }}_/           # Copier directory rename
│       ├── __init__.py
│       ├── conftest.py                   # Always generated (HA fixtures, mock entry setup)
│       ├── test_config_flow.py           # Always generated
│       ├── test_coordinator.py           # Always generated
│       ├── {% if use_websocket %}test_websocket.py{% endif %}.jinja
│       └── {% if use_services %}test_services.py{% endif %}.jinja
│
└── .github-template/                     # Template-side CI (copied to generated project)
    └── workflows/
        ├── validate.yml                  # Always generated (hassfest + hacs/action)
        └── release.yml                   # Always generated (tag-based release + zip)
```

**Note on `.github-template/`:** The template repo's own `.github/workflows/` are for the template repo itself. Generated projects need their own CI workflows, stored in `.github-template/` in the template and renamed during generation via a Copier `tasks` step or by naming the directory `{% raw %}.github{% endraw %}/` — Copier handles `.github/` directory rendering. Verify the correct approach during implementation.

### Copier Configuration File: `copier.yml`

```yaml
# copier.yml — top-level template configuration

_subdirectory: "."               # Template files at repo root
_templates_suffix: ".jinja"      # Only .jinja files are rendered; others copied verbatim
_skip_if_exists: []              # Files to skip on copier update if user has customized

questions:
  project_domain:
    type: str
    help: "Integration domain (snake_case, e.g. argos_translate)"
    validator: "{% if not (project_domain | regex_search('^[a-z][a-z0-9_]*$')) %}Must be snake_case{% endif %}"

  project_name:
    type: str
    help: "Human-readable integration name (e.g. Argos Translate)"

  project_description:
    type: str
    help: "Short description for manifest.json and README"

  iot_class:
    type: str
    choices:
      - local_polling
      - local_push
      - cloud_polling
      - cloud_push
    default: local_polling
    help: "IoT class for manifest.json"

  use_websocket:
    type: bool
    default: false
    help: "Include WebSocket command registration pattern?"

  use_services:
    type: bool
    default: false
    help: "Include HA service call pattern with SupportsResponse?"

  use_multi_coordinator:
    type: bool
    default: false
    help: "Include second DataUpdateCoordinator with independent polling interval?"

  use_multi_step_config:
    type: bool
    default: false
    help: "Include multi-step config flow pattern (multiple service connections)?"

  github_username:
    type: str
    help: "GitHub username for codeowners and documentation URL"

  min_ha_version:
    type: str
    default: "2025.7.0"
    help: "Minimum Home Assistant version"
```

### Copier Directory Renaming Mechanics

The `_{{ project_domain }}_` directory name uses Copier's convention: underscores wrap the Jinja2 expression. Given `project_domain: argos_translate`, Copier renders `_{{ project_domain }}_/` as `argos_translate/`.

This is the **only** place Copier handles directory renaming. File names within use standard `{{ project_domain }}` Jinja2 syntax.

### Conditional File Inclusion Mechanism

Copier evaluates templated file names. An empty filename after Jinja2 evaluation causes the file to be skipped:

```
# File on disk in template:
{% if use_websocket %}websocket.py{% endif %}.jinja

# When use_websocket=true: renders as websocket.py
# When use_websocket=false: renders as empty string → file skipped
```

The `.jinja` suffix is stripped by Copier during generation (controlled by `_templates_suffix`). Files **without** `.jinja` suffix are copied verbatim without Jinja2 processing — useful for files with curly braces (e.g., package.json) that must not be rendered.

### What Stays In-File vs. What Is Whole-File Conditional

**In-file Jinja2 blocks (minimal — used only where exclusion is semantically wrong):**

```python
# __init__.py — always exists, but imports change based on features
{% if use_websocket %}
from .websocket import async_setup_websocket_commands
{% endif %}
{% if use_services %}
from .services import async_setup_services
{% endif %}

async def async_setup_entry(hass: HomeAssistant, entry: MyConfigEntry) -> bool:
    coordinator = {{ project_name | replace(" ", "") }}Coordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await _async_register_frontend(hass)
    {% if use_websocket %}
    async_setup_websocket_commands(hass)
    {% endif %}
    {% if use_services %}
    async_setup_services(hass)
    {% endif %}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
```

**Whole-file conditional (preferred for optional modules):**

- `websocket.py` — WebSocket command registration
- `services.py` + `services.yaml` — Service call definitions
- `coordinator_secondary.py` — Second coordinator
- Test files corresponding to optional modules

---

## Part 2: Generated Integration Structure

### What a Child Project Looks Like After `copier copy`

Using `project_domain=argos_translate`, `project_name="Argos Translate"`, `use_websocket=false`, `use_services=true`, `use_multi_coordinator=false`, `use_multi_step_config=false`:

```
ha-argos-translate/
├── custom_components/
│   └── argos_translate/                  # Renamed from _{{ project_domain }}_/
│       ├── __init__.py                   # Setup/teardown, frontend registration
│       ├── manifest.json                 # HA integration metadata
│       ├── const.py                      # DOMAIN, CONF_*, defaults
│       ├── strings.json                  # UI strings
│       ├── config_flow.py                # Single-step config + options flow
│       ├── coordinator.py                # DataUpdateCoordinator
│       ├── sensor.py                     # CoordinatorEntity sensors
│       ├── api_client.py                 # Generic API client base
│       ├── services.py                   # SupportsResponse service (generated)
│       ├── services.yaml                 # Service schema definitions
│       ├── translations/
│       │   └── en.json
│       └── frontend/
│           └── argos_translate-card.js   # LitElement card
├── tests/
│   └── argos_translate/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_config_flow.py
│       ├── test_coordinator.py
│       └── test_services.py              # Generated because use_services=true
├── .github/
│   └── workflows/
│       ├── validate.yml
│       └── release.yml
├── hacs.json
└── README.md
```

### Generated Integration File Responsibilities

| File | Responsibility | Communicates With |
|------|---------------|-------------------|
| `__init__.py` | Entry setup/teardown, platform forwarding, frontend registration | coordinator.py, websocket.py (if present), services.py (if present) |
| `config_flow.py` | User-facing setup wizard + options flow, writes to `entry.data` | HA config entries system, api_client.py (for connection validation) |
| `const.py` | All constants: DOMAIN, config keys, defaults | Imported by all other modules |
| `coordinator.py` | Polls external API, stores data, notifies entities | api_client.py, HA DataUpdateCoordinator base |
| `api_client.py` | HTTP session management, auth, timeout, error handling | External service API over HTTP/HTTPS via aiohttp |
| `sensor.py` | Exposes coordinator data as HA sensor entities | coordinator.py (via CoordinatorEntity), HA entity registry |
| `websocket.py` | (Conditional) Registers HA WebSocket commands, handles card → HA → service bridge | HA websocket_api component, api_client.py |
| `services.py` | (Conditional) Registers HA services with SupportsResponse | HA service registry, api_client.py |
| `services.yaml` | (Conditional) Service schema/description for HA UI | HA service registry (loaded automatically) |
| `coordinator_secondary.py` | (Conditional) Second DataUpdateCoordinator with different interval | api_client.py |
| `frontend/{domain}-card.js` | LitElement Lovelace card — renders UI, calls WebSocket or reads entity states | HA frontend via `hass.callWS()` or `hass.states` |
| `strings.json` + `translations/en.json` | Config flow UI strings | HA config flow renderer |
| `manifest.json` | Integration metadata for HA and HACS validation | HA integration loader, hassfest, hacs/action |

---

## Component Boundaries and Data Flow

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Browser (Lovelace)                            │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  {domain}-card.js (LitElement)                               │    │
│  │  - Reads: hass.states[entity_id]  (polling via entity state) │    │
│  │  - Sends: hass.callWS(type, params)  (WebSocket, if enabled) │    │
│  └──────────────┬───────────────────────────────────────────────┘    │
└─────────────────│────────────────────────────────────────────────────┘
                  │ HA WebSocket protocol (ws://)
┌─────────────────▼────────────────────────────────────────────────────┐
│                    Home Assistant Core                                 │
│                                                                        │
│  ┌─────────────────────┐     ┌───────────────────────────────────┐   │
│  │  websocket_api      │     │  Service Registry                  │   │
│  │  (websocket.py reg) │     │  (services.py reg)                 │   │
│  └──────────┬──────────┘     └──────────────┬────────────────────┘   │
│             │                               │                          │
│  ┌──────────▼──────────────────────────────▼────────────────────┐   │
│  │                     api_client.py                              │   │
│  │  Generic base: session, auth, timeout, retry, error handling   │   │
│  └──────────────────────────────┬─────────────────────────────── ┘   │
│                                  │                                     │
│  ┌───────────────────────────────▼──────────────────────────────┐    │
│  │  coordinator.py (+ coordinator_secondary.py if multi)         │    │
│  │  - Polls via api_client on interval                           │    │
│  │  - Stores data dict, notifies subscribers                     │    │
│  └──────────────┬─────────────────────────────────────────────── ┘   │
│                  │                                                      │
│  ┌───────────────▼──────────────────────────────────────────────┐    │
│  │  sensor.py (CoordinatorEntity)                                │    │
│  │  - Exposes coordinator.data keys as HA states                 │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  config_flow.py                                               │    │
│  │  - user step: host/port/api_key + connection validation       │    │
│  │  - options flow: reconfiguration without losing entity history │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
                  │ HTTP/HTTPS (aiohttp via async_get_clientsession)
┌─────────────────▼────────────────────────────────────────────────────┐
│                    External Service (e.g. LibreTranslate)             │
└──────────────────────────────────────────────────────────────────────┘
```

### Primary Data Flow: Config → Coordinator → Entity → Card

```
1. User completes config_flow
        ↓
   ConfigEntry created in HA (entry.data = {host, port, api_key, ...})
        ↓
2. async_setup_entry() called
        ↓
   Coordinator instantiated with entry data
   Coordinator.async_config_entry_first_refresh() — first poll
   entry.runtime_data = coordinator             ← modern pattern (not hass.data[DOMAIN])
        ↓
3. Platform setup (sensor.py async_setup_entry)
        ↓
   CoordinatorEntity subclasses registered with HA
   Each entity subscribes to coordinator updates
        ↓
4. Coordinator._async_update_data() on interval
        ↓
   api_client.get_data() called
   Returns dict[str, Any]
   coordinator.data updated
   All subscribed entities receive async_write_ha_state()
        ↓
5. HA state machine updated → hass.states[entity_id].state reflects new value
        ↓
6. LitElement card reads hass.states[entity_id] on next render cycle
   (No push to card; card reactively renders when hass prop changes)
```

### Secondary Data Flow: Card → WebSocket → Service (optional)

```
User interaction in card (e.g. "Translate" button click)
        ↓
hass.callWS({ type: "argos_translate/translate", params: {...} })
        ↓
HA routes to registered handler in websocket.py
        ↓
websocket handler calls api_client.translate(params)
        ↓
api_client makes HTTP POST to external service
        ↓
Result returned through WebSocket connection to card
        ↓
Card updates its local state (not HA state machine — transient UI data)
```

### Service Call Data Flow (optional, for SupportsResponse.ONLY pattern)

```
Automation/script calls service: domain.translate
        ↓
HA service registry routes to handler in services.py
        ↓
Handler calls api_client.translate(params)
        ↓
Response dict returned to caller via SupportsResponse
        ↓
Automation stores response in variable for further use
```

---

## Generated Integration Patterns

### Pattern 1: Config Entry with `entry.runtime_data`

**What:** Store the coordinator on the typed config entry instead of in `hass.data[DOMAIN]`.
**When to use:** Always — this is the modern HA pattern as of 2024+.
**Trade-offs:** Eliminates domain-keyed dict lookups; provides type safety via `ConfigEntry[CoordinatorType]`.

```python
# __init__.py
type MyConfigEntry = ConfigEntry[MyCoordinator]  # Python 3.12+ type alias

async def async_setup_entry(hass: HomeAssistant, entry: MyConfigEntry) -> bool:
    coordinator = MyCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator  # modern: not hass.data[DOMAIN][entry.entry_id]
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

# sensor.py — access coordinator from entry, not hass.data
async def async_setup_entry(hass, entry: MyConfigEntry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([MySensor(coordinator, entry)])
```

### Pattern 2: Frontend Registration with `async_register_static_paths`

**What:** Register the LitElement card JS file as a static HTTP path.
**When to use:** Always — `hass.http.register_static_path()` is removed in HA 2025.7+.

```python
# __init__.py
from homeassistant.components.http import StaticPathConfig

async def _async_register_frontend(hass: HomeAssistant) -> None:
    frontend_path = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            url_path=f"/hacsfiles/{DOMAIN}/{DOMAIN}-card.js",
            path=str(frontend_path / f"{DOMAIN}-card.js"),
            cache_headers=True,
        )
    ])
```

### Pattern 3: Device Registry Integration

**What:** Register a virtual device grouping all entities for the integration instance.
**When to use:** Always — expected for community-quality integrations; enables entity grouping in HA UI.

```python
# coordinator.py or sensor.py
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

@property
def device_info(self) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, self._entry.entry_id)},
        name=self._entry.title,
        entry_type=DeviceEntryType.SERVICE,
        manufacturer="Project Author",
        model="Integration",
    )
```

### Pattern 4: Conditional WebSocket Registration

**What:** Register custom WebSocket commands to bridge the Lovelace card to the external service.
**When to use:** When `use_websocket=true` — for integrations where card needs data not in entity states (e.g., paginated results, search, binary blobs).

```python
# websocket.py (whole file generated conditionally)
from homeassistant.components import websocket_api

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_data",
    vol.Optional("param"): str,
})
@websocket_api.async_response
async def ws_get_data(hass, connection, msg):
    coordinator = hass.config_entries.async_entries(DOMAIN)[0].runtime_data
    try:
        result = await coordinator.client.get_data(msg.get("param"))
        connection.send_result(msg["id"], result)
    except Exception as err:
        connection.send_error(msg["id"], "fetch_error", str(err))

def async_setup_websocket_commands(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_get_data)
```

### Pattern 5: LitElement Base Card Structure

**What:** Self-contained single-file LitElement card that borrows LitElement from HA's existing elements.
**When to use:** Always — no build tools, no npm, no bundler.

```javascript
// Access LitElement from already-loaded HA elements (no import needed)
const LitElement = customElements.get("hui-masonry-view")
  ? Object.getPrototypeOf(customElements.get("hui-masonry-view"))
  : Object.getPrototypeOf(customElements.get("hui-view"));
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class MyCard extends LitElement {
  static get properties() { return { hass: {}, config: {} }; }
  static getConfigElement() { return document.createElement("my-card-editor"); }
  static getStubConfig() { return { entity: "" }; }
  setConfig(config) { this.config = { ...config }; }
  getCardSize() { return 3; }

  render() {
    if (!this.hass || !this.config) return html``;
    // Card body — reads hass.states, calls hass.callWS(), hass.callService()
  }

  static get styles() {
    return css`
      :host { /* use CSS custom properties from HA theme */ }
      ha-card { padding: 16px; }
    `;
  }
}

customElements.define("my-card", MyCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "my-card", name: "My Card", description: "...", preview: true });
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: `hass.http.register_static_path()` (Synchronous/Blocking)

**What people do:** Call the synchronous `register_static_path` method.
**Why it's wrong:** Performs blocking I/O in the HA event loop; removed entirely in HA 2025.7.
**Do this instead:** `await hass.http.async_register_static_paths([StaticPathConfig(...)])` — note the list argument.

### Anti-Pattern 2: Raw `aiohttp.ClientSession()` Creation

**What people do:** Instantiate `aiohttp.ClientSession()` directly in the integration.
**Why it's wrong:** Bypasses HA's session management, doesn't participate in HA's connection lifecycle, may not clean up properly.
**Do this instead:** `session = async_get_clientsession(hass)` — HA manages the session lifecycle.

### Anti-Pattern 3: `hass.data[DOMAIN][entry.entry_id]` Storage

**What people do:** Store coordinator in `hass.data` keyed by DOMAIN + entry_id.
**Why it's wrong:** Dict-based lookup with no type safety; the modern pattern stores on the entry itself.
**Do this instead:** `entry.runtime_data = coordinator` — typed, clear, and always co-located with the entry.

### Anti-Pattern 4: Missing `unique_id` in Config Flow

**What people do:** Create config entries without setting a `unique_id` via `self._async_set_unique_id()`.
**Why it's wrong:** HA cannot detect duplicate entries, users can configure the same service twice; HA logs deprecation warnings.
**Do this instead:** Call `await self.async_set_unique_id(f"{DOMAIN}_{host}_{port}")` and `self._abort_if_unique_id_configured()` before creating the entry.

### Anti-Pattern 5: Fine-Grained Jinja2 Inside Non-Template Files

**What people do:** Scatter `{% if use_websocket %}...{% endif %}` throughout Python files.
**Why it's wrong:** Template source becomes unreadable; diff noise on every update; hard to test conditional paths.
**Do this instead:** Use whole-file conditional generation for optional modules. Reserve in-file Jinja2 blocks only for `__init__.py` imports/calls where the file must always exist.

### Anti-Pattern 6: Registering Services in `async_setup_entry`

**What people do:** Call `hass.services.async_register()` inside `async_setup_entry`.
**Why it's wrong:** Services are called per entry; if two entries exist, services register twice. HA service registry is global.
**Do this instead:** Register services in `async_setup` (global setup function), not in `async_setup_entry`. Guard with `if not hass.services.has_service(DOMAIN, "my_service"):`.

---

## Build Order (Phase Dependencies)

The template must be built in this dependency order to avoid dead ends:

```
Phase 1: Copier Scaffolding Foundation
  copier.yml (questions + metadata)
  Directory structure with _{{ project_domain }}_/ naming
  const.py, manifest.json, hacs.json (Jinja2 variable substitution)
  strings.json, translations/en.json
      ↓
Phase 2: Backend Core (Always-On)
  api_client.py (generic base — no API specifics)
  config_flow.py (single-step + options flow, unique_id, connection validation stub)
  coordinator.py (single coordinator, uses api_client)
  __init__.py (setup_entry with entry.runtime_data, async_register_static_paths)
  sensor.py (CoordinatorEntity with device_info, unique_id)
      ↓
Phase 3: Frontend Core (Always-On)
  {domain}-card.js (LitElement base card, editor, window.customCards registration)
      ↓
Phase 4: Conditional Patterns (Each independent, depends on Phase 2)
  websocket.py (conditional on use_websocket)
  services.py + services.yaml (conditional on use_services)
  coordinator_secondary.py (conditional on use_multi_coordinator)
  Multi-step config additions to config_flow.py (conditional on use_multi_step_config)
      ↓
Phase 5: Test Scaffold
  conftest.py (depends on coordinator.py and config_flow.py being final)
  test_config_flow.py
  test_coordinator.py
  Conditional test files (depend on conditional patterns being finalized)
      ↓
Phase 6: CI/CD
  .github/workflows/validate.yml (hassfest + hacs/action)
  .github/workflows/release.yml (tag-based release, manifest version injection)
```

**Critical dependency:** The `async_register_static_paths` pattern (Phase 2) must be correct before the frontend (Phase 3) is wired up — they must be tested together. Do not build the card before the registration mechanism works.

**Critical dependency:** Conditional files (Phase 4) must not be started before the in-file Jinja2 blocks in `__init__.py` are finalized — adding a new conditional requires touching `__init__.py` imports and `async_setup_entry` simultaneously.

---

## Integration Points

### External Services (in generated projects)

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Local HTTP service (Argos, Immich) | `api_client.py` with `async_get_clientsession(hass)` | `iot_class: local_polling` |
| Cloud service (Requestarr) | Same base, different base URL | `iot_class: cloud_polling` |
| External service WebSocket | Not used — HA WebSocket is HA→Browser only | External APIs use HTTP in `api_client.py` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `config_flow.py` → `api_client.py` | Direct async call for connection validation | Client instantiated with user input, tested, discarded |
| `coordinator.py` → `api_client.py` | Holds client instance, calls on update interval | Client created in coordinator `__init__`, session managed by HA |
| `sensor.py` → `coordinator.py` | `CoordinatorEntity` subscription | Sensor reads `coordinator.data`, never calls client directly |
| `websocket.py` → `coordinator.py` | Access via `entry.runtime_data` | WebSocket handlers look up coordinator from entry |
| `services.py` → `api_client.py` | Direct call in service handler | Services may bypass coordinator for one-shot operations |
| `{domain}-card.js` → HA states | `hass.states[entity_id]` reads | Reactive — card re-renders when `hass` prop changes |
| `{domain}-card.js` → WebSocket | `hass.callWS({ type: "..." })` | Only when `use_websocket=true` |
| `{domain}-card.js` → HA services | `hass.callService(domain, service, data)` | Only when card needs to trigger actions |

---

## Copier Update Lifecycle

After `copier copy` generates a child project, `copier update` merges template changes:

```
ha-hacs-template (upstream) ──copier update──► ha-argos-translate (child)
```

Files managed by Copier are overwritten on update. Child projects must:
1. Put project-specific code in files outside Copier-managed paths (or use `_skip_if_exists`)
2. Never edit template-generated boilerplate files directly
3. Keep `.copier-answers.yml` (auto-generated by Copier, tracks what was answered) committed

This means the template must be designed so child projects **extend** base classes, not **edit** them. The LitElement base card is extended by child cards; the generic API client is subclassed in child projects.

---

## Sources

- [HA Developer Docs: Integration File Structure](https://developers.home-assistant.io/docs/creating_integration_file_structure/) — HIGH confidence (official)
- [HA Developer Blog: async_register_static_paths migration](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/) — HIGH confidence (official announcement)
- [HA Architecture Discussion: DataUpdateCoordinator placement](https://github.com/home-assistant/architecture/discussions/1073) — HIGH confidence (official)
- [HA Developer Docs: Device Registry](https://developers.home-assistant.io/docs/device_registry_index/) — HIGH confidence (official)
- [HA Developer Docs: Integration Service Actions](https://developers.home-assistant.io/docs/dev_101_services/) — HIGH confidence (official)
- [HA Developer Docs: Extending WebSocket API](https://developers.home-assistant.io/docs/frontend/extending/websocket-api/) — HIGH confidence (official)
- [Copier Docs: Creating a Template](https://copier.readthedocs.io/en/stable/creating/) — HIGH confidence (official)
- [Copier Docs: Configuring a Template](https://copier.readthedocs.io/en/stable/configuring/) — HIGH confidence (official)
- [jpawlowski/hacs.integration_blueprint](https://github.com/jpawlowski/hacs.integration_blueprint) — MEDIUM confidence (community, 2025-aligned)
- [ludeeus/integration_blueprint](https://github.com/ludeeus/integration_blueprint) — MEDIUM confidence (widely-used community reference)

---
*Architecture research for: Copier-based HA HACS Integration Template*
*Researched: 2026-02-19*
