"""Read-only audit of FlexyGram's user-visible identity (stdlib only).

This is deliberately not a broad search/replace of Exteraless or Telegram names.
Internal packages, JNI symbols, licenses and third-party credits are out of scope.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ANDROID = '{http://schemas.android.com/apk/res/android}'
IDS = {
    'diagnostic': 'io.github.jose22yt.flexygram.diagnostic',
    'production': 'io.github.jose22yt.flexygram.app',
}
LEGACY = re.compile(r'exteraless|telegram beta', re.IGNORECASE)


def _read_xml(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def audit(root: Path) -> dict:
    """Return stable JSON-serializable findings. Never modify repository files."""
    root = Path(root)
    findings: list[dict] = []

    def add(level: str, code: str, path: str, detail: str) -> None:
        findings.append({'level': level, 'code': code, 'path': path, 'detail': detail})

    policy_path = 'gradle/variant-policy.json'
    try:
        variants = json.loads((root / policy_path).read_text(encoding='utf-8'))['variants']
        for flavor, expected in IDS.items():
            if variants[flavor]['applicationId'] != expected:
                add('error', 'IDENTITY_ID_MISMATCH', policy_path, flavor)
        if variants['production']['buildEnabled'] or not variants['diagnostic']['buildEnabled']:
            add('error', 'VARIANT_STATUS_CHANGED', policy_path, 'Unexpected build capability')
    except (OSError, KeyError, TypeError, ValueError) as exc:
        add('error', 'POLICY_UNREADABLE', policy_path, type(exc).__name__)

    manifest_path = 'TMessagesProj/src/diagnostic/AndroidManifest.xml'
    try:
        manifest = _read_xml(root / manifest_path)
        app = manifest.find('application')
        if app is None:
            add('error', 'APPLICATION_MISSING', manifest_path, 'No application element')
        else:
            if app.get(ANDROID + 'label') != 'FlexyGram Diagnostic':
                add('error', 'DIAGNOSTIC_LABEL', manifest_path, str(app.get(ANDROID + 'label')))
            for attribute in ('icon', 'roundIcon'):
                icon = app.get(ANDROID + attribute)
                if icon:
                    if 'exteraless' in icon.lower():
                        add('review', 'LEGACY_PRIMARY_ICON', manifest_path, f'application {attribute}: {icon}')
                    _check_resource(root, icon, manifest_path, add)
            launchers = []
            for alias in app.findall('activity-alias'):
                if alias.get(ANDROID + 'enabled', 'true') != 'true':
                    continue
                for intent in alias.findall('intent-filter'):
                    actions = [x.get(ANDROID + 'name') for x in intent.findall('action')]
                    categories = [x.get(ANDROID + 'name') for x in intent.findall('category')]
                    if ('android.intent.action.MAIN' in actions and
                            'android.intent.category.LAUNCHER' in categories):
                        launchers.append(alias)
                        break
            if len(launchers) != 1:
                add('error', 'DIAGNOSTIC_LAUNCHER_COUNT', manifest_path, str(len(launchers)))
            for alias in launchers:
                for attribute in ('icon', 'roundIcon'):
                    value = alias.get(ANDROID + attribute)
                    if value and 'exteraless' in value.lower():
                        add('review', 'LEGACY_LAUNCHER_ICON', manifest_path, f'{attribute}: {value}')
                    if value:
                        _check_resource(root, value, manifest_path, add)
    except (OSError, ET.ParseError) as exc:
        add('error', 'MANIFEST_UNREADABLE', manifest_path, type(exc).__name__)

    strings_path = 'TMessagesProj/src/main/res/values/strings.xml'
    strings: dict[str, str] = {}
    try:
        for el in _read_xml(root / strings_path).findall('string'):
            name = el.get('name')
            if name:
                strings[name] = ''.join(el.itertext()).strip()
        for name in ('AppName', 'AppNameBeta'):
            value = strings.get(name)
            if value is None:
                add('error', 'BRAND_STRING_MISSING', strings_path, name)
            elif LEGACY.search(value):
                add('review', 'LEGACY_VISIBLE_STRING', strings_path, f'{name}: {value}')
    except (OSError, ET.ParseError) as exc:
        add('error', 'STRINGS_UNREADABLE', strings_path, type(exc).__name__)

    auth_path = 'TMessagesProj/src/main/res/xml/auth.xml'
    try:
        auth = _read_xml(root / auth_path)
        label = auth.get(ANDROID + 'label', '')
        if label.startswith('@string/'):
            key = label.split('/', 1)[1]
            if LEGACY.search(strings.get(key, '')):
                add('review', 'LEGACY_ACCOUNT_LABEL', auth_path, f'{label} -> {strings[key]}')
        elif LEGACY.search(label):
            add('review', 'LEGACY_ACCOUNT_LABEL', auth_path, label)
        for key in ('icon', 'smallIcon'):
            val = auth.get(ANDROID + key, '')
            if 'exteraless' in val.lower():
                add('review', 'LEGACY_ACCOUNT_ICON', auth_path, f'{key}: {val}')
            if val:
                _check_resource(root, val, auth_path, add)
    except (OSError, ET.ParseError) as exc:
        add('error', 'AUTH_XML_UNREADABLE', auth_path, type(exc).__name__)

    settings_path = 'settings.gradle'
    try:
        settings = (root / settings_path).read_text(encoding='utf-8')
        for match in re.finditer(r'(?m)^\s*rootProject\.name\s*=\s*["\']([^"\']+)["\']', settings):
            if 'exteraless' in match.group(1).lower():
                add('review', 'LEGACY_BUILD_NAME', settings_path, match.group(1))
    except OSError as exc:
        add('error', 'SETTINGS_UNREADABLE', settings_path, type(exc).__name__)

    findings.sort(key=lambda f: (f['path'], f['code'], f['detail']))
    return {
        'schema': 1,
        'scope': 'visible labels/icons and diagnostic identity, not source packages or credits',
        'errors': sum(f['level'] == 'error' for f in findings),
        'review_items': sum(f['level'] == 'review' for f in findings),
        'findings': findings,
    }


def _check_resource(root: Path, value: str, source: str, add) -> None:
    """Resource existence only, not image quality or licensing."""
    match = re.fullmatch(r'@(mipmap|drawable)/([a-zA-Z0-9_]+)', value)
    if not match:
        return  # framework references / resources handled separately by AAPT2
    kind, name = match.groups()
    res = root / 'TMessagesProj/src/main/res'
    if not any(p.is_file() for p in res.glob(f'{kind}*/{name}.*')):
        add('error', 'RESOURCE_MISSING', source, value)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--strict', action='store_true', help='fail on errors (legacy review items are nonblocking)')
    args = parser.parse_args(argv)
    report = audit(args.repo)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if args.strict and report['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
