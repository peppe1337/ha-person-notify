# HA HACS Integration Template

A [Copier](https://copier.readthedocs.io/) template for building Home Assistant custom integrations with Lovelace frontend cards, distributed via HACS.

## Generating a New Project

```bash
# Install copier (once)
pipx install copier

# Generate a new project
copier copy gh:Dabentz/ha-hacs-template ./my-integration
```

You will be prompted for:
- **project_domain** — Integration domain (e.g. `my_integration`)
- **project_name** — Human-readable name (e.g. `My Integration`)
- **project_description** — Short description
- **author_name** — GitHub username
- **iot_class** — How the integration communicates (`local_polling`, `cloud_polling`, etc.)
- **integration_type** — Integration type (`service`, `hub`, `device`, etc.)
- Feature flags: WebSocket API, custom services, secondary coordinator, multi-step config flow
- **version** — Initial version (`0.1.0`)

## Template Structure

```
ha-hacs-template/                              # template repo root
├── copier.yml                                 # Copier config + questions
├── README.md                                  # this file
├── LICENSE
├── .github/workflows/                         # template repo CI
└── template/                                  # _subdirectory: template
    ├── {{ _copier_conf.answers_file }}.jinja  # generates .copier-answers.yml
    ├── hacs.json.jinja
    ├── pyproject.toml.jinja
    ├── README.md.jinja                        # generated project README
    ├── .gitignore
    ├── custom_components/
    │   └── [[ project_domain ]]/              # rendered to your domain
    │       ├── __init__.py.jinja
    │       ├── api.py.jinja                   # API client with ServerError/CannotConnectError/InvalidAuthError
    │       ├── binary_sensor.py.jinja         # connectivity status sensor
    │       ├── config_flow.py.jinja           # config + options flow with validation
    │       ├── const.py.jinja
    │       ├── coordinator.py.jinja
    │       ├── manifest.json.jinja
    │       ├── sensor.py.jinja
    │       ├── strings.json.jinja
    │       ├── translations/
    │       │   └── en.json.jinja
    │       └── frontend/
    │           └── [[ project_domain ]]-card.js.jinja
    └── tests/
        ├── __init__.py.jinja
        ├── conftest.py.jinja
        ├── test_config_flow.py.jinja
        ├── test_coordinator.py.jinja
        └── test_sensor.py.jinja
```

Conditional files (generated based on feature flags):
- `services.py.jinja` + `services.yaml.jinja` — if `use_services`
- `test_services.py.jinja` — if `use_services`
- `websocket.py.jinja` + `test_websocket.py.jinja` — if `use_websocket`
- `coordinator_secondary.py.jinja` — if `use_secondary_coordinator`

## Updating a Generated Project

When the template is updated, propagate changes to an existing child project:

```bash
cd my-integration
copier update
```

This uses a 3-way merge to apply template changes while preserving your customizations.

## Key Patterns

The generated project includes:
- **Config Flow**: UI-based setup with host/port/SSL validation, options flow with reload
- **DataUpdateCoordinator**: Centralized polling pattern with `async_get_clientsession`
- **CoordinatorEntity**: Entities that auto-update from coordinator data
- **Binary Sensor**: Connectivity status based on `coordinator.last_update_success`
- **API Client**: Generic client with SSL, optional auth, and proper error classification (ServerError vs CannotConnectError)
- **Frontend Card**: LitElement-based Lovelace card with visual editor
- **Static Path**: Frontend JS served via `hass.http.async_register_static_paths` (HA 2025.7+)
- **Device Registry**: `DeviceEntryType.SERVICE` grouping for all entities
- **Test Suite**: Config flow, coordinator, sensor, and service tests with HA fixtures

For details on the generated project's structure and usage, see the generated `README.md`.

## License

MIT
