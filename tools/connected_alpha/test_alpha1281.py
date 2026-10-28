"""Review boundary and unaffected critical systems; Android rendering is tested separately."""
from pathlib import Path
import unittest
import alpha1281_contract as audit
ROOT=Path(__file__).resolve().parents[2]
class Alpha1281(unittest.TestCase):
 def test_review_and_unknown_edits_fail_closed(self):
  audit.verify_current()
  for path in audit.spec()['reviewed']:
   value=(ROOT/path).read_bytes()+b'\nUNREVIEWED'
   self.assertEqual(value,audit.restore(path,value),path)
 def test_package_signing_build_gates_only_change_version(self):
  for path in ('TMessagesProj/build.gradle','.github/workflows/connected-alpha-arm64.yml','tools/connected_alpha/build_private_apk.py'):
   before=audit.original(path);now=(ROOT/path).read_bytes();self.assertIn(b'1281',now);self.assertEqual(before,now.replace(b'1281',b'1280'),path)
 def test_unrelated_critical_components_are_unchanged(self):
  for path in ('TMessagesProj/src/main/java/app/flexygram/bubbles/SignatureWallpaperBlur.java','TMessagesProj/src/main/java/app/flexygram/motion/FlexyFrameMotion.java','TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java','TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java','TMessagesProj/src/main/java/org/telegram/messenger/MessagesStorage.java','TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java','TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java','tools/connected_alpha/alpha1280_review.json'):
   self.assertEqual(audit.original(path),(ROOT/path).read_bytes(),path)
 def test_original_hotfix_and_visibility_guards_remain(self):
  s=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java').read_text()
  self.assertIn('allowsSingleMessagePreview(groupMessages)',s);self.assertNotIn('&& groupMessages == null',s)
  self.assertIn('SignaturePreviewContext.isMessageRow',s);self.assertIn('restriction_reason.isEmpty()',s)
  self.assertIn('draftMessage == null && !draftVoice',s);self.assertIn('TextUtils.isEmpty(printingString)',s)
  self.assertIn('!clearingDialog && drawTime && currentDialogCommunityId == 0 && !promoDialog',s)
  self.assertIn('SignatureTopicAccent.overlay(topicSurfaceColor',s)
if __name__=='__main__':unittest.main()
