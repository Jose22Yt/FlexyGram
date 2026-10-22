#!/usr/bin/env python3
"""Fail-closed host gate for combined realAlpha local-login + offline-UI builds.

Validates source identity and Gradle opt-in wiring; DOES NOT compile Android.
--prepare materializes both overlays; --check audits existing outputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
LOCAL_ROOT = Path('build/generated/flexygram-local-login')
OFFLINE_ROOT = Path('TMessagesProj/build/generated/flexygram-offline-dialogs-ui/java')
MAIN_ROOT = Path('TMessagesProj/src/main/java')
ALPHA_ROOT = Path('TMessagesProj/src/realAlpha/java')
OFFLINE_PATCH = Path('patches/real-alpha-offline-ui/0001-native-dialogs-offline-ui.patch')
EXPECTED_OFFLINE = frozenset(('org/telegram/ui/DialogsActivity.java',
    'org/telegram/ui/Adapters/DialogsAdapter.java',
    'org/telegram/ui/Adapters/DialogsSearchAdapter.java'))
EXPECTED_ALPHA = frozenset(('org/telegram/ui/realalpha/RealAlphaActivity.java',
    'org/telegram/ui/realalpha/RealAlphaBootstrap.java',
    'org/telegram/ui/realalpha/RealAlphaPolicy.java'))

class PreflightError(RuntimeError):
    pass

def fail(code):
    raise PreflightError(code)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_file(root, relative):
    """Refuse symlink traversal through an input or generated path."""
    path = root / relative
    if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root.parent):
        fail('SYMLINK_SOURCE_OR_OUTPUT:' + relative.as_posix())
    if not path.is_file():
        fail('MISSING_FILE:' + relative.as_posix())
    return path.read_bytes()

def check_sha(root, relative, sha):
    if digest(read_file(root, relative)) != sha:
        fail('SHA256_MISMATCH:' + relative.as_posix())

def inventory(root, relative):
    try:
        return json.loads(read_file(root, relative).decode('utf-8'))
    except (ValueError, UnicodeDecodeError) as exc:
        fail('INVALID_INVENTORY:' + relative.as_posix() + ':' + type(exc).__name__)

def require_keys(found, expected, code):
    if set(found) != set(expected):
        fail(code)

def inspect(root, generated=True):
    root = Path(root).absolute()
    if not root.is_dir() or root.is_symlink():
        fail('INVALID_CHECKOUT_ROOT')
    offline = inventory(root, Path('tools/real_alpha_offline_ui/sources.json'))
    originals = inventory(root, Path('tools/real_alpha_local_login/originals.json'))
    generated_alpha = inventory(root, Path('tools/real_alpha_local_login/generated.json'))
    native_login = inventory(root, Path('patches/native-login-pages/inventory.json'))
    require_keys(offline['sources'], EXPECTED_OFFLINE, 'OFFLINE_SOURCE_INVENTORY_CHANGED')
    require_keys(originals, EXPECTED_ALPHA, 'REALALPHA_ORIGINAL_INVENTORY_CHANGED')
    require_keys(generated_alpha, EXPECTED_ALPHA, 'REALALPHA_GENERATED_INVENTORY_CHANGED')
    check_sha(root, OFFLINE_PATCH, offline['patch_sha256'])
    for p, hashes in offline['sources'].items():
        check_sha(root, MAIN_ROOT / p, hashes['original_sha256'])
    for p, sha in originals.items():
        check_sha(root, ALPHA_ROOT / p, sha)
    check_sha(root, MAIN_ROOT / 'org/telegram/ui/LoginActivity.java', native_login['target_sha256'])
    for p, sha in native_login['prerequisites'].items():
        rel = Path(p)
        if rel.is_absolute() or '..' in rel.parts or not rel.as_posix().startswith('patches/'):
            fail('UNSAFE_PATCH_REFERENCE')
        check_sha(root, rel, sha)
    # No generated source can silently shadow another generated class.
    local_login = 'org/telegram/ui/LoginActivity.java'
    if set(EXPECTED_OFFLINE).intersection(set(EXPECTED_ALPHA) | {local_login}):
        fail('DUPLICATE_GENERATED_JAVA_CLASS')
    gradle = read_file(root, Path('TMessagesProj/build.gradle')).decode('utf-8')
    overlay_gradle = read_file(root, Path('gradle/real-alpha-offline-ui.gradle')).decode('utf-8')
    required_main = (
        "sourceSets.main.java.exclude('org/telegram/ui/LoginActivity.java')",
        "rootProject.file('build/generated/flexygram-local-login/realAlpha')",
        "file('src/realAlphaLocalLogin/java')",
        'sourceSets.realAlpha.java.setSrcDirs(',
        'if (localLoginPagesEnabled && startupDiagnosticsEnabled)',
        "if (localLoginPagesEnabled && !(flavor == 'realAlpha' && builder.buildType == 'debug'))",
        'apply from: rootProject.file("gradle/real-alpha-offline-ui.gradle")',
        "if (localLoginPagesEnabled && providers.gradleProperty('flexygramOfflineDialogsUi').orNull == 'true')",
        "tasks.register('verifyCombinedRealAlphaSources', Exec)",
        "tasks.named('preBuild').configure { dependsOn verifyCombinedRealAlphaSources }",
    )
    for token in required_main:
        if token not in gradle:
            fail('MISSING_LOCAL_LOGIN_GRADLE_GUARD:' + token)
    required_offline = (
        "providers.gradleProperty('flexygramOfflineDialogsUi').orNull == 'true'",
        "providers.gradleProperty('flexygramRealAlpha').orNull != 'true'",
        "providers.gradleProperty('flexygramRealAlphaStartupDiagnostics').orNull == 'true'",
        'android.sourceSets.main.java.exclude(path)',
        'android.sourceSets.realAlpha.java.srcDir(overlayRoot)',
        'android.sourceSets.realAlpha.res.srcDir(',
        "if (flavor != 'realAlpha' || builder.buildType != 'debug')",
    )
    for token in required_offline:
        if token not in overlay_gradle:
            fail('MISSING_OFFLINE_GRADLE_GUARD:' + token)
    if generated:
        expected = {LOCAL_ROOT / 'java' / local_login: native_login['overlay_sha256']}
        expected.update({LOCAL_ROOT / 'realAlpha' / p: sha for p, sha in generated_alpha.items()})
        expected.update({OFFLINE_ROOT / p: hashes['overlay_sha256'] for p, hashes in offline['sources'].items()})
        for path, sha in expected.items():
            check_sha(root, path, sha)
        for location, expected_paths in (
            (LOCAL_ROOT / 'java', {local_login}),
            (LOCAL_ROOT / 'realAlpha', set(EXPECTED_ALPHA)),
            (OFFLINE_ROOT, set(EXPECTED_OFFLINE)),
        ):
            folder = root / location
            seen = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() or p.is_symlink()}
            if seen != expected_paths:
                fail('GENERATED_SOURCE_INVENTORY_CHANGED:' + location.as_posix())
    return {'result': 'PASS', 'scope': 'realAlphaDebug + local login + offline UI',
            'checked_original_java': 7, 'checked_generated_java': 7 if generated else 0,
            'materialized_sources_checked': generated, 'android_compiled': False,
            'signed': False, 'network_required': False}

def prepare(root):
    inspect(root, generated=False)
    for script in ('tools/real_alpha_local_login/materialize.py',
                   'tools/real_alpha_offline_ui/materialize.py'):
        subprocess.run([sys.executable, str(root / script)], cwd=root, check=True,
                       capture_output=True, text=True)
    return inspect(root, generated=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true',
                      help='Materialize both overlays and verify')
    mode.add_argument('--check', action='store_true',
                      help='Verify existing overlays without modifying them')
    mode.add_argument('--static', action='store_true',
                      help='Verify original sources and selection only')
    args = parser.parse_args()
    try:
        result = prepare(ROOT) if args.prepare else inspect(ROOT, generated=not args.static)
    except (PreflightError, subprocess.CalledProcessError) as exc:
        print(json.dumps({'result': 'FAIL', 'reason': str(exc), 'android_compiled': False}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == '__main__':
    sys.exit(main())
