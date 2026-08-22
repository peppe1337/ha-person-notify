# Phase 7: CI/CD and HACS Distribution - Context

**Gathered:** 2026-02-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate .gitignore, README.md, and a single validate workflow for HACS compliance. No release automation, no version injection, no Dependabot. Keep it minimal — this template serves 3 personal projects, not a community framework.

Descoped from original roadmap: release.yml workflow, tag-based version injection into manifest.json. User will set up release automation per-project when ready to publish to HACS.

</domain>

<decisions>
## Implementation Decisions

### Validate workflow
- Single `validate.yml` workflow with hassfest + HACS action
- Triggers, job layout, action version pinning, and conditionality are Claude's discretion — follow HACS community conventions

### README template
- Copier-generated README.md with project name, description, HACS badge, basic setup instructions, card usage section
- Populated from existing copier.yml variables (project_name, project_domain, project_description)
- Keep it concise — not a full documentation site

### .gitignore
- Standard Python + IDE + OS artifacts (.pyc, __pycache__, .DS_Store, .vscode, .idea, etc.)
- Nothing fancy

### Claude's Discretion
- Validate workflow triggers (push/PR/branch selection)
- Separate jobs vs single job for hassfest + HACS action
- Action version pinning strategy
- Whether validate workflow is conditional on any copier flags (probably not — always include both)
- README section ordering and badge style
- .gitignore completeness

</decisions>

<specifics>
## Specific Ideas

- User explicitly wants to avoid overengineering — this is a personal template for 3 HACS integrations, not a community-facing template framework
- Release workflow and version injection can be added per-project later; don't template them
- The goal is "solid base to build from with parity and ease of updating together"

</specifics>

<deferred>
## Deferred Ideas

- Release workflow with tag-based zip artifact and manifest version injection — user will handle per-project
- Dependabot/Renovate for action version updates — not needed for 3 personal projects
- pytest/ruff in CI — user chose hassfest + HACS action only

</deferred>

---

*Phase: 07-cicd-and-hacs-distribution*
*Context gathered: 2026-02-20*
