# Phase 2: Copier Template Scaffolding - Research

**Researched:** 2026-02-19
**Domain:** Copier template tool — copier.yml question syntax, Jinja2/Python brace collision, conditional file generation, update mechanism, hassfest validation
**Confidence:** HIGH (Copier docs verified via official readthedocs.io; hassfest requirements verified via developers.home-assistant.io)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| COPR-01 | `copier.yml` defines questions for project domain, name, author, description, IoT Class, and conditional feature flags | Verified: complete question syntax documented — type, default, choices, help, when, validator, multiselect fields. IoT class uses `choices:` with valid HA values. |
| COPR-02 | Template uses Jinja2 variable substitution for domain name in all files (manifest, const, hacs.json, strings, card JS, etc.) | Verified: `.jinja` suffix on files triggers Jinja rendering; `{{ project_domain }}` substitution works in file content. Non-`.jinja` files are copied verbatim. |
| COPR-03 | Template directory uses Copier Jinja2 naming (`custom_components/{{ project_domain }}/`) for domain directory | Verified: directory names support full Jinja2 expressions; `{{ project_domain }}/` renders to the domain value. No `.jinja` suffix on directories. |
| COPR-04 | All Python template files use `{% raw %}...{% endraw %}` to prevent Jinja2/Python brace collision | Verified: `{% raw %}` is the standard Jinja2 mechanism; each `.jinja` Python file wraps its content. Alternative: `_envops` custom delimiters (`[[ ]]`) avoid needing raw blocks at all — this is the superior approach for files with heavy brace usage. |
| COPR-05 | Conditional files (websocket.py, services.py, coordinator_secondary.py, multi-step config_flow.py) are generated or excluded based on Copier question answers | Verified: `{% if condition %}filename{% endif %}.jinja` pattern — empty filename after render causes file to be skipped. `.jinja` suffix MUST appear outside the condition. |
| COPR-06 | `copier copy` generates a valid HA integration that passes `hassfest` without manual edits | Verified: hassfest checks manifest.json required fields (domain, name, codeowners, documentation, iot_class, integration_type, requirements, dependencies), strings.json/translations key alignment, config_flow declaration. All must be correct in generated output. |
| COPR-07 | `copier update` propagates template changes to existing child projects via 3-way merge | Verified: 3-way merge documented — regenerates fresh project, diffs against current, reapplies custom changes. Requires git tags on template repo and `.copier-answers.yml` in child. |
| COPR-08 | `.copier-answers.yml` is committed in generated projects with inline warning against manual edits | Verified: generate via `{{ _copier_conf.answers_file }}.jinja` template file containing the standard warning comment + `{{ _copier_answers|to_nice_yaml -}}`. |
</phase_requirements>

---

## Summary

Copier 9.11.3 (current as of 2026-01-23, requires Python ≥ 3.10 and Git ≥ 2.27) is a well-documented, production-ready template tool. The core scaffolding work for this phase is mechanically straightforward: move the existing `custom_components/hacs_template/` directory tree into a template subdirectory, rename files to add the `.jinja` suffix where variable substitution is needed, rename the domain directory using Jinja2 syntax, write `copier.yml` with the required questions, and handle the Jinja2/Python brace collision in Python source files.

The single most important architectural decision for this phase is **how to handle Python brace collision** (Python dict literals, f-strings, and type hints all use `{` and `}` which Jinja2 would try to interpret). Two approaches exist: `{% raw %}...{% endraw %}` wrapping per-file, or `_envops` custom delimiters that change Copier's template syntax globally from `{{ }}` to `[[ ]]`. The `_envops` approach eliminates all escaping concerns across every Python file and is the correct choice when templates contain files with substantial brace usage. The `{% raw %}` approach is only practical when a file has one or two variable substitutions surrounded by otherwise brace-free content. For this project's Python files — which contain type annotations (`dict[str, Any]`), f-strings, dataclass fields, and dict literals throughout — `_envops` with `[[ ]]` delimiters is the clearly superior choice.

The `copier update` 3-way merge mechanism requires that the template repository has proper git version tags (PEP 440 format) and that generated child projects commit `.copier-answers.yml`. The hassfest validation requirements are fully known: seven required manifest fields plus strings/translations alignment plus config_flow declaration. All can be ensured by the template if the question defaults and Jinja substitutions are constructed correctly.

**Primary recommendation:** Use `_envops` custom delimiters (`[[ ]]` / `[% %]`) in `copier.yml` to eliminate Python brace collision entirely. Structure the template under a `template/` subdirectory (`_subdirectory: template`) to keep `copier.yml`, docs, and CI at the repo root. Use `{% if condition %}filename{% endif %}.jinja` for conditional files.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `copier` | 9.11.3 (2026-01-23) | Template generation and update | Current release; official tool; handles update via 3-way merge |
| `jinja2` | Bundled with copier | Template rendering engine | Copier uses Jinja2 internally; `{% raw %}`, filters, conditionals all standard Jinja2 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `copier` `_envops` | Built-in setting | Customize Jinja2 delimiters | Always use for templates with Python files to avoid brace collision |
| `copier` `_subdirectory` | Built-in setting | Separate template content from repo metadata | Always use to keep `copier.yml` and CI at repo root, template content in `template/` |
| `copier` `_tasks` | Built-in setting | Post-generation scripts | Use for `git init` or file permission tasks if needed post-copy |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `_envops` custom delimiters | `{% raw %}...{% endraw %}` per Python file | Raw blocks work but require wrapping every Python file; `_envops` is a one-time global fix |
| `_templates_suffix: .jinja` (default) | `_templates_suffix: ""` (render all files) | Empty suffix renders every non-excluded file — risky; default `.jinja` opt-in is safer |
| `_subdirectory: template` | Flat repo (copier.yml at root next to template files) | Flat layout mixes template metadata with template content; `_subdirectory` cleanly separates them |

**Installation:**
```bash
uv tool install copier
# or
pipx install copier
```

---

## Architecture Patterns

### Recommended Template Repository Structure

```
ha-hacs-template/                          # repo root
├── copier.yml                             # questions + config (NOT inside template/)
├── README.md                              # template repo documentation
├── .github/workflows/                     # CI for the template repo itself
│   └── validate.yml
└── template/                              # _subdirectory: template
    ├── {{ _copier_conf.answers_file }}.jinja   # generates .copier-answers.yml
    ├── hacs.json.jinja
    ├── README.md.jinja
    └── custom_components/
        └── [[ project_domain ]]/           # directory name uses [[ ]] (with _envops)
            ├── __init__.py.jinja
            ├── config_flow.py.jinja
            ├── const.py.jinja
            ├── coordinator.py.jinja
            ├── manifest.json.jinja
            ├── strings.json.jinja
            ├── sensor.py.jinja
            ├── translations/
            │   └── en.json.jinja
            ├── frontend/
            │   └── [[ project_domain ]]-card.js.jinja
            ├── [% if use_websocket %]websocket.py[% endif %].jinja
            ├── [% if use_services %]services.py[% endif %].jinja
            └── [% if use_secondary_coordinator %]coordinator_secondary.py[% endif %].jinja
```

Note: With `_envops` using `[[ ]]` for variables and `[% %]` for blocks, the directory name `[[ project_domain ]]/` renders correctly because directory names undergo Jinja rendering with the same environment settings.

### Pattern 1: copier.yml Question Syntax

**What:** Define questions in `copier.yml` at the repo root. Question keys become template variables.
**When to use:** Every variable in the template must be declared as a question (or computed variable).

```yaml
# copier.yml
_subdirectory: template
_templates_suffix: .jinja
_envops:
  autoescape: false
  block_start_string: "[%"
  block_end_string: "%]"
  variable_start_string: "[["
  variable_end_string: "]]"
  comment_start_string: "[#"
  comment_end_string: "#]"
  keep_trailing_newline: true

# Questions
project_domain:
  type: str
  help: "Integration domain (lowercase, underscores only, e.g. my_integration)"
  validator: >-
    [% if not (project_domain | regex_search('^[a-z][a-z0-9_]*$')) %]
    Domain must start with a letter, contain only lowercase letters, digits, and underscores.
    [% endif %]

project_name:
  type: str
  help: "Human-readable name (e.g. My Integration)"
  default: "[[ project_domain | replace('_', ' ') | title ]]"

project_description:
  type: str
  help: "Short description of this integration"
  default: "A Home Assistant integration."

author_name:
  type: str
  help: "Your name or GitHub username (used in manifest codeowners)"

iot_class:
  type: str
  help: "How this integration communicates with devices/services"
  default: local_polling
  choices:
    - assumed_state
    - cloud_polling
    - cloud_push
    - local_polling
    - local_push
    - calculated

integration_type:
  type: str
  help: "Integration type (describes the integration's primary focus)"
  default: service
  choices:
    - hub
    - device
    - entity
    - helper
    - service
    - hardware
    - system
    - virtual

use_websocket:
  type: bool
  help: "Include WebSocket API support?"
  default: false

use_services:
  type: bool
  help: "Include custom services (actions)?"
  default: false

use_secondary_coordinator:
  type: bool
  help: "Include a secondary DataUpdateCoordinator?"
  default: false

use_multi_step_config_flow:
  type: bool
  help: "Include multi-step config flow (e.g. discovery + manual)?"
  default: false

version:
  type: str
  help: "Initial version (SemVer, e.g. 0.1.0)"
  default: "0.1.0"

documentation_url:
  type: str
  help: "Documentation URL (GitHub repo URL is fine)"
  default: "https://github.com/[[ author_name ]]/ha-[[ project_domain | replace('_', '-') ]]"

issue_tracker_url:
  type: str
  help: "Issue tracker URL"
  default: "https://github.com/[[ author_name ]]/ha-[[ project_domain | replace('_', '-') ]]/issues"
```

### Pattern 2: Python File Brace Collision — Use `_envops` (Recommended)

**What:** Change Copier's template delimiters globally so Python files do not need any escaping.
**When to use:** Always, when the template contains Python files.

With `_envops` in `copier.yml` setting `variable_start_string: "[["` and `block_start_string: "[%"`:

```python
# template/custom_components/[[ project_domain ]]/__init__.py.jinja
"""The [[ project_name ]] integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, FRONTEND_SCRIPT_URL
from .coordinator import TemplateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


@dataclass
class [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]Data:
    """Data for the [[ project_name ]] integration."""
    coordinator: TemplateCoordinator


type [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]ConfigEntry = ConfigEntry[
    [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]Data
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the [[ project_name ]] integration."""
    frontend_path = Path(__file__).parent / "frontend"
    try:
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    FRONTEND_SCRIPT_URL,
                    str(frontend_path / f"{DOMAIN}-card.js"),
                    cache_headers=True,
                )
            ]
        )
    except RuntimeError:
        pass
    return True
```

Note: Python braces like `dict[str, Any]`, `{"key": "value"}`, `f"{DOMAIN}"` pass through unmolested because Copier only processes `[[ ]]` and `[% %]` with the `_envops` setting.

### Pattern 3: Python File Brace Collision — `{% raw %}` Alternative (Not Recommended for This Project)

**What:** Wrap entire Python file content in `{% raw %}...{% endraw %}` and use standard `{{ }}` Jinja delimiters.
**When to use:** Only when `_envops` cannot be used (e.g., mixing with another tool).

```python
# template/custom_components/{{ project_domain }}/const.py.jinja
"""Constants for the {{ project_domain }} integration."""

{% raw %}
DOMAIN = "{{ project_domain }}"  # <- This is a PROBLEM with raw: can't substitute here
{% endraw %}
```

**Why this does NOT work cleanly:** The raw block prevents ALL Jinja processing, including variable substitution. You cannot substitute `{{ project_domain }}` inside a raw block. You would need to break the file into alternating raw/non-raw sections, which is unmaintainable.

**Correct `{% raw %}` usage** (standard `{{ }}` delimiters, no `_envops`): wrap only the static Python sections, substitute variables outside raw blocks:

```python
# With standard delimiters - messy for files with many variables
"""Constants for the {{ project_domain }} integration."""

DOMAIN = "{{ project_domain }}"

{% raw %}
CONF_HOST = "host"
CONF_PORT = "port"

DEFAULT_PORT = 8080
DEFAULT_SCAN_INTERVAL = 30

FRONTEND_SCRIPT_URL = f"/{DOMAIN}/{DOMAIN}-card.js"
{% endraw %}
```

**Conclusion:** For Python-heavy templates, `_envops` with `[[ ]]` is the right choice. Raw blocks are only practical for isolated substitutions.

### Pattern 4: Conditional File Generation

**What:** Include or exclude files based on question answers using Jinja2 in the filename.
**When to use:** Optional files (websocket.py, services.py, etc.).

```
# File naming: the template suffix MUST appear outside the condition
[% if use_websocket %]websocket[% endif %].py.jinja
[% if use_services %]services[% endif %].py.jinja
[% if use_secondary_coordinator %]coordinator_secondary[% endif %].py.jinja
```

An empty filename after rendering (when condition is false) causes Copier to skip the file — no file is created in the destination.

For directories:
```
# Directories do NOT get .jinja suffix — just use conditional in the name
[% if use_github_actions %].github[% endif %]/workflows/validate.yml.jinja
```

### Pattern 5: .copier-answers.yml Generation

**What:** Generate the answers file automatically in the child project for future `copier update` support.
**When to use:** Always — required for `copier update` 3-way merge.

Template file path (in the `template/` subdirectory):
```
template/{{ _copier_conf.answers_file }}.jinja
```

Template file content:
```yaml
# Changes here will be overwritten by Copier; NEVER EDIT MANUALLY
{{ _copier_answers|to_nice_yaml -}}
```

This generates `.copier-answers.yml` in the child project root containing:
```yaml
# Changes here will be overwritten by Copier; NEVER EDIT MANUALLY
_commit: 0.1.0
_src_path: gh:Dabentz/ha-hacs-template
iot_class: local_polling
project_description: A Home Assistant integration.
project_domain: my_integration
project_name: My Integration
version: 0.1.0
```

Note: The `answers_file` template path uses standard `{{ }}` delimiters (it is a filename in the template directory, processed before `_envops` takes effect for file content rendering). This is a Copier-internal variable, not rendered as content.

### Pattern 6: copier update 3-Way Merge Requirements

**What:** `copier update` regenerates the project from the latest template version, diffs against the current state, and reapplies custom edits.
**Requirements:**
1. Template repo MUST have git version tags in PEP 440 format (e.g., `0.1.0`, `1.0.0`)
2. Child project MUST have `.copier-answers.yml` committed
3. Child project SHOULD be a git repo (strongly recommended)

**Command:**
```bash
# In the child project directory:
copier update

# With conflict handling:
copier update --conflict inline    # default: inline git conflict markers
copier update --conflict rej       # creates .rej files for unresolvable conflicts
```

**Git tag requirement for template repo:**
```bash
git tag 0.1.0
git push origin 0.1.0
```

Without a tag, `copier update` cannot determine what version the child project was generated from.

### Pattern 7: manifest.json Template for hassfest Compliance

All seven required manifest fields must be populated by questions:

```json
{
  "domain": "[[ project_domain ]]",
  "name": "[[ project_name ]]",
  "codeowners": ["@[[ author_name ]]"],
  "config_flow": true,
  "dependencies": ["frontend"],
  "documentation": "[[ documentation_url ]]",
  "integration_type": "[[ integration_type ]]",
  "iot_class": "[[ iot_class ]]",
  "issue_tracker": "[[ issue_tracker_url ]]",
  "requirements": [],
  "version": "[[ version ]]"
}
```

Note: `version` is required for custom integrations (not core); must be SemVer or CalVer recognized by `AwesomeVersion`.

### Anti-Patterns to Avoid

- **`.jinja` suffix on directories:** Directories must NOT have the `.jinja` suffix. Only files use it.
- **Template suffix inside Jinja condition in filename:** `{% if condition %}.pre-commit-config.yaml.jinja{% endif %}` — WRONG. The `.jinja` suffix must be outside: `{% if condition %}.pre-commit-config.yaml{% endif %}.jinja`.
- **Using `{% raw %}` with standard delimiters for Python-heavy files:** Cannot substitute variables inside raw blocks. Use `_envops` instead.
- **Mixing `_envops` with filename-level conditionals:** Filename conditionals use `[% %]` (the custom delimiter) when `_envops` is active — confirm syntax consistency.
- **No git tags on template repo:** `copier update` silently fails or uses wrong version. Tag releases.
- **Manual edits to `.copier-answers.yml` in child projects:** Overwritten on next `copier update`.
- **`_exclude` list overriding defaults:** Setting `_exclude` in `copier.yml` replaces the default exclude list. The defaults (`copier.yaml`, `copier.yml`, `~*`, `*.py[co]`, `__pycache__`, `.git`, `.DS_Store`, `.svn`) must be re-listed or the template metadata files will be copied into child projects.
- **Forgetting `_subdirectory`:** Without it, `copier.yml` itself would be copied into the child project (it is in the default `_exclude` list, so it is excluded — but other repo-root files like CI configs, `README.md` for the template repo, etc. would be copied).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Python brace escaping | Per-line `{{"{"}}` workarounds or manual character substitution | `_envops` custom delimiters | `_envops` is zero-maintenance; manual escaping is fragile and unreadable |
| Update/merge logic | Custom diff/patch scripts | `copier update` built-in 3-way merge | Copier's merge handles git history, conflict markers, and partial updates correctly |
| Conditional file exclusion | Post-generation cleanup scripts | Jinja2 in filenames + empty-name skip | Copier natively skips files with empty rendered names |
| Answers file format | Custom YAML generation in `_tasks` | `{{ _copier_conf.answers_file }}.jinja` with `_copier_answers` | Built-in variable provides exactly the right format for future updates |
| Domain validation | External validation script | `validator:` field in `copier.yml` question | Copier re-prompts on validation failure before generation begins |

**Key insight:** Copier has first-party solutions for every scaffolding concern in this phase. Custom scripts for any of these introduce maintenance burden and defeat the purpose of using Copier.

---

## Common Pitfalls

### Pitfall 1: Template Suffix Position in Conditional Filenames

**What goes wrong:** File is never generated (treated as literal filename) or always generated (condition ignored).
**Why it happens:** If `.jinja` is inside the condition, Copier does not recognize the file as a template.
**How to avoid:**
```
# WRONG:
[% if use_websocket %]websocket.py.jinja[% endif %]

# CORRECT:
[% if use_websocket %]websocket[% endif %].py.jinja
```
**Warning signs:** Conditional file always appears in output, or `.jinja` file literally copied without rendering.

### Pitfall 2: `_envops` Delimiter Mismatch Between File Content and Filenames

**What goes wrong:** Filename conditionals use standard `{% %}` syntax while file content uses `[% %]`, causing filename rendering to fail.
**Why it happens:** Copier applies `_envops` to file content AND to filename rendering — both must use the custom delimiters.
**How to avoid:** After setting `_envops`, use `[[ ]]` and `[% %]` consistently in BOTH filenames AND file content.
**Warning signs:** Copier error during copy about unrecognized template syntax in filename; file not being skipped when condition is false.

### Pitfall 3: Missing Git Tag Prevents copier update

**What goes wrong:** `copier update` fails with "no version found" or uses wrong base version.
**Why it happens:** Copier stores `_commit` in `.copier-answers.yml` from the template's git tag. Without tags, there is no version anchor.
**How to avoid:** Create an initial tag (`git tag 0.1.0`) on the template repo before first use. Include tagging in the release workflow.
**Warning signs:** `.copier-answers.yml` shows `_commit: HEAD` instead of a version number; `copier update` reports nothing to update or errors.

### Pitfall 4: answers_file Template in Wrong Location

**What goes wrong:** `.copier-answers.yml` is not generated in child project, breaking future `copier update`.
**Why it happens:** The answers file template must be inside the `_subdirectory` (`template/`), not at the repo root.
**How to avoid:** Place `template/{{ _copier_conf.answers_file }}.jinja` (note: standard `{{ }}` for the filename itself — this is the path, not file content) inside the `template/` subdirectory.
**Warning signs:** No `.copier-answers.yml` in generated child project; `copier update` cannot find answers file.

### Pitfall 5: hassfest Failure from Missing Required manifest.json Fields

**What goes wrong:** Generated project fails hassfest validation, requiring manual post-generation edits.
**Why it happens:** One or more of the seven required fields is missing, malformed, or uses an invalid enum value.
**How to avoid:** Template `manifest.json.jinja` must include all seven required fields: `domain`, `name`, `codeowners`, `dependencies`, `documentation`, `integration_type`, `iot_class`, `requirements`. `iot_class` must be one of `assumed_state`, `cloud_polling`, `cloud_push`, `local_polling`, `local_push`, `calculated`. `integration_type` must be one of `hub`, `device`, `entity`, `helper`, `service`, `hardware`, `system`, `virtual`. `version` must be SemVer/CalVer.
**Warning signs:** hassfest CI fails with `KeyError` or validation error pointing to manifest.

### Pitfall 6: strings.json / translations Mismatch Fails hassfest

**What goes wrong:** hassfest validates that `strings.json` and `translations/en.json` have matching keys. A mismatch causes failure.
**Why it happens:** Template generates both files but they diverge if template variables are not substituted consistently.
**How to avoid:** Template both `strings.json.jinja` and `translations/en.json.jinja` to be identical in structure. For custom integrations, hassfest validates `strings.json` if it exists (priority) or falls back to `translations/en.json`.
**Warning signs:** hassfest CI fails with translation key mismatch error.

### Pitfall 7: _exclude Default List Replacement

**What goes wrong:** `copier.yml` itself, `__pycache__`, `.git`, etc. are copied into the child project.
**Why it happens:** Setting `_exclude` in `copier.yml` replaces (not extends) the default exclude list.
**How to avoid:** If using `_subdirectory: template`, this is less of a concern because repo-root files are outside the template root. But if `_exclude` is set, include the defaults explicitly.
**Warning signs:** `copier.yml` appearing in generated child project; `.pyc` files copied.

---

## Code Examples

Verified patterns from official sources:

### Complete copier.yml (with _envops custom delimiters)

```yaml
# Source: https://copier.readthedocs.io/en/stable/configuring/
_subdirectory: template
_templates_suffix: .jinja
_answers_file: .copier-answers.yml
_envops:
  autoescape: false
  block_start_string: "[%"
  block_end_string: "%]"
  variable_start_string: "[["
  variable_end_string: "]]"
  comment_start_string: "[#"
  comment_end_string: "#]"
  keep_trailing_newline: true

project_domain:
  type: str
  help: "Integration domain (lowercase letters, digits, underscores)"
  validator: >-
    [% if not (project_domain | regex_search('^[a-z][a-z0-9_]*$')) %]
    Domain must match ^[a-z][a-z0-9_]*$
    [% endif %]

project_name:
  type: str
  help: "Human-readable integration name"
  default: "[[ project_domain | replace('_', ' ') | title ]]"

author_name:
  type: str
  help: "GitHub username for codeowners"

iot_class:
  type: str
  help: "IoT class for the integration"
  default: local_polling
  choices:
    - assumed_state
    - cloud_polling
    - cloud_push
    - local_polling
    - local_push
    - calculated

integration_type:
  type: str
  help: "Integration type"
  default: service
  choices:
    - hub
    - device
    - entity
    - helper
    - service
    - hardware
    - system
    - virtual

version:
  type: str
  help: "Initial version (SemVer)"
  default: "0.1.0"

use_websocket:
  type: bool
  help: "Include WebSocket API module?"
  default: false

use_services:
  type: bool
  help: "Include custom services module?"
  default: false
```

### .copier-answers.yml Template

```yaml
# Source: https://copier.readthedocs.io/en/stable/creating/
# template/{{ _copier_conf.answers_file }}.jinja
# Changes here will be overwritten by Copier; NEVER EDIT MANUALLY
{{ _copier_answers|to_nice_yaml -}}
```

Note: The answers file template itself uses standard `{{ }}` delimiters in its filename path (Copier resolves this path before applying `_envops` to content), but its content uses standard `{{ }}` too since the file's own Jinja processing is for the `_copier_answers` variable output — not for user-defined variables that conflict with Python.

### Conditional File Pattern

```
# Source: https://copier.readthedocs.io/en/stable/creating/
# Filename in template directory (with _envops active):
[% if use_websocket %]websocket[% endif %].py.jinja
[% if use_services %]services[% endif %].py.jinja
```

### Python File with _envops (no escaping needed)

```python
# Source: copier.readthedocs.io/en/stable/configuring/ (_envops section)
# template/custom_components/[[ project_domain ]]/const.py.jinja
"""Constants for the [[ project_name ]] integration."""

DOMAIN = "[[ project_domain ]]"

CONF_HOST = "host"
CONF_PORT = "port"

DEFAULT_PORT = 8080
DEFAULT_SCAN_INTERVAL = 30

FRONTEND_SCRIPT_URL = f"/{DOMAIN}/{DOMAIN}-card.js"
```

Python braces in `f"/{DOMAIN}/{DOMAIN}-card.js"` are literal Python — Copier ignores them because it only looks for `[[ ]]`.

### manifest.json Template for hassfest Compliance

```json
{
  "domain": "[[ project_domain ]]",
  "name": "[[ project_name ]]",
  "codeowners": ["@[[ author_name ]]"],
  "config_flow": true,
  "dependencies": ["frontend"],
  "documentation": "[[ documentation_url ]]",
  "integration_type": "[[ integration_type ]]",
  "iot_class": "[[ iot_class ]]",
  "issue_tracker": "[[ issue_tracker_url ]]",
  "requirements": [],
  "version": "[[ version ]]"
}
```

### copier copy and copier update Commands

```bash
# Source: https://copier.readthedocs.io/en/stable/generating/

# Generate new project:
copier copy gh:Dabentz/ha-hacs-template ./my-integration

# Generate from local template clone:
copier copy /path/to/ha-hacs-template ./my-integration

# Generate from specific git tag:
copier copy --vcs-ref 0.1.0 gh:Dabentz/ha-hacs-template ./my-integration

# Update existing child project (run from within child project):
cd my-integration
copier update

# Update with explicit conflict strategy:
copier update --conflict inline    # default: git-style conflict markers in files
copier update --conflict rej       # creates .rej files for unresolvable conflicts
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `{% raw %}...{% endraw %}` per Python file | `_envops` custom delimiters `[[ ]]` | Copier v6 (2021) introduced configurable envops | Custom delimiters are cleaner; raw blocks still work but are verbose for Python-heavy templates |
| `_envops` with Copier v5 bracket defaults | Standard Jinja `{{ }}` as Copier default | Copier v6 PR #363 (2021) | Copier now defaults to `{{ }}`, matching Jinja standard — previous bracket default was non-standard |
| `copier copy` for fresh projects only | `copier copy` + `copier update` lifecycle | Stable since Copier v5+ | Template updates propagate to existing child projects via 3-way merge |
| Flat template structure (copier.yml next to template files) | `_subdirectory: template` separation | Available since early Copier versions; now best practice | Clean separation of template metadata from template content |

**Deprecated/outdated:**
- Copier v5 bracket-style `[[ ]]` as DEFAULT delimiters: Copier v6+ uses `{{ }}` by default. Existing templates that relied on `[[ ]]` as the default will need explicit `_envops` to preserve that behavior if migrating.

---

## Open Questions

1. **answers_file template: standard `{{ }}` or custom `[[ ]]` delimiters?**
   - What we know: The answers file template filename uses `{{ _copier_conf.answers_file }}` (standard Copier internal variable), and its content uses `{{ _copier_answers|to_nice_yaml }}`. The official docs show standard `{{ }}` in this file.
   - What's unclear: With `_envops` active, does Copier apply custom delimiters to the answers file template content as well? If so, the content would need to use `[[ _copier_answers|to_nice_yaml ]]`.
   - Recommendation: Test empirically during implementation. Most likely `_envops` applies globally including the answers file content, so use `[[ _copier_answers|to_nice_yaml -]]`. The file's name resolution (figuring out which file IS the answers file template) is separate from content rendering.

2. **Class name derivation from project_domain**
   - What we know: The Python class names in `__init__.py` (e.g., `HacsTemplateData`, `HacsTemplateConfigEntry`) must be derived from `project_domain`. The Jinja filter chain `project_domain | replace('_', ' ') | title | replace(' ', '')` converts `my_integration` to `MyIntegration`.
   - What's unclear: Whether Copier's bundled `jinja2-ansible-filters` includes all needed string filters, or if a custom extension is needed.
   - Recommendation: The standard Jinja2 `replace` and `title` filters are available. Test the filter chain `[[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]` during implementation to confirm output.

3. **Template git tag format for copier update**
   - What we know: Tags must be PEP 440 compliant (SemVer `0.1.0` or CalVer `2026.1.0` work). Copier uses the latest tag as the default for `copier copy`.
   - What's unclear: Whether the template repo's existing commits need re-tagging or if a fresh `0.1.0` tag on the Phase 2 completion commit is sufficient.
   - Recommendation: Tag the first complete template commit as `0.1.0`. Future changes become `0.2.0`, etc. This is sufficient for smoke testing `copier update`.

4. **Smoke test child project: how to run hassfest locally**
   - What we know: hassfest is available as a GitHub Action (`home-assistant/actions/hassfest`). Running it locally requires checking out HA core.
   - What's unclear: Whether there is a simpler local validation path (e.g., `pre-commit` hook with hassfest, or a Docker image).
   - Recommendation: Use the GitHub Actions workflow for CI validation as the primary hassfest check. For local smoke testing, a manual inspection of generated `manifest.json` against the required fields list is sufficient to verify template correctness before pushing.

---

## Sources

### Primary (HIGH confidence)

- [Copier official docs — Configuring a template](https://copier.readthedocs.io/en/stable/configuring/) — `_envops`, `_subdirectory`, `_answers_file`, `_exclude`, `_skip_if_exists`, `_tasks`, question fields (type, default, choices, help, when, validator, multiselect)
- [Copier official docs — Creating a template](https://copier.readthedocs.io/en/stable/creating/) — `.jinja` suffix, conditional filenames, `{{ _copier_conf.answers_file }}.jinja`, `_copier_answers` variable
- [Copier official docs — Updating a project](https://copier.readthedocs.io/en/stable/updating/) — 3-way merge mechanism, `--conflict` options, git tag requirements
- [Copier official docs — Generating a project](https://copier.readthedocs.io/en/stable/generating/) — `copier copy` syntax, `--vcs-ref` flag
- [Copier PyPI page](https://pypi.org/project/copier/) — version 9.11.3 (2026-01-23), Python ≥ 3.10, Git ≥ 2.27
- [HA Developer Docs — Integration manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/) — required fields, valid `iot_class` values, valid `integration_type` values, `version` format (AwesomeVersion)
- [Jinja2 official docs — Template Designer](https://jinja.palletsprojects.com/en/stable/templates/) — `{% raw %}` block syntax

### Secondary (MEDIUM confidence)

- [DeepWiki — Copier Creating Templates](https://deepwiki.com/copier-org/copier/3.1-creating-templates) — conditional filename examples, `_templates_suffix`, answers file format; verified against official Copier docs
- [DiamondLightSource/python-copier-template](https://github.com/DiamondLightSource/python-copier-template) — real-world `_subdirectory: template` usage, `.jinja` file naming, conditional GitHub directory pattern
- [Copier GitHub issue #247](https://github.com/copier-org/copier/issues/247) — history of delimiter change from `[[ ]]` to `{{ }}` default in v6; confirms `_envops` is the path back to custom delimiters
- [HA Community: hassfest validation strings.json PR #135789](https://github.com/home-assistant/core/pull/135789) — strings.json priority for custom integrations in hassfest

### Tertiary (LOW confidence)

- WebSearch findings about `_envops` being "recommended" for delimiter-heavy files — consistent across multiple sources but not a single authoritative statement; treat as community consensus.

---

## Metadata

**Confidence breakdown:**
- Standard stack (Copier version, install): HIGH — PyPI page verified 2026-01-23
- copier.yml question syntax: HIGH — official Copier configuring docs
- `_envops` custom delimiters: HIGH — official Copier configuring docs
- Conditional filenames: HIGH — official Copier creating docs, confirmed by DeepWiki
- answers file generation: HIGH — official Copier creating docs
- 3-way merge / update mechanism: HIGH — official Copier updating docs
- hassfest required fields: HIGH — official HA developer docs
- Valid iot_class/integration_type values: HIGH — official HA manifest docs
- `_envops` vs `{% raw %}` recommendation: MEDIUM — community consensus, not a single official statement; reasoning from first principles is clear

**Research date:** 2026-02-19
**Valid until:** 2026-08-19 (180 days — Copier and HA manifest specs are stable; only a Copier major version or new required manifest field would invalidate)
