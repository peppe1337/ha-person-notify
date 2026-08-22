# Phase 6: Test Scaffold - Research

**Researched:** 2026-02-20
**Domain:** pytest infrastructure for Home Assistant custom components — conftest fixtures, config flow testing, coordinator mocking, conditional test file generation via Copier
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TEST-01 | `conftest.py` with `enable_custom_integrations` fixture and HA test helpers | `enable_custom_integrations` pattern confirmed from pytest-homeassistant-custom-component README; autouse fixture approach confirmed from community discussion |
| TEST-02 | `test_config_flow.py` covering successful setup, connection failure, duplicate abort, and options flow | Canonical scaffold patterns confirmed from HA core `script/scaffold/templates/config_flow/tests/test_config_flow.py`; options flow test pattern confirmed |
| TEST-03 | `test_coordinator.py` with mocked API client and coordinator refresh testing | `DataUpdateCoordinator.async_refresh()` confirmed from HA core source; `MockConfigEntry` pattern confirmed from pytest-homeassistant-custom-component docs |
| TEST-04 | Conditional test files generated matching conditional source modules (e.g., `test_websocket.py` when WebSocket enabled) | Copier conditional filename pattern `[% if use_websocket %]test_websocket.py[% endif %].jinja` — same pattern used successfully in Phase 5 for `websocket.py` |
| TEST-05 | `pyproject.toml` or `pytest.ini` with `asyncio_mode = auto` and `pytest-homeassistant-custom-component` dependency | `asyncio_mode = auto` in `[tool.pytest.ini_options]` confirmed from official pytest-asyncio docs; package version 0.13.315 (tracking HA 2026.2.2) confirmed from PyPI |
</phase_requirements>

---

## Summary

Phase 6 adds a working pytest infrastructure to the Copier template so that every generated project ships with tests that run out of the box. The test scaffold consists of five template files: `pyproject.toml` (pytest config + dependency), `tests/conftest.py` (always-on fixtures), `tests/test_config_flow.py` (always-on), `tests/test_coordinator.py` (always-on), and the conditional `tests/test_websocket.py` (only when `use_websocket=true`).

The canonical test framework for HA custom components is `pytest-homeassistant-custom-component` (version 0.13.315, tracking HA 2026.2.2). It re-exports all HA core testing fixtures including `hass`, `MockConfigEntry`, and `enable_custom_integrations`. The key setup requirement is an autouse conftest fixture that activates custom integration loading — without it, HA's loader will not find the generated integration during tests.

Test patterns for config flow, coordinator, and WebSocket commands are well-established in HA core's scaffold templates. The most important implementation insight is that tests mock `_async_validate_connection` (or `ApiClient.async_get_data` for coordinator) using `unittest.mock.patch`, not by subclassing or dependency-injecting. The mock target path is `custom_components.<domain>.config_flow._async_validate_connection`.

**Primary recommendation:** Use a single `pyproject.toml.jinja` at the template root (alongside `hacs.json.jinja`) for pytest config. Tests go in `template/tests/` as `.jinja` files with Copier `[[ domain ]]` substitution. The conditional `test_websocket.py` uses the same `[% if use_websocket %]test_websocket.py[% endif %].jinja` pattern already proven in Phase 5.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pytest-homeassistant-custom-component` | 0.13.315 (PyPI, Feb 2026) | Re-exports HA core test fixtures (`hass`, `MockConfigEntry`, `enable_custom_integrations`) | Official community standard; tracks HA daily; Python >=3.13 required |
| `pytest` | Pulled by above | Test runner | Standard; pytest-homeassistant-custom-component declares it as a dependency |
| `pytest-asyncio` | Pulled by above | Async test support | Bundled; must set `asyncio_mode = auto` in config |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `unittest.mock.patch` | stdlib | Patching API client calls | Always — the standard HA test pattern for mocking I/O |
| `unittest.mock.AsyncMock` | stdlib | Mock for async functions | When mocking `async_get_data`, `async_test_connection`, etc. |
| `homeassistant.data_entry_flow.FlowResultType` | HA bundled | Assert flow result types (`FORM`, `CREATE_ENTRY`, `ABORT`) | Config flow tests |
| `homeassistant.config_entries.SOURCE_USER` | HA bundled | Context source for `async_init` | Config flow test setup |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `pytest-homeassistant-custom-component` | Raw `homeassistant` package | Raw HA is 100MB+ install; pytest-homeassistant-custom-component is a lightweight re-export package — always prefer it |
| `pyproject.toml` | `pytest.ini` or `setup.cfg` | `pyproject.toml` is the modern Python standard; preferred for new projects |
| `asyncio_mode = auto` | `asyncio_mode = strict` (decorator-per-test) | Auto requires zero per-test annotation; HA core uses auto; use auto |

**Installation (in generated project):**
```bash
pip install pytest-homeassistant-custom-component
```

Or, in `pyproject.toml` dev dependencies:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[project.optional-dependencies]
test = ["pytest-homeassistant-custom-component"]
```

---

## Architecture Patterns

### Recommended Test Directory Structure

Generated project structure (what Copier produces into the child project):

```
<child-project>/
├── custom_components/
│   └── <domain>/          # integration source (from existing templates)
├── tests/
│   ├── __init__.py        # empty, required for pytest discovery
│   ├── conftest.py        # enable_custom_integrations autouse fixture
│   ├── test_config_flow.py
│   ├── test_coordinator.py
│   └── test_websocket.py  # only when use_websocket=true
└── pyproject.toml         # pytest config + test dependency
```

Copier template files (what this phase adds to the template/):

```
template/
├── pyproject.toml.jinja
├── tests/
│   ├── __init__.py.jinja        # empty file — enables pytest discovery
│   ├── conftest.py.jinja
│   ├── test_config_flow.py.jinja
│   ├── test_coordinator.py.jinja
│   └── [% if use_websocket %]test_websocket.py[% endif %].jinja
└── (existing: custom_components/, hacs.json.jinja, README.md.jinja)
```

Note: `tests/__init__.py` must be a `.jinja` file even though it is empty — Copier only processes files with the `_templates_suffix` (`.jinja`). An empty `.jinja` file renders to an empty file.

### Pattern 1: conftest.py — enable_custom_integrations autouse

This is the mandatory fixture that makes HA's loader recognize the `custom_components/` directory during tests.

```python
# Source: community.home-assistant.io/t/custom-integration-tests-for-config-flow/348165
# and pytest-homeassistant-custom-component README
import pytest

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test environment."""
    yield
```

The `enable_custom_integrations` fixture is provided automatically by `pytest-homeassistant-custom-component`. Without the `autouse=True` wrapper, every test would need to explicitly request it.

The conftest also patches `async_setup_entry` to prevent the full HA setup from running during config flow tests:

```python
from collections.abc import Generator
from unittest.mock import AsyncMock, patch
import pytest

@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry so config flow tests don't trigger real setup."""
    with patch(
        "custom_components.[[ project_domain ]].async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry
```

### Pattern 2: test_config_flow.py — four required test cases

The four scenarios from TEST-02, each using the same `hass.config_entries.flow.async_init` / `async_configure` pattern:

**Successful setup:**
```python
# Source: github.com/home-assistant/core/blob/dev/script/scaffold/templates/config_flow/tests/test_config_flow.py
async def test_form(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.[[ project_domain ]].config_flow._async_validate_connection",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.1.100", CONF_PORT: 8080, CONF_API_KEY: "test-key"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: "192.168.1.100", CONF_PORT: 8080, CONF_API_KEY: "test-key"}
    assert len(mock_setup_entry.mock_calls) == 1
```

**CannotConnect error display:**
```python
async def test_form_cannot_connect(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "custom_components.[[ project_domain ]].config_flow._async_validate_connection",
        side_effect=CannotConnect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.1.100", CONF_PORT: 8080, CONF_API_KEY: "test-key"},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
```

**Duplicate entry abort:**
```python
async def test_form_duplicate_abort(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="192.168.1.100:8080",
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 8080, CONF_API_KEY: "key"},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "custom_components.[[ project_domain ]].config_flow._async_validate_connection",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.1.100", CONF_PORT: 8080, CONF_API_KEY: "key"},
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
```

**Options flow save:**
```python
async def test_options_flow(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 8080, CONF_API_KEY: "old-key"},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.100", CONF_PORT: 8080, CONF_API_KEY: "new-key"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_API_KEY] == "new-key"
```

Note: The options flow test uses `hass.config_entries.options.async_init` (not `flow.async_init`). The options flow saves to `entry.data` (not `entry.options`) per the Phase 3 decision.

### Pattern 3: test_coordinator.py — mocked API client

```python
from unittest.mock import AsyncMock, patch
from pytest_homeassistant_custom_component.common import MockConfigEntry

async def test_coordinator_update(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 8080, CONF_API_KEY: "key"},
    )
    entry.add_to_hass(hass)

    mock_data = {"sensor_value": 42}

    with patch(
        "custom_components.[[ project_domain ]].coordinator.ApiClient.async_get_data",
        new_callable=AsyncMock,
        return_value=mock_data,
    ):
        coordinator = TemplateCoordinator(hass, entry)
        await coordinator.async_refresh()

    assert coordinator.data == mock_data
```

### Pattern 4: Conditional test_websocket.py

When `use_websocket=true`, a test that verifies the WebSocket command handler is registered and produces a result. This uses the `hass_ws_client` fixture from HA core (re-exported by pytest-homeassistant-custom-component):

```python
async def test_websocket_get_data(hass: HomeAssistant, hass_ws_client) -> None:
    """Test the WebSocket get_data command."""
    entry = MockConfigEntry(domain=DOMAIN, data={...})
    entry.add_to_hass(hass)

    with patch(
        "custom_components.[[ project_domain ]].coordinator.ApiClient.async_get_data",
        new_callable=AsyncMock,
        return_value={"value": 1},
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": f"{DOMAIN}/get_data"})
    result = await client.receive_json()

    assert result["success"] is True
    assert result["result"] == {"value": 1}
```

Note: `hass_ws_client` is a fixture from `pytest_homeassistant_custom_component` (re-exported from HA core). Confidence on the exact fixture name is MEDIUM — it is widely referenced in HA core tests but not explicitly documented in the pytest-homeassistant-custom-component README. Verify by checking `from pytest_homeassistant_custom_component import hass_ws_client` or inspecting available fixtures at test time.

### Pattern 5: pyproject.toml — pytest configuration

The `pyproject.toml.jinja` sits at the template root (same level as `hacs.json.jinja`). It configures pytest and declares the test dependency:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[project.optional-dependencies]
test = [
    "pytest-homeassistant-custom-component",
]
```

The `asyncio_mode = "auto"` setting is mandatory — without it, pytest-asyncio (which pytest-homeassistant-custom-component pulls in) will refuse to run async test functions without per-function decorators.

Note on `pyproject.toml` scope: This file also serves as the future home of project metadata and linting config (Phase 7 may add more sections). For Phase 6, only the `[tool.pytest.ini_options]` and optional test dependency sections are needed. There is no `[build-system]` required since generated projects are not Python packages.

### Anti-Patterns to Avoid

- **Importing from `tests.common` instead of `pytest_homeassistant_custom_component.common`:** The `tests.common` path is HA core's internal path; in custom component tests always use `pytest_homeassistant_custom_component.common`.
- **Forgetting `enable_custom_integrations` autouse:** Tests will fail with "Integration not found" at runtime without it.
- **Patching at the wrong module path:** Patch where the function is *called*, not where it is *defined*. For `_async_validate_connection`, patch `custom_components.<domain>.config_flow._async_validate_connection`, not `custom_components.<domain>.api.ApiClient.async_test_connection`.
- **Skipping `await hass.async_block_till_done()` after `CREATE_ENTRY`:** Required to let HA process the setup tasks triggered by entry creation; missing it causes `mock_setup_entry.mock_calls` count assertions to fail.
- **Using `asyncio_mode = strict` or omitting asyncio_mode:** Forces per-test `@pytest.mark.asyncio` decorators; HA ecosystem expects auto mode.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HA instance for tests | Custom HA setup code | `hass` fixture from pytest-homeassistant-custom-component | HA startup is complex (event loop, component loading, state machine); the fixture handles all of it |
| Mock config entry | `ConfigEntry(...)` constructor directly | `MockConfigEntry` from `pytest_homeassistant_custom_component.common` | `ConfigEntry` has many required fields and internal state; `MockConfigEntry` provides safe defaults |
| Async mock functions | `MagicMock` (non-async) | `unittest.mock.AsyncMock` | `MagicMock` returns a coroutine object when called async, not the awaited result; `AsyncMock` is the correct stdlib tool |

**Key insight:** The HA test ecosystem is tightly coupled to specific fixture names and import paths. Deviating from these paths produces cryptic failures. Always follow the exact import paths shown in the canonical scaffold template.

---

## Common Pitfalls

### Pitfall 1: asyncio_mode not configured — SyntaxWarning or collection error

**What goes wrong:** pytest-asyncio raises `PytestUnraisableExceptionWarning` or silently skips async test functions when `asyncio_mode` is not set, OR raises a `DeprecationWarning` that becomes an error depending on warning filters.

**Why it happens:** pytest-asyncio requires explicit mode configuration since 0.21. Auto mode is the intended HA ecosystem mode.

**How to avoid:** Always include `asyncio_mode = "auto"` in `[tool.pytest.ini_options]` in `pyproject.toml`.

**Warning signs:** Tests appear to pass instantly with 0 assertions run, or you see "PytestUnraisableExceptionWarning: RuntimeError: Task attached to a different loop".

### Pitfall 2: Wrong patch target — mock has no effect

**What goes wrong:** `patch("custom_components.domain.api.ApiClient.async_get_data", ...)` patches the class definition but the test's code already imported and instantiated the client before the patch applied.

**Why it happens:** Python's import system means you must patch where the name is *used*, not where it is *defined*. The coordinator imports `ApiClient` at the top of `coordinator.py`, so you must patch `custom_components.<domain>.coordinator.ApiClient.async_get_data`.

**How to avoid:** Always patch at the module that *imports and uses* the target, not the defining module. For config flow, patch `config_flow._async_validate_connection`. For coordinator, patch `coordinator.ApiClient.async_get_data`.

**Warning signs:** `AsyncMock` was never called (`mock_calls == []`) despite the code path running.

### Pitfall 3: Missing `tests/__init__.py` — pytest discovery failure

**What goes wrong:** pytest finds no tests when `tests/__init__.py` is absent, producing "no tests ran" with exit code 5 (or worse, silently).

**Why it happens:** Without `__init__.py`, Python does not treat `tests/` as a package. While modern pytest can sometimes discover without it, the HA test ecosystem expects it.

**How to avoid:** Include an empty `tests/__init__.py.jinja` file in the template. Copier renders it as an empty `tests/__init__.py`.

**Warning signs:** `pytest tests/` finds 0 tests even though test files exist.

### Pitfall 4: Options flow uses `entry.options` instead of `entry.data`

**What goes wrong:** Test asserts `entry.options[CONF_API_KEY] == "new-key"` but the options flow handler writes to `entry.data` (per Phase 3 decision).

**Why it happens:** Standard HA integrations write options to `entry.options`; this template deviates by using `async_update_entry` to merge into `entry.data` to avoid having two sources of truth.

**How to avoid:** Test asserts against `entry.data` for options flow save verification, not `entry.options`.

**Warning signs:** Test fails with `KeyError` or `AssertionError` on `entry.options`.

### Pitfall 5: Copier rendering strips empty files — `__init__.py` disappears

**What goes wrong:** An empty `tests/__init__.py.jinja` may not render if Copier skips empty-output files.

**Why it happens:** Copier does NOT skip empty-output files by default — it renders them normally. However, this should be verified during smoke testing. A safe guard is adding a single comment line: `# Tests package`.

**How to avoid:** Add `# Tests package` as the sole content of `tests/__init__.py.jinja` to ensure it is non-empty and renders correctly.

### Pitfall 6: `hass_ws_client` fixture scope — not finding the websocket client fixture

**What goes wrong:** Test fails with `fixture 'hass_ws_client' not found`.

**Why it happens:** `hass_ws_client` is a fixture from HA core's conftest, re-exported by pytest-homeassistant-custom-component. If the package version is outdated or the fixture was renamed, it may not be available.

**How to avoid:** Confirm fixture availability with a quick `pytest --fixtures | grep ws_client` on a freshly generated project. If unavailable, the websocket test can alternatively test that the command is registered by checking `hass.data` directly rather than making a full WS call.

---

## Code Examples

Verified patterns from official sources:

### pyproject.toml.jinja — complete

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

This is the minimum viable pytest config. The `[project]` section is optional; child projects that only need to run tests locally don't need a full `[build-system]` section.

### conftest.py.jinja — complete

```python
"""Common fixtures for the [[ project_name ]] tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this package."""
    yield


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry to prevent full integration setup during config flow tests."""
    with patch(
        "custom_components.[[ project_domain ]].async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry
```

### test_config_flow.py.jinja — imports section

```python
"""Tests for [[ project_name ]] config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.[[ project_domain ]].config_flow import CannotConnect
from custom_components.[[ project_domain ]].const import DOMAIN
```

### test_coordinator.py.jinja — imports and coordinator test

```python
"""Tests for [[ project_name ]] coordinator."""

from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.[[ project_domain ]].const import DOMAIN
from custom_components.[[ project_domain ]].coordinator import TemplateCoordinator


async def test_coordinator_update(hass: HomeAssistant) -> None:
    """Test coordinator fetches data from the API and stores it."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 8080, CONF_API_KEY: "test-key"},
    )
    entry.add_to_hass(hass)

    mock_data = {"sensor_value": 42, "status": "ok"}

    with patch(
        "custom_components.[[ project_domain ]].coordinator.ApiClient.async_get_data",
        new_callable=AsyncMock,
        return_value=mock_data,
    ):
        coordinator = TemplateCoordinator(hass, entry)
        await coordinator.async_refresh()

    assert coordinator.data == mock_data


async def test_coordinator_update_failed(hass: HomeAssistant) -> None:
    """Test coordinator raises UpdateFailed when the API is unreachable."""
    from homeassistant.helpers.update_coordinator import UpdateFailed
    from custom_components.[[ project_domain ]].api import CannotConnectError

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 8080, CONF_API_KEY: "test-key"},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.[[ project_domain ]].coordinator.ApiClient.async_get_data",
        new_callable=AsyncMock,
        side_effect=CannotConnectError("Connection refused"),
    ):
        coordinator = TemplateCoordinator(hass, entry)
        try:
            await coordinator.async_refresh()
        except UpdateFailed:
            pass
        else:
            assert False, "Expected UpdateFailed was not raised"
```

### Conditional test_websocket.py.jinja — skeleton

```python
"""Tests for [[ project_name ]] WebSocket commands."""

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.[[ project_domain ]].const import DOMAIN


async def test_websocket_get_data(hass: HomeAssistant, hass_ws_client) -> None:
    """Test that the WebSocket get_data command returns coordinator data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.100", "port": 8080, "api_key": "key"},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.[[ project_domain ]].coordinator.ApiClient.async_get_data",
        new_callable=AsyncMock,
        return_value={"sensor_value": 42},
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": f"{DOMAIN}/get_data"})
    result = await client.receive_json()

    assert result["success"] is True
    assert result["result"] == {"sensor_value": 42}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@pytest.mark.asyncio` per test | `asyncio_mode = "auto"` in pyproject.toml | pytest-asyncio 0.21 (2023) | Zero annotation overhead; HA ecosystem default |
| Import from `tests.common` | Import from `pytest_homeassistant_custom_component.common` | Since package launch | Required for custom components; `tests.common` is only for HA core |
| `OptionsFlowWithConfigEntry` (passed `config_entry` to `__init__`) | `OptionsFlow` base class only; `self.config_entry` auto-injected | HA 2024.11 / Nov 2024 | Template already uses the new pattern; tests must not pass `config_entry` to constructor |
| `hass.data[DOMAIN]` for runtime data | `entry.runtime_data` | HA 2024.x | Template already uses `runtime_data`; tests access data via `entry.runtime_data` |
| `asyncio_mode` not set (deprecated) | Explicit `asyncio_mode = "auto"` required | pytest-asyncio 1.0 (May 2025) | Without this, async tests may silently not run in newer pytest-asyncio versions |

**Deprecated/outdated:**
- `pytest-homeassistant`: Old package (github.com/boralyl/pytest-homeassistant); superseded by `pytest-homeassistant-custom-component` which tracks HA core automatically. Do not use.
- `setup.cfg` for pytest config: Still works but `pyproject.toml` is the modern standard for new projects.

---

## Open Questions

1. **`hass_ws_client` fixture availability in pytest-homeassistant-custom-component**
   - What we know: `hass_ws_client` is a fixture in HA core's conftest; pytest-homeassistant-custom-component re-exports many core fixtures
   - What's unclear: Whether `hass_ws_client` specifically is re-exported, or if a different fixture name is used in the custom component test context
   - Recommendation: During plan execution, verify with `pytest --fixtures 2>/dev/null | grep ws` in a freshly generated project. If not available, fall back to testing that `async_setup_websocket` was called (simpler, lower-fidelity) rather than making a full WS connection.

2. **Empty `pyproject.toml` — no `[build-system]` needed**
   - What we know: Generated projects are not Python packages; they have no `setup.py` or `__init__.py` at the root
   - What's unclear: Whether pytest requires a `[build-system]` section or `[project]` section to parse `[tool.pytest.ini_options]`
   - Recommendation: `[tool.pytest.ini_options]` is standalone and does not require `[build-system]`. Verify by running `pytest --co` in a generated project with only that section present.

3. **Smoke test for conditional test file exclusion**
   - What we know: The `[% if use_websocket %]test_websocket.py[% endif %].jinja` pattern worked for `websocket.py` in Phase 5
   - What's unclear: Nothing — the pattern is confirmed. Just needs verification that `pytest` does not error when `test_websocket.py` is absent.
   - Recommendation: Run two smoke tests: `copier copy --data use_websocket=true` (confirm `test_websocket.py` present) and `copier copy --data use_websocket=false` (confirm absent).

---

## Sources

### Primary (HIGH confidence)
- `github.com/home-assistant/core/blob/dev/script/scaffold/templates/config_flow/tests/test_config_flow.py` — canonical HA config flow test patterns (`async_init`, `async_configure`, `FlowResultType`, `mock_setup_entry`)
- `github.com/home-assistant/core/blob/dev/script/scaffold/templates/config_flow/tests/conftest.py` — canonical `mock_setup_entry` fixture pattern
- `pypi.org/project/pytest-homeassistant-custom-component/` — version 0.13.315, Python >=3.13, MIT license
- `github.com/MatthewFlamm/pytest-homeassistant-custom-component` — `enable_custom_integrations` requirement, `MockConfigEntry` import path, autouse fixture pattern
- HA developer blog `developers.home-assistant.io/blog/2024/11/12/options-flow/` — `OptionsFlow` base class, `self.config_entry` auto-injection (Nov 2024)

### Secondary (MEDIUM confidence)
- `community.home-assistant.io/t/custom-integration-tests-for-config-flow/348165` — autouse `enable_custom_integrations` pattern, confirmed by multiple community members
- `github.com/jpawlowski/hacs.integration_blueprint` — `pyproject.toml` with `asyncio_mode = "auto"`, `testpaths = ["tests"]` (HIGH alignment with standard)
- `aarongodfrey.dev/home automation/building_a_home_assistant_custom_component_part_4/` — options flow test using `hass.config_entries.options.async_init` / `async_configure`
- `github.com/home-assistant/core/blob/dev/homeassistant/helpers/update_coordinator.py` — `async_refresh()` and `async_config_entry_first_refresh()` method signatures

### Tertiary (LOW confidence)
- `hass_ws_client` fixture for websocket tests — referenced in HA core tests but not explicitly documented as available in pytest-homeassistant-custom-component; verify at plan execution time.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pytest-homeassistant-custom-component is the sole standard; version and requirements confirmed from PyPI
- Architecture: HIGH — conftest fixture patterns confirmed from HA core scaffold template; Copier conditional filename pattern proven in Phase 5
- Pitfalls: HIGH — asyncio_mode pitfall confirmed from official pytest-asyncio docs; patch target pitfall is a well-known Python mock pattern
- WebSocket test pattern: MEDIUM — `hass_ws_client` fixture is referenced in HA core tests but not explicitly confirmed as re-exported by pytest-homeassistant-custom-component

**Research date:** 2026-02-20
**Valid until:** 2026-03-20 (pytest-homeassistant-custom-component tracks HA daily; core patterns are stable; check for asyncio_mode changes if pytest-asyncio 2.0 releases)
