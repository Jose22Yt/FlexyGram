"""Actual native bot Button and its command binding; rows/emoji loading/theme services are doubles."""
def write(put,root,source):
 s=(root/'TMessagesProj/src/main/java/org/telegram/ui/bots/BotKeyboardView.java').read_text()
 button=s[s.index('    private class Button extends'):s.index('    public int getKeyboardHeight()')]
 margin=next(line.strip()for line in s.splitlines()if 'private static final int BORDER_MARGIN ='in line)
 binding=next(line.strip() for line in s.splitlines()if 'textView.setOnClickListener('in line)
 put('BotMotionProbe.java','''import android.content.Context;import android.graphics.Color;import android.view.*;import android.widget.*;import android.util.TypedValue;import android.text.*;import androidx.core.graphics.ColorUtils;
import org.telegram.ui.Components.spoilers.SpoilersTextView;import org.telegram.messenger.*;import org.telegram.messenger.utils.tlutils.TLKeyboardHelper;import org.telegram.tgnet.tl.TL_keyboard;import org.telegram.ui.Components.*;import org.telegram.ui.Components.chat.ChatInputViewsContainer;import org.telegram.ui.ActionBar.Theme;
public class BotMotionProbe extends FrameLayout {
 public interface Delegate {void didPressedButton(TL_keyboard.KeyboardButton button);}public Delegate delegate;
 public BotMotionProbe(Context c){super(c);}static int dp(float f){return (int)f;}int getThemedColor(int key){return 0xff333333;}
 public View button(TL_keyboard.KeyboardButton value){Button textView=new Button(getContext(),value);textView.setPositionFlags(true,true,true,true);addView(textView,new FrameLayout.LayoutParams(200,48));ScaleStateListAnimator.apply(textView,.02f,1.5f);'''+binding+'''return textView;}
'''+margin+'\n'+button+'}')
 put('org/telegram/ui/Components/ScaleStateListAnimator.java',(root/'TMessagesProj/src/main/java/org/telegram/ui/Components/ScaleStateListAnimator.java').read_text())
 put('org/telegram/ui/Components/spoilers/SpoilersTextView.java','package org.telegram.ui.Components.spoilers;public class SpoilersTextView extends android.widget.TextView{public boolean allowClickSpoilers;public SpoilersTextView(android.content.Context c){super(c);}}')
 put('org/telegram/ui/Components/AnimatedEmojiSpan.java','package org.telegram.ui.Components;public class AnimatedEmojiSpan extends android.text.style.ForegroundColorSpan{public AnimatedEmojiSpan(long id,android.graphics.Paint.FontMetricsInt metrics){super(0xff333333);}}')
 put('org/telegram/messenger/Emoji.java','package org.telegram.messenger;public class Emoji{public static CharSequence replaceEmoji(CharSequence text,android.graphics.Paint.FontMetricsInt metrics,boolean unused){return text;}}')
 put('org/telegram/messenger/NotificationCenter.java','package org.telegram.messenger;public class NotificationCenter{public static void listenEmojiLoading(android.view.View v){}}')
 put('org/telegram/tgnet/tl/TL_keyboard.java','package org.telegram.tgnet.tl;public class TL_keyboard{public static class Style{public long icon;public boolean bg_primary,bg_danger,bg_success;}public static class KeyboardButton{public String text;public Style style;public boolean web;}}')
 put('org/telegram/messenger/utils/tlutils/TLKeyboardHelper.java','package org.telegram.messenger.utils.tlutils;public class TLKeyboardHelper{public static boolean isButtonWebView(org.telegram.tgnet.tl.TL_keyboard.KeyboardButton b){return b.web;}}')
 put('org/telegram/ui/Components/chat/ChatInputViewsContainer.java','package org.telegram.ui.Components.chat;public class ChatInputViewsContainer{public static int INPUT_KEYBOARD_RADIUS=24;}')
 put('org/telegram/ui/Components/LayoutHelper.java','''package org.telegram.ui.Components;public class LayoutHelper{public static int MATCH_PARENT=-1,WRAP_CONTENT=-2;public static android.widget.FrameLayout.LayoutParams createFrame(float w,float h,int g){return createFrame(w,h,g,0,0,0,0);}public static android.widget.FrameLayout.LayoutParams createFrame(float w,float h,int g,float l,float t,float r,float b){android.widget.FrameLayout.LayoutParams p=new android.widget.FrameLayout.LayoutParams((int)w,(int)h,g);p.setMargins((int)l,(int)t,(int)r,(int)b);return p;}}''')
 p=source/'org/telegram/messenger/AndroidUtilities.java';p.write_text(p.read_text().replace('public class AndroidUtilities {','public class AndroidUtilities {public static android.graphics.Typeface bold(){return android.graphics.Typeface.DEFAULT_BOLD;}'))
 p=source/'org/telegram/messenger/R.java';p.write_text(p.read_text().replace('class drawable {','class drawable {public static final int bot_webview=android.R.drawable.ic_menu_search;'))
 p=source/'org/telegram/ui/ActionBar/Theme.java';s=p.read_text().replace('public class Theme {','public class Theme {public static final int key_chat_botKeyboardButtonText=10,key_chat_botKeyboardButtonBackground=11,key_chat_botKeyboardButtonBackgroundPressed=12,key_botKeyboard_button_primary=13,key_botKeyboard_button_danger=14,key_botKeyboard_button_success=15,key_listSelector=16;public static android.graphics.drawable.Drawable createSimpleSelectorRoundRectDrawable(float a,float b,float c,float d,int color,int pressed,int mask){return new android.graphics.drawable.ColorDrawable(color);}')
 p.write_text(s)
