# Pitfalls Research

**Domain:** Copier template generating HA HACS custom integrations with Lovelace cards
**Researched:** 2026-02-19
**Confidence:** HIGH (HA-specific pitfalls verified against official docs and real GitHub issues; Copier pitfalls MEDIUM from docs + community)

---

## Critical Pitfalls

### Pitfall 1: Deprecated Static Path Registration Blocks HA Startup

**What goes wrong:**
`hass.http.register_static_path()` is synchronous and does blocking I/O in the event loop. HA deprecated it in 2024 and removed it in **HA 2025.7**. Any integration using the old API will fail to load on HA 2025.7+. The current scaffold uses it in `_async_register_frontend()`, meaning all three child projects (Argos, Immich, Requestarr) currently break on the target HA version.

**Why it happens:**
Old tutorials and blog posts pre-dating the June 2024 deprecation notice still circulate. The method name looks harmless; nothing in the Python type system warns you that it blocks the event loop.

**How to avoid:**
Replace with the async form — import `StaticPathConfig` from `homeassistant.components.http`, then:
```python
from homeassistant.components.http import StaticPathConfig

await hass.http.async_register_static_paths([
    StaticPathConfig(FRONTEND_SCRIPT_URL, str(frontend_path / f"{DOMAIN}-card.js"), True)
])
```
The template must use this form exclusively. Target HA 2025.7+ minimum (already a project constraint) — no need to maintain a compatibility shim.

**Warning signs:**
- Log message: `"Detected that custom integration 'X' calls hass.http.register_static_path which is deprecated"`
- Integration fails to load on HA 2025.7+
- CI hassfest or HACS action job surfaces this as a warning/error

**Phase to address:** Phase 1 (HA API Fixes) — first thing fixed before anything else lands in child projects

---

### Pitfall 2: Raw `aiohttp.ClientSession()` Causes Resource Leaks

**What goes wrong:**
Constructing a bare `aiohttp.ClientSession()` in an integration creates a session that is never closed — HA does not know about it. Each HA restart or config entry reload leaks an open connection pool. Over time this causes "Unclosed client session" warnings and can exhaust system file descriptors. The current scaffold omits this (the API client is a TODO stub), but the template must not generate code that reaches for `aiohttp.ClientSession` directly.

**Why it happens:**
aiohttp documentation shows `async with aiohttp.ClientSession() as session` as its primary example. Developers copy this pattern without knowing HA provides a managed shared session.

**How to avoid:**
Always use HA's managed session:
```python
from homeassistant.helpers.aiohttp_client import async_get_clientsession

session = async_get_clientsession(hass)
```
The exception is when cookies are required (e.g., cookie-based auth), in which case `async_create_clientsession(hass)` creates a HA-managed session with its own cookie jar — but the template projects use API key auth, not cookies. Use `async_get_clientsession` universally in the template's API client base class.

**Warning signs:**
- Log: `"Unclosed client session"` on HA shutdown or entry reload
- Growing memory use over time under load
- `asyncio` warning about unclosed resources in test output

**Phase to address:** Phase 1 (HA API Fixes) — must be in the API client base class before child projects implement API calls

---

### Pitfall 3: Missing `unique_id` in Config Flow Allows Duplicate Entries

**What goes wrong:**
Without calling `await self.async_set_unique_id(...)` in `async_step_user`, users can add the same integration multiple times, creating duplicate config entries pointing at the same service. Each duplicate spawns a full set of entities, causing entity ID conflicts, double polling, and confusing UI state. The current scaffold's `config_flow.py` has no `unique_id` set.

**Why it happens:**
`async_create_entry` works without a `unique_id` — HA doesn't enforce it. The absence is invisible until a user accidentally adds the integration twice.

**How to avoid:**
Set a stable unique ID from the connection details (host + port, or a device serial/UUID if available) before creating the entry:
```python
await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
self._abort_if_unique_id_configured()
```
For reconfigure flows, use `self._abort_if_unique_id_mismatch()` instead to prevent changing to a different device's credentials.

**Warning signs:**
- No `async_set_unique_id` call anywhere in `config_flow.py`
- User can open "Add Integration" on the same domain and get a second entry without any abort/error
- Log: entity ID collision warnings when entity slugs collide

**Phase to address:** Phase 1 (HA API Fixes)

---

### Pitfall 4: `hass.data[DOMAIN]` Storage Pattern Is Being Superseded

**What goes wrong:**
The current scaffold stores the coordinator in `hass.data[DOMAIN][entry.entry_id]` and manually pops it in `async_unload_entry`. This works but is error-prone: if unload logic is incomplete, references linger. The modern pattern (introduced April 2024) is `entry.runtime_data`, which is automatically cleaned up when the entry unloads and supports generic typing.

**Why it happens:**
Every tutorial from before 2024 uses `hass.data`. It still works and won't be removed, but Integration Quality Scale (IQS) now flags it as a lower-quality pattern at Silver/Gold tier.

**How to avoid:**
Use typed `entry.runtime_data`:
```python
@dataclass
class MyIntegrationData:
    coordinator: TemplateCoordinator

type MyConfigEntry = ConfigEntry[MyIntegrationData]

async def async_setup_entry(hass: HomeAssistant, entry: MyConfigEntry) -> bool:
    coordinator = TemplateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = MyIntegrationData(coordinator=coordinator)
    ...
```
The template should use `runtime_data` from the start; child projects inherit clean patterns. If the project needs to stay compatible with HA versions before 2024.4, fall back to `hass.data` — but the 2025.7+ minimum eliminates this concern.

**Warning signs:**
- `hass.data[DOMAIN].pop(...)` in `async_unload_entry` without corresponding cleanup guards
- IQS Bronze/Silver review flags "use runtime_data instead of hass.data"
- KeyError in logs if unload is called before setup completes

**Phase to address:** Phase 1 (HA API Fixes) — establish the correct pattern in the template before child projects cement the old one

---

### Pitfall 5: Options Flow `self.config_entry` Assignment Breaks in HA 2025.12

**What goes wrong:**
The legacy `OptionsFlowHandler.__init__(self, config_entry)` pattern that assigns `self.config_entry = config_entry` is deprecated as of HA 2025.1 and will **stop working in HA 2025.12**. The template will generate broken options flows if it uses the old pattern.

**Why it happens:**
Every tutorial pre-2024 shows the old pattern. The deprecation was only announced in November 2024 and has not yet propagated to most tutorial content.

**How to avoid:**
Use the new pattern where `OptionsFlow` base class provides `self.config_entry` automatically — do NOT assign it in `__init__`:
```python
class OptionsFlowHandler(OptionsFlow):
    async def async_step_init(self, user_input=None):
        # self.config_entry is available automatically via OptionsFlow base class
        ...
```
The `ConfigFlow` class registers the options flow via:
```python
@staticmethod
@callback
def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
    return OptionsFlowHandler()
```

**Warning signs:**
- Log: `"custom integration 'X' sets option flow config_entry explicitly, which is deprecated"`
- Traceback at options flow open on HA 2025.12+
- HACS integration itself hit this bug (issue #4314)

**Phase to address:** Phase 1 (HA API Fixes) — options flow is part of the Phase 1 additions, use correct pattern from day one

---

### Pitfall 6: Copier Template Jinja2 Syntax Collides with Python Code

**What goes wrong:**
Copier uses Jinja2 to render template files. Python dictionary literals, f-strings, and type hints all use `{` and `}`. Any `{{` in a template file is interpreted by Jinja2 as a variable expression. This means Python code like `{"key": "value"}`, `f"{variable}"`, and type hints like `dict[str, Any]` will be corrupted or cause Copier to crash during rendering.

**Why it happens:**
It's non-obvious that Copier processes every template file through Jinja2 by default. Developers assume only files with explicit `{{ }}` substitutions are affected.

**How to avoid:**
Two approaches, use both as appropriate:
1. Wrap entire Python source files in `{% raw %}...{% endraw %}` and use Copier variables only in isolated spots (comments, docstrings, import paths that vary by domain)
2. Use Copier's `jinja_extensions` or configure alternative block delimiters in `copier.yml` if raw blocks become unwieldy
3. Use `{{ '{{' }}` and `{{ '}}' }}` for inline literal brace output where raw blocks would be too coarse

The cleanest approach for this template: wrap the full content of each `.py` file in `{% raw %}...{% endraw %}`, with Copier variables only in filenames, directory names, and the `manifest.json` / `hacs.json` files which are pure data.

**Warning signs:**
- `copier copy` exits with a Jinja2 `TemplateSyntaxError`
- Generated Python files have `{` characters removed or mangled
- `manifest.json` or `strings.json` contents render correctly but `.py` files look wrong

**Phase to address:** Phase 2 (Copier Configuration) — establish escaping strategy in `copier.yml` before adding any template files with Python source

---

### Pitfall 7: Copier Directory Naming Convention Must Use Jinja2, Not Copier's `_{{ }}_` Style

**What goes wrong:**
Copier uses Jinja2 syntax `{{ variable }}` for directory names — e.g., `custom_components/{{ domain_name }}/`. Some older Copier documentation or examples show `_{{ var }}_` with underscores (a Cookiecutter convention) or `[[ var ]]` (another tool's convention). Using the wrong delimiter style means directory names are not substituted and the generated project has a literal `{{ domain_name }}` folder.

**Why it happens:**
Copier's default Jinja2 delimiters are `{{ }}` for variables and `{% %}` for blocks — same as standard Jinja2. The `_{{ }}_` style does not exist in Copier; it was mentioned incorrectly in some third-party guides.

**How to avoid:**
Directory names use standard Jinja2: `custom_components/{{ domain_name }}/`. Verify that `copier.yml` defines `domain_name` as a question and that the answer is sanitized (lowercase, underscores, no spaces) before it is used as a directory name — use a Jinja2 filter: `{{ domain_name | lower | replace('-', '_') }}`.

**Warning signs:**
- Generated project contains a directory named literally `{{ domain_name }}`
- `copier copy` succeeds but `ls custom_components/` shows the literal template syntax
- `copier update` conflicts on the domain directory because the name doesn't match

**Phase to address:** Phase 2 (Copier Configuration) — validated as part of the first `copier copy` smoke test

---

### Pitfall 8: `.copier-answers.yml` Must Not Be Edited Manually

**What goes wrong:**
The `.copier-answers.yml` file (auto-generated in the child project root) records which answers were used to render the template. Manually editing this file — to change the domain name, update a version, or fix a typo — causes Copier's 3-way merge algorithm to produce incorrect diffs on the next `copier update`, leading to corruption or conflicts in unexpected files.

**Why it happens:**
The file looks like a normal YAML config file. Developers assume they can edit it like any config to fix a wrong answer.

**How to avoid:**
Never edit `.copier-answers.yml` by hand. To change answers: run `copier recopy` (re-renders from the same template commit with new answers) or `copier update --defaults` with overrides. Document this constraint clearly in the template's README. Add `.copier-answers.yml` to the template's `.gitignore` is wrong — it MUST be committed so updates work — but add a comment in the file itself warning against manual edits.

**Warning signs:**
- `copier update` produces diffs in files that were not changed in the template
- Conflict markers appearing in Python files that should be clean
- Child project diverges from template in ways not explainable by the template diff

**Phase to address:** Phase 2 (Copier Configuration) — document the constraint and add it to template README

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Inline `{% if %}` blocks inside Python files for conditional features | Avoids creating separate conditional files | Template becomes unreadable; Jinja2 inside Python defeats IDE support | Never for complex blocks; only for 1-2 line variations |
| Hardcoding `DOMAIN` in entity `unique_id` without entry ID suffix | Simple to read | Multiple entries of the same domain produce colliding unique IDs | Never |
| Calling `async_setup_entry` platform setup without `async_forward_entry_setups` | Works in older HA | Deprecated, removed in HA 2025.6 | Never |
| Skipping `hassfest` in CI | Faster CI | Catches breaking changes too late — at user install time | Never |
| Using `hass.data` instead of `entry.runtime_data` | Familiar pattern | Manual cleanup required; IQS penalizes at Silver+ | Acceptable for initial MVP if docs note upgrade path |
| No options flow | Less code to write | Users must remove + re-add integration to change host/port/API key | Never for service integrations |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| HA HTTP server (static paths) | `hass.http.register_static_path(url, path, True)` | `await hass.http.async_register_static_paths([StaticPathConfig(url, path, True)])` |
| HA HTTP server (duplicate registration) | Calling registration inside `async_setup_entry` — called once per config entry, so second entry triggers "already registered" error | Guard with a check, or move registration to `async_setup` (called once per domain) |
| aiohttp (session management) | `aiohttp.ClientSession()` constructed in coordinator | `async_get_clientsession(hass)` — shared, managed, never needs closing |
| Config entry (duplicate prevention) | No `async_set_unique_id` call | Call before `async_create_entry`; call `_abort_if_unique_id_configured()` after |
| Config entry (data storage) | `hass.data[DOMAIN][entry.entry_id] = coord` | `entry.runtime_data = MyData(coordinator=coord)` — auto-cleaned |
| Options flow (HA 2025.12+) | `self.config_entry = config_entry` in `__init__` | Remove the assignment; `OptionsFlow` base provides it automatically |
| HACS action validation | `hacs.json` missing `homeassistant` key or using wrong minimum version format | Must be `"homeassistant": "2025.7.0"` (semver, not `2025.7`) |
| hassfest (manifest) | Keys not sorted: domain, name, then alphabetical | Run `python -m script.hassfest` locally or in CI to catch before push |
| Copier (Python files) | Jinja2 rendering mangling Python `{}` syntax | Wrap `.py` files in `{% raw %}...{% endraw %}` |
| Copier (answers file) | Manual `.copier-answers.yml` edits | Never edit manually; use `copier recopy` to change answers |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Polling in coordinator too frequently | HA event loop latency, slow UI response, API rate limiting | Set `update_interval` to the minimum the API requires; document it | Immediately if API rate-limits; subtly at all times |
| Frontend JS file not cached | Card reloads full JS file on every dashboard load | Set `cache_headers=True` in `StaticPathConfig` | At scale across multiple browser tabs/users |
| Registering static path inside `async_setup_entry` (per-entry) | "Path already registered" errors when user has two config entries | Move static path registration to `async_setup` (called once per domain load) | On second config entry creation |
| Coordinator fetching all data synchronously in a single HTTP call | Timeout errors, long update intervals | Use `asyncio.gather()` for parallel sub-requests if needed | When API has multiple slow endpoints |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing API keys in `entry.data` without encryption | API key exposed in HA's `.storage/` JSON files in plaintext | HA has no transparent encryption for stored secrets; document the risk and note it's standard HA practice — the risk is acceptable for home use |
| Exposing the HA WebSocket API to unauthenticated callers | Any code on the LAN can call integration WebSocket commands | HA's built-in `@require_admin` decorator on WebSocket handlers; use it for write operations |
| Passing user-controlled strings directly to shell or filesystem paths | Path traversal in file-serving integrations | Immich project must sanitize asset IDs before using them as file paths; the template's base card should not pass URL parameters to the backend without validation |
| Frontend card accessing `hass.auth` or sensitive state without checking permissions | Card in a kiosk/shared dashboard leaks data | HA handles entity visibility, but custom WebSocket commands bypass entity permissions — guard sensitive WS commands with `connection.require_admin()` |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No `title` set in config entry | Integration shows up as generic domain name in UI | Always pass `title=` in `async_create_entry` — use the hostname or service name |
| `getCardSize()` returning wrong value | Card takes wrong amount of rows in Lovelace layout; overlaps or wastes space | Return the actual rendered row count; `3` is a reasonable default, update per card's content height |
| LitElement card not registering in `window.customCards` | Card doesn't appear in the card picker UI | Must push to `window.customCards` with `type`, `name`, `description`, and `preview: true` |
| Card editor not updating parent on config change | Changes in the visual editor don't save | Must fire `config-changed` custom event with `bubbles: true, composed: true` |
| Shadow DOM blocking HA theme CSS variables | Card uses hardcoded colors, ignores user's theme | Use only `var(--primary-color)`, `var(--primary-text-color)`, etc. — never hardcode hex colors |
| Missing `ha-card` wrapper element | Card has no elevation shadow and doesn't match HA card styling | Always wrap content in `<ha-card>` — it provides the HA card visual chrome |

---

## "Looks Done But Isn't" Checklist

- [ ] **Static path registration:** Verify `async_register_static_paths` (plural, async) — not `register_static_path` (singular, sync)
- [ ] **Config entry unique_id:** Verify `async_set_unique_id` is called in `async_step_user` before `async_create_entry`
- [ ] **Duplicate prevention:** Verify `_abort_if_unique_id_configured()` is called immediately after `async_set_unique_id`
- [ ] **Options flow deprecation:** Verify `OptionsFlowHandler.__init__` does NOT set `self.config_entry`; verify `ConfigFlow` has `async_get_options_flow` as a `@staticmethod @callback`
- [ ] **Session management:** Verify no `aiohttp.ClientSession()` constructor calls exist anywhere in the template — only `async_get_clientsession(hass)`
- [ ] **Static path guard:** Verify static path registration is in `async_setup` (domain-level), not `async_setup_entry` (entry-level), to prevent duplicate registration errors
- [ ] **runtime_data:** Verify `entry.runtime_data` is used instead of `hass.data[DOMAIN][entry.entry_id]`
- [ ] **Copier escaping:** Run `copier copy` against a test child project and verify `.py` files contain valid Python syntax (no Jinja2 corruption)
- [ ] **Card registration:** Verify `window.customCards.push(...)` is present and `customElements.define(...)` uses correct element names
- [ ] **Theme variables:** Search card JS for hardcoded colors (`#`, `rgb(`, `hsl(`) — replace with CSS custom properties
- [ ] **hassfest local pass:** Run `python -m script.hassfest --integration-path custom_components/DOMAIN` locally before PR
- [ ] **HACS action pass:** Run `hacs/action` GitHub Actions workflow against both template and a generated child project
- [ ] **manifest.json key order:** Verify `domain`, `name` first, then alphabetical — hassfest will fail if misordered
- [ ] **Copier smoke test:** After any template change, run full `copier copy` + verify generated project structure is correct

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Deprecated `register_static_path` in child projects | LOW | Update template, run `copier update` in each child project, accept the static path registration file changes |
| Raw `aiohttp.ClientSession` in coordinator | LOW | Template fix propagates via `copier update`; existing entries reload cleanly |
| Missing `unique_id` in existing child project entries | MEDIUM | Fix in template; existing entries in users' HA installs will not retroactively get unique IDs — users must remove and re-add; document in child project changelog |
| `hass.data` storage already in use in child projects | LOW | Both patterns coexist; migrate in a single PR per child project after template update |
| `.copier-answers.yml` manually edited and corrupted | HIGH | Delete the file, re-run `copier recopy` from the original template tag to regenerate it, manually re-apply child project customizations |
| Jinja2 rendering corruption discovered after child projects exist | MEDIUM | Fix template escaping, run `copier update` — 3-way merge will propose diffs for each corrupted file |
| Card element name collision (another HACS card uses same `customElements.define` name) | MEDIUM | Rename element in template to include domain slug; propagate via `copier update`; existing Lovelace configs need manual card type update |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| `register_static_path` deprecated API | Phase 1: HA API Fixes | `grep -r "register_static_path" custom_components/` returns no results |
| Raw `aiohttp.ClientSession()` | Phase 1: HA API Fixes | `grep -r "aiohttp.ClientSession()" custom_components/` returns no results |
| Missing `unique_id` in config flow | Phase 1: HA API Fixes | `grep -r "async_set_unique_id" custom_components/` returns a result |
| `hass.data` vs `entry.runtime_data` | Phase 1: HA API Fixes | `grep -r "hass.data\[DOMAIN\]" custom_components/` returns no results |
| Options flow `config_entry` assignment | Phase 1: HA API Fixes | `grep -r "self.config_entry = config_entry" custom_components/` returns no results |
| Static path registered per-entry | Phase 1: HA API Fixes | Registration call is in `async_setup`, not `async_setup_entry` |
| Copier Jinja2/Python brace collision | Phase 2: Copier Configuration | `copier copy` smoke test generates valid Python; no `TemplateSyntaxError` |
| Directory naming with wrong delimiter | Phase 2: Copier Configuration | Generated project has `custom_components/actual_domain/`, not `custom_components/{{ domain }}/` |
| `.copier-answers.yml` misuse | Phase 2: Copier Configuration | Template README documents the constraint; answers file has an inline warning comment |
| LitElement Shadow DOM theme isolation | Phase 3: Frontend Card Base Class | Card uses only CSS custom properties; visual review against dark and light themes |
| Missing `window.customCards` registration | Phase 3: Frontend Card Base Class | Card appears in Lovelace card picker after adding resource |
| Card editor `config-changed` event | Phase 3: Frontend Card Base Class | Changes in visual editor save correctly in Lovelace UI |
| Missing `ha-card` wrapper | Phase 3: Frontend Card Base Class | Card displays with correct HA card chrome and elevation |
| HACS validation failures | Phase 4: CI/CD and HACS Distribution | `hacs/action` GitHub Actions job passes in CI |
| hassfest manifest key order | Phase 4: CI/CD and HACS Distribution | `hassfest` job passes; manifest keys are sorted |
| No test structure | Phase 5: Test Scaffold | `pytest tests/` runs without import errors; config flow test passes |
| Coordinator mock in tests | Phase 5: Test Scaffold | `async_setup_entry` test uses `AsyncMock` for coordinator; no real network calls |

---

## Sources

- [Making http path registration async safe — HA Developer Docs](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/) — HIGH confidence (official HA developer blog)
- [hacs/integration issue #3828 — register_static_path deprecated](https://github.com/hacs/integration/issues/3828) — HIGH confidence (real-world impact documented)
- [Store runtime data inside the config entry — HA Developer Docs](https://developers.home-assistant.io/blog/2024/04/30/store-runtime-data-inside-config-entry/) — HIGH confidence (official HA developer blog)
- [New options flow properties — HA Developer Docs](https://developers.home-assistant.io/blog/2024/11/12/options-flow/) — HIGH confidence (official HA developer blog)
- [hacs/integration issue #4314 — options flow config_entry deprecated](https://github.com/hacs/integration/issues/4314) — HIGH confidence (confirmed real breakage at HA 2025.1)
- [HA inject-websession IQS rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/inject-websession/) — HIGH confidence (official IQS rule)
- [HA Config Flow Handler docs](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) — HIGH confidence (official HA developer docs)
- [Copier configuration docs](https://copier.readthedocs.io/en/stable/configuring/) — HIGH confidence (official Copier docs)
- [Copier updating docs](https://copier.readthedocs.io/en/stable/updating/) — HIGH confidence (official Copier docs)
- [Copier issue #1170 — Jinja extension update conflicts](https://github.com/copier-org/copier/issues/1170) — MEDIUM confidence (GitHub issue, not official docs)
- [HACS integration publishing requirements](https://www.hacs.xyz/docs/publish/integration/) — HIGH confidence (official HACS docs)
- [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) — HIGH confidence (official library for testing)
- [HA Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/) — HIGH confidence (official HA developer docs)

---
*Pitfalls research for: Copier template → HA HACS custom integrations with Lovelace cards*
*Researched: 2026-02-19*
