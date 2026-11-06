"""Timestamp ink matches incoming metadata through the active theme/provider."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_timestamp_matches_directional_body_ink_in_light_dark_and_custom_chats(tmp_path):
    source=(JAVA/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
    resolve=method(source,'private int getTimestampColor(boolean selected)')
    probe(tmp_path, {'Probe.java': """
public class Probe {
 static class app{static class flexygram{static class bubbles{static class BubbleConfig{static boolean enabled=true;static boolean smallTimestamps(){return enabled;}}}}}
 static class Theme{static final int key_chat_messageTextIn=1,key_chat_messageTextOut=2;
 static final int key_chat_inTimeText=3,key_chat_outTimeText=4,key_chat_inTimeSelectedText=5,key_chat_outTimeSelectedText=6;
 static int getColor(int key,Object provider){if(provider==null)throw new AssertionError("lost chat provider");return 0xff808080+key;}}
 Object resourcesProvider=new Object();
 static class Message{boolean out;boolean isOutOwner(){return out;}}
 Message currentMessageObject=new Message();int incoming,outgoing;
 int getThemedColor(int key){if(key==1)return incoming;if(key==2)return outgoing;throw new AssertionError("timestamp used metadata/accent ink");}
 RESOLVE
 public static void main(String[] args){Probe p=new Probe();
  for(int[] colors:new int[][]{{0xff111111,0xff222222},{0xffffffff,0xffeeeeee},{0xffcadcfe,0xff112233}}){
   p.incoming=colors[0];p.outgoing=colors[1];
   for(boolean out:new boolean[]{false,true})for(boolean selected:new boolean[]{false,true}){
    p.currentMessageObject.out=out;
    if(p.getTimestampColor(selected)!=(out?p.outgoing:p.incoming))throw new AssertionError();
    app.flexygram.bubbles.BubbleConfig.enabled=false;
    int key=out?(selected?Theme.key_chat_outTimeSelectedText:Theme.key_chat_outTimeText):(selected?Theme.key_chat_inTimeSelectedText:Theme.key_chat_inTimeText);
    if(p.getTimestampColor(selected)!=Theme.getColor(key,p.resourcesProvider))throw new AssertionError("native palette not restored");
    app.flexygram.bubbles.BubbleConfig.enabled=true;
   }
  }
 }
}""".replace('RESOLVE',resolve)})


def test_all_timestamp_setup_paths_and_preview_share_theme_ink_but_media_stays_native():
    source=(JAVA/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
    assert source.count('getTimestampColor(isDrawSelectionBackground())')==4
    draw=method(source,'private void drawTimeInternal(')
    assert 'Theme.chat_timePaint.setColor(getTimestampColor(drawSelectionBackground));' in draw
    assert 'Theme.key_chat_outTimeText' not in draw and 'Theme.key_chat_outTimeSelectedText' not in draw
    assert 'Theme.chat_timePaint.setColor(getThemedColor(Theme.key_chat_mediaTimeText));' in draw
    assert 'Theme.chat_timePaint.setColor(getThemedColor(Theme.key_chat_serviceText));' in draw
    preview=(JAVA/'app/flexygram/bubbles/BubblePreviewView.java').read_text()
    assert 'BubbleConfig.smallTimestamps() ? text.getColor() : Theme.getColor(out ? Theme.key_chat_outTimeText : Theme.key_chat_inTimeText)' in preview
    assert 'if (BubbleConfig.smallTimestamps()) time.setTextSize(AndroidUtilities.dpf2(9));' in preview
    assert 'timestampPaint.set(Theme.chat_timePaint);' in source
    assert 'if (measuredSmallTimestamp) timestampPaint.setTextSize(AndroidUtilities.dpf2(9));' in source
    assert 'measuredSmallTimestamp != app.flexygram.bubbles.BubbleConfig.smallTimestamps()' in source
    assert 'new StaticLayout(currentTimeString, timestampPaint,' in source
    assert 'Math.ceil(timestampPaint.measureText(currentTimeString,' in source
    assert 'new StaticLayout(editedStr, timestampPaint,' in source
    assert 'new StaticLayout(spannableStringBuilder, timestampPaint,' in source
