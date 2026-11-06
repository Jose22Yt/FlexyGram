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
  for(ChatGlassColorProvider p:surfaces)check((p.getBackgroundColor()>>>24)==expectedAlpha&&p.getBackgroundColor()==input.getBackgroundColor());
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
