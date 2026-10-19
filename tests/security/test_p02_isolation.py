"""P0.2 offline checks: production resolver, RPC gate, native guards and manifest.
No Android app, account, socket or external service is executed by this suite.
"""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
MAIN=ROOT/'TMessagesProj/src/main'
JAVA=MAIN/'java'
ANDROID='{http://schemas.android.com/apk/res/android}'
TOOLS='{http://schemas.android.com/tools}'
ID='io.github.jose22yt.flexygram.diagnostic'


def run(command, **kw):
    result=subprocess.run(command,capture_output=True,text=True,**kw)
    if result.returncode:raise AssertionError(result.stdout+result.stderr)
    return result


class IsolationTests(unittest.TestCase):
    def test_identity_backup_permissions_components(self):
        manifest=ET.parse(MAIN/'AndroidManifest.xml').getroot()
        self.assertIn('APP_PACKAGE='+ID,(ROOT/'gradle.properties').read_text())
        app=manifest.find('application')
        self.assertEqual(app.get(ANDROID+'label'),'FlexyGram Diagnostic')
        self.assertEqual(app.get(ANDROID+'allowBackup'),'false')
        self.assertNotIn(ANDROID+'backupAgent',app.attrib)
        self.assertEqual(app.get(ANDROID+'restoreAnyVersion'),'false')
        internet=next(e for e in manifest.findall('uses-permission') if e.get(ANDROID+'name')=='android.permission.INTERNET')
        self.assertEqual(internet.get(TOOLS+'node'),'remove')
        # Keep all 18 existing tests; strengthen this contract against inherited
        # sensitive permissions and every IPC category, not just six services.
        requested={e.get(ANDROID+'name') for e in manifest.findall('uses-permission')
                   if e.get(ANDROID+'name') and e.get(TOOLS+'node')!='remove'}
        self.assertEqual(requested,{'android.permission.ACCESS_NETWORK_STATE',
                                  '${applicationId}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'})
        self.assertTrue(any(e.get(TOOLS+'node')=='removeAll' for e in manifest.findall('uses-permission')))
        for kind in ['service','receiver','provider','activity','activity-alias']:
            self.assertTrue(any(e.get(TOOLS+'node')=='removeAll' for e in app.findall(kind)),kind)
            for component in app.findall(kind):
                if component.get(TOOLS+'node') in ['remove','removeAll']:
                    continue
                if kind=='provider' and component.get(ANDROID+'name')=='ru.noties.jlatexmath.JLatexMathInitProvider':
                    self.assertEqual(component.get(ANDROID+'enabled'),'true')
                    self.assertEqual(component.get(ANDROID+'exported'),'false')
                    self.assertEqual(component.get(ANDROID+'authorities'),'${applicationId}.jlatexmathinitprovider')
                elif kind in ['service','receiver','provider']:
                    self.assertEqual(component.get(ANDROID+'enabled'),'false',component.attrib)
                    self.assertEqual(component.get(ANDROID+'exported'),'false',component.attrib)
                if kind=='activity':
                    self.assertEqual(component.get(ANDROID+'exported'),'false',component.attrib)
        active_aliases=[e for e in app.findall('activity-alias')
                        if e.get(TOOLS+'node') not in ['remove','removeAll']
                        and e.get(ANDROID+'enabled','true')=='true']
        self.assertEqual([e.get(ANDROID+'name') for e in active_aliases],['org.telegram.messenger.ExteralessIcon'])
        launch=next(e for e in app.findall('activity') if e.get(ANDROID+'name')=='org.telegram.ui.LaunchActivity')
        self.assertFalse(launch.findall('intent-filter'))
        fcm=next(e for e in manifest.findall('uses-permission') if e.get(ANDROID+'name')=='com.google.android.c2dm.permission.RECEIVE')
        self.assertEqual(fcm.get(TOOLS+'node'),'remove')
        for kind,name in [
            ('service','androidx.sharetarget.ChooserTargetServiceCompat'),
            ('service','androidx.credentials.playservices.CredentialProviderMetadataHolder'),
            ('service','com.google.mlkit.common.internal.MlKitComponentDiscoveryService'),
            ('service','com.google.firebase.components.ComponentDiscoveryService'),
            ('service','androidx.room.MultiInstanceInvalidationService'),
            ('receiver','androidx.car.app.notification.CarAppNotificationBroadcastReceiver'),
            ('receiver','androidx.profileinstaller.ProfileInstallReceiver')]:
            component=next(e for e in app.findall(kind) if e.get(ANDROID+'name')==name)
            self.assertEqual(component.get(TOOLS+'node'),'remove',name)
        for name in ['.AuthenticatorService','.ContactsSyncAdapterService','.GcmPushListenerService','.UnifiedPushService','.FilesMigrationService','.ImportingService']:
            component=next(e for e in app.findall('service') if e.get(ANDROID+'name')==name)
            self.assertEqual(component.get(ANDROID+'enabled'),'false',name)
        for provider in app.findall('provider'):
            authority=provider.get(ANDROID+'authorities')
            if authority:self.assertTrue(authority.startswith('${applicationId}.'),authority)
        for file in ['auth.xml','sync_contacts.xml']:
            node=ET.parse(MAIN/'res/xml'/file).getroot()
            self.assertEqual(node.get(ANDROID+'accountType'),ID)
        extraction=ET.parse(MAIN/'res/xml/diagnostic_data_extraction.xml').getroot()
        for kind in ['cloud-backup','device-transfer']:
            self.assertEqual(len(extraction.find(kind).findall('exclude')),9)

    def test_diagnostic_api_and_engine_controls_are_immutable(self):
        gradle=(ROOT/'TMessagesProj/build.gradle').read_text()
        self.assertIn("'ISOLATED_DIAGNOSTIC', 'true'",gradle)
        self.assertIn("def appId = '0'",gradle)
        self.assertIn("def appHash = ''",gradle)
        self.assertNotIn("def appId = '6'",gradle)
        self.assertNotIn('signingConfig = hasReleaseKeystore',gradle)
        for file,methods in {
            'app/exteraless/plugins/PluginsController.java':['isEngineEnabled','setEngineEnabled','isDeveloperMode','setDeveloperMode','setPluginEnabled'],
            'app/exteraless/plugins/PythonPluginsEngine.java':['ensureStarted'],
            'app/exteraless/updater/GitHubUpdater.java':['check','fetch','download'],
            'org/telegram/messenger/BackupAgent.java':['onCreate','requestBackup'],
        }.items():
            source=(JAVA/file).read_text()
            for name in methods:
                import re
                found=re.search(r'public [^\n]*\b'+name+r'\([^\n]*\) \{([^\n]*\n[^\n]*)',source)
                self.assertIsNotNone(found,(file,name))
                self.assertIn('DiagnosticPolicy.isIsolated()',found[1],(file,name))

    def test_actual_pair_resolver_complete_precedence_and_invalid_inputs(self):
        # Use Groovy bundled with the exact downloaded project Wrapper.
        caches=Path(os.environ.get('GRADLE_USER_HOME',Path.home()/'.gradle'))
        libs=list(caches.glob('wrapper/dists/gradle-9.7.1-bin/*/gradle-9.7.1/lib'))
        self.assertTrue(libs,'Run the project Wrapper once to provision Groovy')
        script=r'''
        def resolver=new GroovyShell().evaluate(new File(args[0]))
        def props={ Map values -> def p=new Properties();p.putAll(values);p }
        def pair=[TELEGRAM_APP_ID:'123456',TELEGRAM_APP_HASH:'0123456789abcdef0123456789abcdef']
        assert resolver(props([:]),[:]) == null
        assert resolver(props([:]),pair).id == 123456
        assert resolver(props(pair),[TELEGRAM_APP_ID:'234567',TELEGRAM_APP_HASH:'abcdef0123456789abcdef0123456789']).source == 'local.properties'
        def bad=[[TELEGRAM_APP_ID:'123456'],[TELEGRAM_APP_HASH:pair.TELEGRAM_APP_HASH],
          [TELEGRAM_APP_ID:'',TELEGRAM_APP_HASH:''],[TELEGRAM_APP_ID:'6',TELEGRAM_APP_HASH:pair.TELEGRAM_APP_HASH],
          [TELEGRAM_APP_ID:'2147483648',TELEGRAM_APP_HASH:pair.TELEGRAM_APP_HASH],
          [TELEGRAM_APP_ID:'123456',TELEGRAM_APP_HASH:'SYNTHETIC_SECRET_DO_NOT_LOG']]
        bad.each { values ->
          boolean failed=false
          try {resolver(props(values),pair)} catch(IllegalArgumentException e){
             failed=true; assert !e.message.contains('SYNTHETIC_SECRET'); assert !e.message.contains(pair.TELEGRAM_APP_HASH)
          };assert failed
          failed=false
          try {resolver(props([:]),values)} catch(IllegalArgumentException e){failed=true};assert failed
        }
        println 'resolver PASS'
        '''
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'test.groovy';p.write_text(script)
            result=run(['java','-cp',str(libs[0]/'*'),'groovy.ui.GroovyMain',str(p),str(ROOT/'gradle/telegram-api.gradle')])
            self.assertEqual(result.stdout.strip(),'resolver PASS')

    def test_production_rpc_gate_and_push_callbacks_no_transport(self):
        spec=importlib.util.spec_from_file_location('harness',Path(__file__).with_name('java_harness.py'))
        h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
        # P0.1 fixture is reused; production FCM/provider classes are compiled.
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);h.write_sources(directory,MAIN/'java/org/telegram/messenger',MAIN)
            package=directory/'org/telegram/messenger'
            (package/'DiagnosticPolicy.java').write_text((JAVA/'org/telegram/messenger/DiagnosticPolicy.java').read_text())
            from push_fixtures import BUILD_CONFIG
            (package/'BuildConfig.java').write_text(BUILD_CONFIG.replace('public class BuildConfig {', 'public class BuildConfig {public static final boolean ISOLATED_DIAGNOSTIC=true;'))
            source=(JAVA/'org/telegram/tgnet/ConnectionsManager.java').read_text()
            signature='public int sendRequest(final TLObject object, final RequestDelegate onComplete, final RequestDelegateTimestamp'
            method=h.method(source,signature)
            (package/'RpcGate.java').write_text('''package org.telegram.messenger; import org.telegram.tgnet.*;import java.util.concurrent.atomic.AtomicInteger;
            public class RpcGate {public static int nativeCalls;AtomicInteger lastRequestToken=new AtomicInteger();
            interface RequestDelegate {void run(TLObject r,TLRPC.TL_error e);} interface RequestDelegateTimestamp {void run(TLObject r,TLRPC.TL_error e,long t);}
            interface QuickAckDelegate {} interface WriteToSocketDelegate {}
            void sendRequestInternal(TLObject o,RequestDelegate d,RequestDelegateTimestamp t,QuickAckDelegate q,WriteToSocketDelegate w,int f,int dc,int c,boolean i,int token){nativeCalls++;}
            '''+method+'''
            public static void main(String[] args){int[] callbacks={0};RpcGate g=new RpcGate();
            for(int i=0;i<20;i++)g.sendRequest(new TLObject(),(r,e)->{if(e.code!=403||!"DIAGNOSTIC_AUTH_DISABLED".equals(e.text))throw new AssertionError();callbacks[0]++;},null,null,null,0,0,0,true);
            if(callbacks[0]!=20||nativeCalls!=0)throw new AssertionError();
            int backups=BackupAgent.calls;TLRPC.TL_auth_authorization auth=new TLRPC.TL_auth_authorization();auth.future_auth_token="SYNTHETIC".getBytes();AuthTokensHelper.saveLogInToken(auth);
            if(BackupAgent.calls!=backups||AuthTokensHelper.getSavedLogInTokens()!=null||AuthTokensHelper.getSavedLogOutTokens()!=null)throw new AssertionError();
            int before=PushListenerController.sends;new GcmPushListenerService().onNewToken("SYNTHETIC");new GooglePushListenerServiceProvider().onRequestPushToken();
            if(PushListenerController.sends!=before)throw new AssertionError();System.out.println("gate PASS");}}
            ''')
            utility=package/'Utilities.java';s=utility.read_text().replace('public static Queue globalQueue','public static Queue stageQueue=new Queue();public static Queue globalQueue');utility.write_text(s)
            compiler=['java','--module','jdk.compiler/com.sun.tools.javac.Main']
            run([*compiler,'-d',str(directory),*[str(p) for p in directory.rglob('*.java')]])
            self.assertEqual(run(['java','-cp',str(directory),'org.telegram.messenger.RpcGate']).stdout.strip(),'gate PASS')

    def test_native_guards_drop_requests_and_prevent_initialization(self):
        source=(ROOT/'TMessagesProj/jni/tgnet/ConnectionsManager.cpp').read_text()
        header=ROOT/'TMessagesProj/jni/tgnet/DiagnosticPolicy.h'
        def guard(signature):
            part=source[source.index(signature):];return part[part.index('{')+1:part.index('\n',part.index('{')+2)]
        # Execute verbatim entry guards from production with a fake transport tail.
        send=guard('void ConnectionsManager::sendRequest(');init=guard('void ConnectionsManager::init(')
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);cpp=p/'test.cpp'
            cpp.write_text('#include "'+str(header)+'"\nint writes=0,loads=0,freed=0;struct Object{~Object(){freed++;}};\nvoid send(Object*object){'+send+'\nwrites++;}\nvoid init(){'+init+'\nloads++;}\nint main(){for(int i=0;i<20;i++){send(new Object);init();}return writes||loads||freed!=20;}')
            run(['c++','-std=c++17',str(cpp),'-o',str(p/'test')]);run([str(p/'test')])
        socket=(ROOT/'TMessagesProj/jni/tgnet/ConnectionSocket.cpp').read_text()
        for name in ['openConnection(', 'openConnectionInternal(']:
            part=socket[socket.index('void ConnectionSocket::'+name):]
            self.assertIn('if (flexygram::isolatedDiagnostic) return;',part[:part.index('{')+100])


if __name__=='__main__':unittest.main()

