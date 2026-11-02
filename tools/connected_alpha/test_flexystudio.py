"""Actual codec/transaction JVM execution plus exact integration and security contracts."""
import subprocess,tempfile,unittest,sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
from studio_contract import BASE,HOOKS,restore
class StudioTests(unittest.TestCase):
 def test_actual_codec_transactions_hostile_corpus(self):
  with tempfile.TemporaryDirectory()as output:
   source=ROOT/'TMessagesProj/src/main/java/app/flexygram/studio/core'
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',output,*map(str,source.glob('*.java')),str(ROOT/'tools/connected_alpha/studio_native/StudioCoreTest.java')],check=True)
   result=subprocess.check_output(['java','-cp',output,'StudioCoreTest'],text=True)
   self.assertIn('hostile_mutations=5000',result);print(result.strip())
 def test_existing_hooks_reverse_exactly_and_reject_mutation(self):
  for path in HOOKS:
   data=(ROOT/path).read_bytes();before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
   self.assertEqual(restore(path,data),before,path)
   with self.assertRaises(ValueError):restore(path,data+b'\n// unexpected change\n')
 def test_resources_translations_identical(self):
  values=[]
  for lang in ['values','values-es','values-ru']:
   tree=ET.parse(ROOT/'TMessagesProj/src/main/res'/lang/'flexystudio.xml')
   values.append({n.attrib['name']for n in tree.getroot()});self.assertTrue(all(n.text for n in tree.getroot()))
  self.assertEqual(values[0],values[1]);self.assertEqual(values[0],values[2])
 def test_no_executable_or_arbitrary_preferences_import(self):
  root=ROOT/'TMessagesProj/src/main/java/app/flexygram/studio'
  data='\n'.join(p.read_text()for p in root.rglob('*.java'))
  for token in ['ObjectInputStream','DexClassLoader','Runtime.getRuntime','Python.getInstance','getAll()','file://','READ_EXTERNAL_STORAGE','MANAGE_EXTERNAL_STORAGE']:
   self.assertNotIn(token,data)
  self.assertIn('StudioSchema.key(',data);self.assertIn('StudioSchema.MAX_BYTES',data)
 def test_provider_scope_and_no_new_permissions(self):
  A='{http://schemas.android.com/apk/res/android}'
  current=ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').getroot()
  baseline=ET.fromstring(subprocess.check_output(['git','show',BASE+':TMessagesProj/src/main/AndroidManifest.xml'],cwd=ROOT))
  self.assertEqual([x.attrib for x in current.findall('uses-permission')],[x.attrib for x in baseline.findall('uses-permission')])
  provider=next(x for x in current.find('application').findall('provider')if x.get(A+'name','').endswith('FlexyStudioProvider'))
  self.assertEqual(provider.get(A+'exported'),'false');self.assertEqual(provider.get(A+'grantUriPermissions'),'true')
  paths=ET.parse(ROOT/'TMessagesProj/src/main/res/xml/flexystudio_paths.xml').getroot()
  self.assertEqual(len(paths),1);self.assertEqual(paths[0].tag,'cache-path');self.assertEqual(paths[0].get('path'),'flexystudio/share/')
if __name__=='__main__':unittest.main()
