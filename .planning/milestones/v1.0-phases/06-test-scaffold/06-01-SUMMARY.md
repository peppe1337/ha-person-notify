---
phase: 06-test-scaffold
plan: 01
subsystem: testing
tags: [pytest, pytest-homeassistant-custom-component, pytest-asyncio, copier, jinja2]

# Dependency graph
requires:
  - phase: 02-copier-template-scaffolding
    provides: "[[ ]] / [% %] envops delimiters and template/ subdirectory structure"
  - phase: 03-backend-core
    provides: "async_setup_entry, coordinator, and domain constants that conftest patches"

provides:
  - "template/pyproject.toml.jinja: pytest asyncio_mode=auto config and test dependency declaration"
  - "template/tests/__init__.py.jinja: non-empty package marker enabling pytest discovery"
  - "template/tests/conftest.py.jinja: auto_enable_custom_integrations autouse fixture and mock_setup_entry fixture"

affects:
  - 06-02 (test_config_flow.py.jinja depends on conftest fixtures)
  - 06-03 (test_coordinator.py.jinja depends on pyproject.toml asyncio config)

# Tech tracking
tech-stack:
  added:
    - "pytest-homeassistant-custom-component (declared in optional-dependencies)"
  patterns:
    - "asyncio_mode=auto in [tool.pytest.ini_options] — zero per-test decorator overhead"
    - "autouse wrapper fixture around enable_custom_integrations — all tests get custom integration loading"
    - "mock_setup_entry as non-autouse fixture — only config flow tests request it explicitly"
    - "[[ project_domain ]] Copier variable in patch target path rendered at copy time"

key-files:
  created:
    - template/pyproject.toml.jinja
    - template/tests/__init__.py.jinja
    - template/tests/conftest.py.jinja
  modified: []

key-decisions:
  - "asyncio_mode=auto is mandatory (not strict) — zero per-test @pytest.mark.asyncio annotation; HA ecosystem default since pytest-asyncio 0.21"
  - "tests/__init__.py.jinja contains a comment line (not empty) to guarantee Copier renders the file (Pitfall 5 from research)"
  - "mock_setup_entry patches custom_components.[[ project_domain ]].async_setup_entry (top-level __init__, not config_flow) — prevents full HA setup during config flow tests"
  - "No [build-system] section in pyproject.toml — generated projects are not Python packages"

patterns-established:
  - "Pattern: conftest autouse=enable_custom_integrations wrapper — mandatory for HA loader to find custom_components/ during tests"
  - "Pattern: Generator[AsyncMock] return type (modern Python; no need for Generator[AsyncMock, None, None])"

requirements-completed: [TEST-01, TEST-05]

# Metrics
duration: 1min
completed: 2026-02-20
---

# Phase 6 Plan 01: Pytest Infrastructure Template Files Summary

**pytest-homeassistant-custom-component scaffold: pyproject.toml with asyncio_mode=auto, tests/__init__.py package marker, and conftest.py with autouse enable_custom_integrations and mock_setup_entry fixtures**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-02-20T15:49:10Z
- **Completed:** 2026-02-20T15:49:50Z
- **Tasks:** 2
- **Files modified:** 3 (all created)

## Accomplishments

- Created `template/pyproject.toml.jinja` with `asyncio_mode = "auto"` and `pytest-homeassistant-custom-component` optional dependency — zero additional pytest configuration needed in generated projects
- Created `template/tests/__init__.py.jinja` as a non-empty Python package marker with a comment line, ensuring Copier renders it and pytest discovers the tests/ directory
- Created `template/tests/conftest.py.jinja` with two fixtures: `auto_enable_custom_integrations` (autouse) wrapping `enable_custom_integrations` from pytest-homeassistant-custom-component, and `mock_setup_entry` patching the correct top-level `async_setup_entry` using `[[ project_domain ]]` Copier variable

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pyproject.toml.jinja and tests/__init__.py.jinja** - `c2baf70` (feat)
2. **Task 2: Create tests/conftest.py.jinja with HA fixtures** - `1b27da0` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `template/pyproject.toml.jinja` - pytest configuration with asyncio_mode=auto and pytest-homeassistant-custom-component test dependency
- `template/tests/__init__.py.jinja` - Python package marker with comment line; Copier renders it as tests/__init__.py in generated projects
- `template/tests/conftest.py.jinja` - autouse enable_custom_integrations fixture + mock_setup_entry fixture with [[ project_domain ]] Copier variable in patch target

## Decisions Made

- `asyncio_mode = "auto"` (not `strict`) selected — HA ecosystem default; zero per-test decorator overhead; mandatory since pytest-asyncio 0.21/1.0
- `tests/__init__.py.jinja` contains `# Tests package` comment (not empty) — guards against Copier skipping empty-output files (Pitfall 5)
- `mock_setup_entry` patches `custom_components.[[ project_domain ]].async_setup_entry` at the top-level module (not `config_flow`) — this is where HA calls the function; prevents full integration setup during config flow tests
- No `[build-system]` section in `pyproject.toml.jinja` — generated projects are not Python packages; `[tool.pytest.ini_options]` is standalone

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- pytest infrastructure complete; TEST-01 (conftest + enable_custom_integrations) and TEST-05 (pyproject.toml asyncio_mode=auto) requirements satisfied
- Plan 06-02 can now create `test_config_flow.py.jinja` and `test_coordinator.py.jinja` using the conftest fixtures established here
- Plan 06-03 can create conditional `[% if use_websocket %]test_websocket.py[% endif %].jinja` using the same Copier pattern proven in Phase 5

---
*Phase: 06-test-scaffold*
*Completed: 2026-02-20*
