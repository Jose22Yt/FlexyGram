"""New Java/Android source adapters, real HOST JNI, SDK24 symbol compile. No Android execution."""
import hashlib,os,re,struct,subprocess,tempfile,unittest
from pathlib import Path
from fixtures import ROOT,write_fixtures
CORE=ROOT/'TMessagesProj_Modules/telegram-session-core/src/main/java'
MODULE=ROOT/'TMessagesProj_Modules/telegram-session-android'
HARNESS=Path(__file__).with_name('AndroidSessionHarness.java')
CASES=re.findall(r'^        case "([^"]+)":',HARNESS.read_text(),re.M)
CANARY='SYNTHETIC_PRIVATE_ADAPTER_401'

class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name);cls.java=Path(os.environ['JAVA_HOME'])/'bin'
        version=subprocess.run([str(cls.java/'java'),'-version'],check=True,capture_output=True,text=True)
        if 'version "21.' not in version.stderr:raise RuntimeError('JDK21_REQUIRED')
        cls.fixtures=cls.folder/'fixtures';write_fixtures(cls.fixtures)
        cls.sources=[*CORE.rglob('*.java'),*MODULE.glob('src/*/java/**/*.java')];cls.classes=cls.folder/'classes'
        p=subprocess.run([str(cls.java/'javac'),'--release','8','-d',str(cls.classes),*map(str,cls.sources),*map(str,cls.fixtures.rglob('*.java')),str(HARNESS)],capture_output=True,text=True)
        if p.returncode:raise RuntimeError(p.stderr)
        source=cls.folder/'native';source.mkdir()
        (source/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject(SessionBridgeHost NONE)\ninclude("'+str(ROOT/'TMessagesProj/jni/real-alpha-policy.cmake')+'")\n')
        digest=hashlib.sha256((ROOT/'gradle/real-alpha.json').read_bytes()).hexdigest()
        subprocess.run([os.environ['FLEXYGRAM_CMAKE'],'-S',str(source),'-B',str(cls.folder/'native-build'),'-DFLEXYGRAM_FLAVOR=realAlpha','-DFLEXYGRAM_POLICY_SCOPE='+digest+':realAlpha'],check=True,capture_output=True,text=True)
        cls.library=cls.folder/'libsession_readonly_host.so'
        p=subprocess.run(['c++','-std=c++17','-fPIC','-fvisibility=hidden','-shared','-Wall','-Wextra','-Werror',
            '-I'+str(Path(os.environ['JAVA_HOME'])/'include'),'-I'+str(Path(os.environ['JAVA_HOME'])/'include/linux'),
            '-I'+str(ROOT/'TMessagesProj/jni/tgnet'),'-I'+str(cls.folder/'native-build/flexygram-policy'),
            str(MODULE/'src/main/cpp/SessionReadOnlyBridge.cpp'),str(ROOT/'TMessagesProj/jni/tgnet/VariantPolicy.cpp'),'-o',str(cls.library)],capture_output=True,text=True)
        if p.returncode:raise RuntimeError(p.stderr)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,case):
        with tempfile.TemporaryDirectory() as directory:
            env=dict(os.environ,FLEXYGRAM_HOST_UID=str(os.getuid()))
            p=subprocess.run([str(self.java/'java'),'-cp',str(self.classes),'io.github.jose22yt.flexygram.session.android.AndroidSessionHarness',case,directory,str(self.library)],capture_output=True,text=True,timeout=15,env=env)
            self.assertNotIn(CANARY,p.stdout+p.stderr);self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertIn('HOST_DOUBLES_NO_TELEGRAM',p.stdout)
    def test_android_api24_symbols_compile_real_sdk(self):
        sdk=Path(os.environ['FLEXYGRAM_ANDROID24_JAR'])
        self.assertEqual(hashlib.sha256(sdk.read_bytes()).hexdigest(),'4c438bf1b3d4e6104faccc62e1ffe95ef197b88055497b540a871349e93c8685')
        # Android APIs from real SDK24; Java APIs from JDK8 release. Not proof of Android Java
        # library support, D8 desugaring or runtime. SDK24 bootclasspath lacks javac's MethodHandles.
        telegram=list((self.fixtures/'org').rglob('*.java'))+list((self.fixtures/'tw').rglob('*.java'))
        p=subprocess.run([str(self.java/'javac'),'--release','8','-classpath',str(sdk),'-d',str(self.folder/'api24-classes'),*map(str,self.sources+telegram)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
    def test_bytecode_java8(self):
        files=list((self.classes/'io/github/jose22yt/flexygram').rglob('*.class'));self.assertGreater(len(files),20)
        for p in files:self.assertEqual(struct.unpack('>H',p.read_bytes()[6:8])[0],52)
    def test_jdk21_default_source_compilation(self):
        # Catch java.lang.Record name collisions which --release 8 cannot expose.
        p=subprocess.run([str(self.java/'javac'),'-d',str(self.folder/'jdk21-classes'),*map(str,self.sources),*map(str,self.fixtures.rglob('*.java')),str(HARNESS)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
    def test_jni_library_has_no_transport_symbols(self):
        text=subprocess.check_output(['nm','-D',str(self.library)],text=True)
        self.assertIn('AndroidNativeBridge_nativeIdentity',text);self.assertIn('AndroidNativeBridge_nativePolicy',text)
        self.assertNotRegex(text,r'\b(?:connect|socket|send|recv|getaddrinfo|SSL_connect|_.*ConnectionsManager.*)\b')
    def test_shared_sources_and_variants_unchanged(self):
        changed=subprocess.check_output(['git','diff','--name-only','985f8ec8f426225dfd7fba772272fd77e02b7fcf'],cwd=ROOT,text=True)
        added={'TMessagesProj_Modules/telegram-session-core/src/main/java/io/github/jose22yt/flexygram/session/AuthenticationController.java'}
        for p in changed.splitlines():self.assertTrue(p in added or p=='tests/session_core/test_integration_contracts.py' or p.startswith(('TMessagesProj_Modules/telegram-session-android/','tests/session_android/','docs/session-android/','TMessagesProj_Modules/telegram-native-login/','tests/native_login/','docs/native-login/')),p)
        self.assertNotIn('telegram-session-android',(ROOT/'settings.gradle').read_text())
        self.assertNotIn('telegram-native-login',(ROOT/'settings.gradle').read_text())
    def test_sources_do_not_mutate_telegram_state_or_log(self):
        text='\n'.join(p.read_text() for p in MODULE.glob('src/*/java/**/*.java'))
        self.assertNotRegex(text,r'FileLog\.|System\.(?:out|err)|printStackTrace\(|getMessage\(|getCause\(')
        self.assertNotRegex(text,r'\.sendRequest\(|\.cleanup\(|\.performLogout\(|\.clearConfig\(|\.saveConfig\(|\.setCurrentUser\(|selectedAccount\s*=')
        self.assertNotRegex(text,r'import (?:java\.net\.|okhttp|org\.apache\.http)')
    def test_unique_inventory_and_slot_contract(self):
        self.assertEqual(len(CASES),len(set(CASES)))
        self.assertRegex((ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java').read_text(),r'MAX_ACCOUNT_COUNT\s*=\s*10\s*;')
        self.assertIn('account>=10',(MODULE/'src/main/cpp/SessionReadOnlyBridge.cpp').read_text())
    def test_unapplied_jni_patch_applies_to_original_cmake(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);target=folder/'TMessagesProj/jni/CMakeLists.txt';target.parent.mkdir(parents=True)
            before=(ROOT/'TMessagesProj/jni/CMakeLists.txt').read_bytes();target.write_bytes(before)
            patch=MODULE/'integration/0001-realalpha-read-only-jni.patch'
            subprocess.run(['git','apply','--check',str(patch)],cwd=folder,check=True,capture_output=True)
            subprocess.run(['git','apply',str(patch)],cwd=folder,check=True,capture_output=True)
            self.assertIn('if(FLEXYGRAM_FLAVOR STREQUAL "realAlpha")',target.read_text())
            self.assertEqual((ROOT/'TMessagesProj/jni/CMakeLists.txt').read_bytes(),before)
    def test_native_open_policy_compile_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);original=(ROOT/'TMessagesProj/jni/tgnet/DiagnosticPolicy.h').read_text()
            needle='inline constexpr bool telegramTransportAllowed = false;';self.assertIn(needle,original)
            (folder/'DiagnosticPolicy.h').write_text(original.replace(needle,needle.replace('false','true')))
            p=subprocess.run(['c++','-std=c++17','-fPIC','-c','-I'+str(folder),'-I'+str(self.folder/'native-build/flexygram-policy'),'-I'+str(Path(os.environ['JAVA_HOME'])/'include'),'-I'+str(Path(os.environ['JAVA_HOME'])/'include/linux'),str(MODULE/'src/main/cpp/SessionReadOnlyBridge.cpp'),'-o',str(folder/'denied.o')],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0);self.assertIn('READ_ONLY_BRIDGE_REQUIRES_CLOSED_POLICY',p.stderr)
    def test_cmake_fragment_build_and_existing_export_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);source=folder/'source';source.mkdir();home=Path(os.environ['JAVA_HOME'])
            exports=subprocess.check_output(['git','show','HEAD:TMessagesProj/jni/exports.map'],cwd=ROOT,text=True);(source/'exports.map').write_text(exports)
            cmake='cmake_minimum_required(VERSION 3.16)\nproject(BridgeIntegrationHost LANGUAGES CXX)\nset(CMAKE_CXX_STANDARD 17)\nset(CMAKE_CXX_VISIBILITY_PRESET hidden)\n'
            cmake+='include("'+str(ROOT/'TMessagesProj/jni/real-alpha-policy.cmake')+'")\nset(NATIVE_LIB session_bridge)\n'
            cmake+='add_library(${NATIVE_LIB} SHARED "'+str(ROOT/'TMessagesProj/jni/tgnet/VariantPolicy.cpp')+'")\ninclude("'+str(MODULE/'integration/read-only-jni.cmake')+'")\n'
            cmake+='target_include_directories(${NATIVE_LIB} PRIVATE "'+str(home/'include')+'" "'+str(home/'include/linux')+'")\n'
            cmake+='target_link_options(${NATIVE_LIB} PRIVATE "-Wl,--version-script='+str(source/'exports.map')+'")\n';(source/'CMakeLists.txt').write_text(cmake)
            scope=hashlib.sha256((ROOT/'gradle/real-alpha.json').read_bytes()).hexdigest()+':realAlpha'
            p=subprocess.run([os.environ['FLEXYGRAM_CMAKE'],'-S',str(source),'-B',str(folder/'build'),'-DFLEXYGRAM_FLAVOR=realAlpha','-DFLEXYGRAM_POLICY_SCOPE='+scope],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            p=subprocess.run([os.environ['FLEXYGRAM_CMAKE'],'--build',str(folder/'build')],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            symbols=subprocess.check_output(['nm','-D',str(folder/'build/libsession_bridge.so')],text=True)
            self.assertIn('AndroidNativeBridge_nativePolicy',symbols);self.assertIn('AndroidNativeBridge_nativeIdentity',symbols);self.assertIn('flexygram_variant_policy',symbols)
            p=subprocess.run([os.environ['FLEXYGRAM_CMAKE'],'-S',str(source),'-B',str(folder/'wrong'),'-DFLEXYGRAM_FLAVOR=diagnostic','-DFLEXYGRAM_POLICY_SCOPE='+scope],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0);self.assertIn('FLEXYGRAM_REAL_ALPHA_PROFILE_MISMATCH',p.stdout+p.stderr)

for case in CASES:
    setattr(AdapterTests,'test_'+case,lambda self,c=case:self.run_case(c))
