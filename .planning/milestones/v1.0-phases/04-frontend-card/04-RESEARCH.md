# Phase 4: Frontend Card - Research

**Researched:** 2026-02-19
**Domain:** Home Assistant custom Lovelace card development -- single-file LitElement, card editor, theme integration, card registry, loading/error states
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CARD-01 | Single-file LitElement card with HA prototype extraction (no CDN, no npm, no build tools) | Verified: prototype extraction from `hui-masonry-view` / `hui-view` is the standard no-build pattern. Existing card already uses this correctly. See Architecture Patterns. |
| CARD-02 | Card editor class with `getConfigElement()`, `config-changed` event dispatch (`bubbles: true, composed: true`) | Verified: official HA dev docs confirm `static getConfigElement()` returns editor element; config-changed event uses `new Event()` with manual `event.detail` assignment. Existing card already implements this but uses `CustomEvent` -- both work. See Code Examples. |
| CARD-03 | `window.customCards` registration with `type`, `name`, `description`, and `preview: true` | Verified: official docs confirm `window.customCards.push()` with `type`, `name`, `description`, `preview`. Optional `documentationURL` also available. Existing card already implements this correctly. |
| CARD-04 | `getStubConfig()` returns default config for card picker preview | Verified: official docs confirm `static getStubConfig()` returns JSON config without the `type:` key. Used by card picker dialog. Existing card returns `{ header, entity }`. Consider accepting `hass` parameter for smarter defaults. |
| CARD-05 | `getCardSize()` returns appropriate row count for dashboard layout | Verified: official docs confirm 1 unit = ~50px. Existing card returns 3. Should also implement `getGridOptions()` for sections view (12-column grid, introduced HA 2024.11). |
| CARD-06 | Theme integration via CSS custom properties only -- no hardcoded colors | Verified: `ha-card` component uses `--ha-card-background`, `--ha-card-border-color`, `--primary-text-color`, `--divider-color` etc. Existing card already uses `var(--primary-text-color)`, `var(--primary-color)`, `var(--secondary-text-color)`. See Common Pitfalls for completeness. |
| CARD-07 | Loading state (spinner while coordinator data unavailable) and error state (message when entity unavailable) | CRITICAL GAP: existing card has NO loading/error states. Use `<ha-spinner>` for loading (replaced `ha-circular-progress` in frontend 20250326.0). Use `<ha-alert alert-type="error">` for error state. See Code Examples. |
| CARD-08 | `ha-card` wrapper element for consistent HA card visual chrome | Verified: `<ha-card>` provides background, border, border-radius, header slot via CSS custom properties. Existing card already wraps in `<ha-card header="...">`. Confirm `card-content` class usage for proper padding. |
</phase_requirements>

---

## Summary

Phase 4 completes the Lovelace card template file that ships with every generated integration. The existing card file (`frontend/[domain]-card.js.jinja`) already has a solid foundation: LitElement prototype extraction, `ha-card` wrapper, card editor with `ha-entity-picker` and `ha-textfield`, `window.customCards` registration, `getStubConfig()`, `getCardSize()`, and basic CSS theme variable usage. The main gaps are: (1) no loading state when coordinator data is unavailable, (2) no error state when the configured entity does not exist, (3) `getGridOptions()` is missing for the sections view, and (4) the `getStubConfig()` could accept `hass` to provide smarter defaults.

The card uses the standard "prototype extraction" pattern to get LitElement, `html`, and `css` from HA's bundled Lit without any CDN imports or build tools. This pattern extracts the LitElement class from `customElements.get("hui-masonry-view")` (falling back to `"hui-view"`) and then accesses `html` and `css` from the prototype. This is the only viable approach for single-file cards that must work without a build step, and it is used by the vast majority of community custom cards. The existing code implements this correctly.

For the loading spinner, `ha-circular-progress` was removed in frontend version 20250326.0 (approximately HA 2025.4). The replacement is `<ha-spinner>`, which extends WebAwesome's Spinner component. Since the template targets HA 2025.7+ minimum, `ha-spinner` is the correct component to use. For error display, `<ha-alert alert-type="error">` provides a themed error banner with appropriate icon and color. Both are HA built-in custom elements available at runtime without imports.

**Primary recommendation:** Enhance the existing `[domain]-card.js.jinja` with loading/error states using `ha-spinner` and `ha-alert`, add `getGridOptions()`, improve `getStubConfig(hass)` to find a real entity, and add the Lovelace resource auto-registration to `__init__.py` for storage-mode dashboards. The editor should be enhanced to also support `getConfigForm()` as a modern alternative, but the existing `getConfigElement()` approach is perfectly valid and more flexible.

---

## Standard Stack

### Core (all HA-bundled, no external dependencies)

| Library/Component | Version | Purpose | Why Standard |
|-------------------|---------|---------|--------------|
| LitElement (via prototype extraction) | Lit 2.x or 3.x (HA-bundled) | Base class for reactive web components | HA bundles Lit; prototype extraction is the only no-build-tool access method |
| `html` tagged template literal | (from LitElement prototype) | Declarative HTML templating | Lit's template syntax; reactive, efficient DOM updates |
| `css` tagged template literal | (from LitElement prototype) | Scoped component styles | Shadow DOM style encapsulation |
| `<ha-card>` | HA built-in | Card chrome (background, border, header, shadow) | Standard wrapper for ALL Lovelace cards; provides theme integration |
| `<ha-spinner>` | HA 2025.4+ (frontend 20250326.0+) | Indeterminate loading indicator | Replaced `ha-circular-progress`; uses WebAwesome Spinner base |
| `<ha-alert>` | HA built-in | Themed alert banners (info/warning/error/success) | Built-in component with proper icon, color, and dismissable support |
| `<ha-entity-picker>` | HA built-in | Entity selection in card editor | Standard entity selector used by all HA card editors |
| `<ha-textfield>` | HA built-in | Text input in card editor | Standard text input component |
| `window.customCards` | Lovelace API | Card registration for picker dialog | Only way to appear in "Add Card" picker |

### Supporting

| Library/Component | Version | Purpose | When to Use |
|-------------------|---------|---------|-------------|
| `<ha-icon>` | HA built-in | Material design icons | When card needs to display icons |
| `homeassistant.components.http.StaticPathConfig` | HA 2025.7+ | Register static file paths | Already in `__init__.py` for serving card JS |
| Lovelace resources API (`hass.data["lovelace"].resources`) | HA built-in | Programmatic resource registration | For auto-registering card JS in storage-mode dashboards |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Prototype extraction | CDN import (`unpkg.com/lit-element`) | CDN requires internet; adds latency; version mismatch risk with HA's bundled Lit; HACS discourages external deps |
| Prototype extraction | Build tools (rollup/webpack) | Adds complexity; HACS single-file preference; harder for template consumers to modify |
| `getConfigElement()` (custom editor) | `getConfigForm()` (schema-based editor) | `getConfigForm` is simpler but less flexible; good for simple configs; does not support custom UI widgets |
| `<ha-spinner>` | CSS-only spinner animation | Less consistent with HA UI; ha-spinner inherits theme colors automatically |
| `<ha-alert>` | Custom error div with styling | Less consistent; ha-alert handles icon, color, border-radius, dismissable pattern |

**Installation:** No installation needed. All components are HA-bundled. The card JS file is a single `.js` file served via `async_register_static_paths`.

---

## Architecture Patterns

### Recommended File Structure

```
custom_components/{domain}/
├── __init__.py              # async_setup registers static path + lovelace resource
├── frontend/
│   └── {domain}-card.js     # Single-file LitElement card + editor + registration
├── const.py                 # FRONTEND_SCRIPT_URL constant
└── manifest.json            # dependencies: ["frontend"]
```

### Pattern 1: LitElement Prototype Extraction

**What:** Extract LitElement, html, and css from HA's bundled Lit library via the prototype chain of a known HA custom element.
**When to use:** Always, for single-file cards without build tools.
**Confidence:** HIGH -- this is the de facto standard used by hundreds of community cards.

```javascript
// Source: HA community standard, confirmed by multiple custom cards and HA dev blog
const LitElement = customElements.get("hui-masonry-view")
  ? Object.getPrototypeOf(customElements.get("hui-masonry-view"))
  : Object.getPrototypeOf(customElements.get("hui-view"));
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;
```

**Fallback note:** `hui-masonry-view` replaced `hui-view` as the extraction target around HA 0.116 (2020). The fallback chain ensures compatibility. Both extend LitElement.

### Pattern 2: Card Lifecycle

**What:** The HA Lovelace framework manages the card lifecycle with specific method call ordering.
**When to use:** Understanding this is essential for correct card implementation.

```
1. setConfig(config)      -- Called FIRST, before hass is available
2. set hass(hass)         -- Called whenever state changes (frequent)
3. render()               -- Lit calls this when reactive properties change
4. getCardSize()          -- Called for masonry view layout
5. getGridOptions()       -- Called for sections view layout
```

**Critical ordering:** `setConfig` is always called before `hass` is first set. Never access `this.hass` inside `setConfig`.

### Pattern 3: Card Editor Communication

**What:** The card editor communicates configuration changes back to the dashboard via DOM events.
**When to use:** In the editor class's event handlers.

```javascript
// Source: Official HA Developer Docs
// https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/
_updateConfig(key, value) {
  const newConfig = { ...this.config, [key]: value };
  const event = new Event("config-changed", {
    bubbles: true,
    composed: true,
  });
  event.detail = { config: newConfig };
  this.dispatchEvent(event);
}
```

**Note:** The official HA docs use `new Event()` with manual `event.detail` assignment. `new CustomEvent()` with `detail` in constructor also works. The existing card uses `CustomEvent` which is fine.

### Pattern 4: Lovelace Resource Auto-Registration

**What:** Programmatically register the card JS as a Lovelace dashboard resource so users don't need to manually add it.
**When to use:** In `async_setup()` for storage-mode dashboards.
**Confidence:** MEDIUM -- community pattern (KipK guide), not official API. Used by many integrations.

```python
# Source: KipK community guide
# https://gist.github.com/KipK/3cf706ac89573432803aaa2f5ca40492
async def async_setup(hass, config):
    # ... static path registration (existing) ...

    # Auto-register as Lovelace resource (storage mode only)
    lovelace = hass.data.get("lovelace")
    if lovelace and getattr(lovelace, "mode", None) == "storage":
        # Wait for lovelace resources to be loaded
        if lovelace.resources.loaded:
            await _register_lovelace_resource(hass, lovelace)
        else:
            async def _on_lovelace_loaded(_event=None):
                await _register_lovelace_resource(hass, lovelace)
            hass.bus.async_listen_once("lovelace_updated", _on_lovelace_loaded)

async def _register_lovelace_resource(hass, lovelace):
    url = FRONTEND_SCRIPT_URL
    existing = [r for r in lovelace.resources.async_items()
                if url in r.get("url", "")]
    if not existing:
        await lovelace.resources.async_create_item({
            "res_type": "module",
            "url": url,
        })
```

### Pattern 5: Copier Template Variable Substitution

**What:** The card JS file is a Jinja template with `[[ variable ]]` substitutions.
**When to use:** For all project-specific values in the card file.

Key substitutions already in use:
- `[[ project_name ]]` -- human-readable name for header, registration
- `[[ project_domain ]]` -- domain for element names, entity IDs
- `[[ project_description ]]` -- description for card picker
- `[[ version ]]` -- card version from Copier answers
- `[[ project_domain | replace('_', '-') ]]` -- kebab-case for custom element names
- `[[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]` -- PascalCase for class names
- `[[ project_domain | upper | replace('_', '-') ]]` -- UPPER-KEBAB for console.info prefix

### Anti-Patterns to Avoid

- **Importing Lit from CDN:** Never use `import from "https://unpkg.com/lit-element..."`. It creates version conflicts with HA's bundled Lit and requires internet access.
- **Accessing `this.hass` in `setConfig()`:** `setConfig` is called before `hass` is first provided. Always guard with `if (!this.hass)` in `render()`.
- **Hardcoded colors:** Never use hex/rgb values. Always use `var(--primary-color)`, `var(--primary-text-color)`, etc.
- **Missing `composed: true` on events:** Without `composed: true`, events won't cross shadow DOM boundaries and the editor won't work.
- **Registering custom elements inside a function:** `customElements.define()` must be at module scope (top level), not inside a constructor or method.
- **Not guarding `customElements.define()`:** If the card file is loaded twice (e.g., reload), defining the same element throws. Consider wrapping in `if (!customElements.get("..."))`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Loading spinner | CSS animation or SVG spinner | `<ha-spinner size="small">` | Matches HA UI perfectly; inherits theme colors; accessible |
| Error alert banner | Custom div with red background | `<ha-alert alert-type="error">` | Themed, includes icon, supports dismissable, i18n-ready |
| Entity picker dropdown | Custom `<select>` element | `<ha-entity-picker>` | Autocomplete, fuzzy search, entity filtering, domain icons |
| Text input field | Raw `<input type="text">` | `<ha-textfield>` | Material design, floating label, theme-aware, validation states |
| Card background/chrome | Custom card wrapper div | `<ha-card>` element | Border, shadow, border-radius, background all theme-integrated |
| Card size calculation | Manual pixel math | `getCardSize()` + `getGridOptions()` | HA framework handles layout; 1 unit = ~50px for masonry |

**Key insight:** HA provides themed UI components for every standard UI pattern. Using them ensures the card looks native in any theme and automatically adapts to light/dark modes.

---

## Common Pitfalls

### Pitfall 1: Missing Loading/Error States
**What goes wrong:** Card renders empty or throws errors when entity is unavailable or coordinator hasn't loaded yet.
**Why it happens:** Developers only test with working entities and forget edge cases.
**How to avoid:** Always check for three states in `render()`: (1) hass/config not yet set -> show spinner, (2) entity not found in `hass.states` -> show error, (3) entity available -> show content.
**Warning signs:** Blank white card on first dashboard load; "TypeError: Cannot read properties of undefined" in console.

### Pitfall 2: ha-circular-progress Removed
**What goes wrong:** Card shows no spinner and console shows "ha-circular-progress is not defined" error on HA 2025.4+.
**Why it happens:** `ha-circular-progress` was removed in frontend 20250326.0 and replaced by `<ha-spinner>`.
**How to avoid:** Use `<ha-spinner>` (not `<ha-circular-progress>`) since our minimum is HA 2025.7.
**Warning signs:** Loading indicator breaks after HA update; error in browser console about undefined element.

### Pitfall 3: Duplicate Custom Element Registration
**What goes wrong:** `customElements.define()` throws "has already been defined" error if the card JS file is loaded twice.
**Why it happens:** Dashboard resource re-registration, HACS updates, or integration reloads can cause the script to execute multiple times.
**How to avoid:** Guard with `if (!customElements.get("element-name"))` before `customElements.define()`.
**Warning signs:** Card works on fresh load but breaks after integration reload; error in browser console.

### Pitfall 4: Event Detail on Regular Event
**What goes wrong:** The official HA docs pattern sets `event.detail` on a `new Event()`, which is technically a read-only property on the base Event class.
**Why it happens:** Browser implementations allow setting `detail` on Event objects even though the spec says it's read-only on Event (only writable on CustomEvent).
**How to avoid:** Using `new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true })` is also valid and more semantically correct. Both patterns work in all major browsers. The existing card uses CustomEvent, which is fine.
**Warning signs:** None currently -- both work. But using CustomEvent is safer long-term.

### Pitfall 5: Card Not Appearing in Picker
**What goes wrong:** Card is registered as a resource and loads, but doesn't appear in the "Add Card" dialog.
**Why it happens:** `window.customCards.push()` was not executed, or `type` doesn't match the custom element name.
**How to avoid:** Ensure `type` in `window.customCards.push()` exactly matches the string in `customElements.define()`. Registration must happen at module scope (not lazily).
**Warning signs:** Card works when manually added to YAML config but is invisible in the UI card picker.

### Pitfall 6: Jinja2 Template Variable Collision in JS
**What goes wrong:** JavaScript template literals `${...}` or object destructuring `{...}` get interpreted as Jinja2 expressions.
**Why it happens:** The Copier template uses `[[ ]]` for variables and `[% %]` for blocks (custom `_envops`), NOT standard `{{ }}`/`{% %}`. So `${...}` in JS is safe.
**How to avoid:** The custom `_envops` in `copier.yml` completely avoids this collision. No `{% raw %}` blocks needed in `.js.jinja` files (unlike `.py.jinja` files which needed them for Python f-strings and dicts before the _envops change).
**Warning signs:** Card JS renders with broken template literals after `copier copy`.

### Pitfall 7: Static Path Not Registered for Card
**What goes wrong:** Browser returns 404 when trying to load the card JS file.
**Why it happens:** `async_register_static_paths` was called in `async_setup_entry` (per-entry) instead of `async_setup` (per-domain), or the path/filename doesn't match.
**How to avoid:** Registration must be in `async_setup()`. The existing `__init__.py` already does this correctly. Verify `FRONTEND_SCRIPT_URL` in `const.py` matches the registered path.
**Warning signs:** 404 error in browser network tab; card shows "Custom element doesn't exist" error.

---

## Code Examples

Verified patterns from official sources and existing codebase:

### Complete Card Render with Loading/Error States (NEW -- addresses CARD-07)

```javascript
// Source: Composite pattern from HA dev docs + ha-spinner source + ha-alert source
render() {
  if (!this.hass || !this.config) {
    return html`
      <ha-card>
        <div class="card-content loading">
          <ha-spinner size="small"></ha-spinner>
        </div>
      </ha-card>
    `;
  }

  const entityId = this.config.entity;
  if (!entityId) {
    return html`
      <ha-card header="${this.config.header || ""}">
        <div class="card-content">
          <div class="empty">No entity configured</div>
        </div>
      </ha-card>
    `;
  }

  const stateObj = this.hass.states[entityId];
  if (!stateObj) {
    return html`
      <ha-card header="${this.config.header || ""}">
        <div class="card-content">
          <ha-alert alert-type="error">
            Entity not available: ${entityId}
          </ha-alert>
        </div>
      </ha-card>
    `;
  }

  return html`
    <ha-card header="${this.config.header || ""}">
      <div class="card-content">
        <div class="state">
          <span class="label">
            ${stateObj.attributes.friendly_name || entityId}
          </span>
          <span class="value">${stateObj.state}</span>
        </div>
      </div>
    </ha-card>
  `;
}
```

### CSS Styles with Complete Theme Variable Usage (enhances CARD-06)

```javascript
// Source: ha-card.ts source code for variable names
// https://github.com/home-assistant/frontend/blob/master/src/components/ha-card.ts
static get styles() {
  return css`
    :host {
      display: block;
    }
    .card-content {
      padding: 0 16px 16px;
    }
    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 32px 16px;
    }
    .state {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
    }
    .label {
      font-weight: 500;
      color: var(--primary-text-color);
    }
    .value {
      font-size: 1.2em;
      font-weight: bold;
      color: var(--primary-color);
    }
    .empty {
      color: var(--secondary-text-color);
      font-style: italic;
      text-align: center;
      padding: 16px;
    }
  `;
}
```

### getStubConfig with hass Parameter (enhances CARD-04)

```javascript
// Source: Official HA dev docs
// https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/
static getStubConfig(hass) {
  // Find a sensor entity to use as default
  const entities = Object.keys(hass.states);
  const sensorEntity = entities.find((e) => e.startsWith("sensor."));
  return {
    header: "[[ project_name ]]",
    entity: sensorEntity || "",
  };
}
```

### getGridOptions for Sections View (enhances CARD-05)

```javascript
// Source: HA Developer Blog - Custom card sections support
// https://developers.home-assistant.io/blog/2024/11/06/custom-card-sections-support/
getGridOptions() {
  return {
    rows: 3,
    columns: 6,
    min_rows: 2,
    min_columns: 3,
  };
}
```

### Custom Element Definition with Duplicate Guard (addresses Pitfall 3)

```javascript
// Guard against duplicate registration on reload
if (!customElements.get("[[ project_domain | replace('_', '-') ]]-card")) {
  customElements.define(
    "[[ project_domain | replace('_', '-') ]]-card",
    [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]Card
  );
}
if (!customElements.get("[[ project_domain | replace('_', '-') ]]-card-editor")) {
  customElements.define(
    "[[ project_domain | replace('_', '-') ]]-card-editor",
    [[ project_domain | replace('_', ' ') | title | replace(' ', '') ]]CardEditor
  );
}
```

### config-changed Event (official pattern)

```javascript
// Source: Official HA Developer Docs
// https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/
// Note: Both patterns work. Official docs use new Event() + manual detail.
// Existing card uses new CustomEvent() which is also valid.
_updateConfig(key, value) {
  if (!this.config) return;
  const newConfig = { ...this.config, [key]: value };
  const event = new CustomEvent("config-changed", {
    detail: { config: newConfig },
    bubbles: true,
    composed: true,
  });
  this.dispatchEvent(event);
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `ha-circular-progress` for loading | `<ha-spinner>` | Frontend 20250326.0 (~HA 2025.4) | Old element removed; cards using it break silently |
| `register_static_path()` (sync) | `async_register_static_paths([StaticPathConfig(...)])` | HA 2024.6 introduced, old removed 2025.7 | Hard failure on HA 2025.7+ -- existing code already correct |
| `hui-view` for prototype extraction | `hui-masonry-view` with `hui-view` fallback | HA 0.116 (2020) | `hui-view` became UpdatingElement; masonry-view stays LitElement |
| No `getGridOptions()` | `getGridOptions()` for sections view | HA 2024.11 | Cards without it get default sizing in sections view |
| Manual Lovelace resource registration | Programmatic via `lovelace.resources.async_create_item()` | Community pattern (2024-2025) | Better UX; card auto-appears in dashboard resources |
| `getConfigElement()` custom editor | `getConfigForm()` schema-based editor | HA ~2024 (PR #16142) | Simpler for basic editors; getConfigElement still fully supported |

**Deprecated/outdated:**
- `ha-circular-progress`: Removed. Use `<ha-spinner>`.
- `register_static_path()`: Removed in HA 2025.7. Use `async_register_static_paths()`.
- `hui-view` as sole extraction target: Unreliable since HA 0.116. Use `hui-masonry-view` with fallback.
- Manual-only Lovelace resource setup: Still works but poor UX. Prefer auto-registration for storage mode.

---

## Open Questions

1. **ha-textfield availability on HA 2025.7+**
   - What we know: The existing card editor uses `<ha-textfield>`. HA is migrating to WebAwesome components (e.g., `ha-wa-dialog` replacing `ha-dialog`). `ha-textfield` may have been renamed or replaced.
   - What's unclear: Whether `ha-textfield` is still available or has been migrated to a WebAwesome equivalent in HA 2025.7.
   - Recommendation: Keep `ha-textfield` for now -- it was still in use as of early 2025 and is used in the official custom card docs example. If it breaks on the target HA version, it will be immediately obvious during smoke testing. A `getConfigForm()` schema-based editor avoids this issue entirely since HA renders the form fields itself.

2. **Lovelace resource auto-registration robustness**
   - What we know: The `lovelace.resources` API (`hass.data["lovelace"].resources.async_create_item()`) is used by community integrations (KipK guide, multiple HACS integrations) for auto-registering card JS.
   - What's unclear: This is an internal API, not officially documented. It could change without notice. The `lovelace.resources.loaded` property and `async_items()` method are not in any public API docs.
   - Recommendation: Implement it with a defensive try/except that silently falls back to manual registration. Include a note in the generated README about manual resource registration as fallback.

3. **Lit version in HA 2025.7**
   - What we know: HA has been on Lit 2.x for years. The prototype extraction pattern works regardless of whether HA uses Lit 2 or Lit 3, since both expose `html` and `css` on the prototype.
   - What's unclear: Exact Lit version bundled with HA 2025.7. A prior decision noted this as needing confirmation at smoke-test time.
   - Recommendation: The extraction pattern is version-agnostic. No action needed beyond smoke testing.

---

## Sources

### Primary (HIGH confidence)
- [Official HA Custom Card Docs](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/) -- setConfig, getCardSize, getStubConfig, getConfigElement, getConfigForm, config-changed events, window.customCards
- [HA Frontend ha-card.ts source](https://github.com/home-assistant/frontend/blob/master/src/components/ha-card.ts) -- Complete CSS custom properties for ha-card component
- [HA Frontend ha-spinner.ts source](https://github.com/home-assistant/frontend/blob/master/src/components/ha-spinner.ts) -- ha-spinner API: size prop (tiny/small/medium/large), CSS variables
- [HA Frontend ha-alert.ts source](https://github.com/home-assistant/frontend/blob/master/src/components/ha-alert.ts) -- ha-alert API: alert-type (info/warning/error/success), title, dismissable, narrow
- [HA Developer Blog: async_register_static_paths](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/) -- StaticPathConfig dataclass, migration from register_static_path
- [HA Developer Blog: Custom card sections support](https://developers.home-assistant.io/blog/2024/11/06/custom-card-sections-support/) -- getGridOptions() API for 12-column sections view

### Secondary (MEDIUM confidence)
- [KipK Embedded Card Guide (Community)](https://community.home-assistant.io/t/developer-guide-embedded-lovelace-card-in-a-home-assistant-integration/974909) -- Lovelace resource auto-registration pattern, version management
- [KipK Gist: Complete code](https://gist.github.com/KipK/3cf706ac89573432803aaa2f5ca40492) -- JSModuleRegistration class, full Python + JS implementation
- [thomasloven: Simplest Custom Card](https://gist.github.com/thomasloven/1de8c62d691e754f95b023105fe4b74b) -- Minimal card structure, lifecycle documentation
- [mini-graph-card issue #1222](https://github.com/kalkih/mini-graph-card/issues/1222) -- Confirms ha-circular-progress removed in frontend 20250326.0, migrated to ha-spinner

### Tertiary (LOW confidence)
- [HA Community: getConfigForm()](https://community.home-assistant.io/t/getconfigform-configure-editor-for-custom-card/845004) -- Schema-based editor as alternative to getConfigElement; PR #16142 reference
- [HA Community: Handling imports](https://community.home-assistant.io/t/handling-imports-in-custom-cards/857667) -- Confirms no direct import path for HA modules in single-file cards

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- prototype extraction pattern is universally used; ha-card/ha-spinner/ha-alert verified from source code
- Architecture: HIGH -- card lifecycle, event patterns, and file structure verified from official docs and existing working code
- Pitfalls: HIGH -- ha-circular-progress removal confirmed from issue tracker; duplicate registration and missing states are well-documented community issues
- Lovelace resource auto-registration: MEDIUM -- community pattern, not official API; works but could change

**Research date:** 2026-02-19
**Valid until:** 2026-03-19 (30 days -- HA frontend components are relatively stable within a release cycle)
