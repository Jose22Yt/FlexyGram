"""Current integrated behavior and original Work2 bytes; no security gates are skipped."""
import json,os,re,subprocess,tempfile,unittest
from pathlib import Path
from integration_contract import WORK1,LOGIN,MUSIC,restore_delivery,combined_paths
from music_contract import PRODUCTION
from build_private_apk import CERT,ROOT,load_private_inputs,redact
class IntegratedRelease(unittest.TestCase):
 def test_music_design_and_engine_sources_match_exact_approved_work2(self):
  for path in PRODUCTION:self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show',MUSIC+':'+path],cwd=ROOT),path)
  for name in ['MediaController','MusicPlayerService','NotificationsController','UserConfig']:
   path='TMessagesProj/src/main/java/org/telegram/messenger/'+name+'.java';self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show',WORK1+':'+path],cwd=ROOT),path)
 def test_login_production_matches_approved_candidate_except_direct_delivery_copy(self):
  from login_contract import PATHS
  for path in PATHS:
   if path.endswith('.java') and '/src/' in path:self.assertEqual(restore_delivery(path,(ROOT/path).read_bytes()),subprocess.check_output(['git','show',LOGIN+':'+path],cwd=ROOT),path)
 def test_approved_composer_home_icons_and_session_identity_are_preserved(self):
  for prefix in ['TMessagesProj/src/main/java/app/flexygram/composer','TMessagesProj/src/main/java/app/flexygram/home','TMessagesProj/src/main/java/app/exteraless/appicons','TMessagesProj/src/main/AndroidManifest.xml','gradle.properties']:
   self.assertEqual(subprocess.check_output(['git','diff',WORK1,'--',prefix],cwd=ROOT),b'',prefix)
 def test_private_direct_delivery_and_full_build_are_mandatory(self):
  workflow=(ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text()
  self.assertNotIn('age --encrypt',workflow);self.assertNotIn('.tar.age',workflow)
  builder=(ROOT/'tools/connected_alpha/build_private_apk.py').read_text()
  for required in [':TMessagesProj:assembleConnectedAlpha','verify_apk.py','--certificate-sha256',"report['elf_count']!=96",'FlexyGram_Alpha_1271_ARM64_TEST.apk','stage(env)']:self.assertIn(required,builder)
  for forbidden in ['NATIVE_TARGET=SKIP','--exclude-task','upload-artifact','age --','shutil.copy2(apks[0], ROOT']:self.assertNotIn(forbidden,builder)
  for lang in ['values','values-es','values-ru']:
   copy=(ROOT/f'TMessagesProj/src/main/res/{lang}/flexygram_login.xml').read_text();self.assertIn('APK',copy);self.assertNotIn('entrega cifrada original',copy)
 def test_private_input_permissions_and_short_secrets_are_protected(self):
  self.assertNotIn('abc',redact('failure abc and long_secret',['abc','long_secret','']))
  self.assertNotIn('long_secret',redact('failure abc and long_secret',['abc','long_secret','']))
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'inputs.json';p.write_text(json.dumps({'ALPHA_CERTIFICATE_SHA256':CERT}));p.chmod(0o644)
   with self.assertRaises(ValueError):load_private_inputs(p)
   p.chmod(0o600);self.assertEqual(load_private_inputs(p)['ALPHA_CERTIFICATE_SHA256'],CERT)
   p.write_text(json.dumps({'ALPHA_CERTIFICATE_SHA256':'0'*64}))
   with self.assertRaises(ValueError):load_private_inputs(p)

 def test_integrated_variant_strings_have_one_authoritative_brand_key(self):
  import xml.etree.ElementTree as ET
  values={}
  for path in (ROOT/'TMessagesProj/src/connectedAlpha/res/values').glob('*.xml'):
   for node in ET.parse(path).getroot():
    if node.tag!='string':continue
    name=node.get('name');self.assertNotIn(name,values,str(path)+': duplicate string '+str(name));values[name]=node.text
  self.assertEqual(values['NagramX'],'FlexyGram Alpha')
  self.assertEqual(values['AppName'],'FlexyGram Alpha')
  self.assertEqual(values['AppNameBeta'],'FlexyGram Alpha')
  path='TMessagesProj/src/connectedAlpha/res/values/alpha_name.xml'
  self.assertEqual(restore_delivery(path,(ROOT/path).read_bytes()),subprocess.check_output(['git','show',WORK1+':'+path],cwd=ROOT))
  for locale in ['values','values-es','values-ru']:
   labels={x.get('name'):x.text for x in ET.parse(ROOT/f'TMessagesProj/src/main/res/{locale}/flexygram_login.xml').getroot() if x.tag=='string'}
   self.assertEqual(labels['FlexySignatureName'],'FlexyGram')
