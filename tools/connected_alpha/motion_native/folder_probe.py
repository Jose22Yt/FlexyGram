"""Exact folder-color factory/entry/property, real Android View; folder list/account are doubles."""
from player_probe import method

def write(put,root):
 s=(root/'TMessagesProj/src/main/java/org/telegram/ui/Components/FilterTabsView.java').read_text()
 factory=method(s,'    private Animator createFolderColorTransition(')
 entry=method(s,'    public void animateColorsTo(')
 a=s.index('    private final AnimationProperties.FloatProperty<FilterTabsView> COLORS')
 b=s.index('    public FilterTabsView(',a)
 prop=s[a:b].replace('FilterTabsView','FolderMotionProbe')
 put('FolderMotionProbe.java','''import android.animation.*;import android.view.*;import android.widget.*;import android.util.Property;import androidx.core.graphics.ColorUtils;import org.telegram.ui.ActionBar.Theme;
 public class FolderMotionProbe extends FrameLayout {
 public FolderMotionProbe(android.content.Context c){super(c);listView=new List(c);}
 public Animator colorChangeAnimator;public float animationValue;public int tabLineColorKey=1,activeTextColorKey=2,unactiveTextColorKey=3,backgroundColorKey=4,selectorColorKey=5,aTabLineColorKey=-1,aActiveTextColorKey=-1,aUnactiveTextColorKey=-1,aBackgroundColorKey=-1,accentRefreshes;
 boolean signatureHome=true;Theme.ResourcesProvider resourcesProvider;final android.graphics.drawable.GradientDrawable selectorDrawable=new android.graphics.drawable.GradientDrawable();final List listView;
 static class List extends FrameLayout {int invalidates;List(android.content.Context c){super(c);}void setSelectorDrawableColor(int color){}void invalidateViews(){invalidates++;}}
 void refreshSignatureAccent(){accentRefreshes++;}
 static class AnimationProperties {abstract static class FloatProperty<T> extends Property<T,Float>{FloatProperty(String name){super(Float.class,name);}public abstract void setValue(T object,float value);public void set(T object,Float value){setValue(object,value);}}}
 '''+prop+factory+entry+'}')
