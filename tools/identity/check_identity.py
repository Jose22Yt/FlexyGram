#!/usr/bin/env python3
"""Source-only identity audit. Never invokes Gradle, Android tools or a signer."""
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASE = '258dd3590f40ca0083a4b7bad6b413433c4e2c14'
ALPHA = 'io.github.jose22yt.flexygram.alpha'
BETA = 'com.flexygram.messenger'
A = '{http://schemas.android.com/apk/res/android}'
XML_NAMES = ['auth.xml', 'sync_contacts.xml', 'contacts.xml', 'auth_menu.xml', 'shortcuts.xml']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return (ROOT / path).read_text()


def original(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)


def main():
    props = dict(re.findall(r'^(\w+)=(.*)$', read('gradle.properties'), re.M))
    require(props['APP_PACKAGE'] == BETA, 'Default package must be Beta')
    require(props['BETA_VERSION_NAME'] == '1.0.0-beta.1', 'Unexpected Beta version')
    require(int(props['BETA_VERSION_CODE']) > 1286, 'Beta version code must increase')
    gradle = read('TMessagesProj/build.gradle')
    require("namespace = 'org.telegram.messenger'" in gradle, 'Preserve namespace')
    require("variant.applicationId.set(variant.buildType == 'connectedAlpha' ? '" + ALPHA + "' : APP_PACKAGE)" in gradle, 'Explicit variant identity missing')
    require("builder.buildType in ['connectedAlpha', 'beta']" in gradle, 'Unexpected enabled variants')
    require('signingConfigs.release : signingConfigs.debug' not in gradle, 'Release/debug fallback')
    for channel, package in [('connectedAlpha', ALPHA), ('beta', BETA)]:
        merged = ROOT / 'TMessagesProj/src' / channel / 'res'
        for name in XML_NAMES:
            path = merged / 'xml' / name
            text = path.read_text()
            root = ET.fromstring(text)
            require(package in text, f'{channel}: package missing from {name}')
            require((BETA if channel == 'connectedAlpha' else ALPHA) not in text, f'{channel}: cross-identity {name}')
            if name in ['auth.xml', 'sync_contacts.xml']:
                require(root.get(A + 'accountType') == package, 'Wrong account type')
            if name in ['shortcuts.xml', 'auth_menu.xml']:
                for node in root.iter():
                    if A + 'targetPackage' in node.attrib:
                        require(node.get(A + 'targetPackage') == package, 'Wrong shortcut package')
        for p in merged.rglob('*.xml'):
            ET.parse(p)
    manifest = ET.fromstring(read('TMessagesProj/src/main/AndroidManifest.xml'))
    require(A + 'sharedUserId' not in manifest.attrib, 'Unexpected shared UID')
    for provider in manifest.find('application').findall('provider'):
        require(provider.get(A + 'authorities', '').startswith('${applicationId}.'), 'Hardcoded provider identity')
    require((ROOT/'TMessagesProj/src/main/AndroidManifest.xml').read_bytes() == original('TMessagesProj/src/main/AndroidManifest.xml'), 'Unexpected manifest edit')
    # Compare every original Alpha asset; only the new identity XML files are additions.
    assets = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, 'TMessagesProj/src/connectedAlpha/res'], cwd=ROOT, text=True).splitlines()
    for name in assets:
        require((ROOT/name).read_bytes() == original(name), 'Alpha asset changed: ' + name)
        beta = name.replace('/connectedAlpha/', '/beta/')
        expected = original(name)
        if name.endswith('.xml'):
            expected = expected.replace(ALPHA.encode(), BETA.encode()).replace(b'FlexyGram Alpha', b'FlexyGram')
        require((ROOT/beta).read_bytes() == expected, 'Beta approved asset mismatch: ' + beta)
    for name in XML_NAMES:
        main = 'TMessagesProj/src/main/res/xml/' + name
        require(read(main) == original(main).decode().replace(ALPHA, BETA), 'Unexpected main XML delta')
        require((ROOT/'TMessagesProj/src/connectedAlpha/res/xml'/name).read_bytes() == original(main), 'Alpha XML regression')
    # Any Java/Kotlin/C++ change must be exactly the reviewed identity predicate.
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, '--', 'TMessagesProj'], cwd=ROOT, text=True).splitlines()
    for name in changed:
        if name.endswith(('.java', '.kt', '.cpp', '.h', '.c')):
            if name != 'TMessagesProj/src/main/java/org/telegram/messenger/SharedConfig.java':
                sys.path.insert(0, str(ROOT/'tools/connected_alpha'))
                from performance_p0_contract import restore as project_performance, original as before_performance
                data = (ROOT/name).read_bytes() if (ROOT/name).is_file() else b''
                require(project_performance(name, data) == before_performance(name), 'Source outside exact reviewed performance overlay: ' + name)
                continue
            require(name == 'TMessagesProj/src/main/java/org/telegram/messenger/SharedConfig.java', 'Functional source modified: ' + name)
            expected = original(name).decode().replace('"'+ALPHA+'".equals(ApplicationLoader.applicationContext.getPackageName())', 'BuildConfig.CONNECTED_ALPHA')
            require(read(name) == expected, 'Unreviewed SharedConfig change')
    identity = dict(re.findall(r'^(\w+)=(.*)$', read('config/signing/identity.properties'), re.M))
    official = '5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c'
    require(identity['applicationId'] == BETA and identity['alias'] == 'flexygram-release', 'Registered identity/package mismatch')
    require(identity['certificateSha256'] == official, 'Official fingerprint changed')
    require(hashlib.sha256((ROOT/identity['certificateFile']).read_bytes()).hexdigest() == official, 'Registered public DER mismatch')
    require(official in read('tools/signing/VerifySigning.java') and official in read('tools/signing/owner_wizard.py'), 'Local verifier/wizard pin mismatch')
    require("'-genkeypair'" not in read('tools/signing/owner_wizard.py'), 'New key generation must remain disabled')
    signing = read('gradle/flexygram-beta.gradle')
    require('def expected = pinned' in signing and 'An external fingerprint cannot replace' in signing, 'Environment may not replace official identity')
    for token in ['FLEXYGRAM_RELEASE_CERT_SHA256', 'KeyStore.getInstance(keyFile, storePass)', 'java.security.PrivateKey', 'cert.checkValidity()', 'CN=Android Debug', 'preBetaBuild', 'src/beta/google-services.json', 'keyFile.toPath().startsWith']:
        require(token in signing, 'Missing signing gate: ' + token)
    # Every new source file is text/approved icon data, never a private input or APK.
    paths = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    historical = set(subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE], cwd=ROOT, text=True).splitlines())
    for name in set(paths) - historical:
        if name.endswith(('.keystore', '.jks', '.p12', '.pfx', '.apk', '.aab', '.pem', '.key')) or name.endswith('google-services.json'):
            raise ValueError('Private/generated material in source delivery: ' + name)
    docs = [ROOT/p for p in ['README.md', 'CREDITS.md', 'CHANGELOG.md', 'CONTRIBUTING.md']]
    docs += [ROOT/'docs'/p for p in ['BUILDING.md', 'SIGNING.md', 'FEATURES.md', 'ANDROID_IDENTITY.md', 'IDENTITY_REVIEW.md', 'screenshots/README.md', 'SIGNING_OWNER_CUSTODY.md', 'SIGNING_CUSTODY_REVIEW.md']]
    for doc in docs:
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
            if not re.match(r'[a-z]+:|#', target):
                require((doc.parent/target.split('#')[0]).exists(), f'Broken relative link: {doc.name} -> {target}')
    for name in ['tools/connected_alpha/check_source.py', 'tools/connected_alpha/check_resources.py', 'tools/connected_alpha/test_signature1271.py']:
        ast.parse(read(name))
    workflow = read('.github/workflows/pr.yml')
    require(workflow.count("github.head_ref != 'feat/official-identity-beta-preparation'") == 2, 'General Android PR jobs must exclude mission branch')
    job = workflow.split('  official-identity-static:\n', 1)[1]
    require('tools/identity/check_identity.py' in job and 'gradlew' not in job, 'Mission job must remain Python-only')
    sys.path.insert(0, str(ROOT/'tools/connected_alpha'))
    from identity_beta_contract import verify_current, spec, restore
    verify_current()
    for name in spec()['reviewed']:
        data = (ROOT/name).read_bytes() if (ROOT/name).is_file() else b''
        mutated = data + b'\nUNREVIEWED\n'
        require(restore(name, mutated) == mutated, 'Audit accepted unknown mutation: ' + name)
    subprocess.run(['git', 'diff', '--check', BASE], cwd=ROOT, check=True)
    print(json.dumps({'status': 'PASS_SOURCE_ONLY', 'base': BASE, 'alpha_application_id': ALPHA,
                      'beta_application_id': BETA, 'alpha_assets_preserved': len(assets),
                      'manifest_sha256': hashlib.sha256(original('TMessagesProj/src/main/AndroidManifest.xml')).hexdigest(),
                      'historical_full_suite': 'NOT_RUN_BY_THIS_CHECK', 'beta_key': 'OWNER_REPORTED_CREATED_PRIVATE_NOT_RECEIVED', 'certificate_sha256': official, 'independent_backups': 'OWNER_CONFIRMATION_PENDING', 'gradle_and_apk': 'NOT_RUN', 'android_runtime': 'NOT_TESTED'}, indent=2))


if __name__ == '__main__':
    main()
