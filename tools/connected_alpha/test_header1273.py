"""Actual geometry and source boundaries. Not a full chat/device acceptance test."""
from pathlib import Path
import subprocess,tempfile,unittest,xml.etree.ElementTree as ET
from next_alpha_contract import ROOT
HEADER='TMessagesProj/src/main/java/app/flexygram/header/'
BASE='43e917e035045f07e0d206ed9f86c83912992094'
class HeaderTests(unittest.TestCase):
 def test_actual_geometry_equal_heights_screen_center_rtl_and_large_fonts(self):
  rect='''package android.graphics; public class RectF {public float left,top,right,bottom;public void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}public float width(){return right-left;}public float height(){return bottom-top;}public float centerX(){return(left+right)/2;}public void offset(float x,float y){left+=x;right+=x;top+=y;bottom+=y;}}'''
  code='''import app.flexygram.header.HeaderGeometry;class Geometry {public static void main(String[] args){int cases=0;for(float d:new float[]{.75f,1,1.5f,2,3,4})for(int w:new int[]{240,281,360,401,600})for(float font:new float[]{1,1.5f,2,3})for(boolean compact:new boolean[]{false,true})for(boolean rtl:new boolean[]{false,true})for(int count:new int[]{0,1,3,999}){int width=Math.round(w*d);float h=HeaderGeometry.height(width,17.5f*d*font,13.5f*d*font,d,compact);HeaderGeometry g=new HeaderGeometry();g.update(width,24*d,h,count==0?0:count==999?40*d:10*d,d,rtl);if(Math.abs(g.back.height()-h)>.001||Math.abs(g.title.height()-h)>.001||Math.abs(g.avatar.height()-h)>.001)throw new AssertionError("height");if(Math.abs(g.title.centerX()-width/2f)>.001)throw new AssertionError("center");if(g.title.width()<0||g.back.left<0||g.avatar.left<0||g.back.right>width||g.avatar.right>width)throw new AssertionError("bounds");if((rtl?g.avatar.right>g.title.left||g.title.right>g.back.left:g.back.right>g.title.left||g.title.right>g.avatar.left))throw new AssertionError("overlap");cases++;}if(cases!=1920)throw new AssertionError(cases);System.out.println(cases);}}'''
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp);(p/'android/graphics').mkdir(parents=True);(p/'android/graphics/RectF.java').write_text(rect);(p/'Geometry.java').write_text(code)
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(p/'android/graphics/RectF.java'),str(ROOT/(HEADER+'HeaderGeometry.java')),str(p/'Geometry.java')],check=True,capture_output=True)
   result=subprocess.run(['java','-cp',tmp,'Geometry'],check=True,capture_output=True,text=True);self.assertIn('1920',result.stdout)
 def test_p0_engine_auth_and_compact_music_are_preserved(self):
  for p in ['TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java','TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java','TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java','TMessagesProj/src/main/java/org/telegram/messenger/MediaController.java','TMessagesProj/src/main/java/app/exteraless/player/SignatureMusicBubble.java']:
   self.assertEqual((ROOT/p).read_bytes(),subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT),p)
 def test_real_cached_source_counter_and_existing_navigation_handlers(self):
  from test_signature_matte import body
  chat=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java').read_text()
  count=body(chat,'private void updateSignatureHeaderCounter(')
  for token in ['containsKey("dialog_folder_id")','containsKey("dialog_filter_id")','getMainUnreadCount()','getArchiveUnreadCount()','filter.id == dialogFilterId','filter.unreadCount']:self.assertIn(token,count)
  for token in ['new Thread','postDelayed','getAllDialogs','getStorageQueue','addObserver','removeView']:self.assertNotIn(token,count)
  before=subprocess.check_output(['git','show',BASE+':TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java'],cwd=ROOT,text=True)
  self.assertEqual(body(before,'protected boolean onAvatarClick('),body(chat,'private boolean openNativeHeaderOptions('))
  surface=(ROOT/(HEADER+'HeaderSurface.java')).read_text()
  self.assertNotIn('new ',body(surface,'public void draw('));self.assertNotIn('new ',body(surface,'private void piece('));self.assertNotIn('Blur',surface)
 def test_translations_and_new_settings_route(self):
  keys=None
  for locale in ['values','values-es','values-ru']:
   strings={n.get('name'):n.text for n in ET.parse(ROOT/'TMessagesProj/src/main/res'/locale/'flexygram_header.xml').getroot()};self.assertTrue(all(strings.values()));keys=set(strings)if keys is None else keys;self.assertEqual(set(strings),keys)
  hub=(ROOT/'TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraChatsActivity.java').read_text();self.assertIn('new app.flexygram.header.HeaderSettingsActivity()',hub)
  settings=(ROOT/(HEADER+'HeaderSettingsActivity.java')).read_text();self.assertIn('FlexySignatureSlider',settings);self.assertNotIn('rebuild',settings);self.assertNotIn('recreate',settings)

 def test_appearance_routes_to_one_header_selector_and_master_tracks_actual_style(self):
  from test_signature_matte import body
  s=(ROOT/'TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraAppearanceActivity.java').read_text()
  click=body(s,'protected void onItemClick(')
  branch=click[click.index('position == iosChatHeaderRow'):click.index('position == dividerStyleRow')]
  self.assertIn('BuildConfig.CONNECTED_ALPHA',branch)
  self.assertIn('presentFragment(new app.flexygram.header.HeaderSettingsActivity())',branch)
  self.assertIn('AppearanceConfig.iosChatHeader.setConfigBool',branch)
  self.assertIn('HeaderConfig.signature()',body(s,'private int iosSelectedCount('))
  master=body(s,'private void toggleAllIosStyles(')
  self.assertIn('HeaderConfig.style(enable)',master)
  self.assertIn('AppearanceConfig.iosChatHeader.setConfigBool(enable)',master)
  self.assertIn('BuildConfig.CONNECTED_ALPHA',master)
  self.assertIn('iosChatHeaderRow = addRow("iosChatHeader")',body(s,'protected void updateRows()'))
  self.assertIn('position == iosChatHeaderRow && org.telegram.messenger.BuildConfig.CONNECTED_ALPHA',s)
