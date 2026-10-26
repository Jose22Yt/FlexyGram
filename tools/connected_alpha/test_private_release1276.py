"""Current candidate guards independent of the exact historical release audits."""
import re,subprocess,unittest,yaml
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE='175b299e0d4faeb246eca8e1be16a362a3a62213'
class PrivateRelease1276(unittest.TestCase):
 def test_only_version_changes_in_gradle_and_verifier_keeps_every_original_gate(self):
  path='TMessagesProj/build.gradle';current=(ROOT/path).read_text();before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
  self.assertEqual(re.search(r'def verCode = (\d+)',current)[1],'1276')
  self.assertEqual(current.replace('def verCode = 1276','def verCode = 1275'),before)
  path='.github/workflows/connected-alpha-arm64.yml';current=(ROOT/path).read_text();before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
  self.assertEqual(current.replace('--expected-version-code 1276','--expected-version-code 1275'),before)
  jobs=yaml.safe_load(current)['jobs'];steps=jobs['build-arm64']['steps']
  self.assertFalse(any('upload-artifact' in s.get('uses','')for s in steps))
  verifier=next(s['run']for s in steps if s.get('name')=='Verify APK against independently authorized certificate')
  self.assertIn('--expected-version-code 1276',verifier);self.assertIn("data['elf_count'] != 96",verifier)
  self.assertIn('c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c',verifier)
  manifest=(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').read_bytes()
  self.assertEqual(manifest,subprocess.check_output(['git','show',BASE+':TMessagesProj/src/main/AndroidManifest.xml'],cwd=ROOT))
 def test_core_files_engine_and_studio_codec_remain_exact(self):
  for suffix in ('app/flexygram/studio/core/StudioCodec.java','app/flexygram/studio/core/StudioTransaction.java','app/flexygram/files/core/SelectedDocument.java','app/flexygram/files/FilesWork.java','org/telegram/ui/ActionBar/ActionBarLayout.java','org/telegram/messenger/SendMessagesHelper.java'):
   path='TMessagesProj/src/main/java/'+suffix
   with self.subTest(path=path):self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT))
