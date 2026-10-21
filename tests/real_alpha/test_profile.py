"""Execute actual Groovy/CMake validators and inspect source boundaries, not a merged APK."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
BASE='2d532562f68946a83f5cdd2fc1059e3024beb525'
A='{http://schemas.android.com/apk/res/android}'
T='{http://schemas.android.com/tools}'

class ProfileTests(unittest.TestCase):
    def test_production_remains_rejected_with_synthetic_overrides(self):
        with tempfile.TemporaryDirectory() as d:
            script=Path(d)/'check.groovy'
            script.write_text('''def reject=new GroovyShell().evaluate(new File(args[0]))
System.setProperty('FLEXYGRAM_PRODUCTION_ENABLED','true')
System.setProperty('TELEGRAM_APP_ID','123456')
boolean blocked=false
try { reject.call() } catch (IllegalStateException e) {
    blocked=e.message.startsWith('FLEXYGRAM_PRODUCTION_INCOMPLETE')
}
if (!blocked) throw new AssertionError('production opened')
println('PRODUCTION_BLOCKED')
''')
            p=subprocess.run([str(Path(os.environ['JAVA_HOME'])/'bin/java'),'-cp',str(Path(os.environ['FLEXYGRAM_GRADLE_HOME'])/'lib/*'),'groovy.ui.GroovyMain',str(script),str(ROOT/'gradle/production-readiness.gradle')],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('PRODUCTION_BLOCKED',p.stdout)

    def test_actual_groovy_closed_profile_and_mutations(self):
        java=Path(os.environ['JAVA_HOME'])/'bin/java'
        libs=Path(os.environ['FLEXYGRAM_GRADLE_HOME'])/'lib/*'
        row=json.loads((ROOT/'gradle/real-alpha.json').read_text())
        cases=[row,dict(row,applicationId='com.exteraless.app'),dict(row,isolated=False),dict(row,capabilities={}),dict(row,apiHash='SYNTHETIC_FORBIDDEN')]
        cases.extend(dict(row,capabilities=dict(row['capabilities'],**{key:True})) for key in row['capabilities'])
        cases.extend(dict(row,capabilities=dict(row['capabilities'],authentication=value)) for value in [None,'false',0])
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);script=folder/'check.groovy'
            script.write_text('new GroovyShell().evaluate(new File(args[0])).call(new File(args[1]));println("CLOSED")')
            for index,case in enumerate(cases):
                path=folder/'row.json';path.write_text(json.dumps(case))
                p=subprocess.run([str(java),'-cp',str(libs),'groovy.ui.GroovyMain',str(script),str(ROOT/'gradle/real-alpha.gradle'),str(path)],capture_output=True,text=True)
                with self.subTest(case=index):self.assertEqual(p.returncode==0,index==0,p.stderr)

    def test_actual_native_profile_binding_and_denial_constants(self):
        cmake=os.environ['FLEXYGRAM_CMAKE']
        scope=hashlib.sha256((ROOT/'gradle/real-alpha.json').read_bytes()).hexdigest()+':realAlpha'
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);source=folder/'src';source.mkdir()
            (source/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject(Alpha NONE)\ninclude("'+str(ROOT/'TMessagesProj/jni/real-alpha-policy.cmake')+'")\n')
            for name,flavor,value,good in [('valid','realAlpha',scope,True),('old','betaDevelopment',scope,False),('production','production',scope,False),('scope','realAlpha','0'*64+':realAlpha',False)]:
                p=subprocess.run([cmake,'-S',str(source),'-B',str(folder/name),'-DFLEXYGRAM_FLAVOR='+flavor,'-DFLEXYGRAM_POLICY_SCOPE='+value],capture_output=True,text=True)
                with self.subTest(case=name):self.assertEqual(p.returncode==0,good,p.stdout+p.stderr)
            # Execute the actual immutable JNI policy constants with this profile's generated header.
            cpp=folder/'constants.cpp'
            cpp.write_text('#include "'+str(ROOT/'TMessagesProj/jni/tgnet/DiagnosticPolicy.h')+'"\nint main(){return !flexygram::isolatedDiagnostic || flexygram::authenticationAllowed || flexygram::telegramTransportAllowed || flexygram::pushAllowed || flexygram::translationAllowed || flexygram::pluginsAllowed || flexygram::sessionRestoreAllowed;}')
            subprocess.run(['c++','-std=c++17','-I'+str(folder/'valid/flexygram-policy'),str(cpp),'-o',str(folder/'constants')],check=True,capture_output=True)
            self.assertEqual(subprocess.run([str(folder/'constants')]).returncode,0)

    def test_offline_sources_and_security_contracts_byte_identical(self):
        files=['gradle/variant-policy.json','gradle/variant-policy.gradle','gradle/production-readiness.gradle','gradle/beta-development.json','gradle/beta-development.gradle','gradle/telegram-api.gradle','TMessagesProj/jni/variant-policy.cmake','TMessagesProj/jni/beta-development-policy.cmake','TMessagesProj/jni/tgnet/DiagnosticPolicy.h','TMessagesProj/jni/tgnet/ConnectionsManager.cpp','TMessagesProj/jni/tgnet/ConnectionSocket.cpp','TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java','TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java','TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java','TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java','TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java','TMessagesProj/src/main/AndroidManifest.xml','tests/native_compatibility/android_lab/contract.json']
        for source_set in ['diagnostic','betaDevelopment','production']:
            files.extend(str(p.relative_to(ROOT)) for p in (ROOT/'TMessagesProj/src'/source_set).rglob('*') if p.is_file())
        for path in files:
            expected=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
            with self.subTest(path=path):self.assertEqual((ROOT/path).read_bytes(),expected)

    def test_minimal_native_launch_hook_only(self):
        path='TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java'
        original=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).decode()
        self.assertEqual((ROOT/path).read_text(),original.replace('private BaseFragment getClientNotActivatedFragment()','protected BaseFragment getClientNotActivatedFragment()'))
        # Catch signature drift hidden by the Android doubles.
        self.assertIn('public void onNewIntent(Intent intent)',original)
        self.assertIn('public boolean needPresentFragment(INavigationLayout layout, INavigationLayout.NavigationParams params)',original)

    def test_source_manifest_is_closed_and_namespaced(self):
        manifest=ET.parse(ROOT/'TMessagesProj/src/realAlpha/AndroidManifest.xml').getroot()
        permissions={e.get(A+'name') for e in manifest.findall('uses-permission') if e.get(T+'node') not in ['remove','removeAll']}
        self.assertEqual(permissions,{'android.permission.ACCESS_NETWORK_STATE','${applicationId}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'})
        self.assertTrue(any(e.get(T+'node')=='removeAll' for e in manifest.findall('uses-permission')))
        app=manifest.find('application')
        for kind in ['activity','activity-alias','service','receiver','provider']:
            self.assertTrue(any(e.get(T+'node')=='removeAll' for e in app.findall(kind)),kind)
        live=[e for e in app.findall('activity') if e.get(T+'node') not in ['remove','removeAll']]
        self.assertEqual(len(live),1);self.assertEqual(live[0].get(A+'name'),'org.telegram.ui.realalpha.RealAlphaActivity')
        actions=[e.get(A+'name') for e in live[0].findall('intent-filter/action')]
        self.assertEqual(actions,['android.intent.action.MAIN'])
        providers=[e for e in app.findall('provider') if e.get(T+'node') not in ['remove','removeAll']]
        self.assertEqual([e.get(A+'authorities') for e in providers],['${applicationId}.jlatexmathinitprovider'])
        self.assertEqual(providers[0].get(A+'exported'),'false')
        common=ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').getroot().find('application')
        for attr in ['allowBackup','restoreAnyVersion','fullBackupContent']:self.assertEqual(common.get(A+attr),'false')

    def test_no_synthetic_ui_or_account_fabrication(self):
        source='\n'.join(p.read_text() for p in (ROOT/'TMessagesProj/src/realAlpha/java').rglob('*.java'))
        for forbidden in ['setCurrentUser(', 'putUser(', 'ThemePreviewMessagesCell', 'OfflineConversationView','BetaPreviewActivity','TL_auth_resetAuthorizations','TL_auth_logOut','native_init(', 'native_sendRequest(']:
            with self.subTest(token=forbidden):self.assertNotIn(forbidden,source)
        self.assertIn('extends LaunchActivity',source);self.assertIn('new DialogsActivity(null)',source)

    def test_gradle_is_opt_in_unsigned_debug_arm64(self):
        source=(ROOT/'TMessagesProj/build.gradle').read_text()
        self.assertIn("providers.gradleProperty('flexygramRealAlpha').orNull == 'true'",source)
        self.assertIn("realAlphaEnabled && System.getenv('NATIVE_TARGET') != 'arm64-v8a'",source)
        self.assertIn("realAlphaEnabled && flavor == 'realAlpha' && builder.buildType == 'debug'",source)
        self.assertIn("realAlphaImplementation project(':translation-compat-beta-offline')",source)
        self.assertIn("def appId = '0'",source);self.assertIn("def appHash = ''",source)
        block=source.split('            realAlpha {',1)[1].split('\n            }',1)[0]
        self.assertNotIn('signingConfig',block)
