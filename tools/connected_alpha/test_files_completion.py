"""Continuation boundaries, explicit capability scope and actual bounded history engine."""
import hashlib,json,subprocess,tempfile,unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from files_completion_contract import ROOT,BASE,restore,paths

class FilesCompletion(unittest.TestCase):
 def test_exact_source_deltas_reject_unreviewed_changes(self):
  spec=json.loads((ROOT/'tools/connected_alpha/files_completion.json').read_text())
  for path in spec['existing']:
   with self.subTest(path=path):
    data=(ROOT/path).read_bytes();before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
    self.assertEqual(restore(path,data),before)
    with self.assertRaises(ValueError):restore(path,data+b'\nUNREVIEWED\n')
 def test_manifest_identity_sessions_and_original_studio_codec_are_unchanged(self):
  for path in ['TMessagesProj/src/main/AndroidManifest.xml','TMessagesProj/build.gradle','TMessagesProj/src/main/java/app/flexygram/studio/core/StudioCodec.java','TMessagesProj/src/main/java/app/flexygram/studio/core/StudioSchema.java','TMessagesProj/src/main/java/app/flexygram/studio/FlexyStyleInstallHelper.java','TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java','TMessagesProj/src/main/java/org/telegram/messenger/SendMessagesHelper.java','TMessagesProj/src/main/java/org/telegram/messenger/MediaController.java']:
   from startup_contract import restore as restore_current
   self.assertEqual(restore_current(path,(ROOT/path).read_bytes()),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),path)
 def test_translations_cover_same_actual_labels(self):
  values=[]
  for lang in ['values','values-es','values-ru']:
   resource=ET.parse(ROOT/'TMessagesProj/src/main/res'/lang/'flexyfiles.xml').getroot();values.append({x.attrib['name']for x in resource});self.assertTrue(all(x.text for x in resource))
  self.assertEqual(values[0],values[1]);self.assertEqual(values[0],values[2]);self.assertGreater(len(values[0]),20)
 def test_worker_has_no_idle_engine_and_opt_in_cannot_be_imported(self):
  entry=(ROOT/'TMessagesProj/src/main/java/app/flexygram/files/FlexyFiles.java').read_text();eligibility=entry.split('public static boolean eligible',1)[1].split('public static void open',1)[0]
  for token in ['new File','loadFile','Executor','Timer','schedule','getPathToMessage']:self.assertNotIn(token,eligibility)
  worker=(ROOT/'TMessagesProj/src/main/java/app/flexygram/files/FilesWork.java').read_text();self.assertIn('ThreadPoolExecutor(0,1',worker);self.assertIn('shutdownNow()',worker);self.assertNotIn('static final ThreadPoolExecutor',worker)
  schema=(ROOT/'TMessagesProj/src/main/java/app/flexygram/studio/core/StudioSchema.java').read_text();self.assertNotIn('flexyfiles_local',schema)
 def test_actual_history_delta_engine_stays_bounded(self):
  code='''import app.flexygram.files.core.EditHistory;class HistoryProbe {public static void main(String[]x){EditHistory h=new EditHistory();String value="initial";for(int i=0;i<10000;i++){String next="v"+i;h.record(0,value,next);value=next;if(h.retainedChars()>512*1024)throw new AssertionError();}int n=0;EditHistory.Change c;while((c=h.undo())!=null){if(!value.equals(c.after))throw new AssertionError();value=c.before;n++;}if(n!=64)throw new AssertionError();while((c=h.redo())!=null){if(!value.equals(c.before))throw new AssertionError();value=c.after;}if(!value.equals("v9999"))throw new AssertionError();h.record(0,"x".repeat(600000),"");if(h.retainedChars()>512*1024)throw new AssertionError();System.out.println("PASS actual bounded delta history");}}'''
  with tempfile.TemporaryDirectory()as tmp:
   f=Path(tmp)/'HistoryProbe.java';f.write_text(code)
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(ROOT/'TMessagesProj/src/main/java/app/flexygram/files/core/EditHistory.java'),str(f)],check=True,capture_output=True)
   self.assertIn('PASS',subprocess.check_output(['java','-cp',tmp,'HistoryProbe'],text=True))
