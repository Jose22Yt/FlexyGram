"""Native host wiring checks; Android presenter and full-app checks remain separate."""
from pathlib import Path
import unittest
from integration1284_contract import historical_bytes
ROOT=Path(__file__).resolve().parents[2]
class ContextPanelWiring(unittest.TestCase):
 def test_native_permissions_actions_and_overflow_are_retained(self):
  s=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java').read_text()
  start=s.index('            if (compactContext) {');end=s.index('            ChatScrimPopupContainerLayout ',start);host=s[start:end]
  self.assertIn('panelCell.getMessageObject()!=panelMessage',host)
  self.assertIn('fillMessageMenu(panelCell.getPrimaryMessageObject()',host)
  self.assertIn('signatureContextActions(freshOptions).contains(action)',host)
  for action in ['REPLY','COPY','FORWARD','EDIT','PIN','DELETE']:self.assertIn('processSelectedOption(OPTION_'+action+')',host)
  self.assertIn('popupLayout.getSwipeBack().openForeground(nativeMenuIndex)',host)
  self.assertIn('nativeMenu.addView(nativeItem)',host)
  self.assertIn('createMenu(panelCell,false,false',host)
  self.assertNotIn('performClick(',host);self.assertNotIn('MotionEvent.obtain',host)
 def test_unverified_stickers_and_cancelled_motion_are_not_exposed(self):
  p=ROOT/'TMessagesProj/src/main/java/app/flexygram/bubbles/interaction'
  s=historical_bytes(str((p/'BubbleActionPanelView.java').relative_to(ROOT))).decode();settings=(p/'BubbleInteractionSettings.java').read_text()
  self.assertIn('if(stickerEnabled) headerTab',s);self.assertNotIn('stickerEnabled = true',s)
  self.assertIn('getBoolean("signature_panel",false)',settings)
  for file in p.glob('*.java'):self.assertNotIn('app.flexygram.motion',file.read_text())
  # Historical Alpha1285 omitted tap animation; current cell-owned replacement is tested separately.
  self.assertEqual(b'',__import__('interaction1286_contract').original('TMessagesProj/src/main/java/app/flexygram/bubbles/interaction/BubbleTapMotion.java'))
if __name__=='__main__':unittest.main()
