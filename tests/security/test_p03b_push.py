"""Offline synthetic service tests; requires project Groovy for resolver coverage."""
import os,subprocess,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from java_harness import method,write_sources
ROOT=Path(__file__).resolve().parents[2];MAIN=ROOT/'TMessagesProj/src/main';JAVA=MAIN/'java/org/telegram/messenger'
CANARY='SYNTHETIC_PUSH_SECRET_DO_NOT_LOG_031b'
class PushTests(unittest.TestCase):
    def test_private_resolver(self):
        cache=Path(os.environ.get('GRADLE_USER_HOME',Path.home()/'.gradle'))
        libs=list(cache.glob('wrapper/dists/gradle-9.7.1-bin/*/gradle-9.7.1/lib'));self.assertTrue(libs,'Provision project Gradle/Groovy first')
        script=r'''
        import groovy.json.JsonOutput
        def resolve=new GroovyShell().evaluate(new File(args[0]));def props={Map m->def p=new Properties();p.putAll(m);p};def id='io.github.jose22yt.flexygram.synthetic'
        assert !resolve(props([:]),[:],id,false).fcm;assert !resolve(props([:]),[:],id,true).unified
        def file=new File(args[1],'flexygram-push.private.json');def env=[FLEXYGRAM_PUSH_CONFIG_FILE:file.absolutePath]
        def firebase=[projectId:'flexygram-synthetic',senderId:'123456789012',appId:'1:123456789012:android:0123456789abcdef012345',apiKey:'AIza'+('X'*35)]
        def good=[schema:1,ownerApproved:true,androidId:id,firebase:firebase,unifiedPush:[gateway:'https://push.invalid/path',distributor:'test.synthetic.distributor']]
        def write={data->file.text=JsonOutput.toJson(data)};write(good);def result=resolve(props([:]),env,id,false);assert result.fcm&&result.unified&&result.scope.size()==64;assert result.gateway=='https://push.invalid/path/';def scope=result.scope
        def reject={boolean isolated=false->boolean failed=false;try{resolve(props([:]),env,id,isolated)}catch(IllegalArgumentException e){failed=true;assert !e.message.contains(file.absolutePath)&&!e.message.contains('SYNTHETIC_PUSH_SECRET')&&!e.message.contains(firebase.apiKey)};assert failed};reject(true)
        for(def patch:[[schema:2],[ownerApproved:false],[androidId:'com.exteraless.app'],[private_key:'SYNTHETIC_PUSH_SECRET_DO_NOT_LOG_031b'],[firebase:firebase+[projectId:'exteraless']],[firebase:firebase.findAll{it.key!='apiKey'}],[firebase:firebase+[senderId:'335004274031']],[firebase:firebase+[apiKey:'SYNTHETIC_PUSH_SECRET_DO_NOT_LOG_031b']],[unifiedPush:[gateway:'http://push.invalid/',distributor:'test.synthetic.distributor']],[unifiedPush:[gateway:'https://user:password@push.invalid/',distributor:'test.synthetic.distributor']],[unifiedPush:[gateway:'https://push.invalid/?secret=x',distributor:'test.synthetic.distributor']],[unifiedPush:[gateway:'https://p2p.belloworld.it/',distributor:'test.synthetic.distributor']]]){write(good+patch);reject()}
        file.text='SYNTHETIC_PUSH_SECRET_DO_NOT_LOG_031b';reject();file.delete();reject();reject(true);good.firebase.apiKey='AIza'+('Y'*35);write(good);assert resolve(props([:]),env,id,false).scope!=scope;assert !resolve(props([FLEXYGRAM_PUSH_CONFIG_FILE:'']),env,id,false).fcm
        println 'PASS resolver'
        '''
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'test.groovy';p.write_text(script)
            result=subprocess.run(['java','-cp',str(libs[0]/'*'),'groovy.ui.GroovyMain',str(p),str(ROOT/'gradle/push-services.gradle'),temp],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    def test_production_callbacks_and_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);write_sources(root,JAVA,MAIN);pkg=root/'org/telegram/messenger'
            for name in ['PushServicesPolicy','UnifiedPushListenerServiceProvider']:(pkg/f'{name}.java').write_text((JAVA/f'{name}.java').read_text())
            p=pkg/'SharedConfig.java';p.write_text(p.read_text().replace('public class SharedConfig {','public class SharedConfig {public static void saveConfig(){}'))
            (pkg/'P03bMain.java').write_text(r'''
package org.telegram.messenger;import com.google.firebase.*;import com.google.firebase.messaging.*;import org.unifiedpush.android.connector.UnifiedPush;
public class P03bMain {static void ok(boolean b){if(!b)throw new AssertionError();}public static void main(String[] args){
String secret="SYNTHETIC_PUSH_SECRET_DO_NOT_LOG_031b";BuildConfig.FLEXYGRAM_FCM_API_KEY="AIza"+"X".repeat(35);FirebaseApp.instance=new FirebaseApp();GooglePushListenerServiceProvider google=new GooglePushListenerServiceProvider();UnifiedPushListenerServiceProvider up=new UnifiedPushListenerServiceProvider();
BuildConfig.FLEXYGRAM_FCM_ENABLED=false;BuildConfig.FLEXYGRAM_UNIFIED_PUSH_ENABLED=false;int lookups=FirebaseApp.lookups,sends=PushListenerController.sends;google.onRequestPushToken();new GcmPushListenerService().onNewToken(secret);google.hasServices();up.hasServices();up.onRequestPushToken();ok(FirebaseApp.lookups==lookups&&FirebaseApp.initializations==0&&UnifiedPush.probes==0&&UnifiedPush.registrations==0&&PushListenerController.sends==sends);
BuildConfig.FLEXYGRAM_FCM_ENABLED=true;BuildConfig.FLEXYGRAM_UNIFIED_PUSH_ENABLED=true;DiagnosticPolicy.isolated=true;google.onRequestPushToken();new GcmPushListenerService().onNewToken(secret);up.onRequestPushToken();ok(!PushServicesPolicy.anyAllowed()&&FirebaseApp.lookups==lookups&&UnifiedPush.probes==0);
DiagnosticPolicy.isolated=false;ok(PushServicesPolicy.fcmAllowed()&&PushServicesPolicy.unifiedAllowed());BuildConfig.FLEXYGRAM_PUSH_ANDROID_ID="com.exteraless.app";ok(!PushServicesPolicy.anyAllowed());BuildConfig.FLEXYGRAM_PUSH_ANDROID_ID=BuildConfig.APPLICATION_ID;String scope=BuildConfig.FLEXYGRAM_PUSH_SCOPE;BuildConfig.FLEXYGRAM_PUSH_SCOPE="";ok(!PushServicesPolicy.anyAllowed());BuildConfig.FLEXYGRAM_PUSH_SCOPE=scope;ok(!PushServicesPolicy.isTypeAllowed(13));
FirebaseApp.instance.options=new FirebaseOptions.Builder().setProjectId("foreign").build();new GcmPushListenerService().onNewToken(secret);google.onRequestPushToken();ok(PushListenerController.sends==sends);FirebaseApp.instance=new FirebaseApp();FirebaseMessaging.token=secret;google.onRequestPushToken();ok(secret.equals(PushListenerController.registered));UnifiedPush.distributors.add("foreign.distributor");up.onRequestPushToken();ok(UnifiedPush.registrations==0);UnifiedPush.distributors.add(PushServicesPolicy.distributor());up.onRequestPushToken();ok(UnifiedPush.registrations==1&&PushServicesPolicy.distributor().equals(UnifiedPush.saved));for(String line:FileLog.lines)ok(!line.contains(secret));ok(!PushServicesPolicy.crashReportingAllowed());System.out.println("PASS production policy/callbacks; no real services");}}
''')
            result=subprocess.run(['javac','-d',str(root),*[str(p) for p in root.rglob('*.java')]],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run(['java','-cp',str(root),'org.telegram.messenger.P03bMain'],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertNotIn(CANARY,result.stdout+result.stderr)
    def test_artifact_scanner(self):
        import io,zipfile,json
        from push_artifact_scan import scan_bytes
        def archive(entries):
            b=io.BytesIO()
            with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
                for name,data in entries.items():z.writestr(name,data)
            return b.getvalue()
        self.assertTrue(scan_bytes(archive({'classes.dex':b'empty configuration'}),[CANARY])['passed']);bad=scan_bytes(archive({'assets/runtime.imy':archive({'config':CANARY.encode('utf-16le')})}),[CANARY]);self.assertFalse(bad['passed']);self.assertGreater(bad['forbidden_value_hits'],0);self.assertNotIn(CANARY,json.dumps(bad));self.assertFalse(scan_bytes(archive({'resources.arsc':('AIza'+'X'*35).encode('utf-16le')}),[])['passed'])
    def test_manifest_and_guards(self):
        a='{http://schemas.android.com/apk/res/android}';app=ET.parse(MAIN/'AndroidManifest.xml').getroot().find('application')
        for key in ['firebase_messaging_auto_init_enabled','firebase_analytics_collection_enabled','firebase_crashlytics_collection_enabled']:self.assertEqual(next(e for e in app.findall('meta-data') if e.get(a+'name')==key).get(a+'value'),'false')
        for file,sigs in {'PushListenerController.java':['public static void processRemoteMessage(','private static void sendRegistrationToServerInternal(','public static void refreshRegistration(','private static void unregisterPush('],'ApplicationLoader.java':['private static void initPushServices(','private static void startPushServiceInternal(']}.items():
            source=(JAVA/file).read_text()
            for sig in sigs:self.assertIn('PushServicesPolicy.','\n'.join(method(source,sig).splitlines()[1:4]))
        up=(JAVA/'UnifiedPushService.java').read_text();self.assertIn('UP_GATEWAY_DEFAULT = ""',up);self.assertNotIn('e.getMessage()',up);self.assertNotIn('FileLog.e(e)',up);self.assertNotIn('+ reason)',up);self.assertNotIn('getString(NaConfig.INSTANCE.getPushServiceTypeUnifiedGateway()',up)
        shared=(JAVA/'SharedConfig.java').read_text();self.assertIn('ownPushState ? preferences.getString("pushString2"',shared);self.assertIn('ownPushState ? preferences.getString("pushAuthKey"',shared);self.assertFalse((ROOT/'TMessagesProj/google-services.json').exists());self.assertIn('APP_PACKAGE, true)',(ROOT/'TMessagesProj/build.gradle').read_text())
