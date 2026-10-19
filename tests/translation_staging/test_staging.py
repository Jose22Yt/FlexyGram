"""Actual Diagnostic facade + consumers. Offline JVM fixtures, not ART tests."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,unittest,sys,zipfile
ROOT=Path(__file__).resolve().parents[2]
MODULE=ROOT/'TMessagesProj_Modules/translation-compat-diagnostic'
PROD=ROOT/'TMessagesProj/src/main/java'
TRANS=PROD/'tw/nekomimi/nekogram/translate'
sys.path.insert(0,str(Path(__file__).parent))
from review_scope import assert_scope,BASE
sys.path.insert(0,str(ROOT/'tests/translation_safety'))
from artifact_gate import scan

def run(args):
 r=subprocess.run(list(map(str,args)),capture_output=True,text=True)
 if r.returncode:raise AssertionError(r.stdout+r.stderr)
 return r.stdout+r.stderr

def write(root,name,s):
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s);return p

class StagingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.work=Path(cls.temp.name)
  cls.classes=cls.work/'classes';cls.gson=Path(os.environ['GSON_JAR']);cls.aar=Path(os.environ['TRANSLATOR_CLASSES_JAR'])
  cls.cp=os.pathsep.join(map(str,[cls.classes,cls.gson]));cls.sources=list((MODULE/'src/main/java').rglob('*.java'))
  run(['javac','--release','8','-encoding','UTF-8','-cp',cls.gson,'-d',cls.classes,*cls.sources])
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_production_public_protected_abi_matches_recorded_aar(self):
  for name in ['BaseTranslator','Result','MicrosoftTranslator','DeepLTranslator','Http429Exception']:
   original=run(['javap','-protected','-s','-classpath',self.aar,'app.nekogram.translator.'+name])
   current=run(['javap','-protected','-s','-classpath',self.classes,'app.nekogram.translator.'+name])
   for line in original.splitlines():
    if line.strip().startswith(('public ','protected ','descriptor:')):self.assertIn(line.strip(),[x.strip() for x in current.splitlines()],name)
 def test_no_injection_constructors_or_network_and_default_closed(self):
  source='\n'.join(p.read_text() for p in self.sources)
  for forbidden in ['FixtureTransport','lab.flexygram','java.net','okhttp','getenv','getProperty','http://','https://','setTransport','printStackTrace','System.out','System.err']:
   self.assertNotIn(forbidden,source)
  f=write(self.work,'Closed.java','''import app.nekogram.translator.*;
public class Closed {public static void main(String[] a)throws Exception {
for(Class<?> c:new Class<?>[]{MicrosoftTranslator.class,DeepLTranslator.class}) {
if(c.getConstructors().length!=1||c.getConstructors()[0].getParameterCount()!=0)throw new AssertionError();}
for(BaseTranslator p:new BaseTranslator[]{new MicrosoftTranslator(),new DeepLTranslator(),MicrosoftTranslator.getInstance(),DeepLTranslator.getInstance()}) {
try{p.translate("SYNTHETIC_PRIVATE",null,"en");throw new AssertionError();}catch(SecurityException e){if(e.getCause()!=null||e.toString().contains("SYNTHETIC_PRIVATE"))throw new AssertionError();}}
try{DeepLTranslator.setJwt("SYNTHETIC_PRIVATE");throw new AssertionError();}catch(SecurityException e){if(e.toString().contains("SYNTHETIC_PRIVATE"))throw new AssertionError();}
Result r=Result.of("synthetic","en");if(!r.translation.equals("synthetic")||!r.sourceLanguage.equals("en"))throw new AssertionError();
System.out.println("closed; no injection constructors; safe result fields");}}
''')
  run(['javac','-cp',self.cp,'-d',self.classes,f]);self.assertIn('closed',run(['java','-cp',self.cp,'Closed']))
 def test_ordered_catalogs_and_conversions_are_preserved(self):
  d=json.loads((ROOT/'docs/security-p03e/evidence/language-inventory.json').read_text())
  f=write(self.work,'Catalogs.java','''import app.nekogram.translator.*;import java.util.*;
public class Catalogs {public static void main(String[] a){BaseTranslator[] ps={new MicrosoftTranslator(),new DeepLTranslator()};
for(int i=0;i<2;i++)if(!ps[i].getTargetLanguages().equals(Arrays.asList(a[i].split(","))))throw new AssertionError();
if(!ps[0].supportLanguage("zh-CN")||ps[0].supportLanguage("ZH-CN"))throw new AssertionError();}}
''')
  run(['javac','-cp',self.cp,'-d',self.classes,f])
  run(['java','-cp',self.cp,'Catalogs',*[','.join(d[n]['constructor_languages']) for n in ['MicrosoftTranslator','DeepLTranslator']]])
  # Language helper is exercised directly in its own package, without any provider call.
  f=write(self.work,'LanguageFixture.java','''package app.nekogram.translator;
public class LanguageFixture {public static void main(String[] a){String[][] pairs={{"zh-CN","zh-Hans"},{"zh-TW","zh-Hant"}};
for(String[] p:pairs)if(!LanguageCodes.convert(p[0],false).equals(p[1])||!LanguageCodes.convert(p[1],true).equals(p[0]))throw new AssertionError();
for(String c:new String[]{null,"","auto","zh","ZH-cn"})if(!java.util.Objects.equals(c,LanguageCodes.convert(c,false)))throw new AssertionError();}}
''')
  run(['javac','-cp',self.cp,'-d',self.classes,f]);run(['java','-cp',self.cp,'app.nekogram.translator.LanguageFixture'])
 def test_google_stub_stays_denied_even_with_permissive_test_policy(self):
  for allowed in [False,True]:
   out=self.work/('allowed' if allowed else 'denied');out.mkdir(exist_ok=True)
   policy=(TRANS/'TranslationServicesPolicy.java').read_text() if not allowed else '''package tw.nekomimi.nekogram.translate;public class TranslationServicesPolicy {public enum Route {GOOGLE_LEGACY_LIBRARY,DEEPL_LIBRARY} public static void requireRoute(Route r){} public static SecurityException denied(){return new SecurityException("TRANSLATION_DIAGNOSTIC_DISABLED");}}'''
   paths=[write(out,'TranslationServicesPolicy.java',policy),write(out,'DiagnosticPolicy.java','package org.telegram.messenger;public class DiagnosticPolicy {public static boolean isIsolated(){return true;}}')]
   paths+=[TRANS/'source/fallback/GoogleTranslatorNeko.java',TRANS/'source/fallback/DeepLTranslatorNeko.java']
   f=write(out,'Wrappers.java','''import tw.nekomimi.nekogram.translate.source.fallback.*;
public class Wrappers {public static void main(String[] a)throws Exception {for(int i=0;i<20;i++) {
try{GoogleTranslatorNeko.translate("SYNTHETIC_PRIVATE","auto","en");throw new AssertionError();}catch(SecurityException e){if(e.toString().contains("SYNTHETIC_PRIVATE")||e.getCause()!=null)throw new AssertionError();}
try{DeepLTranslatorNeko.translate("SYNTHETIC_PRIVATE","auto","en");throw new AssertionError();}catch(SecurityException e){if(e.toString().contains("SYNTHETIC_PRIVATE")||e.getCause()!=null)throw new AssertionError();}}
System.out.println("wrappers remain denied; no Google binary needed");}}
''')
   run(['javac','-cp',self.cp,'-d',out,*paths,f]);run(['java','-cp',str(out)+os.pathsep+self.cp,'Wrappers'])
 def test_real_kotlin_consumers_compile_against_production_facade(self):
  lib=Path(os.environ['KOTLIN_LIB']);compiler=os.pathsep.join(str(p) for p in lib.glob('*.jar'))
  out=self.work/'kotlin-consumers';out.mkdir(exist_ok=True);java=out/'classes'
  paths=[]
  for name,s in {
   'org/telegram/messenger/DiagnosticPolicy.java':'package org.telegram.messenger;public class DiagnosticPolicy {public static boolean isIsolated(){return true;}}',
   'org/telegram/messenger/LocaleController.java':'package org.telegram.messenger;public class LocaleController {public static String getString(int id){return "UNSUPPORTED";}}',
   'org/telegram/messenger/R.java':'package org.telegram.messenger;public class R {public static class string {public static int TranslateApiUnsupported=1;}}',
   'org/telegram/tgnet/TLRPC.java':'package org.telegram.tgnet;public class TLRPC {public static class MessageEntity{} public static class TL_textWithEntities {public String text;public java.util.ArrayList<MessageEntity> entities=new java.util.ArrayList<>();}}'
  }.items():paths.append(write(out,name,s))
  run(['javac','-cp',self.cp,'-d',java,*paths,TRANS/'TranslationServicesPolicy.java',TRANS/'source/fallback/DeepLTranslatorNeko.java',TRANS/'source/fallback/GoogleTranslatorNeko.java'])
  paths=[]
  paths.append(write(out,'Translator.kt','''package tw.nekomimi.nekogram.translate
import org.telegram.tgnet.TLRPC
interface Translator {suspend fun doTranslate(from:String,to:String,query:String,entities:ArrayList<TLRPC.MessageEntity>):TLRPC.TL_textWithEntities}
object HTMLKeeper {fun entitiesToHtml(q:String,e:ArrayList<TLRPC.MessageEntity>,b:Boolean):String=error("NO_FORMAT_EXPECTED")
fun htmlToEntities(q:String,e:ArrayList<TLRPC.MessageEntity>,b:Boolean):Pair<String,ArrayList<TLRPC.MessageEntity>> =error("NO_FORMAT_EXPECTED")}
'''))
  paths.append(write(out,'TranslateAlert2.kt','''package org.telegram.ui.Components
import org.telegram.tgnet.TLRPC
object TranslateAlert2 {fun preprocess(a:TLRPC.TL_textWithEntities,b:TLRPC.TL_textWithEntities):TLRPC.TL_textWithEntities=error("NO_FORMAT_EXPECTED")}
'''))
  paths.append(write(out,'Components.kt','''package androidx.core.util
operator fun <A,B> Pair<A,B>.component1():A=first
operator fun <A,B> Pair<A,B>.component2():B=second
'''))
  paths.append(write(out,'Check.kt','''import kotlinx.coroutines.runBlocking
import tw.nekomimi.nekogram.translate.source.*
fun main()=runBlocking {for(i in 0..20) {
try{RealMicrosoftTranslator.doTranslate("auto","es","SYNTHETIC_PRIVATE",arrayListOf());error("unguarded")}catch(e:SecurityException){check(e.message=="TRANSLATION_DIAGNOSTIC_DISABLED")}
try{GoogleTranslator.doTranslate("auto","es","SYNTHETIC_PRIVATE",arrayListOf());error("unguarded")}catch(e:SecurityException){check(e.message=="TRANSLATION_DIAGNOSTIC_DISABLED")}}
println("actual complete Kotlin consumers linked; real policy denied")}
'''))
  run(['java','-cp',compiler,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-jvm-target','1.8','-classpath',str(java)+os.pathsep+self.cp+os.pathsep+compiler,'-d',out/'kclasses',*paths,TRANS/'source/RealMicrosoftTranslator.kt',TRANS/'source/GoogleTranslator.kt'])
  result=run(['java','-cp',str(out/'kclasses')+os.pathsep+str(java)+os.pathsep+self.cp+os.pathsep+compiler,'CheckKt'])
  self.assertIn('real policy denied',result)
 def test_translator_format_entities_preferences_and_isolation_unchanged(self):
  names=['translate/Translator.kt','translate/HTMLKeeper.java','translate/TranslationServicesPolicy.java','translate/source/RealMicrosoftTranslator.kt','translate/source/DeepLTranslator.kt','translate/source/MicrosoftTranslator.kt']
  paths=[str((PROD/'tw/nekomimi/nekogram'/n).relative_to(ROOT)) for n in names]
  paths+=['TMessagesProj/src/main/java/org/telegram/tgnet/TLRPC.java','TMessagesProj/src/main/AndroidManifest.xml','TMessagesProj/src/main/java/org/telegram/messenger/DiagnosticPolicy.java']
  for path in paths:
   current=ROOT/('TMessagesProj/src/diagnostic/AndroidManifest.xml' if path=='TMessagesProj/src/main/AndroidManifest.xml' else path)
   self.assertEqual(current.read_bytes(),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),path)
  assert_scope(self)
 def test_active_aar_removed_and_exclusion_mandatory(self):
  s=(ROOT/'TMessagesProj/build.gradle').read_text()
  self.assertNotIn("implementation 'app.nekogram.translator:translator:1.6.1'",s)
  self.assertIn("diagnosticImplementation project(':translation-compat-diagnostic')",s)
  self.assertIn("exclude group: 'app.nekogram.translator', module: 'translator'",s)
  self.assertIn("dependsOn 'verifyDiagnosticTranslationClasspath'",s)
  self.assertNotIn('GoogleAppTranslator',(TRANS/'source/fallback/GoogleTranslatorNeko.java').read_text())
  for p in [*self.sources,TRANS/'source/GoogleTranslator.kt',TRANS/'source/fallback/GoogleTranslatorNeko.java']:
   result=scan(p.read_bytes(),json.loads((ROOT/'tests/translation_safety/retired_fingerprints.json').read_text()));self.assertTrue(result['passed'],str(p))
 def test_android24_compilation_d8_and_no_duplicate_facade_classes(self):
  sdk=Path(os.environ['ANDROID_SDK_ROOT']);boot=sdk/'platforms/android-24/android.jar';out=self.work/'api24'
  run(['javac','-source','8','-target','8','-encoding','UTF-8','-bootclasspath',boot,'-cp',self.gson,'-d',out,*self.sources])
  jar=self.work/'facade.jar'
  with zipfile.ZipFile(jar,'w') as z:
   paths=list(out.rglob('*.class'));self.assertEqual(len(paths),6)
   for p in paths:z.write(p,str(p.relative_to(out)))
  dex=self.work/'dex';dex.mkdir(exist_ok=True)
  run([sdk/'build-tools/36.0.0/d8','--min-api','24','--lib',boot,'--classpath',self.gson,'--output',dex,jar]);self.assertTrue((dex/'classes.dex').is_file())
if __name__=='__main__':unittest.main()
