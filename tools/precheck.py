#!/usr/bin/env python3
"""
HACS pre-submission check script for peppe1337/ha-person-notify.

Prueft lokal alle HACS-Pflichtanforderungen die ohne die echte GitHub-Action
pruefbar sind. Holt GitHub-Repo-Metadaten via `gh api`.

Aufruf:  python3 tools/precheck.py
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CUSTOM_COMPONENTS = REPO_ROOT / "custom_components"
GITHUB_REPO = "peppe1337/ha-person-notify"

# Erlaubte Keys in hacs.json (PREVENT_EXTRA-Schema aus HACS-Quelle)
HACS_JSON_ALLOWED_KEYS = {
    "name",
    "content_in_root",
    "country",
    "filename",
    "hacs",
    "hide_default_branch",
    "homeassistant",
    "persistent_directory",
    "render_readme",
    "zip_release",
}

# Pflichtfelder manifest.json fuer Custom Integrations (aus HACS validate/integrate_manifest.py)
MANIFEST_REQUIRED_FIELDS = {
    "codeowners",
    "documentation",
    "domain",
    "issue_tracker",
    "name",
    "version",
}


# ---------------------------------------------------------------------------
# Hilfsklassen
# ---------------------------------------------------------------------------
class CheckResult:
    """Sammelt Pass/Fail-Ergebnisse."""

    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []

    def ok(self, msg: str) -> None:
        print(f"  PASS  {msg}")
        self.passed.append(msg)

    def fail(self, msg: str) -> None:
        print(f"  FAIL  {msg}")
        self.failed.append(msg)

    def summary(self) -> int:
        print()
        print(f"Ergebnis: {len(self.passed)} bestanden, {len(self.failed)} fehlgeschlagen")
        if self.failed:
            print()
            print("Fehlgeschlagene Pruefungen:")
            for f in self.failed:
                print(f"  - {f}")
            return 1
        print("Alle Pruefungen bestanden.")
        return 0


# ---------------------------------------------------------------------------
# GitHub-Metadaten laden
# ---------------------------------------------------------------------------
def get_github_repo() -> dict:
    """Lade Repo-Metadaten via `gh api`."""
    result = subprocess.run(
        ["gh", "api", f"repos/{GITHUB_REPO}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Fehler beim Abruf der GitHub-API: {result.stderr.strip()}")
        sys.exit(1)
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Einzelne Pruefungen
# ---------------------------------------------------------------------------
def check_github(repo: dict, r: CheckResult) -> None:
    """Prueft GitHub-Repo-Eigenschaften."""
    print("\n[GitHub-Repo-Pruefungen]")

    # Nicht archiviert
    if repo.get("archived"):
        r.fail("Repo ist archiviert")
    else:
        r.ok("Repo ist nicht archiviert")

    # Beschreibung nicht leer
    desc = repo.get("description") or ""
    if not desc.strip():
        r.fail("GitHub-Beschreibung ist leer")
    else:
        r.ok(f"GitHub-Beschreibung vorhanden: \"{desc[:60]}\"")

    # Mindestens ein Topic
    topics = repo.get("topics") or []
    if not topics:
        r.fail("Keine Topics gesetzt")
    else:
        r.ok(f"Topics gesetzt: {topics}")

    # Issues aktiviert
    if not repo.get("has_issues"):
        r.fail("Issues sind deaktiviert")
    else:
        r.ok("Issues sind aktiviert")

    # Lizenz mit SPDX-ID
    license_info = repo.get("license") or {}
    spdx_id = license_info.get("spdx_id", "")
    if not spdx_id:
        r.fail("Keine Lizenz gefunden")
    elif spdx_id == "NOASSERTION":
        r.fail("Lizenz konnte nicht identifiziert werden (NOASSERTION)")
    else:
        r.ok(f"Lizenz mit SPDX-ID: {spdx_id} ({license_info.get('name', '')})")


def check_readme(r: CheckResult) -> None:
    """Prueft ob eine README-Datei im Root des Repos liegt."""
    print("\n[README-Pruefung]")
    readme_variants = ["README", "README.md", "readme", "readme.md", "INFO", "INFO.md", "info", "info.md"]
    found = [v for v in readme_variants if (REPO_ROOT / v).exists()]
    if found:
        r.ok(f"README gefunden: {found[0]}")
    else:
        r.fail("Keine README/INFO-Datei im Root gefunden")


def check_license_file(r: CheckResult) -> None:
    """Prueft ob eine LICENSE-Datei im Root liegt."""
    print("\n[LICENSE-Datei-Pruefung]")
    license_variants = ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENCE.md"]
    found = [v for v in license_variants if (REPO_ROOT / v).exists()]
    if found:
        r.ok(f"LICENSE-Datei gefunden: {found[0]}")
    else:
        r.fail("Keine LICENSE-Datei im Root gefunden")


def check_hacs_json(r: CheckResult) -> tuple[dict, bool]:
    """Prueft hacs.json auf Gueligkeit (PREVENT_EXTRA-Schema)."""
    print("\n[hacs.json-Pruefung]")
    hacs_json_path = REPO_ROOT / "hacs.json"

    if not hacs_json_path.exists():
        r.fail("hacs.json fehlt im Root")
        return {}, False

    try:
        with open(hacs_json_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        r.fail(f"hacs.json ist kein gueltiges JSON: {e}")
        return {}, False

    r.ok("hacs.json ist gueltiges JSON")

    # Pflichtfeld 'name'
    if "name" not in data:
        r.fail("hacs.json: Pflichtfeld 'name' fehlt")
    else:
        r.ok(f"hacs.json: name = \"{data['name']}\"")

    # PREVENT_EXTRA: keine unerlaubten Keys
    extra_keys = set(data.keys()) - HACS_JSON_ALLOWED_KEYS
    if extra_keys:
        r.fail(f"hacs.json: unerlaubte Keys (PREVENT_EXTRA): {sorted(extra_keys)}")
    else:
        r.ok("hacs.json: keine unerlaubten Keys")

    # version-Feld in hacs.json: nicht erlaubt
    if "version" in data:
        r.fail("hacs.json: Key 'version' ist nicht erlaubt (wird von HACS aus manifest.json gelesen)")

    return data, True


def check_structure(r: CheckResult) -> tuple[str, pathlib.Path | None]:
    """Prueft custom_components/<domain>/ Struktur und genau eine manifest.json."""
    print("\n[Verzeichnisstruktur-Pruefung]")

    # custom_components/ muss existieren
    if not CUSTOM_COMPONENTS.exists():
        r.fail("custom_components/ Verzeichnis fehlt")
        return "", None

    r.ok("custom_components/ Verzeichnis gefunden")

    # Genau ein Domain-Verzeichnis
    domains = [d for d in CUSTOM_COMPONENTS.iterdir() if d.is_dir() and not d.name.startswith("__")]
    if len(domains) != 1:
        r.fail(f"Erwartet genau ein Verzeichnis in custom_components/, gefunden: {[d.name for d in domains]}")
        return "", None

    domain_dir = domains[0]
    domain = domain_dir.name
    r.ok(f"Genau ein Domain-Verzeichnis: custom_components/{domain}/")

    # Genau eine manifest.json im gesamten Repo (in custom_components/ Unterordner)
    all_manifests = list(REPO_ROOT.rglob("manifest.json"))
    # Schliesse hacore und andere nicht-Repo-Pfade aus
    repo_manifests = [m for m in all_manifests if str(m).startswith(str(REPO_ROOT)) and "tools" not in str(m)]

    if len(repo_manifests) == 0:
        r.fail("Keine manifest.json im Repo gefunden")
        return domain, None
    elif len(repo_manifests) > 1:
        r.fail(f"Mehr als eine manifest.json gefunden: {[str(m.relative_to(REPO_ROOT)) for m in repo_manifests]}")
    else:
        r.ok(f"Genau eine manifest.json: {repo_manifests[0].relative_to(REPO_ROOT)}")

    return domain, domain_dir


def check_manifest_json(domain_dir: pathlib.Path, domain: str, r: CheckResult) -> None:
    """Prueft manifest.json auf HACS-Pflichtfelder."""
    print("\n[manifest.json-Pruefung]")
    manifest_path = domain_dir / "manifest.json"

    if not manifest_path.exists():
        r.fail(f"manifest.json fehlt in custom_components/{domain}/")
        return

    try:
        with open(manifest_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        r.fail(f"manifest.json ist kein gueltiges JSON: {e}")
        return

    r.ok("manifest.json ist gueltiges JSON")

    # Pflichtfelder
    for field in sorted(MANIFEST_REQUIRED_FIELDS):
        if field not in data:
            r.fail(f"manifest.json: Pflichtfeld '{field}' fehlt")
        else:
            val = data[field]
            r.ok(f"manifest.json: {field} = {json.dumps(val) if not isinstance(val, str) else repr(val)}")

    # Domain muss mit Verzeichnisnamen uebereinstimmen
    if data.get("domain") and data["domain"] != domain:
        r.fail(f"manifest.json: domain='{data['domain']}' stimmt nicht mit Verzeichnis '{domain}' ueberein")
    elif data.get("domain"):
        r.ok(f"manifest.json: domain stimmt mit Verzeichnisnamen ueberein")


def check_brand_icon(domain_dir: pathlib.Path, domain: str, r: CheckResult) -> None:
    """Prueft ob brand/icon.png im Integrationsordner vorhanden ist."""
    print("\n[Brand-Icon-Pruefung]")
    icon_path = domain_dir / "brand" / "icon.png"
    if icon_path.exists():
        r.ok(f"brand/icon.png vorhanden: {icon_path.relative_to(REPO_ROOT)}")
    else:
        r.fail(
            f"brand/icon.png fehlt in custom_components/{domain}/brand/icon.png "
            f"(und Domain ist noch nicht im HA-Brands-Repo gelistet)"
        )


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------
def main() -> int:
    """Fuehre alle Pruefungen aus und gib Exit-Code zurueck."""
    print(f"HACS Pre-Submission Check")
    print(f"Repo:  {GITHUB_REPO}")
    print(f"Local: {REPO_ROOT}")

    r = CheckResult()

    # GitHub-Metadaten abrufen
    print("\n[GitHub-API wird abgefragt...]")
    repo = get_github_repo()

    check_github(repo, r)
    check_readme(r)
    check_license_file(r)
    check_hacs_json(r)
    domain, domain_dir = check_structure(r)

    if domain_dir is not None:
        check_manifest_json(domain_dir, domain, r)
        check_brand_icon(domain_dir, domain, r)

    return r.summary()


if __name__ == "__main__":
    sys.exit(main())
