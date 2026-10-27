"""Exact MainTabsLayout interaction/driver excerpts, real View/ClickHelper; explicit layout/theme doubles."""
def write(put,root):
 put('androidx/annotation/Nullable.java','package androidx.annotation;public @interface Nullable {}')
 s=(root/'TMessagesProj/src/main/java/org/telegram/ui/MainTabsLayout.java').read_text()
 selection=s[s.index('    public void setTabSelected('):s.index('    @Override\n    protected void dispatchDraw')]
 drivers=s[s.index('    private float animatedLongSelectedViewCenterX;'):s.index('    @Override\n    public void setScaleY')]
 tail=s[s.index('    @Override\n    public void setScaleY'):s.rfind('}')]
 put('MainTabsLayout.java','''import android.view.*;import androidx.annotation.Nullable;import android.widget.*;import android.graphics.*;import java.util.*;
import app.flexygram.motion.*;import me.vkryl.android.util.ClickHelper;import org.telegram.messenger.AndroidUtilities;import org.telegram.ui.ActionBar.Theme;
public class MainTabsLayout extends FrameLayout {
 public MainTabsLayout(android.content.Context c){super(c);}
 @Override protected void onLayout(boolean changed,int l,int t,int r,int b){for(int i=0;i<getChildCount();i++)getChildAt(i).layout(i*100,0,(i+1)*100,50);}static float lerp(float a,float b,float f){return a+(b-a)*f;}
 final Paint selectorPaint=new Paint();final Theme.ResourcesProvider resourcesProvider=null;
 static class GlassTabView extends Button {boolean selected;GlassTabView(android.content.Context c){super(c);}public void setSelected(boolean v,boolean animated){selected=v;}public boolean isTabSelected(){return selected;}public void setSkipDrawSelector(boolean v){}}
 public float center(){return animatedLongSelectedViewCenterX;}public float offset(){return animatedLongSelectedViewOffsetX;}public boolean custom(){return drawCustomSelector;}
 public void begin(float x){clickHelper.delegateForTest.onLongPressRequestedAt(this,x,20);clickHelper.onLongPress(this,x,20);}
 public void move(float x){clickHelper.delegateForTest.onLongPressMove(this,null,x,20,0,20);}
 public void finish(float x){clickHelper.cancel(this,x,20);}
 public void press(boolean v){animateTabPress(v);}
'''+selection+drivers+tail+'}')
 # Only expose the delegate to invoke native gesture phases without synthesizing production touches.
 click=(root/'TMessagesProj/src/main/java/me/vkryl/android/util/ClickHelper.java').read_text()
 click=click.replace('private final Delegate delegate;','private final Delegate delegate; public final Delegate delegateForTest;').replace('this.delegate = delegate;','this.delegate = delegate; this.delegateForTest = delegate;')
 put('me/vkryl/android/util/ClickHelper.java',click)
 put('me/vkryl/android/ViewUtils.java','package me.vkryl.android;public class ViewUtils {public static void hapticVibrate(android.view.View v,boolean a,boolean b){}public static void onClick(android.view.View v){}}')
 put('me/vkryl/core/BitwiseUtils.java','package me.vkryl.core;public class BitwiseUtils {public static int setFlag(int x,int f,boolean v){return v?x|f:x&~f;}}')
 put('tw/nekomimi/nekogram/NekoConfig.java','package tw.nekomimi.nekogram;public class NekoConfig {public static final Flag disableVibration=new Flag();public static class Flag {public boolean Bool(){return true;}}}')
