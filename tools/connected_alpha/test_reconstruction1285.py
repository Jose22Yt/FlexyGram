"""Current-source corrections, independent of audit-only historical projections."""
import hashlib,subprocess,unittest
from pathlib import Path
import reconstruction1285_contract as audit
J='TMessagesProj/src/main/java/'
class Reconstruction1285(unittest.TestCase):
 def text(self,path):return (audit.ROOT/path).read_text()
 def test_exact_scope_and_all_unknown_edits_are_rejected(self):
  audit.verify_current()
  for path in audit.spec()['reviewed']:
   raw=audit.read_current(path)+b'\nUNREVIEWED'
   self.assertEqual(raw,audit.restore(path,raw),path)
 def test_custom_conversion_is_removed_and_native_stickers_are_unchanged(self):
  folder=audit.ROOT/J/'app/flexygram/bubbles/interaction'
  for path in folder.glob('*.java'):
   self.assertNotIn('BUILD_STICKER',path.read_text());self.assertNotIn('sticker_conversion',path.read_text())
  self.assertFalse(any(folder.glob('*Sticker*.java')))
  self.assertNotIn('BubbleSticker',self.text(J+'org/telegram/ui/ChatActivity.java'))
  for path in ['org/telegram/messenger/SendMessagesHelper.java','org/telegram/messenger/MediaDataController.java','org/telegram/ui/Components/StickersAlert.java']:
   self.assertEqual(audit.original(J+path),(audit.ROOT/J/path).read_bytes(),path)
 def test_native_actions_permissions_and_popup_lifecycle_are_retained(self):
  source=self.text(J+'org/telegram/ui/ChatActivity.java')
  start=source.index('            if (compactContext) {');end=source.index('            ChatScrimPopupContainerLayout ',start)
  block=source[start:end]
  for action in ['REPLY','COPY','FORWARD','EDIT','PIN','DELETE']:
   self.assertIn('processSelectedOption(OPTION_'+action+')',block)
  self.assertIn('signatureContextActions(freshOptions).contains(action)',block)
  self.assertIn('nativeMenu.addView(nativeItem)',block)
  self.assertIn('dimBehindView(v, true, true)',source)
  self.assertIn('blurGeneration != scrimBlurGeneration',source)
  self.assertIn('bitmapBg.recycle()',source)
  self.assertIn('(selectedBubblePreviewScale-1f)*selectedBubbleMotion.progress()',source)
 def test_original_blur_has_no_glass_blend_or_scope_and_matte_stays_off(self):
  config=self.text(J+'app/flexygram/bubbles/BubbleConfig.java')
  self.assertIn('getBoolean("signature_cached_blur", false)',config)
  self.assertIn('matteEnabled() { return false; }',config)
  for token in ['glassIntensity','glassOutgoing','bubbleGlassEnabled']:self.assertNotIn(token,config)
  self.assertFalse((audit.ROOT/J/'app/flexygram/bubbles/BubbleGlassPolicy.java').exists())
  settings=self.text(J+'app/flexygram/bubbles/BubbleSettingsActivity.java')
  self.assertIn('FlexyBubbleBackgroundBlur',settings)
  self.assertNotIn('surfaceRow',settings)
  self.assertIn('Math.max(0, Math.min(255, alpha)) * reveal',self.text(J+'app/flexygram/bubbles/SignatureWallpaperBlur.java'))
 def test_only_bubble_glass_is_removed(self):
  for path in ['org/telegram/ui/ActionBar/ActionBar.java','org/telegram/ui/Components/ChatActivityEnterView.java','app/flexygram/header/SignatureChatHeader.java','app/flexygram/composer/ComposerStyle.java']:
   self.assertEqual(audit.original(J+path),(audit.ROOT/J/path).read_bytes(),path)
 def test_home_lens_is_removed_and_bar_avoids_per_frame_bitmaps(self):
  self.assertFalse((audit.ROOT/J/'app/flexygram/navigation/LiquidLensRenderer.java').exists())
  bar=self.text(J+'org/telegram/ui/MainTabsLayout.java')
  for bad in ['createBitmap','clipPath','LiquidLensRenderer','setRenderEffect']:self.assertNotIn(bad,bar)
  self.assertIn('slotWidth=inner/Math.max(1,count)',bar)
if __name__=='__main__':unittest.main()
