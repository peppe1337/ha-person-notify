---
phase: 02-copier-template-scaffolding
plan: 02
subsystem: infra
tags: [copier, jinja2, conditional-files, template, smoke-test, home-assistant]

requires:
  - phase: 02-01-copier-template-scaffolding
    provides: copier.yml with _envops [[ ]] delimiters and 13 questions; template/ subdirectory with all .jinja integration files

provides:
  - Three conditional file templates (websocket.py, services.py, coordinator_secondary.py) with [% if %] filename pattern
  - Verified copier copy pipeline: domain substitution in paths and file content, all hassfest-required manifest fields
  - Verified conditional file inclusion/exclusion based on boolean flags
  - Verified .copier-answers.yml generation with DO NOT EDIT warning and _commit version
  - Verified copier update 3-way merge against tagged template version (0.1.0 tag)
  - Corrected conditional filename pattern: [% if cond %]name.py[% endif %].jinja (not [% if cond %]name[% endif %].py.jinja)
  - Corrected answers file template delimiter: [[ _copier_conf.answers_file ]].jinja (not {{ }}.jinja)

affects:
  - Phase 3 and all subsequent phases (conditional file pattern established; correct copier pipeline verified)
  - Phase 5 (WebSocket, services, secondary coordinator stubs ready for implementation)

tech-stack:
  added: [copier 9.11.3 (installed in venv)]
  patterns:
    - "Conditional file pattern: [% if cond %]filename.py[% endif %].jinja — entire name+extension inside [% if %] block, only .jinja suffix outside"
    - "When condition is false, Jinja2 renders filename to empty string; Copier skips files with empty rendered path"
    - "Answers file template uses [[ _copier_conf.answers_file ]].jinja — _envops [[ ]] delimiters apply to filename rendering"
    - "copier update requires git tag in template repo to anchor _commit version for 3-way merge"

key-files:
  created:
    - "template/custom_components/[[ project_domain ]]/[% if use_websocket %]websocket.py[% endif %].jinja"
    - "template/custom_components/[[ project_domain ]]/[% if use_services %]services.py[% endif %].jinja"
    - "template/custom_components/[[ project_domain ]]/[% if use_secondary_coordinator %]coordinator_secondary.py[% endif %].jinja"
    - "template/[[ _copier_conf.answers_file ]].jinja (renamed from {{ _copier_conf.answers_file }}.jinja)"
  modified: []

key-decisions:
  - "Correct copier conditional filename pattern is [% if cond %]name.py[% endif %].jinja — the ENTIRE base+extension must be inside the [% if %] block; when false, the expression renders to empty string and copier skips the file"
  - "Wrong pattern [% if cond %]name[% endif %].py.jinja renders to .py (non-empty) when false — copier creates .py file instead of skipping"
  - "Answers file template must use [[ ]] delimiters in filename: [[ _copier_conf.answers_file ]].jinja — _envops changes apply globally including filename rendering; {{ }} is not rendered with custom envops"
  - "copier update requires git tag 0.1.0 in the template repo — without it, _commit cannot be anchored and update fails"

patterns-established:
  - "Conditional file pattern: wrap ENTIRE filename (name.ext) in [% if condition %]...[% endif %], keep only .jinja suffix outside"
  - "Phase 5 optional module stubs (websocket, services, secondary coordinator) exist as placeholder .jinja files"

requirements-completed: [COPR-05, COPR-06, COPR-07]

duration: 5min
completed: 2026-02-19
---

# Phase 2 Plan 02: Copier Smoke Test Summary

**Conditional file stubs for websocket/services/secondary coordinator plus full end-to-end copier copy/update pipeline verification — discovered and fixed two filename pattern bugs (wrong conditional pattern and wrong delimiter in answers file template)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-19T20:55:37Z
- **Completed:** 2026-02-19T21:00:55Z
- **Tasks:** 2
- **Files modified:** 4 (3 conditional stubs created, 1 answers file template renamed; 4 renames for pattern fixes)

## Accomplishments

- Created three conditional file templates for Phase 5 optional modules (websocket.py, services.py, coordinator_secondary.py) with correct `[% if condition %]filename.py[% endif %].jinja` filename pattern
- Installed copier 9.11.3 via existing mediaparser venv and verified full `copier copy` pipeline: domain substitution in directory paths and file content, all 9 hassfest-required manifest fields, Python syntax validity for all generated .py files
- Verified conditional file inclusion (all three appear when flags=true) and exclusion (none appear when flags=false)
- Verified `.copier-answers.yml` generation with `# Changes here will be overwritten by Copier; NEVER EDIT MANUALLY` warning and `_commit: 0.1.0`
- Verified `copier update --defaults` completes successfully against tagged template version

## Task Commits

Each task was committed atomically:

1. **Task 1: Create conditional file templates for optional modules** - `0f0a627` (feat)
2. **Task 2 (deviation fix): Fix conditional filename and answers file delimiter patterns** - `27b3384` (fix)

Task 2 is a verification/smoke-test task. No separate commit needed — the deviation fix IS the task 2 work product.

## Files Created/Modified

- `template/custom_components/[[ project_domain ]]/[% if use_websocket %]websocket.py[% endif %].jinja` - WebSocket API placeholder stub for Phase 5
- `template/custom_components/[[ project_domain ]]/[% if use_services %]services.py[% endif %].jinja` - Service handlers placeholder stub for Phase 5
- `template/custom_components/[[ project_domain ]]/[% if use_secondary_coordinator %]coordinator_secondary.py[% endif %].jinja` - Secondary coordinator placeholder stub for Phase 5
- `template/[[ _copier_conf.answers_file ]].jinja` - Renamed from `{{ _copier_conf.answers_file }}.jinja` to use correct `[[ ]]` envops delimiters

## Decisions Made

- **Correct conditional filename pattern discovered:** `[% if cond %]name.py[% endif %].jinja` — the ENTIRE base+extension must be inside the `[% if %]` block. When false, Jinja2 renders the expression to empty string `""`. Copier's `_render_parts()` skips path components that render to empty string. The plan's documented pattern (`[% if cond %]name[% endif %].py.jinja`) renders to `.py` when false (non-empty), causing copier to create `.py` file.
- **Answers file template delimiter:** Must use `[[ _copier_conf.answers_file ]].jinja` because `_envops` changes apply globally including filename rendering. The original `{{ _copier_conf.answers_file }}.jinja` was kept as-is (literal filename in output) because `{{ }}` is not the configured delimiter.
- **Tag must be on fixed commit:** The `0.1.0` git tag was moved to the post-fix commit so copier's `_commit` anchors to the correct (working) template state.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wrong copier conditional filename pattern**
- **Found during:** Task 2 (smoke test — copier copy with defaults)
- **Issue:** Template files named `[% if cond %]name[% endif %].py.jinja` render to `.py` when condition is false (non-empty string → copier creates file). Expected behavior: skip file when condition is false.
- **Fix:** Renamed all three conditional template files to `[% if cond %]name.py[% endif %].jinja` — entire base+extension inside the block. When false, renders to `""` → copier skips.
- **Files modified:** All three conditional .jinja template files (git rename)
- **Verification:** `copier copy --defaults` (all booleans false) → no websocket.py, services.py, coordinator_secondary.py in output. `copier copy` with `use_websocket=true,use_services=true,use_secondary_coordinator=true` → all three files present.
- **Committed in:** `27b3384`

**2. [Rule 1 - Bug] Answers file template uses wrong delimiter in filename**
- **Found during:** Task 2 (smoke test — checking generated output)
- **Issue:** Template file `template/{{ _copier_conf.answers_file }}.jinja` uses standard Jinja2 `{{ }}` delimiter. With `_envops` custom delimiters (`[[ ]]`), the `{{ }}` in the filename is NOT rendered — copier creates a file literally named `{{ _copier_conf.answers_file }}` in the output directory.
- **Fix:** Renamed to `template/[[ _copier_conf.answers_file ]].jinja` so the filename is rendered using the configured `[[ ]]` delimiter → creates `.copier-answers.yml`.
- **Files modified:** `template/[[ _copier_conf.answers_file ]].jinja` (git rename from `{{ _copier_conf.answers_file }}.jinja`)
- **Verification:** `copier copy` output contains `.copier-answers.yml` with `# Changes here will be overwritten by Copier; NEVER EDIT MANUALLY` comment.
- **Committed in:** `27b3384`

---

**Total deviations:** 2 auto-fixed (both Rule 1 - Bug)
**Impact on plan:** Both fixes essential for correctness — the wrong conditional pattern defeats the purpose of conditional files; the wrong answers file delimiter breaks `copier update`. No scope creep.

## Issues Encountered

- `copier` not in system PATH. Installed via `pip install copier` into an existing Python venv (`/home/dab/mediaparser-venv`). System Python has no `pip` module (Debian/Ubuntu disabled ensurepip). Used the venv's pip to install copier 9.11.3 and invoked as `/home/dab/mediaparser-venv/bin/copier`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The Copier template pipeline is fully verified: `copier copy` → valid HA integration with domain substitution, all hassfest fields, valid Python syntax
- Conditional files are proven to work: include when true, exclude when false
- The pattern for Phase 5 optional modules is established: add `[% if use_feature %]feature.py[% endif %].jinja` to the domain directory
- Phase 3 (GitHub Actions CI) can proceed — the template structure is stable
- Phase 5 stubs exist and are wired into copier.yml questions (`use_websocket`, `use_services`, `use_secondary_coordinator`)

---
*Phase: 02-copier-template-scaffolding*
*Completed: 2026-02-19*

## Self-Check: PASSED

- websocket.py stub: FOUND
- services.py stub: FOUND
- coordinator_secondary.py stub: FOUND
- answers file template [[ _copier_conf.answers_file ]].jinja: FOUND
- 02-02-SUMMARY.md: FOUND
- Commit 0f0a627 (feat: conditional stubs): FOUND
- Commit 27b3384 (fix: filename patterns): FOUND
- Git tag 0.1.0: FOUND
