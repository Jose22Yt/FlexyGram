"""Beta guards; mocked Android tools and synthetic ZIP are NOT a real signed APK."""
from pathlib import Path
import importlib.util,json,struct,subprocess,sys,tempfile,unittest,zipfile
from unittest.mock import patch
from xml.etree import ElementTree as ET
import beta_release_contract as audit
from test_verify_apk import PACKAGED_MANIFEST
ROOT=audit.ROOT
sys.path.insert(0,str(ROOT/'tools/beta_release'))
import verify_beta_apk as v
import preflight as pre

def elf():
    data=bytearray(120);data[:6]=b'\x7fELF\x02\x01';struct.pack_into('<H',data,18,183)
    struct.pack_into('<Q',data,32,64);struct.pack_into('<HH',data,54,56,1)
    struct.pack_into('<IIQQQQQQ',data,64,1,5,0,0,0,120,120,16384)
    return bytes(data)

class BetaRelease(unittest.TestCase):
    def test_all_beta_labels_cover_all_main_label_locales(self):
        label=ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').getroot().find('application').get('{http://schemas.android.com/apk/res/android}label')
        self.assertEqual('@string/NagramX',label)
        beta_label=ET.parse(ROOT/'TMessagesProj/src/beta/res/values/flexygram_identity.xml').getroot()
        self.assertEqual('FlexyGram Beta',beta_label.find("string[@name='NagramX']").text)
        beta=ROOT/'TMessagesProj/src/beta/res'
        for p in beta.glob('values*/alpha_name.xml'):
            entries={n.get('name'):n.text for n in ET.parse(p).getroot()}
            for key in ['AppName','AppNameBeta']:self.assertEqual('FlexyGram Beta',entries[key],str(p))
        for p in (ROOT/'TMessagesProj/src/main/res').glob('values*/*.xml'):
            if {n.get('name') for n in ET.parse(p).getroot()}&{'AppName','AppNameBeta'}:
                self.assertTrue((beta/p.parent.name/'alpha_name.xml').is_file(),str(p))
    def test_exact_scope_runtime_and_gradle_frozen(self):
        audit.verify_current()
        for p in audit.spec()['reviewed']:
            data=(ROOT/p).read_bytes()+b'UNKNOWN';self.assertEqual(data,audit.restore(p,data))
        frozen=['TMessagesProj/src/main/java','TMessagesProj/src/connectedAlpha','TMessagesProj/jni','TMessagesProj/build.gradle','gradle.properties','gradle']
        self.assertEqual(b'',subprocess.check_output(['git','diff',audit.BASE,'--',*frozen],cwd=ROOT))
        config_changes=set(subprocess.check_output(['git','diff','--name-only',audit.BASE,'--','config/signing'],cwd=ROOT,text=True).splitlines())
        self.assertLessEqual(config_changes,{'config/signing/flexygram-release.cer','config/signing/identity.properties','config/signing/public-verification.json'})
    def fixture(self,folder,count=96):
        apk=Path(folder)/'synthetic-input.zip'
        with zipfile.ZipFile(apk,'w') as z:
            z.writestr('classes.dex',b'TEST_DOUBLE_NOT_REAL_DEX')
            z.writestr('lib/arm64-v8a/libtmessages.49.so',elf())
            for i in range(count-1):z.writestr(f'lib/arm64-v8a/libfixture{i}.so',elf())
        manifest=PACKAGED_MANIFEST.replace('    E: activity (line=15)','    A: android:allowBackup(0x01010280)=(type 0x12)0x0\n    A: android:restoreAnyVersion(0x010102ba)=(type 0x12)0x0\n    E: activity (line=15)')
        manifest+='    E: provider (line=50)\n      A: android:authorities(0x01010018)="com.flexygram.messenger.provider"\n'
        code,name=v.expected_version()
        badging=f"package: name='{v.APP}' versionCode='{code}' versionName='{name}'\napplication-label:'FlexyGram Beta'\napplication-label-es:'FlexyGram Beta'\nuses-permission: name='android.permission.INTERNET'\nnative-code: 'arm64-v8a'\n"
        signature='\n'.join(f'Verified using v{i} scheme (APK Signature Scheme v{i}): true' for i in [2,3])+'\nSigner #1 certificate SHA-256 digest: '+v.OFFICIAL
        return apk,dict(signature=signature,badging=badging,manifest=manifest)
    def verify(self,apk,text):
        def fake(*args):
            if args[0].endswith('apksigner'):return text['signature']
            if 'badging' in args:return text['badging']
            if 'xmltree' in args:return text['manifest']
            return ''
        with patch.object(v,'command',side_effect=fake):return v.verify(apk,Path('/fake-build-tools'))
    def test_positive_tool_doubles_are_not_physical_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            apk,text=self.fixture(folder);r=self.verify(apk,text)
            self.assertEqual(96,r['elf_count']);self.assertEqual('NOT_TESTED',r['android_runtime'])
    def test_wrong_signer_missing_v3_and_multiple_signers_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            apk,t=self.fixture(folder)
            cases=[t['signature'].replace(v.OFFICIAL,'c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c'),t['signature'].replace(v.OFFICIAL,'5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c'),t['signature'].replace(v.OFFICIAL,'0'*64),t['signature'].replace('v3): true','v3): false'),t['signature']+'\nSigner #2 certificate SHA-256 digest: '+v.OFFICIAL]
            for s in cases:
                with self.subTest(signer=s[-64:]),self.assertRaises(ValueError):self.verify(apk,{**t,'signature':s})
    def test_wrong_package_version_name_label_debug_abi_provider_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            apk,t=self.fixture(folder);code,_=v.expected_version();s=t['badging']
            cases=[s.replace(v.APP,'io.github.jose22yt.flexygram.alpha'),s.replace(f"versionCode='{code}'","versionCode='1'"),s.replace('1.0.0-beta.1','alpha'),s.replace('FlexyGram Beta','FlexyGram'),s+'application-debuggable\n',s.replace("'arm64-v8a'","'arm64-v8a' 'x86_64'")]
            for b in cases:
                with self.subTest(badging=b),self.assertRaises(ValueError):self.verify(apk,{**t,'badging':b})
            with self.assertRaises(ValueError):self.verify(apk,{**t,'manifest':t['manifest'].replace(v.APP+'.provider','other.provider')})
    def test_incomplete_native_payload_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            apk,t=self.fixture(folder,95)
            with self.assertRaises(ValueError):self.verify(apk,t)
    def test_preflight_missing_inputs_and_no_secret_disclosure(self):
        with tempfile.TemporaryDirectory() as folder:
            r=pre.inspect({},Path(folder));self.assertEqual('BLOCKED_MISSING_OR_INVALID_INPUTS',r['status'])
            self.assertIn('FLEXYGRAM_RELEASE_KEYSTORE',r['missing_input_names'])
            r=pre.inspect({'FLEXYGRAM_RELEASE_KEY_ALIAS':'PRIVATE_SENTINEL'},Path(folder))
            self.assertNotIn('PRIVATE_SENTINEL',json.dumps(r));self.assertIn('WRONG_OFFICIAL_ALIAS',r['problems'])
if __name__=='__main__':unittest.main()
