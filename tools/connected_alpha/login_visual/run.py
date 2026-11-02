#!/usr/bin/env python3
"""Render production login views with isolated native Android graphics.

Requires JDK 17+, Maven and Android API37/build-tools36. Does not initialize Telegram,
exercise login/voice/IME, emulate Android17 or replace physical chat acceptance.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse, unquote
from xml.etree import ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', type=Path, required=True)
    parser.add_argument('--maven', default='mvn')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'build/connected-alpha-login-visual')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    sdk = args.sdk_root.resolve()
    aapt = sdk/'build-tools/36.0.0/aapt2'
    android = sdk/'platforms/android-37.0/android.jar'
    if not aapt.is_file() or not android.is_file():
        raise SystemExit('Original build-tools36/API37 required; no resource validation skipped.')
    shutil.rmtree(output/'res', ignore_errors=True)
    shutil.rmtree(output/'src/test/java', ignore_errors=True)
    for name in ('resources.zip','resources.ap_'): (output/name).unlink(missing_ok=True)
    res = output/'res/drawable'
    res.mkdir(parents=True, exist_ok=True)
    for name in ('foreground','background'):
        shutil.copyfile(HERE/('work1_plane_'+name+'.xml'),res/('flexy_blue_'+name+'.xml'))
    (res/'msg_send.xml').write_text('<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24"><path android:fillColor="#FF1767C4" android:pathData="M2,2L22,12L2,22L6,12Z"/></vector>')
    values=output/'res/values';values.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/'TMessagesProj/src/main/res/values/flexygram_login.xml',values/'login.xml')
    (values/'shared.xml').unlink(missing_ok=True)
    mipmap=output/'res/mipmap-anydpi-v26';mipmap.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(HERE/'work1_adaptive.xml',mipmap/'ic_flexy_blue.xml')
    for locale in ('values-es','values-ru'):
        target=output/'res'/locale;target.mkdir(exist_ok=True)
        shutil.copyfile(ROOT/('TMessagesProj/src/main/res/'+locale+'/flexygram_login.xml'),target/'login.xml')
    manifest = output/'AndroidManifest.xml'
    manifest.write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="app.flexygram.visualprobe"><uses-sdk android:minSdkVersion="24"/><application/></manifest>')
    subprocess.run([str(aapt), 'compile', '--dir', str(res.parent), '-o', str(output/'resources.zip')], check=True)
    subprocess.run([str(aapt), 'link', '-I', str(android), '--manifest', str(manifest),
                    '--java', str(output/'src/test/java'), '--custom-package', 'org.telegram.messenger', '-o', str(output/'resources.ap_'), str(output/'resources.zip')], check=True)
    # Remove stale bytecode before repeated visual comparisons after policy edits.
    shutil.rmtree(output/'target/test-classes', ignore_errors=True)
    source = output/'src/test/java'
    source.mkdir(parents=True, exist_ok=True)
    package = source/'app/flexygram/login'
    package.mkdir(parents=True, exist_ok=True)
    production = ROOT/'TMessagesProj/src/main/java/app/flexygram/login'
    for path in production.glob('*.java'): shutil.copyfile(path,package/path.name)
    from stubs import STUBS
    for name,data in STUBS.items():
        path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(data)
    native=source/'org/telegram/ui/Components';native.mkdir(parents=True,exist_ok=True)
    for name in ('OutlineTextContainerView.java','SimpleFloatPropertyCompat.java'):
        shutil.copyfile(ROOT/('TMessagesProj/src/main/java/org/telegram/ui/Components/'+name),native/name)
    shutil.copyfile(HERE/'LoginVisualTest.java.in', source/'LoginVisualTest.java')
    shutil.copyfile(HERE/'pom.xml', output/'pom.xml')
    repository = Path.home()/'.m2/repository'
    command = [args.maven, '-B', '-f', str(output/'pom.xml'), '-Dandroid.sdk.jar='+str(android)]
    proxy = urlparse(os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy') or '')
    with tempfile.TemporaryDirectory(prefix='composer-maven-') as tmp:
        if proxy.hostname:
            # Reuse the execution environment's transport; never log/store proxy credentials.
            settings = ET.Element('settings', {'xmlns':'http://maven.apache.org/SETTINGS/1.0.0'})
            p = ET.SubElement(ET.SubElement(settings, 'proxies'), 'proxy')
            values = {'id':'runtime', 'active':'true', 'protocol':'http', 'host':proxy.hostname, 'port':str(proxy.port or 80)}
            if proxy.username: values['username'] = unquote(proxy.username)
            if proxy.password: values['password'] = unquote(proxy.password)
            for key, value in values.items(): ET.SubElement(p, key).text = value
            path = Path(tmp)/'settings.xml'
            path.write_bytes(ET.tostring(settings)); path.chmod(0o600)
            command += ['-s', str(path), '-Dprobe.proxy.host='+proxy.hostname, '-Dprobe.proxy.port='+str(proxy.port or 80)]
        subprocess.run(command + ['dependency:resolve'], check=True)
        aar_dir = output/'target/aar'
        aar_dir.mkdir(parents=True, exist_ok=True)
        for group, artifact, version in [('androidx.test', 'monitor', '1.8.0'), ('androidx.test.espresso', 'espresso-idling-resource', '3.7.0'), ('androidx.dynamicanimation', 'dynamicanimation', '1.0.0')]:
            path = repository/group.replace('.', '/')/artifact/version/(artifact+'-'+version+'.aar')
            with zipfile.ZipFile(path) as archive:
                (aar_dir/(artifact+'.jar')).write_bytes(archive.read('classes.jar'))
        subprocess.run(command + ['-Dprobe.native=true', 'test'], check=True)
    print('PASS: API37 login resources, API35 production welcome/native outline probes; full auth and device performance NOT_TESTED.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
