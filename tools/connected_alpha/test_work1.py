"""Scope/permission/identity regressions for the three owner-approved corrections."""
from pathlib import Path
import hashlib,subprocess,unittest
import work1_contract as audit
ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'
class Work1(unittest.TestCase):
 def test_exact_reviewed_overlay_rejects_unknown_bytes(self):
  audit.verify_current()
  for name in audit.spec()['reviewed']:
   p=ROOT/name;data=p.read_bytes() if p.is_file() else b''
   self.assertEqual(data+b'UNKNOWN',audit.restore(name,data+b'UNKNOWN'),name)
 def test_work2_identity_startup_network_scroll_and_idle_motion_are_intact(self):
  names=['app/flexygram/performance/StartupAccounts.java','app/flexygram/performance/NetworkSnapshotAge.java','app/flexygram/performance/CoalescedTask.java','app/flexygram/performance/ScrollFrameRateHint.java','app/flexygram/performance/RefreshRateMonitor.java','app/flexygram/bubbles/SignatureBorderPath.java','org/telegram/messenger/ApplicationLoader.java','org/telegram/tgnet/ConnectionsManager.java','org/telegram/ui/Cells/DialogCell.java','org/telegram/ui/Components/RecyclerListView.java','org/telegram/ui/LaunchActivity.java']
  for name in names:
   path='TMessagesProj/src/main/java/'+name
   data=(JAVA/name).read_bytes()
   if name=='app/flexygram/bubbles/SignatureBorderPath.java':
    # Only the exact new invalidation API is projected for this historical byte freeze.
    # Candidate behavior/pixels/geometry lifetime are exercised by ScrollEffectsCacheTest.
    from deep_performance_contract import restore as before_deep
    data=before_deep(path,data)
   self.assertEqual(audit.original(path),data,name)
  for name in ['config/signing/identity.properties','config/signing/flexygram-release.cer','gradle.properties','TMessagesProj/src/main/AndroidManifest.xml']:
   self.assertEqual(audit.original(name),(ROOT/name).read_bytes(),name)
  signing='gradle/flexygram-beta.gradle'
  self.assertEqual(audit.original(signing).decode().split('tasks.configureEach')[0],(ROOT/signing).read_text().split('// AGP deduplicates')[0])
  self.assertEqual('5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c',hashlib.sha256((ROOT/'config/signing/flexygram-release.cer').read_bytes()).hexdigest())
 def test_single_tap_requests_both_real_reactions_and_native_actions(self):
  s=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
  self.assertIn('createMenu(view,true,false,x,y,true,false,false,false,true)',s)
  self.assertIn('NaConfig.INSTANCE.getShowReactions().Bool() || onDoubleTapped || bubbleTap',s)
  self.assertIn('finalReactionsLayout.startEnterAnimation(true)',s)
  for token in ['fillMessageMenu(primaryMessage, icons, items, options)','panel.setAllowedActions(admitted)','fillMessageMenu(panelCell.getPrimaryMessageObject(),freshIcons,freshItems,freshOptions)','scrimPopupWindow.showAtLocation','dimBehindView(v, true, true)','selectedBubbleMotion.enter','scrimPopupWindow != signatureMenuOwner']:
   self.assertIn(token,s)
  self.assertIn('if (bubbleTap && (scrimPopupWindow != null',s)
  self.assertIn('if(view instanceof ChatMessageCell && ((ChatMessageCell)view).isSignatureTap() && app.flexygram.bubbles.interaction.BubbleInteractionSettings.tapPanel(view.getContext()))return false;',s)
 def test_native_controls_stay_first_and_selection_is_not_a_tap(self):
  s=(JAVA/'org/telegram/ui/Cells/ChatMessageCell.java').read_text();start=s.index('signatureTapEligible=compatible && !result')
  self.assertGreater(start,s.index('checkReactionsTouchEvent(event)'))
  for token in ['!delegate.hasSelectedMessages()','!currentMessageObject.preview','currentMessagesGroup==null','getLongPressTimeout()','signatureTapReleased>0','ACTION_POINTER_DOWN','ACTION_CANCEL']:
   self.assertIn(token,s)
 def test_no_home_glass_or_custom_share_route_survives(self):
  for name in ['org/telegram/ui/MainTabsLayout.java']:
   s=(JAVA/name).read_text()
   for bad in ['LiquidLensRenderer','setLiquidLensBackground','setLiquidGlassEffectAllowed','clipPath','RenderNodeWithHash']:self.assertNotIn(bad,s)
  self.assertFalse((JAVA/'app/flexygram/navigation/LiquidLensRenderer.java').exists())
  self.assertFalse(any((JAVA/'app/flexygram/share').glob('*.java')))
  for name in ['org/telegram/ui/ChatActivity.java','org/telegram/ui/Components/ShareAlert.java','app/exteraless/settings/OpenExteraAppearanceActivity.java']:
   self.assertNotIn('app.flexygram.share',(JAVA/name).read_text())
  for name in ['org/telegram/messenger/SendMessagesHelper.java','org/telegram/messenger/MediaDataController.java','org/telegram/ui/ActionBar/ActionBar.java','org/telegram/ui/Components/ChatActivityEnterView.java','app/flexygram/bubbles/BubbleFusion.java']:
   self.assertEqual(audit.original('TMessagesProj/src/main/java/'+name),(JAVA/name).read_bytes(),name)
 def test_hidden_destinations_and_editor_limits_share_real_navigation(self):
  s=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
  self.assertIn('if (index == INDEX_CHATS)',s)
  self.assertIn('()->openFlexyDestination(destination)',s)
  self.assertIn('int slots = Math.max(2, inner / dp(48))',s)
  self.assertFalse((JAVA/'app/flexygram/navigation/LiquidNavigationTabsActivity.java').exists())
  self.assertIn('return LiquidNavigationDestinations.defaults()', (JAVA/'app/flexygram/navigation/LiquidNavigationConfig.java').read_text())
if __name__=='__main__':unittest.main()
