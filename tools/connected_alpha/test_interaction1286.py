"""Current code integration gates, complementary to Android graphics and physical acceptance."""
from pathlib import Path
import subprocess,unittest
import interaction1286_contract as audit
ROOT=audit.ROOT;JAVA=ROOT/'TMessagesProj/src/main/java'
class Interaction1286(unittest.TestCase):
 def text(self,path):return (JAVA/path).read_text()
 def test_exact_changes_and_unknown_byte_rejection(self):
  audit.verify_current()
  for path in audit.spec()['reviewed']:
   current=(ROOT/path).read_bytes() if (ROOT/path).is_file() else b''
   mutated=current+b'\nUNREVIEWED\n';self.assertEqual(mutated,audit.restore(path,mutated),path)
 def test_tap_is_after_every_native_hit_test_and_draws_cell_and_parent_background(self):
  source=self.text('org/telegram/ui/Cells/ChatMessageCell.java')
  start=source.index('public boolean onTouchEvent(MotionEvent event)');end=source.index('private boolean checkReactionsTouchEvent',start);block=source[start:end]
  self.assertLess(block.index('result = checkAdminTouchEvent(event)'),block.index('signatureTapEligible=compatible && !result'))
  for token in ['ACTION_DOWN','ACTION_UP','ACTION_CANCEL','ACTION_POINTER_DOWN','getScaledTouchSlop','cancelSignatureTap()','applySignatureTap(canvas)','try{drawSignatureContent(canvas);}finally','if(fromParent)applySignatureTap(canvas)']:
   self.assertIn(token,source)
  controller=self.text('app/flexygram/bubbles/interaction/BubbleTapMotion.java');self.assertIn('postOnAnimation(this)',controller);self.assertIn('SystemClock.uptimeMillis()',controller);self.assertNotIn('ValueAnimator',controller)
 def test_one_tap_panel_is_independent_and_only_calls_one_native_menu(self):
  s=self.text('org/telegram/ui/ChatActivity.java');start=s.index('if(view instanceof ChatMessageCell && ((ChatMessageCell)view).isSignatureTap())');end=s.index('public boolean hasDoubleTap',start);block=s[start:end]
  self.assertIn('tapPanel(view.getContext())',block);self.assertEqual(1,block.count('createMenu(view,true,false,x,y,true,false,false,false,true)'));self.assertIn('return;',block)
  self.assertIn('(bubbleTap || longpress || single) && !onDoubleTapped',s)
 def test_six_destination_cap_and_solid_symmetric_layout(self):
  d=self.text('app/flexygram/navigation/LiquidNavigationDestinations.java');self.assertIn('MAX_VISIBLE=6',d)
  bar=self.text('org/telegram/ui/MainTabsLayout.java');self.assertIn('slotWidth=inner/Math.max(1,count)',bar)
  for removed in ['LiquidLensRenderer','clipPath','flexyExpansion','RenderEffect']:self.assertNotIn(removed,bar)
 def test_home_customization_screens_are_removed_without_touching_chat_composer(self):
  for name in ['LiquidNavigationPreviewView','LiquidNavigationSettingsActivity','LiquidNavigationTabsActivity']:
   self.assertFalse((JAVA/'app/flexygram/navigation'/str(name+'.java')).exists())
  config=self.text('app/flexygram/navigation/LiquidNavigationConfig.java')
  self.assertNotIn('p.getInt(',config);self.assertNotIn('p.getString(',config)
  self.assertIn('return LiquidNavigationDestinations.defaults()',config)
 def test_native_share_and_submission_are_restored_exactly(self):
  path='org/telegram/ui/Components/ShareAlert.java';self.assertEqual(audit.original('TMessagesProj/src/main/java/'+path).decode(),self.text(path).replace('        // Native sharing must bind the source account before constructing adapters/requests.\n        if(fragment!=null)currentAccount=fragment.getCurrentAccount();\n        else if(messages!=null&&!messages.isEmpty())currentAccount=messages.get(0).currentAccount;\n',''))
  self.assertNotIn('app.flexygram.share',self.text('org/telegram/ui/ChatActivity.java'))
 def test_fusion_is_optional_and_does_not_restore_glass_or_matte(self):
  config=self.text('app/flexygram/bubbles/BubbleConfig.java');self.assertIn('signature_fusion_mode",fuseGlass?1:0',config);self.assertIn('matteEnabled() { return false; }',config);self.assertIn('getBoolean("signature_cached_blur", false)',config)
  renderer=self.text('app/flexygram/bubbles/BubbleFusion.java');self.assertNotRegex(renderer,r'new\s+(?:Paint|Path|Bitmap|\w*Shader)\s*\(');self.assertNotIn('Shader(',renderer)
  draw=self.text('org/telegram/ui/ActionBar/MessageDrawable.java');self.assertIn('fusionMode()==2',draw);self.assertIn('else if (app.flexygram.bubbles.BubbleConfig.fuseGlass()',draw)
 def test_header_composer_and_native_telegram_sending_services_are_unchanged(self):
  for path in ['org/telegram/ui/ActionBar/ActionBar.java','org/telegram/ui/Components/ChatActivityEnterView.java','app/flexygram/header/SignatureChatHeader.java','app/flexygram/composer/ComposerStyle.java','org/telegram/messenger/SendMessagesHelper.java','org/telegram/messenger/MediaDataController.java']:
   self.assertEqual(audit.original('TMessagesProj/src/main/java/'+path),(JAVA/path).read_bytes(),path)
if __name__=='__main__':unittest.main()
