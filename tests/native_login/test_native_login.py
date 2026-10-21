"""Real adapter/core source with local RPC/storage and projected TL declarations. NOT Android/network."""
from pathlib import Path
import importlib.util,os,re,struct,subprocess,tempfile,unittest,hashlib,json
from tl_projection import ROOT,write_projection
MODULE=ROOT/'TMessagesProj_Modules/telegram-native-login'
HARNESS=Path(__file__).with_name('NativeLoginHarness.java')
CASES=re.findall(r'^        case "([^"]+)":',HARNESS.read_text(),re.M)
CANARY='SYNTHETIC_NATIVE_LOGIN_PRIVATE_77291'
CHANGED_SHARED={
 'TMessagesProj_Modules/telegram-session-core/src/main/java/io/github/jose22yt/flexygram/session/AuthenticationController.java',
 'TMessagesProj_Modules/telegram-session-android/src/main/java/io/github/jose22yt/flexygram/session/android/LocalSessionStore.java',
 'TMessagesProj_Modules/telegram-session-android/src/main/java/io/github/jose22yt/flexygram/session/android/JournaledLocalSessionStore.java',
 'TMessagesProj_Modules/telegram-session-android/src/main/java/io/github/jose22yt/flexygram/session/android/LoginFlowOwner.java',
 'tests/session_core/test_integration_contracts.py','tests/session_android/test_adapters.py'}

class NativeLoginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name);cls.java=Path(os.environ['JAVA_HOME'])/'bin'
        version=subprocess.run([str(cls.java/'java'),'-version'],check=True,capture_output=True,text=True)
        if 'version "21.' not in version.stderr:raise RuntimeError('JDK21_REQUIRED')
        cls.fixtures=cls.folder/'fixtures'
        spec=importlib.util.spec_from_file_location('android_fixture_sources',ROOT/'tests/session_android/fixtures.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture);fixture.write_fixtures(cls.fixtures)
        cls.metadata=write_projection(cls.fixtures)
        cls.sources=[]
        for name in ['telegram-session-core','telegram-session-android','telegram-native-login']:
            cls.sources+=list((ROOT/'TMessagesProj_Modules'/name).glob('src/*/java/**/*.java'))
        cls.classes=cls.folder/'classes'
        p=subprocess.run([str(cls.java/'javac'),'--release','8','-d',str(cls.classes),*map(str,cls.sources),*map(str,cls.fixtures.rglob('*.java')),str(HARNESS)],capture_output=True,text=True)
        if p.returncode:raise RuntimeError(p.stderr)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,case):
        p=subprocess.run([str(self.java/'java'),'-cp',str(self.classes),'io.github.jose22yt.flexygram.login.NativeLoginHarness',case],capture_output=True,text=True,timeout=15)
        self.assertNotIn(CANARY,p.stdout+p.stderr);self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertIn('LOCAL_SYNTHETIC_ONLY',p.stdout)
    def test_jdk21_default_source(self):
        p=subprocess.run([str(self.java/'javac'),'-d',str(self.folder/'jdk21'),*map(str,self.sources),*map(str,self.fixtures.rglob('*.java')),str(HARNESS)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
    def test_android_sdk24_symbols(self):
        sdk=Path(os.environ['FLEXYGRAM_ANDROID24_JAR']);self.assertEqual(hashlib.sha256(sdk.read_bytes()).hexdigest(),'4c438bf1b3d4e6104faccc62e1ffe95ef197b88055497b540a871349e93c8685')
        telegram=[p for p in self.fixtures.rglob('*.java') if not str(p.relative_to(self.fixtures)).startswith('android/')]
        p=subprocess.run([str(self.java/'javac'),'--release','8','-cp',str(sdk),'-d',str(self.folder/'sdk24'),*map(str,self.sources+telegram)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
    def test_bytecode_and_projection_scope(self):
        for p in (self.classes/'io/github/jose22yt/flexygram').rglob('*.class'):self.assertEqual(struct.unpack('>H',p.read_bytes()[6:8])[0],52)
        self.assertEqual(len(self.metadata['declarations']),32);self.assertFalse(self.metadata['wire_serializers_compiled'])
        self.assertEqual(self.metadata['declarations']['TL_auth_authorization']['fields'],['public boolean setup_password_required;','public byte[] future_auth_token;','public User user;'])
    def test_no_shared_client_or_capability_files_changed(self):
        changed=subprocess.check_output(['git','diff','--name-only','b09b79301db93e19471bd0c21aecba0bb9e64063'],cwd=ROOT,text=True).splitlines()
        for path in changed:self.assertTrue(path in CHANGED_SHARED or path.startswith(('TMessagesProj_Modules/telegram-native-login/','tests/native_login/','docs/native-login/','TMessagesProj_Modules/telegram-login-wiring/','tests/native_login_wiring/','docs/native-login-wiring/','tools/native_login_wiring/','patches/native-login-wiring/')),path)
        settings=(ROOT/'settings.gradle').read_text();self.assertNotIn('telegram-native-login',settings)
        for path in ['gradle/real-alpha.json','gradle/variant-policy.json','gradle/beta-development.json','TMessagesProj/jni/tgnet/DiagnosticPolicy.h']:
            self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show','b09b79301db93e19471bd0c21aecba0bb9e64063:'+path],cwd=ROOT))
    def test_no_network_or_destructive_telegram_calls(self):
        text='\n'.join(p.read_text() for p in MODULE.rglob('*.java'))
        self.assertNotRegex(text,r'import (?:java\.net\.|okhttp|org\.apache\.http)')
        self.assertNotRegex(text,r'\.sendRequest\(|\.cleanup\(|\.performLogout\(|\.clearConfig\(|\.setCurrentUser\(|native_moveToDatacenter|resetAuthorizations')
        self.assertNotRegex(text,r'FileLog\.|printStackTrace\(|getMessage\(|getCause\(|System\.(?:out|err)')
        self.assertEqual(len(CASES),len(set(CASES)))
    def test_security_series_pinned_and_not_applied(self):
        manifest=json.loads((MODULE/'integration/security-series.json').read_text())
        self.assertEqual(manifest['mode'],'REVIEW_ONLY_NO_APPLY')
        self.assertEqual(len(manifest['patches']),4)
        self.assertEqual(len(manifest['target_git_blobs']),5)
        for row in manifest['patches']:
            self.assertFalse(row['applied_to_client'])
            self.assertEqual(hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest(),row['sha256'])
            self.assertEqual(row['targets'],re.findall(r'^\+\+\+ b/(.+)$',(ROOT/row['path']).read_text(),re.M))
        for path,blob in manifest['target_git_blobs'].items():
            self.assertEqual(subprocess.check_output(['git','hash-object',str(ROOT/path)],text=True).strip(),blob)
            self.assertEqual(subprocess.check_output(['git','rev-parse',manifest['original_source_commit']+':'+path],cwd=ROOT,text=True).strip(),blob)

for case in CASES:
    setattr(NativeLoginTests,'test_'+case,lambda self,c=case:self.run_case(c))
