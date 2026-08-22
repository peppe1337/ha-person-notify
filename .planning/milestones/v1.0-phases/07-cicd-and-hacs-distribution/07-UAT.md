---
status: diagnosed
phase: 07-cicd-and-hacs-distribution
source: [07-01-SUMMARY.md]
started: 2026-02-20T20:00:00Z
updated: 2026-02-20T21:40:00Z
---

## Current Test

[testing complete]

## Tests

### 1. validate.yml template structure
expected: `template/.github/workflows/validate.yml` exists and contains two separate jobs: `hassfest` (with checkout + hassfest action) and `hacs` (with hacs/action). Actions are SHA-pinned (long hex hashes, not version tags). File has `permissions: {}` and `ignore: brands`.
result: pass

### 2. Copier generates validate.yml in child project
expected: Running `copier copy` produces a child project with `.github/workflows/validate.yml` present — identical content to the template file (no Jinja substitution needed since it's a static file).
result: pass

### 3. Generated .gitignore includes test artifacts
expected: Generated child project `.gitignore` contains `.pytest_cache/`, `.coverage`, `coverage.xml`, `htmlcov/` entries alongside the original Python/IDE/OS exclusions (`__pycache__/`, `.vscode/`, `.DS_Store`, etc.).
result: pass

### 4. Generated README has HACS badge and project content
expected: Generated child project `README.md` shows a HACS badge image/link, installation instructions mentioning HACS, and a card usage section with the project's domain name substituted in (not raw Jinja variables).
result: pass

### 5. GitHub Actions: hassfest catches manifest errors
expected: Pushing a generated project to GitHub with a deliberately broken `manifest.json` (e.g., missing required field) causes the hassfest job to fail with a visible error identifying the manifest issue. The HACS job runs independently.
result: pass

### 6. GitHub Actions: both jobs pass on clean project
expected: Pushing a clean generated project (no modifications) to GitHub shows both hassfest and HACS validation jobs completing successfully with green checkmarks.
result: issue
reported: "hassfest fails: (1) http component used but not in manifest dependencies — template uses async_register_static_paths from homeassistant.components.http but manifest only lists frontend in dependencies. (2) CONFIG_SCHEMA not defined — config-entry-only integrations should set CONFIG_SCHEMA = cv.config_entry_only_config_schema. HACS fails on repo metadata (no topics/description) which is per-repo, not template."
severity: major

## Summary

total: 6
passed: 5
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "Generated project passes hassfest validation without errors on a clean push"
  status: failed
  reason: "User reported: hassfest fails: (1) http component used but not in manifest dependencies — template uses async_register_static_paths from homeassistant.components.http but manifest only lists frontend in dependencies. (2) CONFIG_SCHEMA not defined — config-entry-only integrations should set CONFIG_SCHEMA = cv.config_entry_only_config_schema. HACS fails on repo metadata (no topics/description) which is per-repo, not template."
  severity: major
  test: 6
  root_cause: "Two missing declarations in template: (1) manifest.json.jinja dependencies array lacks 'http' — hassfest checks direct imports only, frontend's transitive dep on http gives no coverage. (2) __init__.py.jinja defines async_setup but no CONFIG_SCHEMA — hassfest requires config-entry-only integrations to declare CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)."
  artifacts:
    - path: "template/custom_components/[[ project_domain ]]/manifest.json.jinja"
      issue: "dependencies array missing 'http'"
    - path: "template/custom_components/[[ project_domain ]]/__init__.py.jinja"
      issue: "No CONFIG_SCHEMA defined, no cv import"
  missing:
    - "Add 'http' to dependencies array in manifest.json.jinja"
    - "Add 'from homeassistant.helpers import config_validation as cv' import to __init__.py.jinja"
    - "Add 'CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)' after PLATFORMS declaration in __init__.py.jinja"
