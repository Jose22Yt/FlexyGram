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
  self.assertLess(block.index('result = checkAdminTouchEvent(event)'),block.index('signatureTapEligible=!result'))
  for token in ['ACTION_DOWN','ACTION_UP','ACTION_CANCEL','ACTION_POINTER_DOWN','getScaledTouchSlop','cancelSignatureTap()','applySignatureTap(canvas)','try{drawSignatureContent(canvas);}finally','if(fromParent)applySignatureTap(canvas)']:
   self.assertIn(token,source)
  controller=self.text('app/flexygram/bubbles/interaction/BubbleTapMotion.java');self.assertIn('postOnAnimation(this)',controller);self.assertIn('SystemClock.uptimeMillis()',controller);self.assertNotIn('ValueAnimator',controller)
 def test_one_tap_panel_is_independent_and_only_calls_one_native_menu(self):
  s=self.text('org/telegram/ui/ChatActivity.java');start=s.index('if(view instanceof ChatMessageCell && ((ChatMessageCell)view).isSignatureTap())');end=s.index('public boolean hasDoubleTap',start);block=s[start:end]
  self.assertIn('tapPanel(view.getContext())',block);self.assertEqual(1,block.count('createMenu(view,false,false,x,y,true)'));self.assertIn('return; // animation-only',block)
  self.assertIn('tapAnimation(getContext())',self.text('org/telegram/ui/Cells/ChatMessageCell.java'))
 def test_no_six_destination_cap_and_scrolling_is_explicit(self):
  d=self.text('app/flexygram/navigation/LiquidNavigationDestinations.java');self.assertNotIn('MAX_VISIBLE',d);self.assertNotIn('result.size()<',d)
  s=self.text('app/flexygram/navigation/LiquidNavigationConfig.java');self.assertIn('distribution()==1?LiquidNavigationDestinations.fit(order(),slots):order()',s)
  bar=self.text('org/telegram/ui/MainTabsLayout.java')
  for token in ['viewportOffset','flexyScrollGesture','edgeScroller','ensureSelectedVisible','uniformSlotWidth','expandedWidth/1.55f']:
   self.assertIn(token,bar)
 def test_preview_never_reads_account_identity_or_rebuilds_fragments(self):
  s=self.text('app/flexygram/navigation/LiquidNavigationPreviewView.java');self.assertIn('new MainTabsLayout(',s);self.assertIn('drawScene(canvas)',s)
  for forbidden in ['UserConfig','MessagesController','getUser(','getDialog(','getMessage(']:self.assertNotIn(forbidden,s)
  tabs=self.text('app/flexygram/navigation/LiquidNavigationTabs.java');start=tabs.index('public static GlassTabView createPreview');end=tabs.index('public static GlassTabView create(Context',start);self.assertNotIn('createAvatar',tabs[start:end]);self.assertIn('NAV_PROFILE',tabs[start:end])
 def test_native_send_restrictions_and_submission_are_byte_identical(self):
  path='org/telegram/ui/Components/ShareAlert.java';now=self.text(path);old=audit.original('TMessagesProj/src/main/java/'+path).decode()
  for start,end in [('    protected void sendInternal(', '    private int getCurrentTop('),('    private void selectDialog(', '    private boolean isBotForumWithNotEmptyTopics(')]:
   self.assertEqual(old[old.index(start):old.index(end)],now[now.index(start):now.index(end)])
  for token in ['currentAccount=fragment.getCurrentAccount()','currentAccount=messages.get(0).currentAccount','useClassicShareLayout','flexyShareHeader.preview(summary)']:self.assertIn(token,now)
 def test_fusion_is_optional_and_does_not_restore_glass_or_matte(self):
  config=self.text('app/flexygram/bubbles/BubbleConfig.java');self.assertIn('signature_fusion_mode",fuseGlass?1:0',config);self.assertIn('matteEnabled() { return false; }',config);self.assertIn('getBoolean("signature_cached_blur", false)',config)
  renderer=self.text('app/flexygram/bubbles/BubbleFusion.java');self.assertNotRegex(renderer,r'new\s+(?:Paint|Path|Bitmap|\w*Shader)\s*\(');self.assertNotIn('Shader(',renderer)
  draw=self.text('org/telegram/ui/ActionBar/MessageDrawable.java');self.assertIn('fusionMode()==2',draw);self.assertIn('else if (app.flexygram.bubbles.BubbleConfig.fuseGlass()',draw)
 def test_header_composer_and_native_telegram_sending_services_are_unchanged(self):
  for path in ['org/telegram/ui/ActionBar/ActionBar.java','org/telegram/ui/Components/ChatActivityEnterView.java','app/flexygram/header/SignatureChatHeader.java','app/flexygram/composer/ComposerStyle.java','org/telegram/messenger/SendMessagesHelper.java','org/telegram/messenger/MediaDataController.java']:
   self.assertEqual(audit.original('TMessagesProj/src/main/java/'+path),(JAVA/path).read_bytes(),path)
if __name__=='__main__':unittest.main()
