"""Native rendering is executed by music_visual; no app/device benchmark is implied."""
from pathlib import Path
import subprocess,tempfile,unittest,xml.etree.ElementTree as ET
from next_alpha_contract import ROOT
BASE='340cd323f5f5809abc746507b2e252da71298720'
PLAYER='TMessagesProj/src/main/java/app/exteraless/player/'
class Music3(unittest.TestCase):
 def test_native_audio_compact_players_and_preview_fix_are_unchanged(self):
  from alpha1275_contract import restore as restore_alpha1275
  for p in ['TMessagesProj/src/main/java/org/telegram/messenger/'+x+'.java'for x in ['MediaController','MusicPlayerService']]+[PLAYER+x+'.java'for x in ['PlayerMiniView','PlayerBarView','SignatureMusicBubble','SignatureMusicHost','LyricsView','LyricsFill']]+['TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java','TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java']:
   self.assertEqual(restore_alpha1275(p,(ROOT/p).read_bytes()),subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT),p)
 def test_seek_actions_and_playback_transport_handlers_are_native(self):
  from test_signature_matte import body
  p=PLAYER+'PlayerSheet.java';before=subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT,text=True);after=(ROOT/p).read_text()
  for anchor in ['public void onSeekStart(', 'public void onSeekMove(', 'public void onSeekEnd(', 'private void togglePlay(', 'private void cycleSpeed(', 'private void openQueue(', 'private void setLyricsMode(', 'private void toggleProfile(']:self.assertEqual(body(before,anchor),body(after,anchor),anchor)
  self.assertIn('if (BuildConfig.CONNECTED_ALPHA || !animated)',after);self.assertIn('cover.setListener(fallbackSeed, null)',after)
 def test_static_columns_and_fade_have_no_frame_work_or_extra_bitmaps(self):
  from test_signature_matte import body
  draw=body((ROOT/(PLAYER+'WavySeekBar.java')).read_text(),'private void drawSignatureColumns(')
  for token in ['new ','post','SystemClock','Math.sin','Bitmap','Shader','thread','Thread']:self.assertNotIn(token,draw)
  fade=(ROOT/(PLAYER+'SignatureCoverFade.java')).read_text();self.assertNotIn('Bitmap',fade);self.assertNotIn('Animator',fade);self.assertNotIn('new ',body(fade,'void draw('));self.assertIn('this.width == width && this.height == height && this.color == color',fade)
 def test_all_new_labels_exist_in_each_language_and_sources_parse(self):
  for lang in ['values','values-es','values-ru']:
   strings={x.get('name'):x.text for x in ET.parse(ROOT/'TMessagesProj/src/main/res'/lang/'flexygram_music.xml').getroot()}
   for key in ['FlexyMusicSpeed','FlexyMusicMore','FlexyMusicPlayingFrom','FlexyMusicMyMusic']:self.assertTrue(strings[key])
  code='''import javax.tools.*;import com.sun.source.util.*;import java.util.*;class ParseMusic3{public static void main(String[] a)throws Exception{var c=ToolProvider.getSystemJavaCompiler();var d=new DiagnosticCollector<JavaFileObject>();var f=c.getStandardFileManager(d,null,null);var t=(JavacTask)c.getTask(null,f,d,List.of("-proc:none"),null,f.getJavaFileObjects(a));for(var x:t.parse()){}for(var e:d.getDiagnostics())if(e.getKind()==Diagnostic.Kind.ERROR)throw new AssertionError(e);f.close();}}'''
  with tempfile.TemporaryDirectory()as t:
   p=Path(t)/'ParseMusic3.java';p.write_text(code);subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',t,str(p)],check=True,capture_output=True);subprocess.run(['java','-cp',t,'ParseMusic3',*[str(ROOT/(PLAYER+x+'.java'))for x in ['PlayerSheet','PlayerColors','CoverImage','SignatureCoverFade','WavySeekBar','ControlsRow']]],check=True,capture_output=True)
