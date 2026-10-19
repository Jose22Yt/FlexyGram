"""Isolated source facade: real Java/Kotlin consumers, no app/ART or network execution."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,unittest,zipfile,sys
ROOT=Path(__file__).resolve().parents[2]
MODULE=Path(__file__).parent/'facade'
PROD=ROOT/'TMessagesProj/src/main/java'
TRANS=PROD/'tw/nekomimi/nekogram/translate'
sys.path.insert(0,str(ROOT/'tests/translation_safety'))
from artifact_gate import scan

def run(args):
 r=subprocess.run(list(map(str,args)),capture_output=True,text=True)
 if r.returncode:raise AssertionError(r.stdout+r.stderr)
 return r.stdout+r.stderr

def write(root,name,s):
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s);return p

class FacadeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.work=Path(cls.temp.name);cls.classes=cls.work/'classes'
  cls.gson=Path(os.environ['GSON_JAR']);cls.aar=Path(os.environ['TRANSLATOR_CLASSES_JAR'])
  cls.cp=os.pathsep.join(map(str,[cls.classes,cls.gson]))
  cls.source=list((MODULE/'src/main/java').rglob('*.java'))
  run(['javac','--release','8','-encoding','UTF-8','-cp',cls.gson,'-d',cls.classes,*cls.source])
  run(['javac','--release','8','-encoding','UTF-8','-cp',cls.cp,'-d',cls.classes,MODULE/'src/test/java/FacadeHarness.java'])
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def case(self,name,*args):
  out=run(['java','-cp',self.cp,'FacadeHarness',name,*args]);self.assertNotIn('SYNTHETIC_PRIVATE',out)
 def test_public_result_fields_and_safe_value_semantics(self):self.case('result')
 def test_base_pipeline_protected_array_and_helper_contract(self):self.case('base')
 def test_unconfigured_instances_and_jwt_are_closed(self):self.case('closed')
 def test_complete_ordered_language_catalogs(self):
  d=json.loads((ROOT/'docs/security-p03e/evidence/language-inventory.json').read_text())
  self.case('languages',*[','.join(d[n]['constructor_languages']) for n in ['MicrosoftTranslator','DeepLTranslator']])
 def test_case_sensitive_chinese_null_auto_and_empty_conversion(self):self.case('normalization')
 def test_unicode_html_entities_are_opaque_and_lossless(self):self.case('format')
 def test_safe_errors_and_no_retry_or_provider_switch(self):self.case('errors')
 def test_pre_inflight_exception_thread_cancellation(self):self.case('cancel')
 def test_aar_compiled_base_and_result_binary_linkage(self):
  out=self.work/'binary';out.mkdir(exist_ok=True)
  run(['javac','--release','8','-cp',os.pathsep.join(map(str,[self.aar,self.gson])),'-d',out,MODULE/'src/test/java/BinaryContract.java'])
  original=run(['java','-cp',os.pathsep.join(map(str,[out,self.aar,self.gson])),'BinaryContract'])
  facade=run(['java','-cp',os.pathsep.join(map(str,[out,self.classes,self.gson])),'BinaryContract'])
  self.assertEqual(original,facade)
 def test_consumed_abi_descriptors_and_modifiers(self):
  classes=['BaseTranslator','Result','MicrosoftTranslator','DeepLTranslator','Http429Exception']
  for name in classes:
   original=run(['javap','-protected','-s','-classpath',self.aar,'app.nekogram.translator.'+name])
   facade=run(['javap','-protected','-s','-classpath',self.classes,'app.nekogram.translator.'+name])
   # Public/protected declarations and JVM descriptors must all survive; no private obfuscation names required.
   expected=[s.strip() for s in original.splitlines() if s.strip().startswith(('public ','protected ','descriptor:'))]
   actual=[s.strip() for s in facade.splitlines()]
   for declaration in expected:self.assertIn(declaration,actual,name+': '+declaration)
 def test_real_java_and_kotlin_consumers_compile_and_link(self):
  lib=Path(os.environ['KOTLIN_LIB']);compiler=os.pathsep.join(str(p) for p in lib.glob('*.jar'))
  kotlin_runtime=os.pathsep.join(str(p) for p in lib.glob('kotlin-stdlib-*.jar'))
  # Both compilations use complete unmodified consumer files, NOT extracted/recreated methods.
  for compile_aar in [False,True]:
   out=self.work/('consumer-aar' if compile_aar else 'consumer-facade');out.mkdir(exist_ok=True)
   stubs=out/'stubs';java=out/'java';kotlin=out/'kotlin'
   paths=[]
   paths.append(write(stubs,'org/telegram/messenger/DiagnosticPolicy.java','package org.telegram.messenger;public class DiagnosticPolicy {public static boolean isIsolated(){return true;}}'))
   paths.append(write(stubs,'org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController {public static String getString(int id){return "UNSUPPORTED";}}'))
   paths.append(write(stubs,'org/telegram/messenger/R.java','package org.telegram.messenger;public class R {public static class string {public static int TranslateApiUnsupported=1;}}'))
   paths.append(write(stubs,'org/telegram/tgnet/TLRPC.java','package org.telegram.tgnet;public class TLRPC {public static class MessageEntity{} public static class TL_textWithEntities {public String text;public java.util.ArrayList<MessageEntity> entities=new java.util.ArrayList<>();}}'))
   dep=self.aar if compile_aar else self.classes
   compilecp=os.pathsep.join(map(str,[dep,self.gson]))
   run(['javac','-cp',compilecp,'-d',java,*paths,TRANS/'TranslationServicesPolicy.java',TRANS/'source/fallback/DeepLTranslatorNeko.java'])
   s=write(stubs,'Translator.kt','''package tw.nekomimi.nekogram.translate
import org.telegram.tgnet.TLRPC
interface Translator {suspend fun doTranslate(from:String,to:String,query:String,entities:ArrayList<TLRPC.MessageEntity>):TLRPC.TL_textWithEntities}
object HTMLKeeper {
var encoded=0;var decoded=0
fun entitiesToHtml(q:String,e:ArrayList<TLRPC.MessageEntity>,b:Boolean):String{encoded++;return "<b>"+q+"</b>"}
fun htmlToEntities(q:String,e:ArrayList<TLRPC.MessageEntity>,b:Boolean):Pair<String,ArrayList<TLRPC.MessageEntity>> {decoded++;return Pair(q.removePrefix("<b>").removeSuffix("</b>"),e)}
}
''')
   s2=write(stubs,'TranslateAlert2.kt','''package org.telegram.ui.Components
import org.telegram.tgnet.TLRPC
object TranslateAlert2 {var calls=0;fun preprocess(a:TLRPC.TL_textWithEntities,b:TLRPC.TL_textWithEntities):TLRPC.TL_textWithEntities{calls++;return b}}
''')
   s3=write(stubs,'ConsumerFixture.kt','''import kotlinx.coroutines.runBlocking
import app.nekogram.translator.Result
import tw.nekomimi.nekogram.translate.source.RealMicrosoftTranslator
import tw.nekomimi.nekogram.translate.source.fallback.DeepLTranslatorNeko
fun main(args:Array<String>)=runBlocking {
if(args.isNotEmpty()) {
// Reflection is TEST-ONLY: replace the lazy cached adapter, never the production source/policy.
val transport=object:lab.flexygram.fixture.FixtureTransport {
 override fun exchange(p:lab.flexygram.fixture.FixtureTransport.Provider,text:String,from:String?,to:String):lab.flexygram.fixture.FixtureTransport.Response {
 check(p==lab.flexygram.fixture.FixtureTransport.Provider.MICROSOFT && from==null)
 check(to=="zh-Hans" || to=="zh-Hant")
 return lab.flexygram.fixture.FixtureTransport.Response(200,text,"en")
 }
}
val injected=app.nekogram.translator.MicrosoftTranslator(transport,null)
val field=RealMicrosoftTranslator::class.java.getDeclaredField("translator\\$delegate").apply{isAccessible=true}
val lazy=field.get(null)
lazy.javaClass.getDeclaredField("_value").apply{isAccessible=true}.set(lazy,injected)
val entities=arrayListOf(org.telegram.tgnet.TLRPC.MessageEntity())
for(target in listOf("zh","zh-CN","zh-Hans","zh-TW","zh-HK","zh-Hant","ZH-hK")) {
 val text="💎 &amp; é 中文"
 val result=RealMicrosoftTranslator.doTranslate("auto",target,text,entities)
 check(result.text==text && result.entities===entities)
 val plain=RealMicrosoftTranslator.doTranslate("auto",target,text,arrayListOf())
 check(plain.text==text)
}
check(tw.nekomimi.nekogram.translate.HTMLKeeper.encoded==7)
check(tw.nekomimi.nekogram.translate.HTMLKeeper.decoded==7)
check(org.telegram.ui.Components.TranslateAlert2.calls==7)
// DeepL's real wrapper resolves facade symbols but its default singleton is still closed.
try{DeepLTranslatorNeko.translate("synthetic","auto","es");error("not closed")}catch(e:app.nekogram.translator.FacadeFailure){check(e.message=="TRANSLATION_NOT_AUTHORIZED")}
println("real-consumer-fixture-format-aliases; real HTMLKeeper offsets NOT tested")
return@runBlocking
}

val result=Result.of("synthetic","en")
check(result.translation=="synthetic" && result.sourceLanguage=="en")
try {RealMicrosoftTranslator.doTranslate("auto","zh-HK","synthetic",arrayListOf());error("unguarded")}catch(e:SecurityException){check(e.message=="TRANSLATION_DIAGNOSTIC_DISABLED")}
try {DeepLTranslatorNeko.translate("synthetic","auto","es");error("unguarded")}catch(e:SecurityException){check(e.message=="TRANSLATION_DIAGNOSTIC_DISABLED")}
println("real-consumers-linked-and-policy-denied")
}
''')
   if compile_aar:
    source=s3.read_text();start=source.index('if(args.isNotEmpty())');end=source.index('val result=Result.of',start)
    s3.write_text(source[:start]+source[end:])
   compilecp=os.pathsep.join(map(str,[java,dep,self.gson,compiler]))
   run(['java','-cp',compiler,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-jvm-target','1.8','-classpath',compilecp,'-d',kotlin,s,s2,s3,TRANS/'source/RealMicrosoftTranslator.kt'])
   # Even when compiled against original binary, runtime classpath contains ONLY facade, no AAR.
   runtime=os.pathsep.join(map(str,[kotlin,java,self.classes,self.gson,compiler]))
   out=run(['java','-cp',runtime,'ConsumerFixtureKt'])
   self.assertIn('real-consumers-linked-and-policy-denied',out)
   if not compile_aar:
    allowed=self.work/'allowed-policy';allowed.mkdir(exist_ok=True)
    policy=write(stubs,'allowed/TranslationServicesPolicy.java',"package tw.nekomimi.nekogram.translate;public final class TranslationServicesPolicy {public enum Route {MICROSOFT_LIBRARY,DEEPL_LIBRARY} public static void requireRoute(Route r){} }")
    run(['javac','-d',allowed,policy])
    # The permissive double exists ONLY in this test subprocess. Real policy remains unchanged and denied above.
    result=run(['java','-cp',str(allowed)+os.pathsep+runtime,'ConsumerFixtureKt','fixture'])
    self.assertIn('real-consumer-fixture-format-aliases',result)

 def test_facade_artifact_and_sources_have_no_retired_material(self):
  jar=self.work/'facade.jar'
  with zipfile.ZipFile(jar,'w') as z:
   for p in (self.classes/'app').rglob('*.class'):z.write(p,str(p.relative_to(self.classes)))
   for p in (self.classes/'lab').rglob('*.class'):z.write(p,str(p.relative_to(self.classes)))
  registry=json.loads((ROOT/'tests/translation_safety/retired_fingerprints.json').read_text())
  result=scan(jar.read_bytes(),registry);self.assertTrue(result['passed'] and result['complete'])
  for p in self.source:
   source=p.read_text()
   for forbidden in ['java.net','okhttp','http://','https://','System.getenv','getProperty','android.util.Log','printStackTrace','System.out','System.err']:
    self.assertNotIn(forbidden,source,str(p))
  if os.environ.get('FACADE_EVIDENCE_DIR'):
   e=Path(os.environ['FACADE_EVIDENCE_DIR']);(e/'facade-jar-scan.json').write_text(json.dumps(result,indent=2)+'\n')
   (e/'facade-source-hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.source},indent=2)+'\n')
 def test_production_and_historical_evidence_remain_unchanged(self):
  sys.path.insert(0,str(ROOT/'tests/translation_staging'))
  from review_scope import assert_scope
  assert_scope(self)
  dependency=(ROOT/'TMessagesProj/build.gradle').read_text()
  self.assertNotIn("implementation 'app.nekogram.translator:translator:1.6.1'",dependency)
  self.assertIn("implementation project(':translation-compat-diagnostic')",dependency)
  # The laboratory module itself is still not included in Android.
  self.assertNotIn('tests/translation_dependency/facade',(ROOT/'settings.gradle').read_text())
 def test_android24_bootclasspath_and_d8(self):
  sdk=Path(os.environ['ANDROID_SDK_ROOT']);boot=sdk/'platforms/android-24/android.jar'
  self.assertTrue(boot.is_file(),'Install exact Android API24 platform; do not substitute JDK compilation')
  android=self.work/'android24';android.mkdir(exist_ok=True)
  javac=run(['javac','-source','8','-target','8','-encoding','UTF-8','-bootclasspath',boot,'-cp',self.gson,'-d',android,*self.source])
  jar=self.work/'android24.jar'
  with zipfile.ZipFile(jar,'w') as z:
   for p in android.rglob('*.class'):z.write(p,str(p.relative_to(android)))
  dex=self.work/'dex24';dex.mkdir(exist_ok=True)
  d8=run([sdk/'build-tools/36.0.0/d8','--min-api','24','--lib',boot,'--classpath',self.gson,'--output',dex,jar])
  self.assertTrue((dex/'classes.dex').is_file())
  # This is API24 stub compilation + dexing ONLY; no Android runtime or full application build.
  registry=json.loads((ROOT/'tests/translation_safety/retired_fingerprints.json').read_text())
  result=scan((dex/'classes.dex').read_bytes(),registry);self.assertTrue(result['passed'])
  if os.environ.get('FACADE_EVIDENCE_DIR'):
   e=Path(os.environ['FACADE_EVIDENCE_DIR']);(e/'android24-compile.log').write_text(javac+d8+'API24 bootclasspath compilation and D8 min-api24: PASS\nNo app/APK/ART/emulator execution. Gson is classpath-only, not repackaged.\n')
   (e/'facade-dex24-scan.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':unittest.main()
