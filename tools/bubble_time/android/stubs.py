from pathlib import Path


def method(text, anchor):
    start = text.index(anchor)
    end = text.index('{', start) + 1
    level = 1
    i = end
    while level:
        level += (text[i] == '{') - (text[i] == '}')
        i += 1
    return text[start:i]


def write(dest, root):
    java = root/'TMessagesProj/src/main/java'
    for rel in ['app/exteraless/appearance/GlassContrastPolicy.java', 'app/flexygram/bubbles/BubbleTimeContrast.java']:
        target = dest/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((java/rel).read_text())
    config = dest/'app/flexygram/bubbles/BubbleConfig.java'
    config.write_text('package app.flexygram.bubbles;public class BubbleConfig {public static int opacity=35;public static int transparency(){return opacity;}}')
    target = dest/'org/telegram/messenger/BuildConfig.java'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('package org.telegram.messenger;public class BuildConfig{public static final boolean CONNECTED_ALPHA=true;}')
    (dest/'app/flexygram/bubbles/BubbleStyle.java').write_text((java/'app/flexygram/bubbles/BubbleStyle.java').read_text())
    source = (java/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
    body = method(source, 'private void drawReadableTimeLayout(')
    (dest/'TimeLabelProbe.java').write_text('''
import android.graphics.*;import android.text.*;
public class TimeLabelProbe {
 static class Theme {
  static TextPaint chat_timePaint=new TextPaint(Paint.ANTI_ALIAS_FLAG);
  static final int key_chat_outBubbleSelected=1,key_chat_outBubble=2,key_chat_inBubbleSelected=3,key_chat_inBubble=4,key_chat_outBubbleGradient1=5;
 }
 static class Message {boolean out;boolean isOutOwner(){return out;}}
 static class SpoilerEffect {static void layoutDrawMaybe(StaticLayout l,Canvas c){l.draw(c);}}
 int surface=0xffffffff,gradient;boolean media;
 Message currentMessageObject=new Message();
 private final app.flexygram.bubbles.BubbleTimeContrast bubbleTimeContrast=new app.flexygram.bubbles.BubbleTimeContrast();
 private Paint bubbleTimeSavedPaint;
 static class AndroidUtilities {static float dpf2(float n){return n;}}
 int getThemedColor(int key){return key==Theme.key_chat_outBubbleGradient1?gradient:surface;}
 boolean shouldDrawTimeOnMedia(){return media;}
 int dp(float n){return (int)Math.ceil(n);}
 BODY
 void draw(Canvas c,StaticLayout layout){drawReadableTimeLayout(c,layout,false);}
}
'''.replace('BODY', body))
