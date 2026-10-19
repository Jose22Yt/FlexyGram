"""Audit a real merged diagnostic manifest, not an approximation of library merging.

Usage: python tests/security/manifest_surface.py MERGED_MANIFEST [OUTPUT_JSON]
No Android, account access or network operation is performed.
"""
import json
import copy
from pathlib import Path
import sys
import tempfile
import re
import subprocess
import xml.etree.ElementTree as ET

A = '{http://schemas.android.com/apk/res/android}'
PACKAGE = 'io.github.jose22yt.flexygram.diagnostic'
SIGNATURE_PERMISSION = PACKAGE + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'
LAUNCHER = 'org.telegram.messenger.ExteralessIcon'


def audit(path):
    root = ET.parse(path).getroot()
    assert root.get('package') == PACKAGE, 'Unexpected package'
    permissions = sorted(e.get(A+'name') for tag in ['uses-permission','uses-permission-sdk-23']
                         for e in root.findall(tag))
    assert permissions == sorted(['android.permission.ACCESS_NETWORK_STATE', SIGNATURE_PERMISSION]), permissions
    custom = root.findall('permission')
    assert len(custom) == 1
    assert custom[0].get(A+'name') == SIGNATURE_PERMISSION
    assert custom[0].get(A+'protectionLevel') == 'signature'
    app = root.find('application')
    assert app.get(A+'allowBackup') == 'false'
    assert app.get(A+'backupAgent') is None
    components = []
    for e in app:
        if e.tag not in ['activity','activity-alias','service','receiver','provider']:
            continue
        enabled = app.get(A+'enabled','true') != 'false' and e.get(A+'enabled','true') != 'false'
        exported = e.get(A+'exported')
        if exported is None:
            exported = e.tag != 'provider' and bool(e.findall('intent-filter'))
        else:
            exported = exported == 'true'
        row = {'type':e.tag,'name':e.get(A+'name'),'enabled':enabled,'exported':exported,
               'authority':e.get(A+'authorities'), 'filters':len(e.findall('intent-filter'))}
        components.append(row)
        if e.tag == 'provider' and row['authority']:
            assert all(value.startswith(PACKAGE+'.') for value in row['authority'].split(';')), row
        if e.tag == 'provider' and row['name'] == 'ru.noties.jlatexmath.JLatexMathInitProvider':
            assert enabled and not exported, row
            assert row['authority'] == PACKAGE+'.jlatexmathinitprovider', row
        elif e.tag in ['service','receiver','provider']:
            assert not enabled and not exported, row
        if e.tag == 'activity':
            assert not exported, row
        if e.tag == 'activity-alias' and e.get(A+'name') != LAUNCHER:
            assert not enabled and not exported, row
    public = [e for e in components if e['enabled'] and e['exported']]
    assert len(public) == 1 and public[0]['name'] == LAUNCHER, public
    entry = next(e for e in app.findall('activity-alias') if e.get(A+'name') == LAUNCHER)
    assert entry.get(A+'targetActivity') == 'org.telegram.ui.LaunchActivity'
    assert {e.get(A+'name') for e in entry.findall('.//action')} == {'android.intent.action.MAIN'}
    assert not entry.findall('.//data')
    launch = next(e for e in app.findall('activity') if e.get(A+'name') == 'org.telegram.ui.LaunchActivity')
    assert launch.get(A+'enabled','true') == 'true'
    assert not launch.findall('intent-filter'), 'Launch target must not register deep links or shares'
    return {'package':PACKAGE,'permissions':permissions,'custom_permission_protection':'signature',
            'enabled_exported':public,'components':components,'validation':'passed',
            'limits':'Static merged manifest; not an Android execution or traffic test.'}


def check_mutations(path):
    """Negative tests on copies of the actual merged manifest; no APK changes."""
    audit(path)
    original = ET.parse(path).getroot()
    cases = []
    def permission(name):
        return lambda root: ET.SubElement(root,'uses-permission',{A+'name':name})
    def component(kind,suffix,**attributes):
        def change(root):
            node = next(e for e in root.find('application').findall(kind)
                        if e.get(A+'name','').endswith(suffix))
            for key,value in attributes.items():node.set(A+key,value)
        return change
    cases.extend([
        ('INTERNET reintroduced',permission('android.permission.INTERNET')),
        ('CAMERA reintroduced',permission('android.permission.CAMERA')),
        ('Wear authorization service enabled',component('service','WearAuthListenerService',enabled='true',exported='true')),
        ('Car service enabled',component('service','TelegramCarAppService',enabled='true',exported='true')),
        ('FileProvider exposed',component('provider','FileProvider',enabled='true',exported='true')),
        ('Rendering provider exposed',component('provider','JLatexMathInitProvider',exported='true')),
        ('Launch target exposed directly',component('activity','LaunchActivity',exported='true')),
        ('Weak custom receiver permission',lambda root: root.find('permission').set(A+'protectionLevel','normal')),
        ('Backup enabled',lambda root: root.find('application').set(A+'allowBackup','true')),
        ('Unexpected library service',lambda root: ET.SubElement(root.find('application'),'service',
            {A+'name':'synthetic.unexpected.Service',A+'enabled':'true',A+'exported':'false'})),
    ])
    results = []
    with tempfile.TemporaryDirectory() as directory:
        for index,(name,mutate) in enumerate(cases):
            root = copy.deepcopy(original);mutate(root)
            candidate = Path(directory)/(str(index)+'.xml')
            ET.ElementTree(root).write(candidate,encoding='utf-8')
            try:audit(candidate)
            except AssertionError:results.append({'mutation':name,'rejected':True})
            else:raise AssertionError('Manifest regression accepted: '+name)
    return results


def audit_binary(apk,aapt2):
    """Inspect the actual packaged manifest; do not trust a stale merged output."""
    result=subprocess.run([str(aapt2),'dump','xmltree',str(apk),'--file','AndroidManifest.xml'],
                          check=True,capture_output=True,text=True)
    stack=[];manifest=None
    for line in result.stdout.splitlines():
        element=re.match(r'(\s*)E: ([\w-]+)',line)
        if element:
            indent=len(element[1]);node=ET.Element(element[2])
            while stack and stack[-1][0]>=indent:stack.pop()
            if stack:stack[-1][1].append(node)
            else:manifest=node
            stack.append((indent,node));continue
        attribute=re.match(r'\s*A: ([^=( ]+)(?:\([^)]*\))?=(.*)',line)
        if attribute and stack:
            name,value=attribute.groups()
            if value.startswith('"'):value=value.split('"')[1]
            elif '(type 0x12)' in value:value='true' if value.endswith('0xffffffff') else 'false'
            if name.endswith(':protectionLevel'):
                number=value.split(')')[-1]
                try:
                    if int(number,0)==2:value='signature'
                except ValueError:pass
            if name.startswith('android:'):name=A+name[8:]
            elif name.startswith('http://schemas.android.com/apk/res/android:'):
                name=A+name.rsplit(':',1)[1]
            stack[-1][1].set(name,value)
    assert manifest is not None
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'manifest.xml'
        ET.ElementTree(manifest).write(path,encoding='utf-8')
        return audit(path)


if __name__ == '__main__':
    if sys.argv[1] == '--negative-checks':
        results = check_mutations(sys.argv[2])
        if len(sys.argv) > 3:Path(sys.argv[3]).write_text(json.dumps(results,indent=2)+'\n')
        print('PASS:',len(results),'unsafe manifest mutations rejected')
        sys.exit(0)
    if sys.argv[1]=='--apk':
        result=audit_binary(sys.argv[2],sys.argv[3])
        print('PASS: actual APK binary manifest permission/component allowlist')
        sys.exit(0)
    result = audit(sys.argv[1])
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: merged diagnostic permission/component allowlist')
