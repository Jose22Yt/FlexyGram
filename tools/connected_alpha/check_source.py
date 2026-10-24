#!/usr/bin/env python3
"""Static evidence only: upstream parity and independent Android identity."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASE = '1ad6a60a6834ffca722b1a22f4fba27ecb29a061'
APP = 'io.github.jose22yt.flexygram.alpha'
A = '{http://schemas.android.com/apk/res/android}'
# These components must remain byte-identical, not reimplementations. Home's
# explicit presentation patch must reverse to the same original DialogsActivity.
CORE = [
 'src/main/java/org/telegram/ui/LoginActivity.java',
 'src/main/java/org/telegram/ui/LaunchActivity.java',
 'src/main/java/org/telegram/ui/DialogsActivity.java',
 'src/main/java/org/telegram/ui/ChatActivity.java',
 'src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java',
 'src/main/java/org/telegram/ui/ActionBar/Theme.java',
 'src/main/java/org/telegram/tgnet/ConnectionsManager.java',
 'src/main/java/org/telegram/messenger/MessagesController.java',
 'src/main/java/org/telegram/messenger/SendMessagesHelper.java',
 'src/main/java/org/telegram/messenger/MediaController.java',
 'src/main/java/org/telegram/messenger/NotificationsController.java',
 'src/main/java/app/exteraless/plugins/PluginsController.java',
 'src/main/java/app/exteraless/plugins/PythonPluginsEngine.java',
 'src/main/java/org/telegram/messenger/ContactsController.java',
 'jni/tgnet/ConnectionsManager.cpp',
]

def restore_home_presentation(actual):
    path = 'TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java'
    patch = (ROOT/'tools/connected_alpha/signature_home_dialogs.patch').read_bytes()
    headers = [line for line in patch.splitlines() if line.startswith((b'--- ', b'+++ '))]
    if headers != [('--- a/'+path).encode(), ('+++ b/'+path).encode()]:
        raise ValueError('Home parity patch must cover exactly DialogsActivity')
    with tempfile.TemporaryDirectory(prefix='home-parity-') as directory:
        target = Path(directory)/path
        target.parent.mkdir(parents=True)
        target.write_bytes(actual)
        result = subprocess.run(['git', 'apply', '--reverse', '-'], cwd=directory,
                                input=patch, capture_output=True)
        if result.returncode:
            raise ValueError('Home presentation differs from the reviewed patch')
        return target.read_bytes()

def main():
    evidence = {}
    presentation = {}
    for path in CORE:
        path = 'TMessagesProj/' + path
        expected = subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)
        actual = (ROOT/path).read_bytes()
        if path.endswith('/ui/DialogsActivity.java') and actual != expected:
            restored = restore_home_presentation(actual)
            if restored != expected:
                raise SystemExit('FAIL: Home changes native DialogsActivity beyond the reviewed presentation patch')
            presentation[path] = {'actual_sha256': hashlib.sha256(actual).hexdigest(),
                                  'restored_upstream_sha256': hashlib.sha256(restored).hexdigest()}
            continue
        if path.endswith('/ui/ChatActivity.java') and actual != expected:
            from bubble_parity import restore_bubble_presentation
            restored = restore_bubble_presentation(path, actual)
            if restored != expected: raise SystemExit('FAIL: native chat changed outside bubble presentation')
            presentation[path] = {'actual_sha256': hashlib.sha256(actual).hexdigest(), 'restored_upstream_sha256': hashlib.sha256(restored).hexdigest()}
            continue
        if path.endswith('/ui/LoginActivity.java') and actual != expected:
            from login_parity import restore_login_presentation
            restored = restore_login_presentation(path, actual)
            if restored != expected: raise SystemExit('FAIL: authentication changed outside login presentation')
            presentation[path] = {'actual_sha256': hashlib.sha256(actual).hexdigest(), 'restored_upstream_sha256': hashlib.sha256(restored).hexdigest()}
            continue
        if actual != expected:
            raise SystemExit(f'FAIL: upstream component changed: {path}')
        evidence[path] = hashlib.sha256(actual).hexdigest()
    manifest = ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').getroot()
    assert 'android.permission.INTERNET' in {p.get(A+'name') for p in manifest.findall('uses-permission')}
    assert A+'sharedUserId' not in manifest.attrib
    app = manifest.find('application')
    assert app.get(A+'allowBackup') == 'false' and app.get(A+'restoreAnyVersion') == 'false'
    assert A+'backupAgent' not in app.attrib
    assert app.get(A+'name') == 'org.telegram.messenger.ApplicationLoader'
    for provider in app.findall('provider'):
        assert provider.get(A+'authorities').startswith('${applicationId}.')
    xml = ROOT/'TMessagesProj/src/main/res/xml'
    for name in ['auth.xml', 'sync_contacts.xml']:
        assert ET.parse(xml/name).getroot().get(A+'accountType') == APP
    for name in ['auth_menu.xml','shortcuts.xml','contacts.xml']:
        assert 'com.exteraless.app' not in (xml/name).read_text()
        ET.parse(xml/name)
    assert not (ROOT/'TMessagesProj/google-services.json').exists()
    login = (ROOT/'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java').read_text()
    assert 'LOCAL_LOGIN_UNAVAILABLE' not in login
    assert all(f'class {name}' in login for name in ['PhoneView','LoginActivitySmsView','LoginActivityPasswordView'])
    assert 'APP_PACKAGE='+APP in (ROOT/'gradle.properties').read_text()
    for f in (ROOT/'TMessagesProj/src/connectedAlpha/res').glob('values*/*.xml'):
        ET.parse(f)
    print(json.dumps({'status':'PASS_STATIC_ONLY','upstream_components_identical':len(evidence),
                      'sha256':evidence,'reviewed_presentation_restores_exact_upstream':presentation,
                      'android_runtime':'NOT_TESTED'}, indent=2))

if __name__ == '__main__':
    main()
