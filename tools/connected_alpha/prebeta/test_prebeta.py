"""Pinned source audit, staged patch/policy tests and real SDK signing fixtures. No production keys/accounts."""
import hashlib,json,os,re,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from scan import BASE,WORK1,ROOT,blob,generate,paths
from prepare_identity_patch import prepare
SDK=Path(os.environ.get('FLEXY_AUDIT_SDK')or os.environ.get('ANDROID_HOME')or ROOT.parent/'toolchains/android-sdk')
TOOLS=SDK/'build-tools/36.0.0';ANDROID=SDK/'platforms/android-37.0/android.jar'
KEYS={'AppName','AppNameBeta','NagramX','OpenExtera','CustomTitleHint'}

def run(*args,**kwargs):return subprocess.run(list(map(str,args)),check=True,capture_output=True,text=True,**kwargs)
class Audit(unittest.TestCase):
 def test_application_build_and_distribution_are_byte_exact(self):
  protected=['TMessagesProj','TMessagesProj_Modules','.gitmodules','build.gradle','settings.gradle','gradle','gradlew','buildSrc','.github/workflows/pr.yml','.github/workflows/connected-alpha-arm64.yml']
  self.assertEqual(subprocess.check_output(['git','diff','--name-only',BASE,'--',*protected],cwd=ROOT),b'')
  from contract import PATHS
  self.assertFalse(any(p.startswith(('TMessagesProj/','TMessagesProj_Modules/')) for p in PATHS))
 def test_archived_readme_and_license_are_exact(self):
  self.assertEqual((ROOT/'docs/upstream/README.exteraless.md').read_bytes(),blob('README.md'))
  self.assertEqual((ROOT/'LICENSE').read_bytes(),blob('LICENSE'))
  text=(ROOT/'docs/UPSTREAM.md').read_text();self.assertIn('@the8055u',text);self.assertIn('@BlueprintDsgn',text)
 def test_generated_inventory_is_reproducible(self):
  for name,value in generate().items():self.assertEqual(json.loads((ROOT/'docs/prebeta'/name).read_text()),value,name)
 def test_readme_has_current_identity_and_no_invented_distribution(self):
  text=(ROOT/'README.md').read_text();self.assertIn('# FlexyGram',text);self.assertIn('@Lukhou23',text);self.assertIn('Jose22Yt',text)
  self.assertLess(text.index('# FlexyGram'),text.index('## Origen'))
  for stale in ['# exteraless','## Ramas y alcance del PASO 1','Sin APK','Código original sin modificaciones funcionales'] :self.assertNotIn(stale,text)
  self.assertIn('distribución',text);self.assertIn('privada',text);self.assertIn('Beta',text)
 def test_new_document_links_resolve(self):
  tracked=set(paths())
  for document in [ROOT/'README.md',ROOT/'CONTRIBUTING.md',*list((ROOT/'docs').glob('*.md'))]:
   text=document.read_text()
   links=re.findall(r'\]\(([^)]+)\)|src="([^"]+)"',text)
   for pair in links:
    link=next(x for x in pair if x).split('#',1)[0]
    if not link or '://'in link or link.startswith('mailto:'):continue
    path=(document.parent/link).resolve();relative=str(path.relative_to(ROOT))
    self.assertTrue(path.exists()or relative in tracked,(document.name,link))
 def test_production_gates_still_precede_requests(self):
  source=blob('TMessagesProj/src/main/java/app/exteraless/updater/GitHubUpdater.java').decode()
  for name,nextname in [('public static void check(', 'public static void fetch('),('public static void fetch(', 'public static long lastCheck('),('public static void download(', 'private static void install(')]:
   body=source[source.index(name):source.index(nextname)]
   self.assertIn('BuildConfig.CONNECTED_ALPHA',body)
   gate=body.index('BuildConfig.CONNECTED_ALPHA')
   for token in ['new Thread(', 'client().newCall(', 'fetch((found']:
    if token in body:self.assertLess(gate,body.index(token))
  self.assertIn('"exteraless/exteraless"',source) # Evidence of staged rather than silently activated migration.
  base=blob('TMessagesProj/src/main/java/tw/nekomimi/nekogram/helpers/remote/BaseRemoteHelper.java').decode()
  self.assertIn('CHANNEL_METADATA_ID = 0L',base);self.assertIn('CHANNEL_METADATA_NAME = ""',base)
  helper=blob('TMessagesProj/src/main/java/tw/nekomimi/nekogram/helpers/remote/UpdateHelper.java').decode()
  self.assertIn('if (!hasMetadataChannel())',helper)

 def test_staged_policy_compiles_and_executes_adversarial_cases(self):
  with tempfile.TemporaryDirectory()as d:
   run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,HERE/'staged/FlexyUpdatePolicy.java',HERE/'staged/UpdatePolicyTest.java')
   result=run('java','-cp',d,'UpdatePolicyTest').stdout
   self.assertIn('runtime DISABLED',result);self.assertIn('archive evidence is a double',result);print(result.strip())
 def test_patch_is_deterministic_scoped_and_reversible(self):
  patch,changes=prepare();self.assertEqual((HERE/'android-identity.patch').read_text(),patch)
  self.assertFalse(any(line.endswith((' ','\t'))for line in patch.splitlines()))
  self.assertFalse(patch.endswith('\n\n'))
  work1=set(subprocess.check_output(['git','diff','--name-only',BASE,WORK1],cwd=ROOT,text=True).splitlines());self.assertFalse(set(changes)&work1)
  with tempfile.TemporaryDirectory()as d:
   root=Path(d)
   for path,(before,after)in changes.items():
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
    if before:target.write_text(before)
    if path.endswith('.xml'):
     old={x.get('name'):ET.tostring(x,encoding='unicode')for x in ET.fromstring(before)}if before else {}
     new={x.get('name'):ET.tostring(x,encoding='unicode')for x in ET.fromstring(after)}
     self.assertTrue(set(old)<=set(new));self.assertTrue({k for k in new if old.get(k)!=new[k]}<=KEYS)
    else:self.assertEqual(after,before.replace('return "exteraless";','return "FlexyGram";',1))
   run('git','apply','--check',HERE/'android-identity.patch',cwd=root);run('git','apply',HERE/'android-identity.patch',cwd=root)
   for path,(before,after)in changes.items():self.assertEqual((root/path).read_text(),after)
   run('git','apply','--reverse',HERE/'android-identity.patch',cwd=root)
   for path,(before,after)in changes.items():self.assertEqual((root/path).read_text()if(root/path).exists()else'',before)

@unittest.skipUnless((TOOLS/'aapt2').is_file()and ANDROID.is_file(),'real SDK36/API37 unavailable; no Android validation claimed')
class AndroidSdk(unittest.TestCase):
 def test_changed_identity_resources_link_real_aapt2(self):
  _,changes=prepare()
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);groups={}
   for path,(_,after)in changes.items():
    if not path.endswith('.xml'):continue
    # Alpha overlays dominate same-qualifier main values; select only audited brand keys.
    qualifier=Path(path).parent.name
    group=groups.setdefault(qualifier,{})
    for item in ET.fromstring(after):
     if item.get('name')in KEYS:group[item.get('name')]=''.join(item.itertext())
   for qualifier,values in groups.items():
    folder=root/'res'/qualifier;folder.mkdir(parents=True,exist_ok=True);tree=ET.Element('resources')
    for key,value in values.items():ET.SubElement(tree,'string',name=key).text=value
    ET.ElementTree(tree).write(folder/'identity.xml',encoding='utf-8')
   manifest=root/'AndroidManifest.xml';manifest.write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="app.flexygram.identityprobe"><uses-sdk android:minSdkVersion="24"/><application android:label="@string/NagramX"/></manifest>')
   run(TOOLS/'aapt2','compile','--dir',root/'res','-o',root/'resources.zip')
   run(TOOLS/'aapt2','link','-I',ANDROID,'--manifest',manifest,'-o',root/'resources.ap_',root/'resources.zip')
   self.assertTrue((root/'resources.ap_').stat().st_size>0)
   print('PASS real AAPT2 API37 staged labels only; full merged manifest/APK NOT_TESTED')
 def test_real_apk_v2_test_certificate_and_tampering(self):
  if not shutil.which('keytool')or not(TOOLS/'lib/apksigner.jar').is_file():self.skipTest('keytool/apksigner unavailable')
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);manifest=root/'AndroidManifest.xml'
   manifest.write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="io.github.jose22yt.flexygram.alpha" android:versionCode="1275" android:versionName="signing-fixture"><uses-sdk android:minSdkVersion="24"/><application android:label="Synthetic fixture"/></manifest>')
   unsigned=root/'unsigned.apk';apk=root/'fixture.apk';key=root/'ephemeral-test.p12'
   run(TOOLS/'aapt2','link','-I',ANDROID,'--manifest',manifest,'-o',unsigned)
   run('keytool','-genkeypair','-keystore',key,'-storepass','synthetic-only','-keypass','synthetic-only','-alias','fixture','-keyalg','RSA','-keysize','2048','-validity','1','-dname','CN=FlexyGram Synthetic Audit Fixture')
   run('java','-jar',TOOLS/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','fixture','--ks-pass','pass:synthetic-only','--out',apk,unsigned)
   result=run('java','-jar',TOOLS/'lib/apksigner.jar','verify','--verbose','--print-certs',apk).stdout
   self.assertIn('Verified using v2 scheme (APK Signature Scheme v2): true',result)
   certificate=re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)',result).group(1)
   self.assertNotEqual(certificate,'c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c')
   badging=run(TOOLS/'aapt2','dump','badging',apk).stdout
   package=re.search(r"package: name='([^']+)' versionCode='([0-9]+)'",badging)
   self.assertIsNotNone(package)
   probe=root/'CertificateProbe.java'
   probe.write_text('''import app.flexygram.updates.FlexyUpdatePolicy;import java.util.Set;
class CertificateProbe {public static void main(String[]args){
 var release=new FlexyUpdatePolicy.Release(FlexyUpdatePolicy.REPO,"v1.0.0-alpha.1275","a".repeat(40),FlexyUpdatePolicy.PACKAGE,FlexyUpdatePolicy.Channel.ALPHA,1275,1,"","","0".repeat(64),false,true);
 var evidence=new FlexyUpdatePolicy.VerifiedArchive(args[0],Long.parseLong(args[1]),true,Set.of(args[2]));
 try{FlexyUpdatePolicy.validateArchive(release,evidence);throw new AssertionError("foreign certificate accepted");}
 catch(IllegalArgumentException expected){System.out.println("REJECTED real SDK-verified synthetic certificate");}
}}''')
   run('java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',root,HERE/'staged/FlexyUpdatePolicy.java',probe)
   self.assertIn('REJECTED',run('java','-cp',root,'CertificateProbe',package.group(1),package.group(2),certificate).stdout)
   with zipfile.ZipFile(apk,'a')as out:out.writestr('tampered.txt','changed after signing')
   rejected=subprocess.run(['java','-jar',str(TOOLS/'lib/apksigner.jar'),'verify',str(apk)],capture_output=True)
   self.assertNotEqual(rejected.returncode,0)
   print('PASS real synthetic V2 signature/tamper rejection; no official key or client APK used')

if __name__=='__main__':unittest.main()
