#!/usr/bin/env python3
"""Isolated API35 Android measurement/accessibility/draw of actual production settings cells.
No APK, account, network client or original animation engine is run. See stubs.py for
explicit service/animated-value/switch test doubles; never a complete screen screenshot.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse,unquote
from xml.etree import ElementTree as ET
import zipfile
from stubs import sources
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sdk-root',type=Path,required=True)
    p.add_argument('--maven',default='mvn')
    a=p.parse_args()
    out=ROOT/'build/connected-alpha-matte-visual';out.mkdir(parents=True,exist_ok=True)
    android=a.sdk_root.resolve()/'platforms/android-37.0/android.jar'
    if not android.is_file():raise SystemExit('API37 Android SDK jar required')
    shutil.rmtree(out/'src',ignore_errors=True);shutil.rmtree(out/'target/test-classes',ignore_errors=True)
    src=out/'src/test/java';src.mkdir(parents=True)
    native=''
    for name in ('TextSettingsCell','TextDetailSettingsCell','TextCheckCell2','TextCheckCell'):
        path='org/telegram/ui/Cells/'+name+'.java';text=(ROOT/'TMessagesProj/src/main/java'/path).read_text();native+=text
        dest=src/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
    for path,text in sources(native).items():
        dest=src/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
    for name in ('MatteSettingsLayout','MatteTextSettingsCell','MatteDetailSettingsCell','MatteExpandableSwitchCell','MatteTextCheckCell','FreshInstallSavePath','SignatureNativeRowSurface'):
        path='app/flexygram/settings/'+name+'.java';dest=src/path;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/'TMessagesProj/src/main/java'/path,dest)
    for file in (ROOT/'TMessagesProj/src/main/java/app/flexygram/motion').glob('*.java'):
        # Navigation bridge is compiled in motion_native; this fixture covers Matte pressure.
        if file.name in ('FlexyMotionActivity.java', 'SpringAnimation.java'): continue
        dest=src/'app/flexygram/motion'/file.name
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,dest)
    shutil.copyfile(HERE/'MatteVisualTest.java.in',src/'MatteVisualTest.java')
    shutil.copyfile(HERE/'pom.xml',out/'pom.xml')
    cmd=[a.maven,'-B','-f',str(out/'pom.xml'),'-Dandroid.sdk.jar='+str(android)]
    proxy=urlparse(os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy') or '')
    with tempfile.TemporaryDirectory(prefix='matte-maven-') as tmp:
        if proxy.hostname:
            settings=ET.Element('settings',{'xmlns':'http://maven.apache.org/SETTINGS/1.0.0'})
            element=ET.SubElement(ET.SubElement(settings,'proxies'),'proxy')
            values={'id':'runtime','active':'true','protocol':'http','host':proxy.hostname,'port':str(proxy.port or 80)}
            if proxy.username:values['username']=unquote(proxy.username)
            if proxy.password:values['password']=unquote(proxy.password)
            for k,v in values.items():ET.SubElement(element,k).text=v
            f=Path(tmp)/'settings.xml';f.write_bytes(ET.tostring(settings));f.chmod(0o600)
            cmd+=['-s',str(f),'-Dprobe.proxy.host='+proxy.hostname,'-Dprobe.proxy.port='+str(proxy.port or 80)]
        subprocess.run(cmd+['dependency:resolve'],check=True)
        aar=out/'target/aar';aar.mkdir(parents=True,exist_ok=True)
        for group,artifact,version in [('androidx.test','monitor','1.8.0'),('androidx.test.espresso','espresso-idling-resource','3.7.0')]:
            path=Path.home()/'.m2/repository'/group.replace('.','/')/artifact/version/(artifact+'-'+version+'.aar')
            with zipfile.ZipFile(path) as z:(aar/(artifact+'.jar')).write_bytes(z.read('classes.jar'))
        subprocess.run(cmd+['test'],check=True)
    print('PASS actual production/native cell layout and accessibility probe; full app/device/animation/FPS NOT_TESTED.')
if __name__=='__main__':main()
