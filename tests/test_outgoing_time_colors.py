"""Timestamp ink matches incoming metadata through the active theme/provider."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_timestamp_uses_incoming_theme_colors_in_light_dark_and_custom_chats(tmp_path):
    source=(JAVA/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
    resolve=method(source,'private int getTimestampColor(boolean selected)')
    probe(tmp_path, {'Probe.java': '''
public class Probe {
 static class Theme{static final int key_chat_inTimeText=1,key_chat_inTimeSelectedText=2;
 static int normal,selected;static int getColor(int key,Object provider){if(provider==null)throw new AssertionError("missing chat theme");if(key==1)return normal;if(key==2)return selected;throw new AssertionError("unexpected accent/text color");}}
 Object resourcesProvider=new Object();
 RESOLVE
 public static void main(String[] args){Probe p=new Probe();
  // The chat's provider can override both colors independently of the global mode/accent.
  for(int[] theme:new int[][]{{0xff888888,0xff777777},{0xffaaaaaa,0xffbbbbbb},{0xff91999f,0xff8a9399}}){
   Theme.normal=theme[0];Theme.selected=theme[1];
   for(int i=0;i<10000;i++){
    if(p.getTimestampColor(false)!=theme[0]||p.getTimestampColor(true)!=theme[1])throw new AssertionError();
   }
  }
 }
}'''.replace('RESOLVE',resolve)})


def test_all_timestamp_setup_paths_and_preview_share_theme_ink_but_media_stays_native():
    source=(JAVA/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
    assert source.count('getTimestampColor(isDrawSelectionBackground())')==4
    draw=method(source,'private void drawTimeInternal(')
    assert 'Theme.chat_timePaint.setColor(getTimestampColor(drawSelectionBackground));' in draw
    assert 'Theme.key_chat_outTimeText' not in draw and 'Theme.key_chat_outTimeSelectedText' not in draw
    assert 'Theme.chat_timePaint.setColor(getThemedColor(Theme.key_chat_mediaTimeText));' in draw
    assert 'Theme.chat_timePaint.setColor(getThemedColor(Theme.key_chat_serviceText));' in draw
    preview=(JAVA/'app/flexygram/bubbles/BubblePreviewView.java').read_text()
    assert 'time.setColor(Theme.getColor(Theme.key_chat_inTimeText));' in preview
