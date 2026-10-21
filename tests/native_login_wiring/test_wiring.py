"""LOCAL host tests, original request bodies, reply/framework doubles. No Android runtime."""
from pathlib import Path
import hashlib,json,os,re,subprocess,tempfile,unittest
from fixtures import ROOT,write,COMPLETE
MODULE=ROOT/'TMessagesProj_Modules/telegram-login-wiring'
HARNESS=Path(__file__).with_name('RequestContextHarness.java')
CASES=re.findall(r'^        case "([^"]+)":',HARNESS.read_text(),re.M)
CANARY='SYNTHETIC_CONTEXT_SECRET_89123'
class WiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name);cls.java=Path(os.environ['JAVA_HOME'])/'bin'
        version=subprocess.run([str(cls.java/'java'),'-version'],capture_output=True,text=True,check=True)
        if 'version "21.' not in version.stderr:raise RuntimeError('JDK21_REQUIRED')
        cls.fixtures=cls.folder/'fixtures';cls.metadata=write(cls.fixtures);cls.sources=[]
        for module in ['telegram-session-core','telegram-session-android','telegram-native-login','telegram-login-wiring']:
            cls.sources+=list((ROOT/'TMessagesProj_Modules'/module).glob('src/*/java/**/*.java'))
        original_dir=cls.folder/'originals'
        for relative in ['TMessagesProj/build.gradle','TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java']:
            target=original_dir/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/relative).read_bytes())
        for patch in sorted((ROOT/'patches/native-login-wiring').glob('*.patch')):
            subprocess.run(['git','apply','--check',str(patch)],cwd=original_dir,check=True,capture_output=True)
            subprocess.run(['git','apply',str(patch)],cwd=original_dir,check=True,capture_output=True)
        cls.patched_login=(original_dir/'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java').read_text()
        cls.patched_gradle=(original_dir/'TMessagesProj/build.gradle').read_text()
        methods=cls.patched_login.split('    // BEGIN FLEXYGRAM PREPARED LOCAL BINDING')[1].split('    // END FLEXYGRAM PREPARED LOCAL BINDING')[0]
        methods=methods[methods.index('\n')+1:]
        (cls.fixtures/'PreparedFragmentFixture.java').write_text('package io.github.jose22yt.flexygram.login;import org.telegram.ui.LoginActivity;import android.os.Bundle;public class PreparedFragmentFixture extends LoginActivity {'
            +'private static final int MODE_LOGIN=0,VIEW_PHONE_INPUT=0;int activityMode,currentViewNum,pageCalls;Object cachedFragmentView;Object[] views={new Object()};public PreparedFragmentFixture(){super(0);}public void markCreated(){cachedFragmentView=new Object();}void setPage(int page,boolean a,Bundle b,boolean back){pageCalls++;}'+methods+'}')
        cls.classes=cls.folder/'classes';cls.all_sources=cls.sources+list(cls.fixtures.rglob('*.java'))+[ROOT/'tests/native_login/NativeLoginHarness.java',HARNESS]
        run=subprocess.run([str(cls.java/'javac'),'--release','8','-d',str(cls.classes),*map(str,cls.all_sources)],capture_output=True,text=True)
        if run.returncode:raise RuntimeError(run.stderr)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,case):
        run=subprocess.run([str(self.java/'java'),'-cp',str(self.classes),'io.github.jose22yt.flexygram.login.RequestContextHarness',case],capture_output=True,text=True,timeout=15)
        self.assertNotIn(CANARY,run.stdout+run.stderr);self.assertEqual(run.returncode,0,run.stdout+run.stderr);self.assertIn('HOST_LOCAL_CONTEXT_ONLY',run.stdout)
    def test_original_request_class_bodies_retained(self):
        self.assertEqual(len(COMPLETE),13);self.assertEqual(len(self.metadata['complete_original_request_classes']),14)
        self.assertFalse(self.metadata['full_TLRPC_compiled']);self.assertFalse(self.metadata['wire_parser_executed'])
        from fixtures import original_class
        source=(ROOT/'TMessagesProj/src/main/java/org/telegram/tgnet/TLRPC.java').read_text();compiled=(self.fixtures/'org/telegram/tgnet/TLRPC.java').read_text()
        for name in COMPLETE:self.assertIn(original_class(source,name),compiled)
        self.assertEqual((self.fixtures/'org/telegram/messenger/SRPHelper.java').read_bytes(),(ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/SRPHelper.java').read_bytes())
    def test_android_sdk24_symbols(self):
        sdk=Path(os.environ['FLEXYGRAM_ANDROID24_JAR']);self.assertEqual(hashlib.sha256(sdk.read_bytes()).hexdigest(),'4c438bf1b3d4e6104faccc62e1ffe95ef197b88055497b540a871349e93c8685')
        fixtures=[p for p in self.fixtures.rglob('*.java') if not str(p.relative_to(self.fixtures)).startswith('android/')]
        run=subprocess.run([str(self.java/'javac'),'--release','8','-cp',str(sdk),'-d',str(self.folder/'sdk24'),*map(str,self.sources+fixtures)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
    def test_jdk21_default_compile(self):
        run=subprocess.run([str(self.java/'javac'),'-d',str(self.folder/'jdk21'),*map(str,self.all_sources)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
    def test_no_live_transport_or_policy_changes(self):
        source='\n'.join(p.read_text() for p in MODULE.rglob('*.java'))
        self.assertNotRegex(source,r'\.sendRequest\(|\.cleanup\(|clearConfig\(|native_moveToDatacenter|java\.net\.|FileLog\.|getMessage\(|getCause\(')
        self.assertNotIn('TELEGRAM_APP_',source);self.assertNotIn('api_id=6',source)
        protected=['TMessagesProj','gradle','settings.gradle','.github']
        for path in protected:self.assertEqual(subprocess.check_output(['git','diff','--name-only','19b515e0ce63bdecae235b434ca265dbaf4d48ca','--',path],cwd=ROOT,text=True),'')
        self.assertNotIn('telegram-login-wiring',(ROOT/'settings.gradle').read_text())
        changed=subprocess.check_output(['git','diff','--name-only','19b515e0ce63bdecae235b434ca265dbaf4d48ca'],cwd=ROOT,text=True).splitlines()
        exact={'tests/native_login/test_native_login.py','tests/session_android/test_adapters.py','tests/session_core/test_integration_contracts.py'}
        for path in changed:self.assertTrue(path in exact or path.startswith(('TMessagesProj_Modules/telegram-login-wiring/','tests/native_login_wiring/','docs/native-login-wiring/','patches/native-login-wiring/','tools/native_login_wiring/')),path)
    def test_patches_apply_only_to_temporary_copies(self):
        original=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java').read_text()
        self.assertNotIn('bindPreparedLocalLogin',original)
        self.assertIn('preparedLocalLoginBinding == null ? loadCurrentState',self.patched_login)
        self.assertIn('preparedLocalLoginBinding.saveRestartMarker(outState);',self.patched_login)
        self.assertIn('detachPreparedLocalLogin();',self.patched_login)
        methods=self.patched_login.split('// BEGIN FLEXYGRAM PREPARED LOCAL BINDING')[1].split('// END FLEXYGRAM PREPARED LOCAL BINDING')[0]
        self.assertNotRegex(methods,r'\.sendRequest\(|onAuthSuccess\(|fillNextCodeParams\(')
        self.assertIn('if (!state.mayEnterOriginalPage()) return false;',methods)
    def test_gradle_patch_scopes_sources_to_realalpha(self):
        from fixtures import original_class
        # Execute exactly the injected block, without AGP/plugin downloads or another Gradle build.
        start=self.patched_gradle.index('    // Prepared login sources only')
        end=self.patched_gradle.index("    namespace =",start)
        snippet=self.patched_gradle[start:end]
        script=self.folder/'source_set_contract.groovy'
        script.write_text("import groovy.lang.*\nfor(flag in [false,true]){def variants=[realAlpha:[java:[srcDirs:[]]],diagnostic:[java:[srcDirs:[]]],betaDevelopment:[java:[srcDirs:[]]],production:[java:[srcDirs:[]]]];def b=new Binding([realAlphaEnabled:flag,sourceSets:variants,rootProject:[file:{String p->new File(p)}]]);new GroovyShell(b).evaluate("+repr(snippet)+");if(variants.realAlpha.java.srcDirs.size()!=(flag?7:0))throw new IllegalStateException('SCOPE');for(name in ['diagnostic','betaDevelopment','production'])if(!variants[name].java.srcDirs.empty)throw new IllegalStateException('OTHER_VARIANT');}\n")
        # repr uses Python escapes accepted for this ASCII single-quoted Groovy source.
        jars=list((Path(os.environ['FLEXYGRAM_GRADLE_HOME'])/'lib').glob('groovy-4*.jar'));self.assertEqual(len(jars),1)
        run=subprocess.run([str(self.java/'java'),'-cp',str(jars[0]),'groovy.ui.GroovyMain',str(script)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
    def test_native_page_side_effects_are_not_assumed_safe(self):
        source=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java').read_text()
        qr=source[source.index('public class LoginActivityQrView'):]
        self.assertRegex(qr,r'public void onShow\(\)[\s\S]{0,150}exportLoginToken\(true\)')
        self.assertIn('getConnectionsManager().cleanup(false);',qr)
        self.assertIn('AndroidUtilities.setWaitingForSms(true);',source)
        self.assertIn('NotificationCenter.didReceiveCall',source)
    def test_native_page_numbers_match_original(self):
        source=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java').read_text()
        expected={'PHONE_INPUT':0,'CODE_MESSAGE':1,'CODE_SMS':2,'CODE_FLASH_CALL':3,'CODE_CALL':4,'REGISTER':5,'PASSWORD':6,'CODE_MISSED_CALL':11,'CODE_WORD':16,'CODE_PHRASE':17,'QR_LOGIN':19}
        for name,number in expected.items():self.assertRegex(source,r'VIEW_'+name+r'\s*=\s*'+str(number)+r'\b')
        self.assertEqual(len(CASES),len(set(CASES)))
for case in CASES:setattr(WiringTests,'test_'+case,lambda self,c=case:self.run_case(c))

# Selected previous cases are compatibility regressions, not new tests or a replay of all 77.
PREVIOUS=['nativeCodeAndCommit','missingWriteReceiptsStayUncertain','writeThenThrowIsNeverRolledBack','journalFailureAfterOriginalWrite','foreignRequestCannotStageAuthorization','androidViewRecreationNoRequestReplay','callbackThenThrowCannotCommit','concurrentFirstResponseWins']
def previous(self,case):
    run=subprocess.run([str(self.java/'java'),'-cp',str(self.classes),'io.github.jose22yt.flexygram.login.NativeLoginHarness',case],capture_output=True,text=True,timeout=15)
    self.assertNotIn('SYNTHETIC_NATIVE_LOGIN_PRIVATE_77291',run.stdout+run.stderr)
    self.assertEqual(run.returncode,0,run.stdout+run.stderr)
for case in PREVIOUS:setattr(WiringTests,'test_previous_'+case,lambda self,c=case:previous(self,c))
