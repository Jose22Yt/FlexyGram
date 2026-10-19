"""Architecture regressions: real Gradle policy, Java, CMake and native guards.
Offline synthetic harnesses only. No Android installation or provider request.
"""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,unittest,xml.etree.ElementTree as ET
from native_fixture import configure
ROOT=Path(__file__).resolve().parents[2]
A='{http://schemas.android.com/apk/res/android}'
BASE='d9f2b788cf23e830e84ba24e9f6cb2e71e13bd4d'
def run(args,**kw):
 r=subprocess.run(list(map(str,args)),capture_output=True,text=True,**kw)
 if r.returncode:raise AssertionError(r.stdout+r.stderr)
 return r.stdout+r.stderr
class VariantsTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.dir=Path(self.temp.name)
  self.policy=json.loads((ROOT/'gradle/variant-policy.json').read_text())['variants']
 def tearDown(self):self.temp.cleanup()
 def groovy(self,source,*args):
  p=self.dir/'test.groovy';p.write_text(source)
  lib=Path(os.environ['KOTLIN_LIB'])
  return run(['java','-cp',str(lib/'*'),'groovy.ui.GroovyMain',p,*args])
 def test_real_policy_rejects_unknown_ids_missing_fields_and_enabled_capabilities(self):
  self.groovy('''def resolve=new GroovyShell().evaluate(new File(args[0])); def source=new File(args[1]);
assert resolve(source).diagnostic.applicationId=='io.github.jose22yt.flexygram.diagnostic'
assert resolve(source).production.applicationId=='io.github.jose22yt.flexygram.app'
def original=source.text
for(def patch : [{it.variants.production.buildEnabled=true},{it.variants.production.capabilities.authentication=true},
 {it.variants.diagnostic.capabilities.push=true},{it.variants.production.applicationId='com.exteraless.app'},
 {it.variants.diagnostic.isolated=false},{it.variants.production.capabilities.remove('translation')},
 {it.variants.unknown=it.variants.production},{it.variants.diagnostic.extra='SYNTHETIC_PRIVATE'}]) {
 def data=new groovy.json.JsonSlurper().parseText(original);patch(data)
 def f=new File(args[2]);f.text=groovy.json.JsonOutput.toJson(data)
 boolean denied=false;try{resolve(f)}catch(IllegalArgumentException e){denied=true;assert !e.message.contains('SYNTHETIC_PRIVATE')};assert denied
}''',ROOT/'gradle/variant-policy.gradle',ROOT/'gradle/variant-policy.json',self.dir/'mutated.json')
 def test_production_gate_cannot_be_bypassed_with_synthetic_configuration(self):
  self.groovy('''def deny=new GroovyShell().evaluate(new File(args[0]));
System.setProperty('FLEXYGRAM_PRODUCTION_ENABLED','true');System.setProperty('TELEGRAM_APP_ID','123456');
boolean rejected=false;try{deny()}catch(IllegalStateException e){rejected=true;assert e.message.startsWith('FLEXYGRAM_PRODUCTION_INCOMPLETE');assert !e.message.contains('123456')};assert rejected''',ROOT/'gradle/production-readiness.gradle')
 def test_manifest_source_move_preserves_every_previous_restriction(self):
  original=subprocess.check_output(['git','show',BASE+':TMessagesProj/src/main/AndroidManifest.xml'],cwd=ROOT)
  self.assertEqual((ROOT/'TMessagesProj/src/diagnostic/AndroidManifest.xml').read_bytes(),original)
  for flavor in ['main','production']:
   root=ET.parse(ROOT/f'TMessagesProj/src/{flavor}/AndroidManifest.xml').getroot()
   self.assertFalse(root.findall('uses-permission'))
   self.assertFalse(root.find('application').findall('activity'))
  self.assertEqual(ET.parse(ROOT/'TMessagesProj/src/production/AndroidManifest.xml').getroot().find('application').get(A+'enabled'),'false')
 def test_accounts_storage_and_providers_derive_only_from_variant_identity(self):
  ids=[v['applicationId'] for v in self.policy.values()];self.assertEqual(len(set(ids)),2)
  for f in ['auth.xml','sync_contacts.xml']:
   self.assertEqual(ET.parse(ROOT/'TMessagesProj/src/main/res/xml'/f).getroot().get(A+'accountType'),'@string/flexygram_account_type')
  gradle=(ROOT/'TMessagesProj/build.gradle').read_text()
  self.assertIn("flavor.resValue 'string', 'flexygram_account_type', policy.applicationId",gradle)
  self.assertIn("flavor.resValue 'string', 'flexygram_storage_namespace', policy.applicationId",gradle)
  root=ET.parse(ROOT/'TMessagesProj/src/diagnostic/AndroidManifest.xml').getroot()
  self.assertNotIn(A+'sharedUserId',root.attrib)
  for provider in root.find('application').findall('provider'):
   if provider.get(A+'authorities'):self.assertTrue(provider.get(A+'authorities').startswith('${applicationId}.'))
 def test_productive_modules_and_signing_do_not_inherit_diagnostic(self):
  s=(ROOT/'TMessagesProj/build.gradle').read_text()
  self.assertIn("diagnosticImplementation project(':translation-compat-diagnostic')",s)
  self.assertNotIn("    implementation project(':translation-compat-diagnostic')",s)
  self.assertNotIn('productionImplementation',s)
  self.assertNotIn('signingConfigs.debug',s)
  self.assertNotIn('release.keystore',s)
  self.assertEqual(s.count('signingConfig = signingConfigs.diagnosticLab'),1)
  self.assertIn("builder.enable = flavor == 'diagnostic' && builder.buildType in ['debug', 'staging']",s)
  self.assertNotIn('LOCAL_PROPERTIES',s)
  self.assertNotIn(".call(properties ?: new Properties(), System.getenv())",s)
 def test_real_java_capabilities_are_all_disabled_and_storage_is_per_id(self):
  real=ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/BuildVariantPolicy.java'
  for name,row in self.policy.items():
   out=self.dir/name;out.mkdir();p=out/'BuildConfig.java'
   fields=''.join('public static final boolean FLEXYGRAM_CAP_'+key.upper()+'=false;' for key in row['capabilities'])
   p.write_text('package org.telegram.messenger;public final class BuildConfig{public static final String APPLICATION_ID="'+row['applicationId']+'";'+fields+'}')
   h=out/'Check.java';h.write_text('import org.telegram.messenger.BuildVariantPolicy;public class Check{public static void main(String[] a){if(BuildVariantPolicy.authenticationAllowed()||BuildVariantPolicy.telegramTransportAllowed()||BuildVariantPolicy.pushAllowed()||BuildVariantPolicy.translationAllowed()||BuildVariantPolicy.pluginsAllowed()||BuildVariantPolicy.sessionRestoreAllowed()||!BuildVariantPolicy.storageNamespace().equals(a[0]))throw new AssertionError();}}')
   run(['javac','-d',out,p,real,h]);run(['java','-cp',out,'Check',row['applicationId']])
 def test_native_missing_unknown_and_production_flavors_rejected(self):
  for name in ['production','unknown','']:
   with self.assertRaises(RuntimeError):configure(self.dir/(name or 'empty'),name)
  with self.assertRaises(RuntimeError):configure(self.dir/'scope','diagnostic','invalid:diagnostic')
 def test_native_generated_policy_compiles_real_attestation_and_guard(self):
  generated=configure(self.dir/'policy')
  scope=hashlib.sha256((ROOT/'gradle/variant-policy.json').read_bytes()).hexdigest()+':diagnostic'
  header=ROOT/'TMessagesProj/jni/tgnet/DiagnosticPolicy.h'
  p=self.dir/'check.cpp';p.write_text('#include "'+str(header)+'"\n#include <cstring>\nextern "C" const char*flexygram_variant_policy();int main(){static_assert(flexygram::isolatedDiagnostic);static_assert(!flexygram::authenticationAllowed&&!flexygram::telegramTransportAllowed&&!flexygram::pushAllowed&&!flexygram::translationAllowed&&!flexygram::pluginsAllowed&&!flexygram::sessionRestoreAllowed);return std::strstr(flexygram_variant_policy(),"'+scope+'")?0:1;}')
  run(['c++','-std=c++17','-I'+str(generated),p,ROOT/'TMessagesProj/jni/tgnet/VariantPolicy.cpp','-o',self.dir/'check']);run([self.dir/'check'])
  shared=self.dir/'policy.so'
  run(['c++','-std=c++17','-shared','-fPIC','-I'+str(generated),ROOT/'TMessagesProj/jni/tgnet/VariantPolicy.cpp','-Wl,--version-script='+str(ROOT/'TMessagesProj/jni/exports.map'),'-o',shared])
  self.assertIn('flexygram_variant_policy',run(['nm','-D','--defined-only',shared]))
  # Missing generated configuration cannot silently default to Diagnostic or production.
  result=subprocess.run(['c++','-std=c++17','-c',p,'-o',self.dir/'missing.o'],capture_output=True)
  self.assertNotEqual(result.returncode,0)
 def test_original_data_and_security_sources_remain_byte_identical(self):
  for path in ['org/telegram/messenger/DiagnosticPolicy.java','org/telegram/messenger/BackupAgent.java','org/telegram/messenger/SettingsBackupPolicy.java','org/telegram/messenger/AuthTokensHelper.java','org/telegram/messenger/PushServicesPolicy.java','org/telegram/messenger/SharedConfig.java','org/telegram/messenger/ApplicationLoader.java','org/telegram/messenger/FileLoader.java','org/telegram/messenger/UserConfig.java','tw/nekomimi/nekogram/translate/TranslationServicesPolicy.java']:
   full='TMessagesProj/src/main/java/'+path
   self.assertEqual((ROOT/full).read_bytes(),subprocess.check_output(['git','show',BASE+':'+full],cwd=ROOT),path)
if __name__=='__main__':unittest.main()
