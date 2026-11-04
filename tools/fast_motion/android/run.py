#!/usr/bin/env python3
"""API 35 native animation behavior, SDK 37 compilation; no app/APK build."""
import importlib.util,sys,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
if '--dynamics-aar' not in sys.argv:
 raise SystemExit('Provide --dynamics-aar pointing to the official androidx.dynamicanimation 1.0.0 AAR already used by the app.')
i=sys.argv.index('--dynamics-aar');aar=Path(sys.argv[i+1]);del sys.argv[i:i+2]
if '--collection-jar' not in sys.argv: raise SystemExit('Provide --collection-jar from the existing AndroidX Collection dependency.')
i=sys.argv.index('--collection-jar');collection=Path(sys.argv[i+1]).resolve();del sys.argv[i:i+2]
spec=importlib.util.spec_from_file_location('motion_android_harness',ROOT/'tools/connected_alpha/music_visual/run.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
from stubs import write

def dependency(output,repository,sdk):
 target=output/'target/aar/dynamicanimation.jar';target.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(aar) as archive:target.write_bytes(archive.read('classes.jar'))
 ns={'m':'http://maven.apache.org/POM/4.0.0'};ET.register_namespace('',ns['m'])
 pom=ET.parse(output/'pom.xml');parent=pom.getroot().find('m:dependencies',ns)
 d=ET.SubElement(parent,'{'+ns['m']+'}dependency')
 for name,value in [('groupId','local.androidx'),('artifactId','dynamicanimation'),('version','1.0.0'),('scope','system'),('systemPath',str(target))]:ET.SubElement(d,'{'+ns['m']+'}'+name).text=value
 d=ET.SubElement(parent,'{'+ns['m']+'}dependency')
 for name,value in [('groupId','local.androidx'),('artifactId','collection'),('version','1.2.0'),('scope','system'),('systemPath',str(collection))]:ET.SubElement(d,'{'+ns['m']+'}'+name).text=value
 pom.write(output/'pom.xml',encoding='utf-8',xml_declaration=True)
if __name__=='__main__':raise SystemExit(h.main(here=HERE,test_class='FastMotionAndroidTest',stubs_writer=write,dependency_writer=dependency))
