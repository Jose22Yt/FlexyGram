#!/usr/bin/env python3
"""Focused behavior/scope checks. Host JVM allocations are not Android ART/FPS measurements."""
import hashlib,json,pathlib,re,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'
BASE='4679f74ebd312acc4968dd2e044a6c6b7478445a'
class SmartPreviews2(unittest.TestCase):
 def test_original_detection_and_labels_unchanged(self):
  path='TMessagesProj/src/main/java/app/flexygram/home/SignatureSmartPreviews.java'
  previous=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
  current=(ROOT/path).read_text()
  anchor='    /**\n     * Telegram stores'
  self.assertEqual(previous[previous.index(anchor):],current[current.index(anchor):])
 def test_native_data_and_identity_untouched(self):
  for path in ['TMessagesProj/build.gradle','TMessagesProj/src/main/AndroidManifest.xml','TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java','TMessagesProj/src/main/java/org/telegram/messenger/MessagesStorage.java']:
   self.assertEqual(subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),(ROOT/path).read_bytes())
 def test_single_embedded_section_and_no_legacy_picker(self):
  page=(JAVA/'app/flexygram/settings/signature/SignatureDirectSettingsActivity.java').read_text()
  self.assertEqual(1,page.count('new app.flexygram.home.SmartPreviewsSettingsActivity()'))
  self.assertIn('case "home":\n                add(new app.flexygram.home.SmartPreviewsSettingsActivity())',page)
  legacy=(JAVA/'app/exteraless/settings/OpenExteraChatsActivity.java').read_text()
  self.assertNotIn('smartPreviewsRow = addRow(',legacy)
  self.assertNotIn('postNotificationName(NotificationCenter.dialogsNeedReload)',legacy[legacy.index('    protected void onItemClick'):legacy.index('    protected void onItemClick')+100000] if '    protected void onItemClick' in legacy else '')
 def test_visible_row_update_is_scoped_and_lifecycle_owned(self):
  cell=(JAVA/'org/telegram/ui/Cells/DialogCell.java').read_text()
  self.assertIn('addStyleListener(smartPreviewStyleListener)',cell)
  self.assertIn('removeStyleListener(smartPreviewStyleListener)',cell)
  method=cell[cell.index('private void refreshSmartPreviewStyle('):cell.index('    public void buildLayout()')]
  self.assertIn('smartPreviewKind==0',method)
  self.assertIn('else smartPreviewModeLastBuilt=next',method)
  for denied in ['requestLayout','notifyDataSetChanged','new Paint','new Shader']:
   self.assertNotIn(denied,method)
 def test_draw_never_loads_prefs_or_allocates_paints(self):
  span=(JAVA/'app/flexygram/home/SignatureSmartPillSpan.java').read_text()
  draw=span[span.index('    public void draw('):span.index('    public String label()')]
  self.assertIn('SignatureSmartPreviews.drawingMode()',draw)
  for denied in ['new ','getSharedPreferences','setSpan','ellipsize']:
   self.assertNotIn(denied,draw)
  self.assertIn('sharedInk.setTextSize(textSize)',draw)
 def test_palette_and_preserved_matte(self):
  with tempfile.TemporaryDirectory() as temp:
   p=pathlib.Path(temp)
   old=subprocess.check_output(['git','show',BASE+':TMessagesProj/src/main/java/app/flexygram/home/SignatureSmartPreviewPalette.java'],cwd=ROOT,text=True).replace('SignatureSmartPreviewPalette','OriginalPalette')
   (p/'OriginalPalette.java').write_text(old)
   sources=[JAVA/'app/flexygram/home/SignatureSmartPreviewPalette.java',JAVA/'app/flexygram/home/SignatureMiniPillClassifier.java',JAVA/'app/flexygram/home/SignatureSmartPillLayout.java',p/'OriginalPalette.java',ROOT/'tools/smart_previews2/PaletteTest.java']
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',temp,*map(str,sources)],check=True)
   subprocess.run(['java','-cp',temp,'PaletteTest'],check=True)
if __name__=='__main__':unittest.main()
