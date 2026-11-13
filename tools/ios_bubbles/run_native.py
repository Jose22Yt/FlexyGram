#!/usr/bin/env python3
"""Run isolated Android graphics/widgets tests. Does not build or package an APK."""
import argparse, importlib.util, os, shutil, subprocess, tempfile, urllib.request, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse, unquote
ROOT=Path(__file__).resolve().parents[2]

def main():
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('--android-jar',type=Path,required=True)
    args.add_argument('--maven',default='mvn')
    args.add_argument('--output',type=Path,required=True)
    options=args.parse_args();out=options.output.resolve();source=out/'src/test/java';source.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('bubble_hosts',ROOT/'tools/connected_alpha/bubble_visual/stubs.py')
    hosts=importlib.util.module_from_spec(spec);spec.loader.exec_module(hosts);hosts.write_stubs(source,ROOT)
    theme=source/'org/telegram/ui/ActionBar/Theme.java'
    theme.write_text(theme.read_text().replace('public class Theme {','public class Theme {public static final int key_chat_serviceBackground=130,key_chat_serviceBackgroundSelected=131;'))
    # Service wallpaper availability is isolated; native MessageDrawable, paths, paints and widgets are real.
    (source/'app/flexygram/bubbles/ServiceBubbleSurface.java').write_text('package app.flexygram.bubbles;import android.graphics.*;public class ServiceBubbleSurface{public boolean draw(Canvas c,Path p,Object provider,int w,int h,int x,int y,int alpha,boolean selected){return false;}public boolean drawCached(Canvas c,Path p,Object provider,SignatureWallpaperBlur.Owner owner,int x,int y,int alpha,boolean selected){return false;}public static int textColor(Object p){return 0xff112233;}}')
    # The stage uses real Android layout/bubbles; the header host below only supplies
    # the instanceof/settingsChanged contract, not header appearance or navigation.
    for name in ['app/flexygram/icons/IosListCheckDrawable.java', 'app/flexygram/settings/signature/ConversationPreviewStage.java']:
        path=source/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text((ROOT/'TMessagesProj/src/main/java'/name).read_text())
    path=source/'app/flexygram/header/HeaderPreviewView.java';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('package app.flexygram.header;public class HeaderPreviewView extends android.view.View{public HeaderPreviewView(android.content.Context c){super(c);}public void settingsChanged(){}}')
    for name in ['flexy_check_ios27','flexy_halfcheck_ios27']:
        (out/(name+'.xml')).write_bytes((ROOT/'TMessagesProj/src/main/res/drawable'/(name+'.xml')).read_bytes())
    test=(ROOT/'tools/ios_bubbles/NativeStylesTest.java.in').read_text().replace('"/workspace/work/style-validation/compact-bubbles.png"','System.getProperty("probe.root")+"/compact-bubbles.png"')
    (source/'NativeStylesTest.java').write_text(test)
    (out/'pom.xml').write_text((ROOT/'tools/connected_alpha/bubble_visual/pom.xml').read_text().replace('<version>4.17</version>','<version>4.16</version>'))
    command=[options.maven,'-B','-f',str(out/'pom.xml'),'-Dandroid.sdk.jar='+str(options.android_jar.resolve())]
    proxy=urlparse(os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy') or '')
    with tempfile.TemporaryDirectory(prefix='style-test-') as temp:
        if proxy.hostname:
            settings=ET.Element('settings');entry=ET.SubElement(ET.SubElement(settings,'proxies'),'proxy')
            fields={'id':'runtime','active':'true','protocol':'http','host':proxy.hostname,'port':str(proxy.port or 80)}
            if proxy.username:fields['username']=unquote(proxy.username)
            if proxy.password:fields['password']=unquote(proxy.password)
            for key,value in fields.items():ET.SubElement(entry,key).text=value
            path=Path(temp)/'settings.xml';path.write_bytes(ET.tostring(settings));path.chmod(0o600);command+=['-s',str(path)]
        subprocess.run(command+['dependency:resolve'],check=True)
        repository=Path.home()/'.m2/repository';aars=out/'target/aar';aars.mkdir(parents=True,exist_ok=True)
        for artifact in ['monitor','espresso-idling-resource']:
            archives=sorted(repository.rglob(artifact+'-*.aar'))
            if not archives:raise RuntimeError('Missing AndroidX test runtime: '+artifact)
            with zipfile.ZipFile(archives[-1]) as archive:(aars/(artifact+'.jar')).write_bytes(archive.read('classes.jar'))
        # Download through the same session transport; Robolectric's SDK resolver otherwise ignores HTTPS_PROXY.
        version='15-robolectric-13954326-i7';folder=repository/'org/robolectric/android-all-instrumented'/version;folder.mkdir(parents=True,exist_ok=True)
        for extension in ['pom','pom.sha512','jar','jar.sha512']:
            path=folder/('android-all-instrumented-'+version+'.'+extension)
            if not path.exists():urllib.request.urlretrieve('https://repo.maven.apache.org/maven2/org/robolectric/android-all-instrumented/'+version+'/'+path.name,path)
        subprocess.run(command+['test'],check=True)
if __name__=='__main__':main()
