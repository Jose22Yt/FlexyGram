#!/usr/bin/env python3
"""Static, secret-safe preflight for FlexyGram Connected Alpha.

This check never sends data over a network, runs Gradle, or prints credential values.
It checks the source tree and the intended *effective* build configuration; it does
not replace verification of the merged Android manifest or the built APK.

Run: python3 Tools/connected_alpha_preflight.py --root .
Override an APP_PACKAGE supplied at build time with --application-id.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import sys

ALPHA_APPLICATION_ID = "io.github.jose22yt.flexygram.alpha"


@dataclass(frozen=True)
class Finding:
    name: str
    status: str  # PASS / WARN / FAIL
    description: str


def read_properties(text: str) -> dict[str, str]:
    """Read the straightforward KEY=VALUE subset used by local/Gradle properties."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "!")):
            continue
        if "=" in s:
            key, value = s.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def preflight(
    root: Path,
    *,
    application_id: str | None = None,
    environ: dict[str, str] | None = None,
) -> list[Finding]:
    root = Path(root)
    env = dict(os.environ if environ is None else environ)
    findings: list[Finding] = []

    def result(name: str, status: str, description: str) -> None:
        findings.append(Finding(name, status, description))

    expected = {
        "settings.gradle", "gradle.properties", ".gitignore", ".gitmodules",
        "TMessagesProj/build.gradle", "TMessagesProj/src/main/AndroidManifest.xml",
    }
    missing = sorted(item for item in expected if not (root / item).is_file())
    if missing:
        result("source", "FAIL", "Archivos de la base no encontrados: " + ", ".join(missing))
        return findings
    result("source", "PASS", "Estructura esencial de Exteraless presente.")

    gradle = (root / "TMessagesProj/build.gradle").read_text(encoding="utf-8")
    manifest = (root / "TMessagesProj/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
    props = read_properties((root / "gradle.properties").read_text(encoding="utf-8"))
    ignored = (root / ".gitignore").read_text(encoding="utf-8").splitlines()

    if re.search(r'<uses-permission\s+android:name="android\.permission\.INTERNET"', manifest):
        result("internet", "PASS", "El manifiesto fuente declara INTERNET.")
    else:
        result("internet", "FAIL", "El manifiesto fuente no declara INTERNET.")

    app_package = application_id if application_id is not None else props.get("APP_PACKAGE", "")
    if app_package == ALPHA_APPLICATION_ID:
        result("application-id", "PASS", "Identidad Alpha independiente configurada.")
    else:
        result("application-id", "FAIL", "APP_PACKAGE efectivo no es la identidad independiente de Connected Alpha.")

    required_ignored = {"local.properties", "TMessagesProj/release.keystore"}
    if required_ignored.issubset(set(line.strip() for line in ignored)):
        result("gitignore", "PASS", "Archivos privados habituales ignorados por Git.")
    else:
        result("gitignore", "FAIL", "Faltan reglas de exclusión de credenciales/clave de firma.")

    # Mirror original Gradle's input selection: LOCAL_PROPERTIES base64 wins,
    # otherwise local.properties, otherwise properties is null.
    local: dict[str, str] | None = None
    if env.get("LOCAL_PROPERTIES", "").strip():
        try:
            decoded = base64.b64decode(env["LOCAL_PROPERTIES"], validate=True).decode("utf-8")
            local = read_properties(decoded)
        except (ValueError, UnicodeError):
            result("credentials", "FAIL", "LOCAL_PROPERTIES no contiene propiedades base64 válidas.")
            return findings
    elif (root / "local.properties").is_file():
        local = read_properties((root / "local.properties").read_text(encoding="utf-8"))

    def actual(name: str) -> str:
        return (local or {}).get(name) or env.get(name, "")

    app_id = actual("TELEGRAM_APP_ID")
    app_hash = actual("TELEGRAM_APP_HASH")
    credentials_valid = bool(re.fullmatch(r"[1-9][0-9]*", app_id) and
                             re.fullmatch(r"[0-9a-fA-F]{32}", app_hash))

    default_id = re.search(r"def\s+appId\s*=\s*['\"]([^'\"]+)['\"]", gradle)
    default_hash = re.search(r"def\s+appHash\s*=\s*['\"]([^'\"]+)['\"]", gradle)
    matches_default = bool((default_id and app_id == default_id.group(1)) or
                           (default_hash and app_hash.lower() == default_hash.group(1).lower()))

    # The original Gradle only reads TELEGRAM_APP_ID/HASH env vars inside the
    # if (properties != null) branch. Recheck this if Gradle is refactored.
    env_in_branch_only = bool(re.search(r"if\s*\(properties\s*!=\s*null\).*?"
        r"appId\s*=\s*properties\.getProperty\('TELEGRAM_APP_ID'\).*?"
        r"appHash\s*=\s*properties\.getProperty\('TELEGRAM_APP_HASH'\)",
        gradle, re.DOTALL))
    if local is None and env_in_branch_only:
        result("credentials", "FAIL", "Esta configuración Gradle ignora credenciales solo en entorno sin LOCAL_PROPERTIES/local.properties.")
    elif not credentials_valid:
        result("credentials", "FAIL", "Faltan credenciales propias o su formato no es válido.")
    elif matches_default:
        result("credentials", "FAIL", "No reutilices las credenciales predeterminadas del código original.")
    else:
        result("credentials", "PASS", "Se detectaron credenciales con formato válido (valores ocultos).")

    if default_id or default_hash:
        result("fallback", "WARN", "El proyecto conserva valores Telegram predeterminados; evitar su uso en Connected Alpha.")
    else:
        result("fallback", "PASS", "No se detectan asignaciones literales predeterminadas de Telegram.")

    # A source-level sanity check. The final merged manifest and the APK need
    # separate verification: Firebase and dependency manifests can add providers.
    authorities = re.findall(r'android:authorities="([^"]+)"', manifest)
    fixed = [s for s in authorities if "\${applicationId}" not in s]
    if fixed:
        result("authorities", "WARN", "Hay autoridades fijas en el manifiesto: revisar colisiones con apps instaladas.")
    else:
        result("authorities", "PASS", "Las autoridades del manifiesto fuente usan applicationId.")

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--application-id", help="APP_PACKAGE efectivo si se usa -P u otro override.")
    parser.add_argument("--json", action="store_true", help="Salida JSON sin valores de credenciales.")
    args = parser.parse_args(argv)
    findings = preflight(args.root, application_id=args.application_id)
    if args.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        for f in findings:
            print(f"[{f.status}] {f.name}: {f.description}")
        print(f"Resultado: {sum(f.status == 'PASS' for f in findings)} PASS, "
              f"{sum(f.status == 'WARN' for f in findings)} WARN, "
              f"{sum(f.status == 'FAIL' for f in findings)} FAIL")
    return 1 if any(f.status == "FAIL" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
