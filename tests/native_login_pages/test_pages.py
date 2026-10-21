from pathlib import Path
import os,re,subprocess,tempfile,unittest,json,hashlib
from fixtures_pages import ROOT,write
HARNESS=Path(__file__).with_name('PagesHarness.java');CASES=re.findall(r'^  case "([^"]+)":',HARNESS.read_text(),re.M)
class PagesTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name);cls.java=Path(os.environ['JAVA_HOME'])/'bin';cls.fixtures=cls.folder/'fixtures';cls.metadata,cls.patched,cls.patchroot=write(cls.fixtures,cls.folder)
  cls.sources=[]
  for module in ['telegram-session-core','telegram-session-android','telegram-native-login','telegram-login-wiring','telegram-login-local-ui']:cls.sources+=list((ROOT/'TMessagesProj_Modules'/module).glob('src/*/java/**/*.java'))
  cls.classes=cls.folder/'classes';cls.all=cls.sources+list(cls.fixtures.rglob('*.java'))+[ROOT/'tests/native_login/NativeLoginHarness.java',HARNESS]
  p=subprocess.run([str(cls.java/'javac'),'--release','8','-d',str(cls.classes),*map(str,cls.all)],capture_output=True,text=True)
  if p.returncode:raise RuntimeError(p.stderr)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def run_case(self,case):
  p=subprocess.run([str(self.java/'java'),'-cp',str(self.classes),'io.github.jose22yt.flexygram.login.PagesHarness',case],capture_output=True,text=True,timeout=15)
  self.assertNotIn('SYNTHETIC_LOCAL_UI_SECRET_77121',p.stdout+p.stderr);self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertIn('HOST_NATIVE_GUARDS_LOCAL_ONLY',p.stdout)
 def test_patches_apply_to_pinned_copies_only(self):
  self.assertNotIn('bindClosedLocalPages',(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java').read_text());self.assertIn('bindClosedLocalPages',self.patched)
  self.assertIn('if (!localLoginClosed()) {\n            imageUpdater = new ImageUpdater',self.patched)
  self.assertIn('final boolean allowTestBackend = !localLoginClosed();',self.patched)
  self.assertIn('if (!localLoginClosed() || io.github.jose22yt.flexygram.login.local.EphemeralPages.allowedPage(VIEW_QR_LOGIN))',self.patched)
  self.assertIn('setImportantForAutofill(android.view.View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS)',self.patched)
  self.assertIn('localFence != preparedTransition',self.patched)
  self.assertIn('if (localLoginClosed()) detachClosedLocalView();',self.patched)
  self.assertIn('!preparedLocalFragmentDestroyed) attachClosedLocalView();',self.patched)
  self.assertIn('outState.putInt("flexygram_local_auth_slot", currentAccount)',self.patched)
  self.assertNotIn('flexygram_local_auth_account',self.patched)
 def test_guard_inventory_complete_for_declared_methods(self):
  from prepare_patch import span
  data=json.loads((ROOT/'patches/native-login-pages/inventory.json').read_text());self.assertGreaterEqual(len(data['guarded_methods']),45)
  for entry in data['guarded_methods']:
   a,b,c=span(self.patched,'public class '+entry['class']);body=self.patched[a:c]
   # The first guard is executable, before any old method body.
   found=list(re.finditer(r'(?:public|private|protected)\s+(?:void|boolean)\s+'+entry['method']+r'\s*\([^{};]*?\)\s*\{',body))
   self.assertTrue(found,entry)
   self.assertTrue(any(body[m.end():].lstrip().startswith('if (localLoginClosed())') for m in found),entry)
 def test_native_page_factory_and_loops_reject_unsupported_slots(self):
  assignments=re.findall(r'^        (.*views\[VIEW_\w+\] = new .+;)$',self.patched,re.M)
  self.assertEqual(len(assignments),20)
  for line in assignments:self.assertTrue(line.startswith('if (!localLoginClosed() ||'),line)
  self.assertIn('if (slideView == null) continue;',self.patched);self.assertIn('if (views[a] == null) continue;',self.patched)
 def test_source_sets_patch_realalpha_only(self):
  source=(self.patchroot/'TMessagesProj/build.gradle').read_text();needle="rootProject.file('TMessagesProj_Modules/telegram-login-local-ui/src/main/java')"
  self.assertEqual(source.count(needle),1);self.assertNotIn(needle,(ROOT/'TMessagesProj/build.gradle').read_text())
 def test_channel_has_no_persistence_network_or_raw_parameters(self):
  source='\n'.join(p.read_text() for p in (ROOT/'TMessagesProj_Modules/telegram-login-local-ui').rglob('*.java'))
  self.assertNotRegex(source,r'import (?:java\.net|android\.os\.Bundle)|getSharedPreferences|\.sendRequest\(|FileLog\.|System\.(out|err)|getMessage\(')
  self.assertEqual(len(CASES),len(set(CASES)))
 def test_sdk24_symbols_and_jdk21_source(self):
  sdk=Path(os.environ['FLEXYGRAM_ANDROID24_JAR']);self.assertEqual(hashlib.sha256(sdk.read_bytes()).hexdigest(),'4c438bf1b3d4e6104faccc62e1ffe95ef197b88055497b540a871349e93c8685')
  fixtures=[p for p in self.fixtures.rglob('*.java') if not str(p.relative_to(self.fixtures)).startswith('android/')]
  p=subprocess.run([str(self.java/'javac'),'--release','8','-cp',str(sdk),'-d',str(self.folder/'sdk24'),*map(str,self.sources+fixtures)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
  p=subprocess.run([str(self.java/'javac'),'-d',str(self.folder/'jdk21'),*map(str,self.all)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
 def test_materialized_overlay_is_pinned_and_recovers_identically(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('overlay_tool',ROOT/'tools/native_login_pages/materialize_overlay.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  receipt=module.materialize(ROOT/'build/generated/flexygram-local-login')
  output=ROOT/'build/generated/flexygram-local-login/java/org/telegram/ui/LoginActivity.java'
  self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(),receipt['overlay_sha256'])
  self.assertEqual(output.read_text(),self.patched)
  with self.assertRaises(ValueError):module.materialize(ROOT/'TMessagesProj/src/main/java')
 def test_exact_source_scope_and_no_active_client_patch(self):
  changed=subprocess.check_output(['git','diff','--name-only','40faca6b04563bcacd02d0947addd4c18ff81e81'],cwd=ROOT,text=True).splitlines()
  exact={'TMessagesProj_Modules/telegram-native-login/src/main/java/io/github/jose22yt/flexygram/login/NativeLoginProtocol.java','TMessagesProj_Modules/telegram-native-login/src/main/java/io/github/jose22yt/flexygram/login/NativeLoginTransport.java','TMessagesProj_Modules/telegram-native-login/src/telegram/java/io/github/jose22yt/flexygram/login/TlAuthResponses.java','tests/native_login/tl_projection.py','tests/native_login/test_native_login.py','tests/native_login_wiring/test_wiring.py','tests/session_android/test_adapters.py','tests/session_core/test_integration_contracts.py'}
  for path in changed:self.assertTrue(path in exact or path.startswith(('TMessagesProj_Modules/telegram-login-local-ui/','tests/native_login_pages/','tools/native_login_pages/','patches/native-login-pages/','docs/native-login-pages/')),path)
  self.assertEqual(subprocess.check_output(['git','diff','--name-only','40faca6b04563bcacd02d0947addd4c18ff81e81','--','TMessagesProj','gradle','settings.gradle','.github'],cwd=ROOT,text=True),'')
 def test_constructor_requests_and_outer_notification_are_guarded(self):
  self.assertIn('if (!localLoginClosed()) {\n            String country = null;',self.patched)
  self.assertIn('public void didReceivedNotification(int id, int account, Object... args) {\n        if (localLoginClosed()) return;',self.patched)
  self.assertIn('private void updateProxyButton(boolean animated, boolean force) {\n        if (localLoginClosed()) return;',self.patched)
 def test_actual_gradle_overlay_branch_with_synthetic_providers(self):
  gradle=(self.patchroot/'TMessagesProj/build.gradle').read_text()
  config=gradle[gradle.index("def localLoginPagesEnabled ="):gradle.index('def realAlphaPolicyFile =')]
  start=gradle.index('    if (localLoginPagesEnabled) {',gradle.index('sourceSets.main.jniLibs'))
  source=gradle[start:gradle.index('    namespace =',start)]
  guard=next(line.strip() for line in gradle.splitlines() if "if (localLoginPagesEnabled && !(flavor ==" in line)
  script=self.folder/'variant_scope.groovy'
  root=self.folder/'groovy-root';overlay=root/'build/generated/flexygram-local-login/java/org/telegram/ui/LoginActivity.java';overlay.parent.mkdir(parents=True);overlay.write_text(self.patched)
  inventory=root/'patches/native-login-pages/inventory.json';inventory.parent.mkdir(parents=True);inventory.write_bytes((ROOT/'patches/native-login-pages/inventory.json').read_bytes())
  # Real injected Groovy; providers/sourceSets are doubles, not an AGP build.
  program="class GradleException extends RuntimeException {GradleException(String m){super(m)}}\n"+"def root = new File("+json.dumps(str(root))+")\n"
  program+="def code = "+json.dumps(config+source+"\nreturn [enabled:localLoginPagesEnabled,filter:{flavor,builder->"+guard+";return builder.enable}]\n")+"\n"
  program+="""def test={boolean flag,boolean alpha->def excludes=[];def ss=[main:[java:[exclude:{p->excludes<<p}]],realAlpha:[java:[srcDirs:[]]],diagnostic:[java:[srcDirs:[]]],betaDevelopment:[java:[srcDirs:[]]],production:[java:[srcDirs:[]]]];def b=new Binding([realAlphaEnabled:alpha,providers:[gradleProperty:{p->[orNull:flag?'true':null]}],rootProject:[file:{p->new File(root,p)}],sourceSets:ss]);def result=new GroovyShell(this.class.classLoader,b).evaluate(code);if(ss.realAlpha.java.srcDirs.size()!=(flag?9:0))throw new IllegalStateException('SOURCE_SCOPE');if(excludes.size()!=(flag?1:0))throw new IllegalStateException('EXCLUDE_SCOPE');for(name in ['diagnostic','betaDevelopment','production']){if(!ss[name].java.srcDirs.empty)throw new IllegalStateException('OTHER_SOURCES');def builder=[enable:true,buildType:'debug'];result.filter(name,builder);if(builder.enable==flag)throw new IllegalStateException('VARIANT_FILTER');}}
 test(false,false);test(true,true);boolean denied=false;try{test(true,false)}catch(Exception e){denied=e.toString().contains('REQUIRES_REALALPHA')};if(!denied)throw new IllegalStateException('MISSING_GUARD');new File(root,'build/generated/flexygram-local-login/java/org/telegram/ui/LoginActivity.java').text='SYNTHETIC_TAMPER';denied=false;try{test(true,true)}catch(Exception e){denied=e.toString().contains('OVERLAY_MISMATCH')};if(!denied)throw new IllegalStateException('STALE_OVERLAY_ACCEPTED');
"""
  script.write_text(program)
  lib=Path(os.environ['FLEXYGRAM_GRADLE_HOME'])/'lib';jars=[*lib.glob('groovy-4*.jar'),*lib.glob('groovy-json-*.jar')];self.assertEqual(len(jars),2)
  p=subprocess.run([str(self.java/'java'),'-cp',os.pathsep.join(map(str,jars)),'groovy.ui.GroovyMain',str(script)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
 def test_original_java_parser_syntax_only(self):
  helper=self.folder/'ParseOnly.java';helper.write_text('''import javax.tools.*;import com.sun.source.util.*;import java.util.*;public class ParseOnly{public static void main(String[] a)throws Exception{JavaCompiler c=ToolProvider.getSystemJavaCompiler();DiagnosticCollector<JavaFileObject>d=new DiagnosticCollector<>();try(StandardJavaFileManager f=c.getStandardFileManager(d,null,null)){JavacTask t=(JavacTask)c.getTask(null,f,d,Arrays.asList("-proc:none"),null,f.getJavaFileObjects(a));t.parse();for(Diagnostic<?>x:d.getDiagnostics())if(x.getKind()==Diagnostic.Kind.ERROR)throw new IllegalStateException(x.toString());}System.out.println("PARSE_ONLY_NO_TYPECHECK_NO_ANDROID");}}''')
  subprocess.run([str(self.java/'javac'),'-d',str(self.folder),str(helper)],check=True,capture_output=True,text=True)
  p=subprocess.run([str(self.java/'java'),'-cp',str(self.folder),'ParseOnly',str(self.patchroot/'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java')],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr);self.assertIn('PARSE_ONLY_NO_TYPECHECK_NO_ANDROID',p.stdout)
for case in CASES:setattr(PagesTests,'test_'+case,lambda self,c=case:self.run_case(c))
