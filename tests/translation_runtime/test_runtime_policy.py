"""Offline executable production-method fixtures, not Android/ART or network tests.
KOTLIN_LIB points to the exact Gradle 9.7.1 lib directory. No compiler download here.
"""
from pathlib import Path
import os, re, subprocess, tempfile, unittest, json, hashlib, sys
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'TMessagesProj/src/main/java/tw/nekomimi/nekogram'
TRANS=BASE/'translate'
CANARY='SYNTHETIC_PRIVATE_TEXT_URL_KEY_RESPONSE_NOT_REAL'
sys.path.insert(0,str(ROOT/'tests/translation_staging'))
from review_scope import reviewed_change


def method(path, signature):
    """Extract complete production body using the reviewed lexical masker."""
    import sys
    sys.path.insert(0,str(ROOT/'tests/translation_safety'))
    from inventory import STRINGS_COMMENTS
    text=path.read_text(); start=text.index(signature)
    clean=STRINGS_COMMENTS.sub(lambda m: ''.join('\n' if c=='\n' else ' ' for c in m[0]),text)
    opening=clean.index('{',start); level=1; end=opening+1
    while level:
        level+=(clean[end]=='{')-(clean[end]=='}');end+=1
    return text[start:end]


def command(args,**kw):
    r=subprocess.run(args,text=True,capture_output=True,**kw)
    if r.returncode:raise AssertionError(r.stdout+r.stderr)
    return r.stdout+r.stderr


class RuntimePolicyTests(unittest.TestCase):
    def test_real_java_policy_and_library_wrappers(self):
        for isolated in ['true','false']:
            with tempfile.TemporaryDirectory() as td:
                t=Path(td)
                def write(name,s):
                    f=t/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s)
                for f in [TRANS/'TranslationServicesPolicy.java',TRANS/'source/fallback/GoogleTranslatorNeko.java',TRANS/'source/fallback/DeepLTranslatorNeko.java']:
                    write(str(f.relative_to(ROOT/'TMessagesProj/src/main/java')),f.read_text())
                write('org/telegram/messenger/BuildConfig.java','package org.telegram.messenger; public class BuildConfig { public static final boolean ISOLATED_DIAGNOSTIC='+isolated+'; }')
                write('org/telegram/messenger/DiagnosticPolicy.java',(ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/DiagnosticPolicy.java').read_text())
                for cls in ['GoogleAppTranslator','DeepLTranslator']:
                    write('app/nekogram/translator/'+cls+'.java','''package app.nekogram.translator;
public class CLASS {public static int calls=0;public static CLASS getInstance(){calls++;return new CLASS();}
public static class Result {public String translation="synthetic";}
public Result translate(String t,String f,String to){calls++;return new Result();}}'''.replace('CLASS',cls))
                write('Main.java','''import tw.nekomimi.nekogram.translate.TranslationServicesPolicy;
import tw.nekomimi.nekogram.translate.source.fallback.*;
public class Main {public static void main(String[] args)throws Exception {
for(int i=-2;i<20;i++){if(TranslationServicesPolicy.isProviderAuthorized(i))throw new AssertionError();
 try{TranslationServicesPolicy.requireProvider(i);throw new AssertionError();}catch(SecurityException expected){}}
for(var route:TranslationServicesPolicy.Route.values())try{TranslationServicesPolicy.requireRoute(route);throw new AssertionError();}catch(SecurityException expected){}
if(TranslationServicesPolicy.bulkProvider(7)!=7)throw new AssertionError("silent remap");
for(int i=0;i<20;i++) {try{GoogleTranslatorNeko.translate(args[0],"auto","es");throw new AssertionError();}catch(SecurityException expected){}
try{DeepLTranslatorNeko.translate(args[0],"auto","es");throw new AssertionError();}catch(SecurityException expected){}}
if(app.nekogram.translator.GoogleAppTranslator.calls!=0||app.nekogram.translator.DeepLTranslator.calls!=0)throw new AssertionError("library initialized");
for(Throwable e:new Throwable[]{new RuntimeException(args[0]),new SecurityException(args[0]),new UnsupportedOperationException(args[0])}) {
var safe=TranslationServicesPolicy.safeFailure(e);if(safe.getCause()!=null||safe.toString().contains(args[0]))throw new AssertionError();
if(TranslationServicesPolicy.safeErrorCode(e).contains(args[0]))throw new AssertionError();
if(e instanceof UnsupportedOperationException && !(safe instanceof UnsupportedOperationException))throw new AssertionError();
if(e instanceof SecurityException && !(safe instanceof SecurityException))throw new AssertionError();}
System.out.println("policy/wrappers denied; 0 singleton/transport calls; safe diagnostics");}}''')
                command(['javac','-d',str(t/'classes')]+[str(f) for f in t.rglob('*.java')])
                out=command(['java','-cp',str(t/'classes'),'Main',CANARY]);self.assertNotIn(CANARY,out)

    def test_all_direct_adapters_guard_before_work(self):
        for f in (TRANS/'source').glob('*Translator.kt'):
            s=f.read_text()
            if 'override suspend fun doTranslate' not in s:continue
            body=method(f,'override suspend fun doTranslate')
            self.assertRegex(body.split('{',1)[1],r'^\s*TranslationServicesPolicy.requireRoute\(')
            self.assertNotIn('private val httpClient = HttpClient.instance',s)
        s=(TRANS/'source/RealMicrosoftTranslator.kt').read_text()
        self.assertIn('by lazy { NekoMicrosoftTranslator.getInstance() }',s)
        # Shared binary and contracts must remain unchanged relative to merged PR9.
        for name in ['TMessagesProj/build.gradle',
                     str((TRANS/'HTMLKeeper.java').relative_to(ROOT)),
                     'TMessagesProj/src/main/java/org/telegram/tgnet/TLRPC.java']:
            f=ROOT/name
            self.assertTrue(f.is_file(),name)
            old=subprocess.run(['git','show','333dd8c9beb35a2e3caa985279858df7b5bc2ee7:'+name],cwd=ROOT,capture_output=True,check=True).stdout
            self.assertTrue(hashlib.sha256(f.read_bytes()).digest()==hashlib.sha256(old).digest() or reviewed_change(name,hashlib.sha256(old).hexdigest()),name)

    def test_private_builders_and_error_surfaces(self):
        pa=method(TRANS/'source/GoogleTranslator.kt','private suspend fun translate(')
        self.assertLess(pa.index('requireRoute'),pa.index('throw TranslationServicesPolicy.denied()'))
        self.assertNotIn('urlBuilder',pa)
        self.assertNotIn('HttpClient',pa)
        llm=method(TRANS/'source/LLMTranslator.kt','private fun doLLMTranslate(')
        self.assertLess(llm.index('requireRoute'),llm.index('getNextApiKey'))
        for name in ['GoogleTranslator','GoogleAppTranslator','GoogleCloudTranslator','LLMTranslator']:
            text=(TRANS/'source'/f'{name}.kt').read_text()
            self.assertNotIn('${e.message}',text)
            self.assertNotIn('$bodyString',text)
            self.assertNotIn('error(respObj.toString',text)
            self.assertNotIn('FileLog.',text)
        self.assertNotIn('GoogleAppTranslator.doTranslate',(TRANS/'source/LLMTranslator.kt').read_text())
        self.assertNotIn('GoogleTranslatorNeko.translate',(TRANS/'source/GoogleTranslator.kt').read_text())

    def test_kotlin_production_methods_and_regressions(self):
        lib=Path(os.environ.get('KOTLIN_LIB',''))
        self.assertTrue(list(lib.glob('kotlin-compiler-embeddable-2.4.0.jar')),'Set KOTLIN_LIB to Gradle 9.7.1/lib')
        cp=os.pathsep.join(str(f) for f in lib.glob('*.jar'))
        with tempfile.TemporaryDirectory() as td:
            t=Path(td)
            # Real production policy compiled alongside Kotlin. A controlled policy
            # double is used only in a second run to reach failure/cancel branches.
            for authorized in [False,True]:
                java=t/'java';java.mkdir(exist_ok=True)
                (java/'TranslationServicesPolicy.java').write_text((TRANS/'TranslationServicesPolicy.java').read_text() if not authorized else '''package tw.nekomimi.nekogram.translate;
public final class TranslationServicesPolicy {
public enum Route {LLM,GOOGLE_LEGACY_PA}
public static boolean isProviderAuthorized(int p){return true;} public static void requireProvider(int p){}
public static void requireRoute(Route r){} public static int bulkProvider(int p){return p;}
public static SecurityException denied(){return new SecurityException("TRANSLATION_NOT_AUTHORIZED");}
public static String safeErrorCode(Throwable t){return "TRANSLATION_FAILED";}
public static RuntimeException safeFailure(Throwable t){return new IllegalStateException(safeErrorCode(t));}}
''')
                (java/'DiagnosticPolicy.java').write_text('package org.telegram.messenger;public class DiagnosticPolicy{public static boolean isIsolated(){return true;}}')
                (java/'TLRPC.java').write_text('package fixture; public class TLRPC {public static class MessageEntity{} public static class TL_textWithEntities {public String text="";public java.util.ArrayList<MessageEntity> entities=new java.util.ArrayList<>();}public static class TL_pollAnswer {public TL_textWithEntities text=new TL_textWithEntities();public byte[] option=new byte[0];}}')
                (java/'TranslateController.java').write_text('package fixture;public class TranslateController {public static class PollText {public TLRPC.TL_textWithEntities question;public TLRPC.TL_textWithEntities solution;public java.util.ArrayList<TLRPC.TL_pollAnswer> answers=new java.util.ArrayList<>();}public int cleanup=0;public void removeAsTranslatingItem(Object m){cleanup++;}public void removeAsManualTranslate(Object m){cleanup++;}}')
                command(['javac','-d',str(t/'classes')]+list(map(str,java.glob('*.java'))))
                source=self.kotlin_fixture(authorized)
                (t/'Fixture.kt').write_text(source)
                outcp=str(t/'classes')+os.pathsep+cp
                command(['java','-cp',cp,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-classpath',outcp,'-d',str(t/'kclasses'),str(t/'Fixture.kt')])
                out=command(['java','-cp',str(t/'kclasses')+os.pathsep+outcp,'FixtureKt'])
                self.assertNotIn(CANARY,out)

    def kotlin_fixture(self, authorized):
        central=method(TRANS/'Translator.kt','private suspend fun translateBase').replace('private suspend','suspend',1)
        bulk=method(TRANS/'Translator.kt','private fun getBulkTranslateProvider').replace('private fun','fun',1)
        llm=method(TRANS/'source/LLMTranslator.kt','override suspend fun doTranslate')
        google=method(TRANS/'source/GoogleTranslator.kt','override suspend fun doTranslate').replace('override suspend','suspend',1)
        message=method(BASE/'parts/MessageTrans.kt','private suspend fun translateText').replace('private suspend','suspend',1)
        poll=method(TRANS/'Translator.kt','fun translatePoll(')
        handler=method(BASE/'parts/MessageTrans.kt','private fun handleTranslationError').replace('private fun','fun',1)
        rich=method(BASE/'parts/MessageTrans.kt','private suspend fun ChatActivity.translateRichMessageContent').replace('private suspend','suspend',1)
        return (r'''
import kotlinx.coroutines.*
import java.io.IOException
import java.util.Locale
import fixture.TLRPC
import fixture.TranslateController
import kotlin.time.Duration.Companion.milliseconds
import tw.nekomimi.nekogram.translate.TranslationServicesPolicy
const val CANARY="SYNTHETIC_PRIVATE_TEXT_URL_KEY_RESPONSE_NOT_REAL"
object HTMLKeeper {fun entitiesToHtml(q:String,e:ArrayList<TLRPC.MessageEntity>,b:Boolean)=q
fun htmlToEntities(q:String,e:ArrayList<TLRPC.MessageEntity>,b:Boolean)=Pair(q,e)}
object TranslateAlert2 {fun preprocess(o:TLRPC.TL_textWithEntities,t:TLRPC.TL_textWithEntities)=t}
object BuildVars {const val LOGS_ENABLED=true}
object AndroidUtil {fun showErrorDialog(s:String){check(!s.contains(CANARY))}}
val String.code2Locale:Locale get()=Locale(this)
val Locale.locale2code:String get()=language
object State {var calls=0;var google=0;var mode="ok";val providers= arrayListOf<Int>();var retries=0}
interface Engine {suspend fun doTranslate(from:String,to:String,query:String,entities:ArrayList<TLRPC.MessageEntity>):TLRPC.TL_textWithEntities}
open class FakeEngine(val id:Int):Engine {override suspend fun doTranslate(from:String,to:String,query:String,entities:ArrayList<TLRPC.MessageEntity>):TLRPC.TL_textWithEntities {
State.calls++;State.providers.add(id)
if(State.mode=="cancel")throw CancellationException(CANARY)
if(State.mode=="fail")throw IllegalStateException(CANARY)
return TLRPC.TL_textWithEntities().apply{text=query;this.entities=entities}}}
object GoogleAppTranslator:FakeEngine(1)
object YandexTranslator:FakeEngine(3)
object LingoTranslator:FakeEngine(4)
object MicrosoftTranslator:FakeEngine(5)
object RealMicrosoftTranslator:FakeEngine(6)
object DeepLTranslator:FakeEngine(7)
object TelegramAPITranslator:FakeEngine(8){fun convertLanguageCode(l:String,c:String)=l}
object TranSmartTranslator:FakeEngine(9)
object Translator {
const val providerGoogle=1;const val providerYandex=3;const val providerLingo=4
const val providerMicrosoft=5;const val providerRealMicrosoft=6;const val providerDeepL=7
const val providerTelegram=8;const val providerTranSmart=9;const val providerLLMTranslator=10
''' +central+'\n'+bulk+r'''
suspend fun translate(t:Locale,q:String,e:ArrayList<TLRPC.MessageEntity>,p:Int)=translateBase(t,q,e,p)
suspend fun translate(t:Locale,q:String,p:Int):String=translateBase(t,q,arrayListOf(),p).text
}
class RateLimitException(s:String):Exception(s)
object LLMTranslator:Engine {
const val MAX_RETRY=3;var attempts=0
suspend fun<T> withTranslationContext(c:String?,block:suspend()->T):T=block()
fun backoffDelayWithJitterMillis(n:Int)=0L
fun backoffDelayMillis(n:Int)=0L
fun doLLMTranslate(to:String,text:String):String {
attempts++
when(State.mode){"io"->throw IOException(CANARY);"rate"->throw RateLimitException(CANARY);"cancel"->throw CancellationException(CANARY);"fail"->throw IllegalArgumentException(CANARY)}
return text}
''' + llm+r'''
}
object PaEngine {
val targetLanguages=listOf("es")
fun getString(i:Int)="unsupported"
object R {object string{const val TranslateApiUnsupported=1}}
fun translate(q:String,f:String,t:String):String {State.google++;if(State.mode=="cancel")throw CancellationException(CANARY);throw IllegalStateException(CANARY)}
''' +google+r'''
}
class Context
class Owner {var rich_message:Any?=Any()}
class MessageObject {val messageOwner=Owner()}

class ChatActivity {val parentActivity=Context();val translateController=TranslateController();fun translateMessages(t:Locale,p:Int,m:List<MessageObject>){State.retries++;State.providers.add(p)}}
object AlertUtil {var calls=0;fun showTransFailedDialog(c:Context,u:Boolean,s:String,retry:()->Unit){check(!s.contains(CANARY));calls++;retry()}}
object RichMessageTransHelper {var writes=0;fun collectPlainTexts(r:Any)=listOf(CANARY);fun getCachedTranslation(r:Any,t:String,s:String):String?=null
fun putCachedTranslation(r:Any,t:String,s:String,v:String){writes++};fun hasFullCache(r:Any,t:String)=writes>0}
''' +message+'\n'+handler+'\n'+rich+r'''
object NekoConfig {object translateToLang{fun String():String?="es"};object translationProvider{fun Int()=7}}
object LocaleController{fun getInstance()=this;val currentLocale=Locale("es")}
object AndroidUtilities {fun runOnUIThread(block:()->Unit)=block()}
object AppScope {val io=CoroutineScope(SupervisorJob()+Dispatchers.Unconfined)}
object PollApi {
interface TranslateCallBack3 {fun onSuccess(p:TranslateController.PollText);fun onFailed(u:Boolean,m:String)}
fun getBulkTranslateProvider(p:Int)=TranslationServicesPolicy.bulkProvider(p)
suspend fun translateBase(t:Locale,q:String,e:ArrayList<TLRPC.MessageEntity>,p:Int)=Translator.translateBase(t,q,e,p)
''' +poll+r'''
}

fun main()= runBlocking {
''' +(r'''
for(p in listOf(-1,0,1,2,3,4,5,6,7,8,9,10,999)){
try{Translator.translateBase(Locale("es"),CANARY,arrayListOf(),p);error("allowed")}catch(e:SecurityException){check(!e.toString().contains(CANARY))}}
check(State.calls==0 && State.google==0)
try{LLMTranslator.doTranslate("auto","es",CANARY,arrayListOf());error("allowed")}catch(e:SecurityException){}
check(LLMTranslator.attempts==0)
try{PaEngine.doTranslate("auto","es",CANARY,arrayListOf());error("allowed")}catch(e:SecurityException){}
check(State.google==0)
try{translateText(Locale("es"),CANARY,null,10,CANARY);error("allowed")}catch(e:SecurityException){}
val chat=ChatActivity()
try{chat.translateRichMessageContent(MessageObject(),Locale("es"),7);error("allowed")}catch(e:SecurityException){}
check(RichMessageTransHelper.writes==0)
''' if not authorized else r'''
// Controlled authority double reaches dormant paths; it is never shipped in Android.
for(p in listOf(3,4,5,6,7,8,9)){
State.mode="ok";check(Translator.translateBase(Locale("es"),CANARY,arrayListOf(),p).text==CANARY);check(State.providers.last()==p)}
check(Translator.getBulkTranslateProvider(7)==7)
val entities=arrayListOf(TLRPC.MessageEntity());check(Translator.translateBase(Locale("es"),CANARY,entities,7).entities===entities)
for(mode in listOf("io","rate","fail","cancel")){
State.mode=mode;LLMTranslator.attempts=0
try{LLMTranslator.doTranslate("auto","es",CANARY,arrayListOf());error("expected failure")}
catch(e:CancellationException){check(mode=="cancel")}
catch(e:Exception){check(mode!="cancel");check(!e.toString().contains(CANARY));check(e.cause==null)}
check(LLMTranslator.attempts==(if(mode=="io"||mode=="rate")3 else 1));check(State.providers.none{it==1})}
State.mode="cancel";try{PaEngine.doTranslate("auto","es",CANARY,arrayListOf());error("cancel swallowed")}catch(e:CancellationException){}
State.mode="fail";try{PaEngine.doTranslate("auto","es",CANARY,arrayListOf());error("expected failure")}catch(e:IllegalStateException){check(!e.toString().contains(CANARY));check(e.cause==null)}
State.mode="ok";val chat=ChatActivity();check(chat.translateRichMessageContent(MessageObject(),Locale("es"),7));check(State.providers.last()==7)
val writes=RichMessageTransHelper.writes
State.mode="fail";val retries=State.retries;check(!chat.translateRichMessageContent(MessageObject(),Locale("es"),7));check(State.retries==retries+1);check(State.providers.last()==7);check(RichMessageTransHelper.writes==writes)
State.mode="cancel";val dialogsBefore=AlertUtil.calls
try{chat.translateRichMessageContent(MessageObject(),Locale("es"),7);error("cancel swallowed")}catch(e:CancellationException){}
check(AlertUtil.calls==dialogsBefore);check(RichMessageTransHelper.writes==writes)
''' )+r'''
var pollSuccess=0;var pollFailed=0
PollApi.translatePoll(Locale("es"),TranslateController.PollText(),object:PollApi.TranslateCallBack3 {
override fun onSuccess(p:TranslateController.PollText){pollSuccess++}
override fun onFailed(u:Boolean,m:String){check(!m.contains(CANARY));pollFailed++}})
check(pollSuccess==EXPECTED_POLL_SUCCESS && pollFailed==1-EXPECTED_POLL_SUCCESS)
val controller=TranslateController();val m=MessageObject()
val retriesBefore=State.retries
handleTranslationError(Context(),SecurityException(CANARY),m,controller){State.retries++}
check(controller.cleanup==2);check(State.retries==retriesBefore)
val dialogs=AlertUtil.calls
try{handleTranslationError(Context(),CancellationException(CANARY),m,controller){State.retries++};error("cancel swallowed")}catch(e:CancellationException){}
check(AlertUtil.calls==dialogs);check(State.retries==retriesBefore)
println("production-method fixture passed; no external transport")
}
''').replace('EXPECTED_POLL_SUCCESS','1' if authorized else '0')

if __name__=='__main__':unittest.main()
