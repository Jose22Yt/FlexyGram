"""Header/input material parity, using actual providers and the native blur gate."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_shared_material_tracks_light_dark_flags_account_and_theme(tmp_path):
    native=(JAVA/'org/telegram/ui/Components/blur3/drawable/color/impl/BlurredBackgroundProviderImpl.java').read_text()
    gate=method(native,'public static boolean checkBlurEnabled(int currentAccount, Theme.ResourcesProvider resourcesProvider)')
    probe(tmp_path, {
        'androidx/annotation/ColorInt.java':'package androidx.annotation;public @interface ColorInt{}',
        'androidx/core/graphics/ColorUtils.java':'package androidx.core.graphics;public class ColorUtils{public static int setAlphaComponent(int c,int a){return(c&0xffffff)|(a<<24);}}',
        'org/telegram/messenger/AndroidUtilities.java':'package org.telegram.messenger;public class AndroidUtilities{public static float computePerceivedBrightness(int c){return((c>>16&255)+(c>>8&255)+(c&255))/765f;}}',
        'org/telegram/messenger/SharedConfig.java':'package org.telegram.messenger;public class SharedConfig{public static boolean enabled;public static boolean chatBlurEnabled(){return enabled;}}',
        'org/telegram/messenger/LiteMode.java':'package org.telegram.messenger;public class LiteMode{public static final int FLAG_LIQUID_GLASS=1;public static boolean liquid;public static boolean isEnabled(int f){return liquid;}}',
        'org/telegram/messenger/MessagesController.java':'''package org.telegram.messenger;public class MessagesController{
 public static final MessagesController[] accounts={new MessagesController(),new MessagesController()};public static MessagesController getInstance(int a){return accounts[a];}
 public final Config config=new Config();public static class Config{public Flag disableBlurInLightTheme=new Flag(),disableBlurInDarkTheme=new Flag();}public static class Flag{public boolean value;public boolean get(){return value;}}}''',
        'org/telegram/ui/ActionBar/Theme.java':'''package org.telegram.ui.ActionBar;public class Theme{
 public static boolean dark;public static int color=-1;public interface ResourcesProvider{boolean isDark();int getColor(int key);}
 public static boolean isCurrentThemeDark(){return dark;}public static int getColor(int key,ResourcesProvider p){return p==null?color:p.getColor(key);}
 public static int getDividerColor(Object p){return 0;}public static int key_windowBackgroundWhiteBlackText=9;
 public static int multAlpha(int c,float a){return(c&0xffffff)|((int)((c>>>24)*a)<<24);}}''',
        'org/telegram/ui/Components/blur3/drawable/color/impl/BlurredBackgroundProviderImpl.java':'''package org.telegram.ui.Components.blur3.drawable.color.impl;
 import org.telegram.ui.ActionBar.Theme;import org.telegram.messenger.*;public class BlurredBackgroundProviderImpl{GATE}'''.replace('GATE',gate),
        'Probe.java':'''import app.flexygram.effects.ChatGlassColorProvider;import org.telegram.ui.ActionBar.Theme;import org.telegram.messenger.*;
 public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}
 static class Palette implements Theme.ResourcesProvider{boolean dark;int bottom,top,white;public boolean isDark(){return dark;}public int getColor(int k){return k==1?bottom:k==2?top:white;}}
 public static void main(String[]args){Palette palette=new Palette();
 // Account 0 disables both; the chat belongs to account 1, independent of global selection.
 MessagesController.accounts[0].config.disableBlurInLightTheme.value=true;MessagesController.accounts[0].config.disableBlurInDarkTheme.value=true;
 ChatGlassColorProvider input=new ChatGlassColorProvider(1,palette,1),header=new ChatGlassColorProvider(1,palette,2),white=new ChatGlassColorProvider(1,palette,3);
 ChatGlassColorProvider[] surfaces={input,header,white};
 for(boolean dark:new boolean[]{false,true})for(boolean blur:new boolean[]{false,true})for(boolean liquid:new boolean[]{false,true})for(boolean disabled:new boolean[]{false,true})for(int rgb:new int[]{0xffffff,0x151515,0x8ab4f8}){
  palette.dark=dark;SharedConfig.enabled=blur;LiteMode.liquid=liquid;
  MessagesController.accounts[1].config.disableBlurInLightTheme.value=disabled;MessagesController.accounts[1].config.disableBlurInDarkTheme.value=disabled;
  palette.bottom=0xff000000|rgb;palette.top=palette.bottom;palette.white=palette.bottom;
  for(ChatGlassColorProvider p:surfaces)p.updateColors();
  int expectedAlpha=!blur||disabled?255:!dark?140:(int)(255*(liquid?.85f:.76f));
  for(ChatGlassColorProvider p:surfaces)check((p.getBackgroundColor()>>>24)==expectedAlpha&&p.getBackgroundColor()==input.getBackgroundColor()&&p.getShadowColor()==0);
 }
 // The same retained provider must switch materials without recreating a drawable.
 SharedConfig.enabled=true;MessagesController.accounts[1].config.disableBlurInDarkTheme.value=false;palette.dark=true;
 LiteMode.liquid=false;int frost=header.getBackgroundColor();LiteMode.liquid=true;int glass=header.getBackgroundColor();check((frost>>>24)==193&&(glass>>>24)==216);
 palette.top=0xff223344;palette.bottom=0xff556677;header.updateColors();input.updateColors();check((header.getBackgroundColor()&0xffffff)==0x223344&&(input.getBackgroundColor()&0xffffff)==0x556677);
 // Master off is opaque and uses the newest palette even before a theme refresh callback.
 palette.top=0xffabcdef;SharedConfig.enabled=false;check(header.getBackgroundColor()==0xffabcdef);
 Theme.dark=false;Theme.color=-1;SharedConfig.enabled=true;MessagesController.accounts[1].config.disableBlurInLightTheme.value=false;
 check((new ChatGlassColorProvider(1,null,1).getBackgroundColor()>>>24)==140);
 }}''',
    }, [JAVA/'app/flexygram/effects/ChatGlassColorProvider.java',
        JAVA/'org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundColorProviderThemed.java',
        JAVA/'org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundColorProvider.java'])


def test_header_input_and_pinned_panel_share_policy_and_native_factory():
    source=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    create=method(source,'public View createView(Context context)')
    for key in ['chat_messagePanelBackground','windowBackgroundWhite','chat_topPanelBackground']:
        assert f'currentAccount, themeDelegate, Theme.key_{key}' in create
    assert create.count('new app.flexygram.effects.ChatGlassColorProvider(')==3
    assert 'actionBar.setupGlass(\n            glassBackgroundDrawableFactory,\n            blurredBackgroundColorProviderTop,' in create
    assert 'chatInputViewsContainer.setCompactGlassFactory(glassBackgroundDrawableFactory, blurredBackgroundColorProvider)' in create
    assert 'topPanelLayout.setBlurredBackground(glassBackgroundDrawableFactory.create(topPanelLayout)\n            .setColorProvider(blurredBackgroundColorProviderTop)' in source
    assert 'blurredBackgroundColorProviderTop.updateColors();' in source
    header=(JAVA/'org/telegram/ui/ActionBar/ActionBar.java').read_text()
    draw=method(header,'public boolean drawSignatureNativeGlass(Canvas canvas,')
    assert 'glassDrawableBack.draw(canvas)' in draw and 'glassDrawable.draw(canvas)' in draw and 'glassDrawableMenu.draw(canvas)' in draw
    assert 'signatureGlassCall.draw(canvas)' in draw


def test_conversation_fades_stop_at_the_system_bars(tmp_path):
    source = (JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    status = method(source, 'private void updateStatusBarFade()')
    navigation = method(source, 'private void updateNavigationBarFade()')
    probe(tmp_path, {'Probe.java': '''
public class Probe {
 static class View {static final int VISIBLE=0;}
 static class AndroidUtilities {static int statusBarHeight=27;}
 static class ActionBar {
  boolean occupy=true;int visibility;
  boolean getOccupyStatusBar(){return occupy;}
  int getVisibility(){return visibility;}
 }
 static class Insets {int navigation=19;int getCurrentNavigationBarInset(){return navigation;}}
 static class Fade {
  int top,bottom;
  void setFadeZoneTop(int height){top=height;}
  void setFadeZoneBottom(int height){bottom=height;}
 }
 ActionBar actionBar=new ActionBar();Insets windowInsetsStateHolder=new Insets();Fade chatActivityFadeView=new Fade();
 boolean inPreviewMode,inBubbleMode,isInsideContainer,hideBottom;
 boolean shouldHideBottomForGesture(){return hideBottom;}
 STATUS NAVIGATION
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args){
  Probe p=new Probe();p.updateStatusBarFade();p.updateNavigationBarFade();
  check(p.chatActivityFadeView.top==27&&p.chatActivityFadeView.bottom==19);
  p.inPreviewMode=true;p.updateStatusBarFade();check(p.chatActivityFadeView.top==0);
  p.inPreviewMode=false;p.actionBar.occupy=false;p.updateStatusBarFade();check(p.chatActivityFadeView.top==0);
  p.actionBar.occupy=true;p.actionBar.visibility=4;p.updateStatusBarFade();check(p.chatActivityFadeView.top==0);
  p.windowInsetsStateHolder.navigation=48;p.updateNavigationBarFade();check(p.chatActivityFadeView.bottom==48);
  p.hideBottom=true;p.updateNavigationBarFade();check(p.chatActivityFadeView.bottom==0);
 }
}
'''.replace('STATUS', status).replace('NAVIGATION', navigation)})


def test_backdrop_regions_follow_opacity_and_visibility(tmp_path):
    directory = JAVA/'org/telegram/ui/Components/blur3'
    drawable = (directory/'drawable/BlurredBackgroundDrawableRenderNode.java').read_text()
    needs_capture = method(drawable, 'public boolean needsBackdropCapture()')
    alpha = method(drawable, 'public void setAlpha(int alpha)')
    colors = method(drawable, 'public void updateColors()')
    source = (directory/'source/BlurredBackgroundSourceRenderNode.java').read_text()
    positions = method(source, 'public int getVisiblePositions(')
    assert 'd.needsBackdropCapture()' in positions

    probe(tmp_path, {'Probe.java': '''
class Drawable {
 int alpha=255,backgroundColor=0xff000000,nextColor=backgroundColor;
 int getAlpha(){return alpha;}public void setAlpha(int alpha){this.alpha=alpha;}
 public void updateColors(){backgroundColor=nextColor;}
}
public class Probe extends Drawable {
 static class Color{static int alpha(int color){return color>>>24;}}
 static class Source{int changes;void dispatchOnDrawablesRelativePositionChange(){changes++;}}
 static class Paint{void setColor(int color){}}
 static class Bounds{boolean useFullStroke;}
 static class RenderNode{void setAlpha(float alpha){}}
 final Source source=new Source();final Paint paintStrokeFull=new Paint(),paintStrokeTop=new Paint(),paintStrokeBottom=new Paint();
 final Bounds boundProps=new Bounds();final RenderNode renderNode=new RenderNode();
 boolean renderNodeInvalidated;int shadowColor,strokeColorFull,strokeColorTop,strokeColorBottom;
 boolean hasDisplayList(){return true;}
 void updateShadowLayer(int color){}
 CAPTURE ALPHA COLORS
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args){
  Probe p=new Probe();
  check(!p.needsBackdropCapture());
  p.nextColor=0x80000000;p.updateColors();check(p.needsBackdropCapture()&&p.source.changes==1);
  p.setAlpha(128);check(p.needsBackdropCapture()&&p.source.changes==1);
  p.setAlpha(0);check(!p.needsBackdropCapture()&&p.source.changes==2);
  p.setAlpha(255);check(p.needsBackdropCapture()&&p.source.changes==3);
  p.nextColor=0xff000000;p.updateColors();check(!p.needsBackdropCapture()&&p.source.changes==4);
 }
}
'''.replace('CAPTURE', needs_capture).replace('ALPHA', alpha).replace('COLORS', colors)})
