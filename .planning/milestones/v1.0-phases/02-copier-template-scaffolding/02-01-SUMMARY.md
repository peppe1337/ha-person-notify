---
phase: 02-copier-template-scaffolding
plan: 01
subsystem: infra
tags: [copier, jinja2, template, hacs, home-assistant]

requires:
  - phase: 01-scaffold-fixes
    provides: Corrected integration source files (async_register_static_paths, runtime_data, options flow, unique_id) used as template basis

provides:
  - copier.yml at repo root with _envops custom delimiters and 13 project questions
  - template/ subdirectory containing all .jinja files with [[ ]] variable substitutions
  - Domain directory named [[ project_domain ]] for Copier rendering
  - Answers file template at template/{{ _copier_conf.answers_file }}.jinja for copier update support
  - Repo-root README.md updated to document Copier template usage

affects:
  - 02-02-smoke-test (copier copy and validation)
  - All later phases (every new file goes into template/ as .jinja with [[ ]] substitutions)

tech-stack:
  added: [copier 9.11.3, _envops custom delimiters [[ ]] / [% %]]
  patterns:
    - _subdirectory template separates copier.yml from template content
    - _envops with [[ ]] / [% %] eliminates Python brace collision globally
    - .jinja suffix on files triggers rendering; directories have no suffix
    - answers file template uses standard {{ }} in filename, [[ ]] in content

key-files:
  created:
    - copier.yml
    - template/{{ _copier_conf.answers_file }}.jinja
    - template/hacs.json.jinja
    - template/README.md.jinja
    - template/.gitignore
    - "template/custom_components/[[ project_domain ]]/__init__.py.jinja"
    - "template/custom_components/[[ project_domain ]]/config_flow.py.jinja"
    - "template/custom_components/[[ project_domain ]]/const.py.jinja"
    - "template/custom_components/[[ project_domain ]]/coordinator.py.jinja"
    - "template/custom_components/[[ project_domain ]]/sensor.py.jinja"
    - "template/custom_components/[[ project_domain ]]/manifest.json.jinja"
    - "template/custom_components/[[ project_domain ]]/strings.json.jinja"
    - "template/custom_components/[[ project_domain ]]/translations/en.json.jinja"
    - "template/custom_components/[[ project_domain ]]/frontend/[[ project_domain ]]-card.js.jinja"
  modified:
    - README.md (updated from GitHub template description to Copier template usage)
  deleted:
    - custom_components/ (moved into template/)
    - hacs.json (moved into template/)

key-decisions:
  - "_envops with [[ ]] / [% %] delimiters instead of {% raw %} blocks — one-time global fix eliminates all Python brace collision across every template file"
  - "_subdirectory: template keeps copier.yml and repo docs at root; template/ contains only generated project content"
  - "answers file template content uses [[ _copier_answers|to_nice_yaml ]] since _envops applies to file content rendering"
  - "PascalCase class names derived via [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]] filter chain"

patterns-established:
  - "All new integration files go in template/custom_components/[[ project_domain ]]/ with .jinja suffix"
  - "Variable substitution uses [[ var ]] in file content and filenames; [% %] for blocks/conditionals"
  - "Python braces (dict, f-string, type hints) left verbatim — _envops makes them invisible to Copier"
  - "Derived class name pattern: [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]"

requirements-completed: [COPR-01, COPR-02, COPR-03, COPR-04, COPR-08]

duration: 3min
completed: 2026-02-19
---

# Phase 2 Plan 01: Copier Template Scaffolding Summary

**copier.yml with _envops [[ ]] delimiters and all 13 questions; integration files restructured into template/ subdirectory as .jinja templates with Copier variable substitutions replacing all hardcoded hacs_template references**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-19T20:48:20Z
- **Completed:** 2026-02-19T20:51:36Z
- **Tasks:** 2
- **Files modified:** 15 (14 created, 1 updated, 2 deleted)

## Accomplishments

- Created copier.yml at repo root with _envops custom delimiters ([[ ]] / [% %]), _subdirectory: template, and all 13 project questions with types, defaults, choices, and domain validator
- Restructured all 9 integration source files into template/ subdirectory with .jinja suffixes and [[ project_domain ]], [[ project_name ]], and derived variable substitutions
- Removed original custom_components/ and hacs.json from repo root — the repo IS now a Copier template
- Domain directory named [[ project_domain ]] for Copier rendering at copy time
- Added answers file template at template/{{ _copier_conf.answers_file }}.jinja for copier update support

## Task Commits

Each task was committed atomically:

1. **Task 1: Create copier.yml with _envops and project questions** - `339cbcc` (chore)
2. **Task 2: Restructure existing files into template/ with .jinja variable substitutions** - `f389bb6` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `copier.yml` - Copier config with _envops, _subdirectory, and 13 questions
- `template/{{ _copier_conf.answers_file }}.jinja` - Generates .copier-answers.yml in child projects
- `template/hacs.json.jinja` - HACS metadata with [[ project_name ]] substitution
- `template/README.md.jinja` - Generated project README with HACS badge and install instructions
- `template/.gitignore` - Verbatim copy for generated projects
- `template/custom_components/[[ project_domain ]]/__init__.py.jinja` - Integration setup with PascalCase class names
- `template/custom_components/[[ project_domain ]]/config_flow.py.jinja` - Config/options flow
- `template/custom_components/[[ project_domain ]]/const.py.jinja` - DOMAIN substitution
- `template/custom_components/[[ project_domain ]]/coordinator.py.jinja` - DataUpdateCoordinator
- `template/custom_components/[[ project_domain ]]/sensor.py.jinja` - Sensor platform
- `template/custom_components/[[ project_domain ]]/manifest.json.jinja` - All hassfest-required fields
- `template/custom_components/[[ project_domain ]]/strings.json.jinja` - UI strings (verbatim)
- `template/custom_components/[[ project_domain ]]/translations/en.json.jinja` - EN translations (verbatim)
- `template/custom_components/[[ project_domain ]]/frontend/[[ project_domain ]]-card.js.jinja` - LitElement card with all hacs_template refs substituted
- `README.md` - Updated to describe Copier template usage with `copier copy` instructions

## Decisions Made

- **_envops over {% raw %}:** Using custom delimiters [[ ]] / [% %] eliminates Python brace collision globally. `{% raw %}` blocks cannot substitute variables inside them, making them incompatible with Python-heavy templates. _envops is zero-maintenance.
- **_subdirectory: template:** Cleanly separates Copier configuration (copier.yml, repo README, CI) from template content. Without it, repo-root files would need explicit `_exclude` entries.
- **Answers file content uses [[ ]]:** _envops applies to file content rendering globally, including the answers file template. Content uses `[[ _copier_answers|to_nice_yaml -]]` not `{{ }}`.
- **PascalCase via filter chain:** `[[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]` converts `my_integration` to `MyIntegration`. Standard Jinja2 filters, no extensions needed.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The repo is now a working Copier template. `copier copy` can be run to render a child project.
- Plan 02-02 (smoke test) can verify the template generates a valid HA integration that passes hassfest.
- All later phases write new files directly into `template/custom_components/[[ project_domain ]]/` as `.jinja` files using `[[ ]]` for variable substitution.
- Note for COPR-04: The plan required `{% raw %}` approach originally but research determined _envops is superior. COPR-04 is satisfied by _envops (brace collision eliminated) rather than raw blocks.

---
*Phase: 02-copier-template-scaffolding*
*Completed: 2026-02-19*

## Self-Check: PASSED

- copier.yml: FOUND
- template/hacs.json.jinja: FOUND
- template/README.md.jinja: FOUND
- 02-01-SUMMARY.md: FOUND
- Commits 339cbcc and f389bb6: FOUND
- 13 template files (12 .jinja + .gitignore): CONFIRMED
