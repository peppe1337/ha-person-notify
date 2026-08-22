---
phase: 07-cicd-and-hacs-distribution
plan: 01
subsystem: cicd
tags: [github-actions, hacs, hassfest, copier, gitignore]

# Dependency graph
requires:
  - phase: 06-test-scaffold
    provides: pytest infrastructure and test templates that generate .pytest_cache artifacts
  - phase: 02-copier-template-scaffolding
    provides: Copier template structure with _subdirectory, _envops, and static file handling
provides:
  - template/.github/workflows/validate.yml — static two-job CI workflow (hassfest + HACS action)
  - template/.gitignore updated with test artifact exclusions (.pytest_cache, .coverage, coverage.xml, htmlcov)
  - Generated projects inherit HACS-compliant CI and complete artifact exclusions out of the box
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Static template files (no .jinja suffix) are copied verbatim by Copier — use for files with no project-specific variables"
    - "SHA-pinned GitHub Actions with version comments — supply chain security best practice from integration_blueprint"
    - "Two-job validate.yml pattern: separate hassfest and HACS jobs for independent pass/fail status on PRs"
    - "permissions: {} deny-by-default security posture for GitHub Actions workflows"
    - "ignore: brands in HACS action — prevents CI failure before brand images submitted to home-assistant/brands"

key-files:
  created:
    - template/.github/workflows/validate.yml
  modified:
    - template/.gitignore

key-decisions:
  - "validate.yml is a STATIC file (no .jinja suffix) — workflow contains zero Copier variables, identical for every generated project"
  - "CICD-02 (release workflow) remains descoped per prior user decision — no release.yml created"
  - "README.md.jinja verified as already satisfying CICD-03 — no modification required"
  - "ignore: brands included in HACS action to prevent early CI failures for new integrations not yet in brands repo"
  - "checkout step only in hassfest job — hacs/action is Docker-based and fetches repo itself; checkout is redundant and wasteful in HACS job"

patterns-established:
  - "Static template files: files in template/ without .jinja suffix are copied verbatim by Copier"

requirements-completed: [CICD-01, CICD-02, CICD-03, CICD-04]

# Metrics
duration: 1min
completed: 2026-02-20
---

# Phase 7 Plan 01: CI/CD and HACS Distribution Summary

**HACS-compliant validate.yml CI workflow (SHA-pinned hassfest + HACS action, two-job pattern) added to Copier template; .gitignore updated with pytest artifact exclusions**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-20T19:44:05Z
- **Completed:** 2026-02-20T19:45:31Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created `template/.github/workflows/validate.yml` as a static (non-.jinja) file with the exact two-job pattern from `ludeeus/integration_blueprint` — the authoritative HACS community template
- Updated `template/.gitignore` with test artifact exclusions (.pytest_cache/, .coverage, coverage.xml, htmlcov/) to cover pytest artifacts from Phase 6 test scaffold
- Copier smoke test confirmed generated project includes .github/workflows/validate.yml (verbatim copy), updated .gitignore, and rendered README.md with HACS badge and Copier variable substitution — all 8 checks passed

## Task Commits

Each task was committed atomically:

1. **Task 1: Create validate.yml workflow and update .gitignore** - `9d72646` (feat)
2. **Task 2: Copier smoke test — validate.yml in generated output** - verification only, no file changes

**Plan metadata:** (docs commit — created after SUMMARY.md)

## Files Created/Modified
- `template/.github/workflows/validate.yml` - Static GitHub Actions workflow: two jobs (hassfest + HACS action), SHA-pinned actions, permissions: {}, ignore: brands
- `template/.gitignore` - Added test artifact exclusions: .pytest_cache/, .coverage, coverage.xml, htmlcov/

## Decisions Made
- `validate.yml` is a static file (no .jinja suffix) — the workflow contains zero Copier variables and is identical for every generated project. Copier copies static files verbatim.
- CICD-02 (release workflow) remains descoped per prior user decision — no release.yml was created.
- `template/README.md.jinja` was verified as already satisfying CICD-03 (HACS badge, setup instructions, card usage with domain substitution) — no changes required.
- `ignore: brands` included in HACS action — prevents CI failure for new integrations that haven't yet submitted brand images to home-assistant/brands.
- `checkout` step only in `hassfest` job — `hacs/action` is Docker-based and fetches the repo internally; adding checkout to the HACS job would be redundant per integration_blueprint pattern.

## Deviations from Plan

None — plan executed exactly as written. The only deviation from a strict reading of the task spec was including the inline comments in validate.yml (the `# https://...` job key comments from integration_blueprint) — these are present in the research document's authoritative source and improve maintainability.

## Issues Encountered
- `copier` binary not on PATH in shell environment — found at `/home/dab/mediaparser-venv/bin/copier` via filesystem search. Used full path for smoke test. Task 2 required adding `--data author_name="testuser"` because `author_name` is a required question with no default in copier.yml.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Phase 7 is the final phase of this project. All 4 CICD requirements are satisfied:
- CICD-01: validate.yml with hassfest + HACS action — COMPLETE
- CICD-02: release workflow — DESCOPED per user decision (deferred to per-project setup)
- CICD-03: README.md.jinja with HACS badge — already satisfied in prior phase
- CICD-04: .gitignore with Python/IDE/OS/test artifacts — COMPLETE

The Copier template is now feature-complete. Generated child projects inherit: backend integration (Phase 1-3), Lovelace card (Phase 4), conditional patterns (Phase 5), test scaffold (Phase 6), and CI/CD workflow (Phase 7).

---
*Phase: 07-cicd-and-hacs-distribution*
*Completed: 2026-02-20*
