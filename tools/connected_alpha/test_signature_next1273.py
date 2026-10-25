"""Strict reviewed visual delta after the separately compiled P0 checkpoint."""
import subprocess,unittest
from next_alpha_contract import ROOT,VISUAL_BASE,VISUAL_PATHS,restore_visual
class NextSignature(unittest.TestCase):
 def test_visual_delta_restores_exact_checkpoint_and_rejects_unreviewed_edits(self):
  for path in VISUAL_PATHS:
   data=(ROOT/path).read_bytes()
   self.assertEqual(restore_visual(path,data),subprocess.check_output(['git','show',VISUAL_BASE+':'+path],cwd=ROOT),path)
   if path.endswith('.java'):
    with self.assertRaises(ValueError,msg=path):restore_visual(path,data.replace(b'public ',b'private ',1))
 def test_message_measurement_grouping_and_engine_are_preserved(self):
  for path in ['TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java','TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java','TMessagesProj/src/main/java/org/telegram/messenger/MediaController.java']:
   self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show',VISUAL_BASE+':'+path],cwd=ROOT),path)
