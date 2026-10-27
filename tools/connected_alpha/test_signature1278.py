"""Incremental behavior checks; source regressions do not stand in for device evidence."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2]
class Signature1278(unittest.TestCase):
 def test_theme_accent_contrast_and_event_cache(self):
  code='''import app.flexygram.home.SignatureFolderAccent;public class AccentProbe {public static void main(String[]args){
   var c=new SignatureFolderAccent();for(int r=0;r<256;r+=17)for(int g=0;g<256;g+=17)for(int b=0;b<256;b+=17){
    int a=0xff000000|(r<<16)|(g<<8)|b;c.update(a,0xffeeeeee,0xff303236);
    if(c.color!=a||SignatureFolderAccent.contrast(c.ink,c.color)<4.5)throw new AssertionError("contrast");
    for(int n=0;n<4;n++)if(c.update(a,0xffeeeeee,0xff303236))throw new AssertionError("cache");
    for(int n=0;n<=128;n++){
     float f=n/128f;int bg=0xff000000;
     for(int shift=0;shift<=16;shift+=8)bg|=Math.round(((0xff303236>>>shift)&255)+(((a>>>shift)&255)-((0xff303236>>>shift)&255))*f)<<shift;
     if(SignatureFolderAccent.contrast(c.inkAt(f),bg)<4.5)throw new AssertionError("transition contrast");
    }
   }
   c.update(0x80336699,0xffffffff,0xff000000);if(c.color!=0xff1a334d)throw new AssertionError("composite");
   c.update(0xffffff00,0xffffffff,0xff000000);if(c.ink!=0xff000000)throw new AssertionError("yellow contrast");
   c.update(0xff000000,0xffffffff,0xffffffff);if(c.ink!=0xffffffff)throw new AssertionError("dark contrast");
   System.out.println("PASS native theme accent gamut and cached resolution");}}'''
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'AccentProbe.java';p.write_text(code)
   r=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',folder,str(ROOT/'TMessagesProj/src/main/java/app/flexygram/home/SignatureFolderAccent.java'),str(p)],capture_output=True,text=True);self.assertEqual(0,r.returncode,r.stderr)
   r=subprocess.run(['java','-cp',folder,'AccentProbe'],capture_output=True,text=True);self.assertEqual(0,r.returncode,r.stderr)
 def test_shared_preferences_and_native_actions_remain(self):
  root=ROOT/'TMessagesProj/src/main'
  config=(root/'kotlin/app/exteraless/appearance/AppearanceConfig.kt').read_text()
  self.assertIn('addConfig("FlexyFolderThemeAccent", ConfigItem.configTypeBool, true)',config)
  bot=(root/'java/org/telegram/ui/Components/ChatActivityEnterView.java').read_text()
  self.assertIn('updateFlexyBotRow();',bot);self.assertIn('textFieldContainer.addView(botCommandsMenuButton',bot)
  self.assertIn('botMenuButtonType!=BotMenuButtonType.NO_BUTTON',bot)
  channel=(root/'java/org/telegram/ui/ChatActivity.java').read_text()
  self.assertIn('chatInfo.stargifts_available',channel);self.assertIn('checkCanOpenChat(args,ChatActivity.this)',channel)
  self.assertIn('setDiscussionButton(useSignatureChannelDiscussion())',channel)
  self.assertIn('new GiftSheet(getContext(), currentAccount, getDialogId()',channel)
 def test_current_release_changes_only_version_and_preserves_all_signing_gates(self):
  base='79ae7c6a4d52d3a787ca8dfddb11660d028bf24f'
  for name,old,new in [('TMessagesProj/build.gradle','def verCode = 1277','def verCode = 1278'),('.github/workflows/connected-alpha-arm64.yml','--expected-version-code 1277','--expected-version-code 1278')]:
   current=(ROOT/name).read_text();self.assertIn(new,current)
   original=subprocess.check_output(['git','show',base+':'+name],cwd=ROOT,text=True)
   self.assertEqual(current.replace(new,old),original)
 def test_historical_review_is_immutable(self):
  path='tools/connected_alpha/stability1277_review.json'
  baseline=subprocess.check_output(['git','show','79ae7c6a4d52d3a787ca8dfddb11660d028bf24f:'+path],cwd=ROOT)
  self.assertEqual(baseline,(ROOT/path).read_bytes())
if __name__=='__main__':unittest.main()
