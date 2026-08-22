# Phase 7: CI/CD and HACS Distribution - Research

**Researched:** 2026-02-20
**Domain:** GitHub Actions (hassfest + HACS validation), Copier template file generation, README and .gitignore content
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Single `validate.yml` workflow with hassfest + HACS action
- Copier-generated README.md with project name, description, HACS badge, basic setup instructions, card usage section
- README populated from existing copier.yml variables: `project_name`, `project_domain`, `project_description`
- README should be concise — not a full documentation site
- Standard Python + IDE + OS artifacts in .gitignore (.pyc, __pycache__, .DS_Store, .vscode, .idea, etc.)
- NO release workflow, NO version injection, NO Dependabot

### Claude's Discretion

- Validate workflow triggers (push/PR/branch selection)
- Separate jobs vs single job for hassfest + HACS action
- Action version pinning strategy
- Whether validate workflow is conditional on any copier flags (probably not — always include both)
- README section ordering and badge style
- .gitignore completeness

### Deferred Ideas (OUT OF SCOPE)

- Release workflow with tag-based zip artifact and manifest version injection
- Dependabot/Renovate for action version updates
- pytest/ruff in CI — hassfest + HACS action only
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CICD-01 | `.github/workflows/validate.yml` running `hassfest` and `hacs/action` on push and PR | Verified exact YAML from ludeeus/integration_blueprint (authoritative community template); action refs and version pins confirmed |
| CICD-02 | `.github/workflows/release.yml` producing version-tagged zip | DESCOPED per CONTEXT.md — user deferred to per-project setup; this requirement is NOT implemented in Phase 7 |
| CICD-03 | Template-generated `README.md` with HACS badge, setup instructions, card usage | README.md.jinja already exists in template/; needs audit against requirements; HACS badge URL and badge format verified |
| CICD-04 | Generated project has correct `.gitignore` for Python, IDE files, OS artifacts | .gitignore already exists in template/ (non-.jinja, static); needs audit against community standards |
</phase_requirements>

---

## Summary

Phase 7 is the final phase of this project. It adds three static-ish files to the Copier template: a `validate.yml` GitHub Actions workflow, a `README.md.jinja`, and a `.gitignore`. The context document descoped CICD-02 (release workflow) entirely — Phase 7 only needs to satisfy CICD-01, CICD-03, and CICD-04.

**Critically, two of the three output files already exist in the template directory:**
- `template/README.md.jinja` — already present with most required content
- `template/.gitignore` — already present but needs comparison against community standards

**Only `template/.github/workflows/validate.yml.jinja` is missing** (though validate.yml does not need Copier variable substitution, so it can be a static `.yml` file rather than a `.jinja` — see Architecture section).

The exact authoritative validate.yml content was sourced directly from `ludeeus/integration_blueprint`, the canonical HACS community template maintained by the creator of HACS. The workflow structure uses **two separate jobs** (one for hassfest, one for HACS action), which is the community standard pattern. Actions are pinned to specific SHA commits with version comments.

**Primary recommendation:** Create `template/.github/workflows/validate.yml` as a static (non-jinja) file using the exact pattern from integration_blueprint. Audit the existing README.md.jinja and .gitignore for gaps, apply minimal additions.

---

## Standard Stack

### Core Actions

| Action | Pinned Ref | Purpose | Why Standard |
|--------|-----------|---------|--------------|
| `actions/checkout` | `de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2` | Check out repo before hassfest | Required by hassfest job |
| `home-assistant/actions/hassfest` | `55b4a5d23e09d627c2773c2ef82afa98904d65b4 # master` | Validate manifest.json, hacs.json, integration structure | Official HA tool; validates all required fields |
| `hacs/action` | `d556e736723344f83838d08488c983a15381059a # 22.5.0` | Validate HACS-specific requirements | Required by HACS for eligible repositories |

**Source:** `ludeeus/integration_blueprint` validate.yml — the authoritative community template for HACS integrations.

Note: The HACS action (latest release: `22.5.0`, May 2024) uses a Docker image `ghcr.io/hacs/action:main` internally. The SHA pin `d556e736723344f83838d08488c983a15381059a` corresponds to 22.5.0.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SHA-pinned actions | Tag-pinned (`@v6`, `@main`) | SHA pins are more secure (supply chain protection) but require manual updates; tag pins are less secure but self-updating. Integration blueprint uses SHA pins — follow their lead. |
| Two separate jobs | Single combined job | Two jobs give independent pass/fail status in GitHub PR checks; single job hides which check failed. HACS community standard is two jobs. |

---

## Architecture Patterns

### Template File Structure to Create/Modify

```
template/
├── .github/
│   └── workflows/
│       └── validate.yml        # NEW — static (no .jinja needed, no Copier vars)
├── README.md.jinja             # EXISTS — audit for gaps
└── .gitignore                  # EXISTS — audit for gaps
```

### Pattern 1: validate.yml — Two-Job Structure

**What:** Two independent jobs in one workflow file — one for hassfest, one for HACS validation.

**When to use:** Always. This is the HACS community standard. Two jobs give separate green/red status indicators on PRs. If hassfest fails and HACS passes, you see exactly which check failed.

**Example (from ludeeus/integration_blueprint, HIGH confidence):**

```yaml
name: Validate

on:
  workflow_dispatch:
  schedule:
    - cron: "0 0 * * *"
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

permissions: {}

jobs:
  hassfest: # https://developers.home-assistant.io/blog/2020/04/16/hassfest
    name: Hassfest validation
    runs-on: ubuntu-latest
    steps:
      - name: Checkout the repository
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

      - name: Run hassfest validation
        uses: home-assistant/actions/hassfest@55b4a5d23e09d627c2773c2ef82afa98904d65b4 # master

  hacs: # https://github.com/hacs/action
    name: HACS validation
    runs-on: ubuntu-latest
    steps:
      - name: Run HACS validation
        uses: hacs/action@d556e736723344f83838d08488c983a15381059a # 22.5.0
        with:
          category: integration
          # Remove this 'ignore' key when you have added brand images for your custom integration to https://github.com/home-assistant/brands
          ignore: brands
```

**Key decisions:**
- `permissions: {}` — deny-by-default security posture; neither action needs special permissions
- `ignore: brands` — brand images registration in `home-assistant/brands` is done after initial publish; leaving this in prevents early CI failures for new projects
- `checkout` is only needed for the hassfest job (which reads files); HACS action fetches the repo itself
- Triggers: push/PR to `main` + daily cron + `workflow_dispatch` (manual trigger from GitHub UI)
- Branch filter `branches: [main]` prevents noisy CI on feature branches

### Pattern 2: validate.yml is a STATIC file (not .jinja)

**What:** `template/.github/workflows/validate.yml` — no Copier variable substitution needed.

**Why:** The workflow file contains no project-specific values — no domain, no name, no author. The HACS action infers the category and repo from GitHub context. The validate.yml is identical for every generated project.

**Therefore:** Place the file as `template/.github/workflows/validate.yml` (not `.yml.jinja`). Copier copies static files verbatim.

**Implication for Copier:** Copier handles `.github` directories as normal directories — no special configuration needed. The `.github` directory is not excluded by default. Just create `template/.github/workflows/validate.yml` and Copier copies it.

### Pattern 3: README.md.jinja — Existing File Audit

**Current state of `template/README.md.jinja`:**
```markdown
# [[ project_name ]]
[[ project_description ]]
[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2025.7%2B-blue.svg)](https://www.home-assistant.io/)
## Installation via HACS
1. Open HACS in Home Assistant
2. Go to Integrations
3. Search for "[[ project_name ]]"
4. Install and restart Home Assistant
## Manual Installation
...
## Card Usage
```yaml
type: custom:[[ project_domain | replace('_', '-') ]]-card
entity: sensor.example
header: "[[ project_name ]]"
```
## Configuration
...
## Links
- [Documentation]([[ documentation_url ]])
- [Issues]([[ issue_tracker_url ]])
## License
MIT
```

**Assessment:** The existing file FULLY satisfies CICD-03 requirements. It has:
- HACS badge (shields.io format, links to HACS integration) ✓
- HA version badge ✓
- Setup instructions (HACS + Manual) ✓
- Card usage section with `project_domain` substitution ✓
- Populated from existing copier.yml variables ✓
- Concise format ✓

**Action required:** None for functional requirements. The HACS badge links to `github.com/hacs/integration` which is standard. The badge URL format using shields.io is the community convention.

**Note:** The badge `[![HACS Default]...]` implies the integration is in the HACS default repository. For a custom/personal integration not yet in the default repo, `[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)` would be more accurate. However, the user said "HACS installation badge" without specifying, and the template is building toward HACS submission — using "Default" as the target state is acceptable. This is Claude's discretion.

### Pattern 4: .gitignore — Existing File Audit

**Current state of `template/.gitignore`:**
```
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/
*.egg
.venv/
venv/
.env
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
node_modules/
```

**Community standard comparison** (ludeeus/integration_blueprint):
```
__pycache__
.pytest*
*.egg-info
*/build/*
*/dist/*
.coverage
.vscode
coverage.xml
.ruff_cache
config/*
!config/configuration.yaml
```

**HACS integration .gitignore:**
```
__pycache__
.pytest*
*.egg-info
*/build/*
*/dist/*
.coverage
.python-version
.venv
.vscode
coverage.xml
htmlcov
outputdata
settings.json
venv
```

**Gap analysis for our template:**
- Current template: Has `*.py[cod]`, `*$py.class`, `*.swp`, `*.swo`, `*~`, `.DS_Store`, `node_modules/` — all reasonable additions
- Missing from template: `.pytest*`, `.coverage`, `coverage.xml`, `htmlcov` — test artifact directories
- The template generates `pyproject.toml` with pytest config so test artifacts are relevant
- `config/` directory exclusion (HA dev config) is relevant if user follows HA dev container pattern
- The existing template is already solid; add test artifacts for completeness

**Action required:** Minor additions — add `.pytest_cache/`, `.coverage`, `coverage.xml`, `htmlcov/` to cover pytest artifacts from the generated test suite (Phase 6 added tests).

### Anti-Patterns to Avoid

- **Using `@main` without SHA pin:** Less secure; use the SHA-pinned version from integration_blueprint as-is
- **Single job combining hassfest + HACS:** Community convention is two jobs; single job obscures which check failed
- **Adding `checkout` step to the HACS job:** The `hacs/action` Docker action fetches the repository itself — no checkout needed for that job
- **Naming the file `hassfest.yml`:** The convention in integration_blueprint is `validate.yml` which covers both checks; separate filenames are also seen in the wild but single file with two jobs is cleaner
- **Omitting `permissions: {}`:** Without this, the workflow inherits default repo permissions; explicit empty permissions is a security best practice

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Manifest field validation | Custom Python validation script | `home-assistant/actions/hassfest` | hassfest validates 20+ fields against HA's live schema including version format, dependencies, requirements, documentation URLs |
| HACS eligibility checking | Custom JSON schema validation | `hacs/action` | HACS action checks brands registry, repository description, hacs.json structure, directory layout |
| README badge generation | Custom badge URL construction | shields.io static badge URLs (already in template) | shields.io is the community standard; URLs already verified in existing template |

**Key insight:** Both validation actions are free, well-maintained, and run in seconds. The only work in this phase is writing the YAML file that invokes them.

---

## Common Pitfalls

### Pitfall 1: HACS action `ignore: brands` — Leave It In
**What goes wrong:** Without `ignore: brands`, the HACS validation fails immediately for any new integration because brand images haven't been submitted to `home-assistant/brands`.
**Why it happens:** HACS validation checks that a domain icon exists in the brands repo. New integrations don't have this until manually submitted.
**How to avoid:** Include `ignore: brands` in the validate.yml template. Add a comment explaining why.
**Warning signs:** CI fails with "domain not in brands repo" error on first push.

### Pitfall 2: Copier .github Directory — No Special Handling Needed
**What goes wrong:** Assuming `.github` directories need special copier configuration.
**Why it happens:** Some template systems exclude hidden directories by default.
**How to avoid:** Copier copies all directories in the template tree including `.github`. Just create the file at `template/.github/workflows/validate.yml` and it works.
**Warning signs:** Generated project missing `.github/workflows/validate.yml`.

### Pitfall 3: `checkout` Step in HACS Job
**What goes wrong:** Adding `actions/checkout` before `hacs/action` is redundant and wastes time.
**Why it happens:** Copy-paste from hassfest job pattern.
**How to avoid:** The `hacs/action` Docker action fetches the repository via GitHub API — no checkout needed. Integration_blueprint omits checkout from the hacs job.

### Pitfall 4: Branch Targeting Too Broad (or Too Narrow)
**What goes wrong:** `push:` with no branch filter runs CI on every branch including temporary work; `push: branches: [main]` misses PR validation if PRs come from forks with different default branches.
**How to avoid:** Use the integration_blueprint pattern: `push: branches: [main]` + `pull_request: branches: [main]` + `schedule` + `workflow_dispatch`. This matches community convention.

### Pitfall 5: HACS badge style
**What goes wrong:** Using `HACS-Default` badge when integration isn't in the HACS default repository yet creates a misleading status signal.
**How to avoid:** The existing template uses `HACS-Default`. This is aspirational (targeting HACS default submission). Both are acceptable; keep existing unless user specifies.

---

## Code Examples

### Complete validate.yml (verbatim from ludeeus/integration_blueprint — HIGH confidence)

```yaml
name: Validate

on:
  workflow_dispatch:
  schedule:
    - cron: "0 0 * * *"
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

permissions: {}

jobs:
  hassfest: # https://developers.home-assistant.io/blog/2020/04/16/hassfest
    name: Hassfest validation
    runs-on: ubuntu-latest
    steps:
      - name: Checkout the repository
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

      - name: Run hassfest validation
        uses: home-assistant/actions/hassfest@55b4a5d23e09d627c2773c2ef82afa98904d65b4 # master

  hacs: # https://github.com/hacs/action
    name: HACS validation
    runs-on: ubuntu-latest
    steps:
      - name: Run HACS validation
        uses: hacs/action@d556e736723344f83838d08488c983a15381059a # 22.5.0
        with:
          category: integration
          # Remove this 'ignore' key when you have added brand images for your custom integration to https://github.com/home-assistant/brands
          ignore: brands
```

**Source:** https://github.com/ludeeus/integration_blueprint/blob/main/.github/workflows/validate.yml (February 2026, directly fetched)

### .gitignore additions (delta from existing template)

The existing `template/.gitignore` already covers the core requirements. These additions would improve coverage for generated projects using pytest (Phase 6):

```
# Test artifacts
.pytest_cache/
.coverage
coverage.xml
htmlcov/
```

### README.md.jinja — No changes needed

The existing file at `template/README.md.jinja` fully satisfies CICD-03. No modification required.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single hassfest job only | Two jobs: hassfest + hacs/action | ~2021 | HACS action became standard validation requirement for HACS submission |
| `@main` / `@master` tag pins | SHA-pinned with comment | ~2023 (supply chain security trend) | More secure; integration_blueprint adopted SHA pins |
| `validate.yml` with `checkout` in both jobs | `checkout` only in hassfest job | Current | HACS action is Docker-based, fetches repo itself |

**Deprecated/outdated:**
- `hacs/action@v1` or other old version tags: The latest is 22.5.0 (SHA-pinned); `@main` Docker image is current
- `home-assistant/actions/hassfest@v1`: No versioned releases; `@master` (SHA-pinned) is the standard reference

---

## Phase Scope Clarification

Per CONTEXT.md, **CICD-02 is descoped**. The requirement in REQUIREMENTS.md states "release.yml producing version-tagged zip from git tag with manifest version injection" — the user explicitly deferred this to per-project setup. Phase 7 only implements:

1. `template/.github/workflows/validate.yml` — NEW file
2. `template/README.md.jinja` — EXISTS, no changes needed
3. `template/.gitignore` — EXISTS, minor additions for completeness

**Recommended plan structure:**
- Single plan (07-01) covering all three files — very small scope
- Can be structured as: create validate.yml, audit README.md.jinja (verify no changes needed), update .gitignore with test artifact patterns
- Smoke test: `copier copy` generates project with `.github/workflows/validate.yml` present

---

## Open Questions

1. **HACS badge: Default vs Custom**
   - What we know: Existing template uses `HACS-Default` (blue) badge pointing to `github.com/hacs/integration`
   - What's unclear: Should it be `HACS-Custom` (orange) for personal projects not yet in default registry?
   - Recommendation: Keep `HACS-Default` — template is aspirational (user wants to publish); both badges are cosmetic only

2. **Branch name in workflow: `main` only or also `master`?**
   - What we know: `main` is the GitHub default since 2020; integration_blueprint uses `main` only
   - What's unclear: Generated projects could be created with `master` as default branch by older git versions
   - Recommendation: Use `main` only — matches community convention; user can change if needed

3. **README `documentation_url` and `issue_tracker_url` variables**
   - What we know: These are defined in copier.yml with GitHub URL defaults
   - What's unclear: If a project doesn't have a GitHub repo yet, these render as placeholder URLs
   - Recommendation: Leave as-is — defaults are sensible; user fills in real URLs during `copier copy`

---

## Sources

### Primary (HIGH confidence)
- `ludeeus/integration_blueprint` validate.yml — exact workflow YAML fetched directly; Feb 2026
  - URL: https://github.com/ludeeus/integration_blueprint/blob/main/.github/workflows/validate.yml
- `hacs.xyz/docs/publish/action/` — official HACS action documentation, inputs verified
  - URL: https://www.hacs.xyz/docs/publish/action/
- `home-assistant/actions` README — hassfest action reference confirmed
  - URL: https://github.com/home-assistant/actions/blob/master/README.md
- `hacs/action` action.yml — all inputs verified (category, ignore, github_token, comment, repository)
  - URL: https://raw.githubusercontent.com/hacs/action/main/action.yml

### Secondary (MEDIUM confidence)
- `hacs/integration` .gitignore — community patterns for what to exclude
  - URL: https://github.com/hacs/integration/blob/main/.gitignore
- `ludeeus/integration_blueprint` .gitignore — minimal community-standard .gitignore
  - URL: https://github.com/ludeeus/integration_blueprint/blob/main/.gitignore
- deepwiki.com/copier-org/copier — confirmed `.github` directories are included normally in Copier templates

### Tertiary (LOW confidence)
- None — all critical claims verified with primary sources

---

## Metadata

**Confidence breakdown:**
- validate.yml content: HIGH — sourced directly from authoritative template; verified against HACS docs
- Action version SHA pins: HIGH — copied verbatim from integration_blueprint; correct as of Feb 2026
- README.md.jinja: HIGH — existing file verified against requirements; no changes needed
- .gitignore additions: MEDIUM — based on community patterns; additions are conservative
- Copier .github directory handling: MEDIUM — verified via deepwiki documentation; consistent with Copier's stated behavior

**Research date:** 2026-02-20
**Valid until:** 2026-05-20 (stable ecosystem; action SHA pins may go stale if actions are updated, but workflow structure is stable)
