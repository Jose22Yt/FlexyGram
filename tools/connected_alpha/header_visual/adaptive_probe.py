"""Real Android channel layout/buttons and actual bot-row methods; explicit native service/blur doubles."""
import re
from pathlib import Path
from stubs import body

def write_probe(source,root):
 def put(name,text):
  p=source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 java=root/'TMessagesProj/src/main/java'
 files=['org/telegram/ui/Components/CubicBezierInterpolator.java','org/telegram/ui/Components/chat/layouts/ChatActivityChannelButtonsLayout.java',
 'org/telegram/ui/Components/chat/buttons/ChatActivityBlurredRoundButton.java',
 'me/vkryl/android/animator/BoolAnimator.java','me/vkryl/android/animator/FactorAnimator.java',
 'me/vkryl/android/AnimatorUtils.java','me/vkryl/core/BitwiseUtils.java',
 'app/flexygram/composer/FlexyComposerConfig.java','app/flexygram/composer/ComposerStyle.java','app/flexygram/composer/ComposerGeometry.java']
 for name in files:put(name,(java/name).read_text())
 put('androidx/annotation/FloatRange.java','package androidx.annotation;public @interface FloatRange{double from() default Double.NEGATIVE_INFINITY;double to() default Double.POSITIVE_INFINITY;}')
 put('androidx/annotation/DrawableRes.java','package androidx.annotation;public @interface DrawableRes{}')
 put('me/vkryl/android/animator/Animated.java','package me.vkryl.android.animator;public interface Animated{default void runOnceViewBecomesReady(android.view.View v,Runnable r){v.post(r);}}')
 put('org/telegram/messenger/utils/ViewOutlineProviderImpl.java','package org.telegram.messenger.utils;public class ViewOutlineProviderImpl{public static android.view.ViewOutlineProvider boundsWithPaddingRoundRect(int p,int r){return new android.view.ViewOutlineProvider(){public void getOutline(android.view.View v,android.graphics.Outline o){o.setRoundRect(0,0,v.getWidth(),v.getHeight(),r);}};}}')
 put('org/telegram/ui/Components/ScaleStateListAnimator.java','package org.telegram.ui.Components;public class ScaleStateListAnimator{public static void apply(android.view.View v,float a,float b){}}')
 put('org/telegram/ui/Components/CircularProgressDrawable.java','package org.telegram.ui.Components;public class CircularProgressDrawable extends android.graphics.drawable.ColorDrawable{public CircularProgressDrawable(int a,float b,int c,int d){}public void setAngleOffset(int a){}public void reset(){}}')
 put('org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundColorProvider.java','package org.telegram.ui.Components.blur3.drawable.color;public interface BlurredBackgroundColorProvider{}')
 put('org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java','''package org.telegram.ui.Components.blur3.drawable;public class BlurredBackgroundDrawable extends android.graphics.drawable.ColorDrawable{
 public BlurredBackgroundDrawable(){super(0xff303236);}public BlurredBackgroundDrawable setColorProvider(org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundColorProvider p){return this;}public BlurredBackgroundDrawable setRadius(float r){return this;}public BlurredBackgroundDrawable setPadding(int p){return this;}public void updateColors(){}}
''')
 put('org/telegram/ui/Components/blur3/BlurredBackgroundDrawableViewFactory.java','''package org.telegram.ui.Components.blur3;public class BlurredBackgroundDrawableViewFactory{
 public org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable create(android.view.View v){return new org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable();}
 public org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable create(android.view.View v,org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundColorProvider p){return create(v);}}''')
 p=source/'org/telegram/messenger/AndroidUtilities.java';s=p.read_text().replace('public class AndroidUtilities {','public class AndroidUtilities {public static final android.graphics.Rect rectTmp2=new android.graphics.Rect();public static float lerp(float a,float b,float p){return a+(b-a)*p;}');p.write_text(s)
 code='\n'.join((java/n).read_text()for n in files)
 p=source/'org/telegram/messenger/R.java';s=p.read_text()
 for kind in ['string','drawable']:
  names=set(re.findall(r'R\.'+kind+r'\.(\w+)',code))-set(re.findall(r'int (\w+)[ =]',s))
  value=lambda i: 'android.R.drawable.ic_menu_search' if kind=='drawable' else str(8000+i)
  s=s.replace('class '+kind+' {','class '+kind+' {'+''.join('public static final int '+name+'='+value(i)+';'for i,name in enumerate(sorted(names))))
 p.write_text(s)
 p=source/'org/telegram/ui/ActionBar/Theme.java';s=p.read_text();names=set(re.findall(r'Theme\.(key_\w+)',code))-set(re.findall(r'int (key_\w+)[ =]',s));s=s.replace('public static boolean dark;', ''.join('public static final int '+name+'='+str(6000+i)+';'for i,name in enumerate(sorted(names)))+'public static boolean dark;');s=s.replace('public class Theme {','''public class Theme {
 public static int multAlpha(int c,float a){return (c&0xffffff)|Math.round((c>>>24)*a)<<24;}
 public static android.graphics.drawable.Drawable createInsetRoundRectDrawable(int c,int r,int i){return new android.graphics.drawable.ColorDrawable(0);}
''');p.write_text(s)
 actual=(java/'org/telegram/ui/Components/ChatActivityEnterView.java').read_text()
 methods='\n'.join(body(actual,a)for a in ['private boolean wantsFlexyBotRow(', 'private void updateFlexyBotRow(', 'private int getFlexyBotRowHeight(', 'private float calculateIslandTotalHeight('])
 put('AdaptiveBotProbe.java','''import android.content.Context;import android.view.*;import android.widget.*;import org.telegram.ui.Components.LayoutHelper;
public class AdaptiveBotProbe extends FrameLayout {
 public boolean flexyCompactRequested=true,isChat=true,isStories,flexyBotRow;public Object parentFragment=new Object();
 enum BotMenuButtonType{NO_BUTTON,COMMANDS,WEB_VIEW}public BotMenuButtonType botMenuButtonType=BotMenuButtonType.COMMANDS;public long dialog_id=1;
 public View topView;public class Height{public float getFactor(){return messageEditTextContainer.getMeasuredHeight();}public float getToFactor(){return getFactor();}}
 public class Top{public boolean getValue(){return false;}public float getFloatValue(){return 0;}}
 public final Height animatorInputFieldHeight=new Height();public final Top animatorTopViewVisibility=new Top();
 private int getFlexyVerticalReservation(){return 0;}
 public float reservedHeight(){return calculateIslandTotalHeight(false);}
 public FrameLayout textFieldContainer,messageEditTextContainer;public TextView botCommandsMenuButton;public EditText text;public int clicks;
 static int dp(float v){return org.telegram.messenger.AndroidUtilities.dp(v);}
 public AdaptiveBotProbe(Context c){super(c);textFieldContainer=new FrameLayout(c);addView(textFieldContainer,new FrameLayout.LayoutParams(-1,-2));messageEditTextContainer=new FrameLayout(c);messageEditTextContainer.setMinimumHeight(dp(44));textFieldContainer.addView(messageEditTextContainer,new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM));text=new EditText(c);text.setText("draft");messageEditTextContainer.addView(text,new FrameLayout.LayoutParams(-1,-2));botCommandsMenuButton=new TextView(c);botCommandsMenuButton.setText("Store");botCommandsMenuButton.setOnClickListener(v->clicks++);messageEditTextContainer.addView(botCommandsMenuButton,new FrameLayout.LayoutParams(120,32,Gravity.BOTTOM|Gravity.LEFT));}
 @Override protected void onMeasure(int w,int h){updateFlexyBotRow();super.onMeasure(w,h);}
'''+methods+'}')
 parent=(java/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
 fields=parent[parent.index('    private final RectF signatureChannelMiddle='):parent.index('    /** Same native backdrop')]
 method=body(parent,'private void drawSignatureChannelBackground(')
 put('ChannelBackdropProbe.java','''import android.graphics.*;import android.graphics.drawable.ColorDrawable;import android.view.*;import android.widget.*;import androidx.core.graphics.ColorUtils;import org.telegram.messenger.AndroidUtilities;
public class ChannelBackdropProbe {
 public org.telegram.ui.Components.chat.layouts.ChatActivityChannelButtonsLayout flexyChannels;
 public FrameLayout inputIslandBubbleContainer=new FrameLayout(org.robolectric.RuntimeEnvironment.getApplication());
 public boolean flexyPearlGlass;public final CountingBackdrop blurredBackgroundDrawable=new CountingBackdrop();
 public static class CountingBackdrop extends ColorDrawable{public int draws;public CountingBackdrop(){super(0xff303236);}@Override public void draw(Canvas c){draws++;super.draw(c);}}
 final Rect tmpRect=new Rect();final RectF tmpRectF=new RectF();final Paint flexySurface=new Paint(3),flexyPearl=new Paint(3);
 static int dp(float v){return AndroidUtilities.dp(v);}
 public void render(Canvas c){drawSignatureChannelBackground(c);}
'''+fields+method+'}')
 (source/'AdaptiveControlsTest.java').write_bytes(Path(__file__).with_name('AdaptiveControlsTest.java.in').read_bytes())
