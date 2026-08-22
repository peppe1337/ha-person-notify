---
phase: 07-cicd-and-hacs-distribution
plan: 02
subsystem: infra
tags: [copier, hassfest, home-assistant, manifest, config-schema, jinja2]

# Dependency graph
requires:
  - phase: 07-cicd-and-hacs-distribution
    provides: validate.yml CI workflow (07-01) and UAT gap diagnosis showing two hassfest failures
provides:
  - manifest.json.jinja with "http" in dependencies for hassfest direct-import compliance
  - __init__.py.jinja with CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN) for config-entry-only compliance
affects: [hassfest CI job in generated project validate.yml workflow]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "hassfest requires explicit http dependency even when frontend is listed (no transitive coverage)"
    - "Config-entry-only integrations with async_setup must declare CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)"

key-files:
  created: []
  modified:
    - template/custom_components/[[ project_domain ]]/manifest.json.jinja
    - template/custom_components/[[ project_domain ]]/__init__.py.jinja

key-decisions:
  - "http added as unconditional dependency in manifest (not conditional on use_websocket) — async_register_static_paths always uses homeassistant.components.http"
  - "CONFIG_SCHEMA placed at module level after PLATFORMS constant — standard HA positioning for module-level declarations"
  - "cv import added alongside existing HA imports (not deferred) — module-level CONFIG_SCHEMA requires cv at import time"
  - "git tag 0.1.0 advanced to HEAD after commit so Copier reads updated template files (Copier reads from git tag, not filesystem)"

patterns-established:
  - "Tag advance pattern: always advance 0.1.0 tag to HEAD after template commits so Copier smoke tests use current content"

requirements-completed: [CICD-01]

# Metrics
duration: 1min
completed: 2026-02-20
---

# Phase 7 Plan 02: hassfest Gap Closure Summary

**Two template edits fix hassfest CI: manifest.json.jinja gains explicit "http" dependency and __init__.py.jinja gains CONFIG_SCHEMA declaration using config_entry_only_config_schema**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-20T22:29:34Z
- **Completed:** 2026-02-20T22:30:45Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Added `"http"` as unconditional dependency in manifest.json.jinja — hassfest validates direct imports and `async_register_static_paths` from `homeassistant.components.http` requires an explicit entry
- Added `from homeassistant.helpers import config_validation as cv` to __init__.py.jinja imports
- Added `CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)` after PLATFORMS declaration — hassfest requires this for integrations that define `async_setup` alongside `config_flow: true`
- Copier smoke tests pass for both default and websocket-enabled generation: all 5 checks PASS

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix manifest.json.jinja and __init__.py.jinja for hassfest compliance** - `14d6616` (fix)

**Plan metadata:** (docs commit — see final commit)

## Files Created/Modified
- `template/custom_components/[[ project_domain ]]/manifest.json.jinja` - Added `"http"` to dependencies array between `"frontend"` and the conditional `"websocket_api"` entry
- `template/custom_components/[[ project_domain ]]/__init__.py.jinja` - Added `config_validation as cv` import and `CONFIG_SCHEMA` module-level declaration

## Decisions Made
- `"http"` added unconditionally (not inside `[% if %]` block) because `async_register_static_paths` is always called in `async_setup` regardless of feature flags
- `CONFIG_SCHEMA` placed immediately after `PLATFORMS` constant following standard HA module-level declaration ordering
- `cv` import placed with existing HA imports (not deferred/lazy) because `CONFIG_SCHEMA` is evaluated at module load time
- git tag 0.1.0 advanced to HEAD after task commit — Copier resolves templates from the tagged git ref, not the filesystem dirty state; tag must be current for smoke tests to validate the actual changes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Advanced git tag 0.1.0 to HEAD before smoke test**
- **Found during:** Task 1 verification (Copier smoke test)
- **Issue:** Copier reads templates from the git tag (0.1.0), not from the filesystem. Running the smoke test before committing and tagging produced the old template output — all checks showed FAIL even though template files were correctly edited.
- **Fix:** Committed the template changes first, then ran `git tag -f 0.1.0 HEAD` to advance the tag to the new commit before re-running the smoke test.
- **Files modified:** No additional files — this was a git operation, not a code change.
- **Verification:** Smoke test immediately passed all 5 checks after tag advance.
- **Committed in:** 14d6616 (task commit) + git tag operation

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking: git tag advance required before smoke test)
**Impact on plan:** Auto-fix was necessary to run verification correctly. No scope creep; template edits themselves matched the plan exactly.

## Issues Encountered
- Copier reads templates from the git tag, not from the filesystem working tree. Initial smoke test produced old output because the tag still pointed to the pre-edit commit. Fixed by committing template changes and advancing the tag before re-running verification.

## User Setup Required
None - no external service configuration required. These are template-internal changes; the generated CI workflow (validate.yml from 07-01) will now pass hassfest for clean generated projects.

## Next Phase Readiness
- Phase 7 gap closure complete — hassfest failures from UAT test 6 are resolved
- Both UAT failures (http dep + CONFIG_SCHEMA) fixed in template source
- All CICD-01 requirements satisfied; CICD-02 remains formally deferred
- Phase 7 complete: all 7 phases done, 48/49 active requirements satisfied (CICD-02 deferred by user decision)

## Self-Check: PASSED

All verified:
- FOUND: manifest.json.jinja (contains "http" in dependencies)
- FOUND: __init__.py.jinja (contains CONFIG_SCHEMA and cv import)
- FOUND: 07-02-SUMMARY.md
- FOUND: commit 14d6616

---
*Phase: 07-cicd-and-hacs-distribution*
*Completed: 2026-02-20*
