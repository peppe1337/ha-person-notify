---
status: complete
phase: 05-conditional-patterns
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md]
started: 2026-02-20T05:40:00Z
updated: 2026-02-20T05:45:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Copier all-OFF produces clean default project
expected: Run copier with defaults. No conditional files generated (no websocket.py, services.py, services.yaml, coordinator_secondary.py). __init__.py has no references to websocket/services/secondary. config_flow.py has single-step only. manifest.json dependencies = ["frontend"]. No "credentials" in strings/translations.
result: pass

### 2. Copier all-ON generates all conditional modules
expected: Run copier with all four flags true. All conditional files generated: websocket.py, services.py, services.yaml, coordinator_secondary.py. No config_flow_multi_step.py (dead stub deleted). All Python files parse. All JSON files parse. No Jinja2 artifacts in generated files.
result: pass

### 3. WebSocket handler has correct decorator order and registration
expected: In all-ON websocket.py: @websocket_command before @async_response. async_setup_websocket function exists. __init__.py calls async_setup_websocket in async_setup (domain-level).
result: pass

### 4. Services handler uses SupportsResponse.OPTIONAL
expected: In all-ON services.py: SupportsResponse.OPTIONAL present. SERVICE_QUERY = "query" constant. async_register_services function. services.yaml has query service. __init__.py calls async_register_services in async_setup.
result: pass

### 5. Multi-step config flow has two steps with correct validation placement
expected: In all-ON config_flow.py: async_step_user AND async_step_credentials present. unique_id set in async_step_credentials (not async_step_user). strings.json and translations/en.json have credentials step. User step does NOT include api_key when multi-step enabled.
result: pass

### 6. Secondary coordinator has independent poll interval
expected: In all-ON coordinator_secondary.py: TemplateSecondaryCoordinator class, DEFAULT_SECONDARY_SCAN_INTERVAL, own ApiClient. __init__.py imports TemplateSecondaryCoordinator and includes coordinator_secondary in runtime_data.
result: pass

### 7. Manifest conditionally includes websocket_api dependency
expected: all-OFF manifest: dependencies = ["frontend"]. all-ON manifest: dependencies includes "websocket_api". Both valid JSON.
result: pass

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0

## Gaps

[none]
