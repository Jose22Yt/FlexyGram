#!/usr/bin/env python3
"""Isolated Compose/Android layout regression. Builds a JVM test library, never an APK.
Only the native FlexyGram host APIs are explicit doubles; Compose layout is real.
Requires JDK21, Android SDK37/build-tools36 and network/cached Maven dependencies.
"""
import argparse,json,os,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--sdk-root',type=Path,required=True)
 p.add_argument('--output-dir',type=Path,required=True)
 p.add_argument('--gradle',type=Path,default=ROOT/'gradlew')
 args=p.parse_args();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
 central_url = os.environ.get('FLEXY_MAVEN_CENTRAL_URL')
 robolectric_repo = ''
 if central_url:
  robolectric_repo = 'maven { url = uri(' + json.dumps(central_url) + '); content { includeGroup("org.robolectric") } }; '
 (out/'settings.gradle').write_text(
  "pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }\n"
  "dependencyResolutionManagement { repositories { google(); " + robolectric_repo
  + "mavenCentral() } }\nrootProject.name='KyantLayoutProbe'\n")
 build_script = Path(__file__).with_name('build.gradle').read_text()
 if central_url:
  build_script = build_script.replace("'https://repo.maven.apache.org/maven2'", json.dumps(central_url))
 (out/'build.gradle').write_text(build_script)
 (out/'gradle.properties').write_text('org.gradle.jvmargs=-Xmx1536m\nandroid.useAndroidX=true\n')
 (out/'local.properties').write_text('sdk.dir='+args.sdk_root.resolve().as_posix()+'\n')
 source=ROOT/'TMessagesProj/src/main'
 for kind in ['java','kotlin']:
  target=out/'src/main'/kind/'app/flexygram/kyant'
  shutil.copytree(source/kind/'app/flexygram/kyant',target,dirs_exist_ok=True)
 (out/'src/main/java/app/flexygram/kyant/KyantDockSettingsActivity.java').unlink(missing_ok=True)
 effects=out/'src/main/java/app/flexygram/effects'
 effects.mkdir(parents=True,exist_ok=True)
 for name in ['ChatEdgeReflection.java','ChatEdgeStyle.java']:
  shutil.copyfile(source/'java/app/flexygram/effects'/name,effects/name)
 shutil.copytree(ROOT/'buildSrc/src',out/'buildSrc/src',dirs_exist_ok=True)
 shutil.copyfile(ROOT/'buildSrc/build.gradle.kts',out/'buildSrc/build.gradle.kts')
 shutil.copytree(Path(__file__).with_name('stubs'),out/'src/main/java',dirs_exist_ok=True)
 raw=out/'src/main/res/raw/kyant_probe.json';raw.parent.mkdir(parents=True,exist_ok=True)
 raw.write_text('{"v":"5.7.4","fr":48,"ip":10,"op":130,"w":32,"h":32,"layers":[]}')
 test=out/'src/test/kotlin/app/flexygram/kyant/NativeBoundsTest.kt';test.parent.mkdir(parents=True,exist_ok=True)
 for kotlin_test in Path(__file__).parent.glob('*Test.kt'):
  shutil.copyfile(kotlin_test, test.parent/kotlin_test.name)
 for extra in Path(__file__).parent.glob('*Test.java'):
  java_test=out/'src/test/java/app/flexygram/kyant'/extra.name
  java_test.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(extra, java_test)
 subprocess.run([str(args.gradle.resolve()),'-p',str(out),'--no-daemon','--max-workers=2','--console=plain','testDebugUnitTest'],check=True)
 generated=list((out/'build/generated').rglob('ResLottieMeta.java'))
 assert len(generated)==1 and 'pack(R.raw.kyant_probe, 48, 120, false)' in generated[0].read_text()
 print('PASS: original Lottie generation and Compose physical bounds LTR/RTL/resize and native host touch dispatch; actual phone/GPU appearance NOT_TESTED.')
if __name__=='__main__':main()
