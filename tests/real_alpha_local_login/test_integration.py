from pathlib import Path
import os,sys,re,subprocess,tempfile,unittest,json,hashlib
from fixtures import ROOT,write
HARNESS=Path(__file__).with_name('IntegrationHarness.java')
CASES=re.findall(r'case "([^" ]+)":',HARNESS.read_text())
MODULES=['telegram-session-core','telegram-session-android','telegram-native-login','telegram-login-wiring','telegram-login-local-ui']
BASE='57e3d958d161d77f3c468dcd9dc45644ccbc2fe7'
class IntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name);cls.java=Path(os.environ['JAVA_HOME'])/'bin';cls.fixtures=cls.folder/'fixtures';write(cls.fixtures)
  cls.sources=[]
  for name in MODULES:cls.sources+=list((ROOT/'TMessagesProj_Modules'/name).glob('src/*/java/**/*.java'))
  cls.sources+=list((ROOT/'TMessagesProj/src/realAlphaLocalLogin/java').rglob('*.java'))
  cls.classes=cls.folder/'classes';cls.all=cls.sources+list(cls.fixtures.rglob('*.java'))+[HARNESS]
  result=subprocess.run([str(cls.java/'javac'),'--release','8','-d',str(cls.classes),*map(str,cls.all)],capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stderr)
  include=cls.folder/'native';include.mkdir()
  for name in ['DiagnosticPolicy.h','VariantPolicy.cpp']:
   (include/name).write_bytes(subprocess.check_output(['git','show',BASE+':TMessagesProj/jni/tgnet/'+name],cwd=ROOT))
  digest=hashlib.sha256((ROOT/'gradle/real-alpha.json').read_bytes()).hexdigest()
  (include/'VariantPolicy.generated.h').write_text('#define FLEXYGRAM_BUILD_DIAGNOSTIC 1\n#define FLEXYGRAM_VARIANT_POLICY_SCOPE "'+digest+':realAlpha"\n')
  cls.library=include/'libreadonly.so'
  result=subprocess.run(['g++','-std=c++17','-shared','-fPIC','-fvisibility=hidden','-I'+str(cls.java.parent/'include'),'-I'+str(cls.java.parent/'include/linux'),'-I'+str(include),str(ROOT/'TMessagesProj_Modules/telegram-session-android/src/main/cpp/SessionReadOnlyBridge.cpp'),str(include/'VariantPolicy.cpp'),'-o',str(cls.library)],capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stderr)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def case(self,name):
  with tempfile.TemporaryDirectory() as d:
   env=dict(os.environ,FLEXYGRAM_HOST_UID=str(os.getuid()))
   r=subprocess.run([str(self.java/'java'),'-cp',str(self.classes),'org.telegram.ui.realalpha.local.IntegrationHarness',name,d,str(self.library)],capture_output=True,text=True,timeout=20,env=env)
   self.assertNotIn('FAKE_LOCAL_ONLY',r.stdout+r.stderr);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertIn('HOST_LOCAL_INTEGRATION_NOT_ANDROID',r.stdout)
 def test_biometric_fix_and_original_views_are_byte_identical(self):
  for path in ['TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java','TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java','TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java','TMessagesProj/src/realAlpha/java/org/telegram/ui/realalpha/RealAlphaActivity.java','TMessagesProj/src/realAlpha/AndroidManifest.xml','gradle/real-alpha.json','gradle/variant-policy.json','gradle/production-readiness.gradle']:
   self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),path)
 def test_overlay_source_selection_and_qr_block(self):
  spec=__import__('importlib.util',fromlist=['']);path=ROOT/'tools/real_alpha_local_login/materialize.py';s=spec.spec_from_file_location('active_overlay',path);m=spec.module_from_spec(s);s.loader.exec_module(m);receipt=m.prepare()
  self.assertEqual(receipt['integration_base'],BASE)
  self.assertEqual(receipt['overlay_sha256'],json.loads((ROOT/'patches/native-login-pages/inventory.json').read_text())['overlay_sha256'])
  original=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java').read_text();self.assertNotIn('bindClosedLocalPages',original)
  generated=(ROOT/'build/generated/flexygram-local-login/java/org/telegram/ui/LoginActivity.java').read_text()
  self.assertIn('EphemeralPages.allowedPage(VIEW_QR_LOGIN)',generated);self.assertIn('preparedLocalFragmentDestroyed = true',generated)
 def test_no_remote_or_account_writer_in_fixture_or_host(self):
  source='\n'.join(p.read_text() for p in (ROOT/'TMessagesProj/src/realAlphaLocalLogin').rglob('*.java'))
  self.assertNotRegex(source,r'ConnectionsManager|\.sendRequest\(|saveConfig\(|setCurrentUser\(|cleanup\(|SharedPreferences|FileLog\.|System\.(?:out|err)|getMessage\(')
  self.assertIn('PERSISTENCE_DISABLED_IN_VISUAL_REHEARSAL',source)
  self.assertIn('AndroidNativeBridge.read(application,account)',source)
  self.assertIn('probe.evidence!=AccountProbe.Evidence.EMPTY',source)
 def test_jni_is_read_only_and_has_expected_exports(self):
  symbols=subprocess.check_output(['nm','-D',str(self.library)],text=True)
  self.assertIn('AndroidNativeBridge_nativePolicy',symbols);self.assertIn('AndroidNativeBridge_nativeIdentity',symbols)
  self.assertNotRegex(symbols,r'ConnectionsManager|ConnectionSocket|connect@|socket@|send@|recv@')
 def test_jdk21_default_source_compile(self):
  p=subprocess.run([str(self.java/'javac'),'-d',str(self.folder/'jdk21'),*map(str,self.all)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
 def test_host_android_api_calls_compile_against_sdk24(self):
  import shutil
  fixture=self.folder/'sdk-fixtures';shutil.copytree(self.fixtures,fixture)
  (fixture/'org/telegram/ui/realalpha/RealAlphaActivity.java').write_text('package org.telegram.ui.realalpha;public class RealAlphaActivity extends android.app.Activity {}')
  item=fixture/'org/telegram/ui/ActionBar/ActionBarMenuItem.java';text=item.read_text().replace('extends android.view.View {','extends android.view.View {public ActionBarMenuItem(){super(null);}') ;item.write_text(text)
  sdk=Path(os.environ['FLEXYGRAM_ANDROID24_JAR']);self.assertEqual(hashlib.sha256(sdk.read_bytes()).hexdigest(),'4c438bf1b3d4e6104faccc62e1ffe95ef197b88055497b540a871349e93c8685')
  doubles=[p for p in fixture.rglob('*.java') if not str(p.relative_to(fixture)).startswith('android/')]
  r=subprocess.run([str(self.java/'javac'),'--release','8','-cp',str(sdk),'-d',str(self.folder/'sdk24'),*map(str,self.sources+doubles)],capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr)
 def test_complete_overlays_parse_only(self):
  helper=self.folder/'ParseOnly.java';helper.write_text('import javax.tools.*;import com.sun.source.util.*;import java.util.*;public class ParseOnly{public static void main(String[]args)throws Exception{JavaCompiler c=ToolProvider.getSystemJavaCompiler();DiagnosticCollector<JavaFileObject>d=new DiagnosticCollector<>();try(StandardJavaFileManager f=c.getStandardFileManager(d,null,null)){JavacTask t=(JavacTask)c.getTask(null,f,d,Arrays.asList("-proc:none"),null,f.getJavaFileObjects(args));t.parse();for(Diagnostic<?>x:d.getDiagnostics())if(x.getKind()==Diagnostic.Kind.ERROR)throw new IllegalStateException(x.toString());}}}')
  subprocess.run([str(self.java/'javac'),'-d',str(self.folder),str(helper)],check=True,capture_output=True,text=True)
  overlays=list((ROOT/'build/generated/flexygram-local-login').rglob('*.java'));self.assertEqual(len(overlays),4)
  r=subprocess.run([str(self.java/'java'),'-cp',str(self.folder),'ParseOnly',*map(str,overlays)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_original_production_gate_still_rejects(self):
  script=self.folder/'production.groovy'
  script.write_text('def gate=new GroovyShell().evaluate(new File('+json.dumps(str(ROOT/'gradle/production-readiness.gradle'))+'));boolean denied=false;try{gate.call()}catch(IllegalStateException e){denied=e.message.startsWith("FLEXYGRAM_PRODUCTION_INCOMPLETE:")};if(!denied)throw new IllegalStateException("PRODUCTION_NOT_CLOSED")')
  jar=next((Path(os.environ['FLEXYGRAM_GRADLE_HOME'])/'lib').glob('groovy-4*.jar'))
  r=subprocess.run([str(self.java/'java'),'-cp',str(jar),'groovy.ui.GroovyMain',str(script)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_gradle_selection_runs_real_groovy_not_agp(self):
  source=(ROOT/'TMessagesProj/build.gradle').read_text()
  config=source[source.index('def localLoginPagesEnabled ='):source.index('def realAlphaPolicyFile =')]
  start=source.index('    if (localLoginPagesEnabled) {',source.index('sourceSets.main.jniLibs'))
  sets=source[start:source.index('    namespace =',start)]
  guard=next(x.strip() for x in source.splitlines() if "if (localLoginPagesEnabled && !(flavor ==" in x)
  script=self.folder/'scope.groovy'
  script.write_text('''class GradleException extends RuntimeException{GradleException(String s){super(s)}}
class JavaDirs {Set<File> srcDirs=[];List<String> exclusions=[];void exclude(String p){exclusions<<p};void setSrcDirs(Collection<File> p){srcDirs=p as Set}}
'''+"def root=new File("+json.dumps(str(ROOT))+")\n"+"def code="+json.dumps(config+sets+"\nreturn { flavor,builder -> "+guard+"; return builder.enable }")+'\n'+'''for(flag in [false,true]){def alpha=new JavaDirs(srcDirs:[new File(root,'TMessagesProj/src/realAlpha/java')] as Set);def main=new JavaDirs();def ss=[main:[java:main],realAlpha:[java:alpha]];def binding=new Binding([realAlphaEnabled:true,providers:[gradleProperty:{p->[orNull:flag?'true':null]}],rootProject:[file:{p->new File(root,p)}],sourceSets:ss,file:{p->new File(root,'TMessagesProj/'+p)}]);def filter=new GroovyShell(this.class.classLoader,binding).evaluate(code);if(alpha.srcDirs.size()!=(flag?11:1))throw new IllegalStateException('SOURCE_COUNT');if(flag){def files=alpha.srcDirs.collectMany{dir->def found=[];dir.eachFileRecurse{f->if(f.name.endsWith('.java'))found<<f};found};if(files.findAll{it.name=='LoginActivity.java'}.size()!=1||files.findAll{it.name=='RealAlphaActivity.java'}.size()!=1||main.exclusions!=['org/telegram/ui/LoginActivity.java'])throw new IllegalStateException('DUPLICATE_SELECTED_CLASS');};if(alpha.srcDirs.contains(new File(root,'TMessagesProj/src/realAlpha/java'))==flag)throw new IllegalStateException('ORIGINAL_REALALPHA_DUPLICATE');for(flavor in ['diagnostic','betaDevelopment','production','realAlpha']){def b=[buildType:'debug',enable:true];filter(flavor,b);if(flag&&b.enable!=(flavor=='realAlpha'))throw new IllegalStateException('VARIANT_FILTER');}}
''')
  lib=Path(os.environ['FLEXYGRAM_GRADLE_HOME'])/'lib';jars=[*lib.glob('groovy-4*.jar'),*lib.glob('groovy-json-*.jar')]
  self.assertEqual(len(jars),2);p=subprocess.run([str(self.java/'java'),'-cp',os.pathsep.join(map(str,jars)),'groovy.ui.GroovyMain',str(script)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
for name in CASES:setattr(IntegrationTests,'test_'+name,lambda self,n=name:self.case(n))
