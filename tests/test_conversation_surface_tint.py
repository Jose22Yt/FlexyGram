"""Real shared color/preference code, native material gates and optional allocation budget."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_theme_accent_keeps_native_alpha_and_disabled_identity_without_repeated_disk_reads(tmp_path):
    probe(tmp_path,{
        'android/content/SharedPreferences.java':'''package android.content;public interface SharedPreferences{boolean getBoolean(String k,boolean d);Editor edit();interface Editor{Editor putBoolean(String k,boolean v);void apply();}}''',
        'android/content/Context.java':'''package android.content;public class Context{public static int reads,writes;public static boolean value;public SharedPreferences getSharedPreferences(String n,int mode){reads++;return new SharedPreferences(){public boolean getBoolean(String k,boolean d){return value;}public Editor edit(){return new Editor(){public Editor putBoolean(String k,boolean v){value=v;return this;}public void apply(){writes++;}};}};}}''',
        'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();}',
        'org/telegram/ui/ActionBar/Theme.java':'package org.telegram.ui.ActionBar;public class Theme{public interface ResourcesProvider{int getColor(int key);}public static int accent=0xff00ff00;public static int key_windowBackgroundWhiteBlueHeader=1;public static int getColor(int k,ResourcesProvider p){return p==null?accent:p.getColor(k);}}',
        'Probe.java':'''import app.flexygram.chat.ConversationSurfaceTint;import app.flexygram.settings.signature.SettingsCardStyle;import org.telegram.ui.ActionBar.Theme;import android.content.Context;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 for(int c:new int[]{0,0xff112233,0x80112233,0xd8112233})check(ConversationSurfaceTint.apply(c,null)==c);
 ConversationSurfaceTint.setEnabled(true);int writes=Context.writes;
 for(int alpha:new int[]{0,128,193,216,255})for(int rgb:new int[]{0x202020,0xeeeeee}){
  int c=(alpha<<24)|rgb;Theme.accent=0xff00ff00;int green=ConversationSurfaceTint.apply(c,null);
  Theme.accent=0xff0000ff;int blue=ConversationSurfaceTint.apply(c,null);
  check(green>>>24==alpha&&blue>>>24==alpha);check((green>>8&255)>(green&255));check((blue&255)>(blue>>8&255));
  check(blue==SettingsCardStyle.accentTint(c,Theme.accent,8));
  check(SettingsCardStyle.accentTint(c,Theme.accent,0)==c);
  check(SettingsCardStyle.accentTint(c,Theme.accent,100)==((alpha<<24)|0x0000ff));
 }
 for(int i=0;i<10000;i++){ConversationSurfaceTint.setEnabled(true);ConversationSurfaceTint.apply(0xd8222222,null);}
 check(Context.reads==1&&Context.writes==writes);
 ConversationSurfaceTint.setEnabled(false);check(ConversationSurfaceTint.apply(0x80123456,null)==0x80123456);
}}'''
    },[JAVA/'app/flexygram/chat/ConversationSurfaceTint.java',JAVA/'app/flexygram/settings/signature/SettingsCardStyle.java'])


def test_custom_composer_materials_are_lazy_and_reused(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
    prepare=method(source,'private void prepareCompactGlass()')
    probe(tmp_path,{
        'org/telegram/messenger/SharedConfig.java':'package org.telegram.messenger;public class SharedConfig{public static boolean glass;public static boolean chatBlurEnabled(){return glass;}}',
        'Probe.java':'''import org.telegram.messenger.SharedConfig;
public class Probe{static class FlexyComposerConfig{static boolean on;static boolean compact(){return on;}}
 static class Material{Material setPadding(int p){return this;}void setAlpha(int a){}}
 static class Factory{int creates;Material create(Object owner,Object colors){creates++;return new Material();}}
 Factory compactGlassFactory=new Factory();Object compactGlassColors=new Object();Material[] compactGlass=new Material[4];
 PREPARE
 public static void main(String[]args){Probe p=new Probe();SharedConfig.glass=true;
 for(int i=0;i<10000;i++)p.prepareCompactGlass();if(p.compactGlassFactory.creates!=0)throw new AssertionError("classic allocates islands");
 FlexyComposerConfig.on=true;SharedConfig.glass=false;p.prepareCompactGlass();if(p.compactGlassFactory.creates!=0)throw new AssertionError("disabled effect allocates islands");
 SharedConfig.glass=true;for(int i=0;i<10000;i++)p.prepareCompactGlass();if(p.compactGlassFactory.creates!=4)throw new AssertionError("material not retained");
 }}'''.replace('PREPARE',prepare)
    })
    header=method((JAVA/'org/telegram/ui/ActionBar/ActionBar.java').read_text(),'public boolean drawSignatureNativeGlass(')
    assert 'NATIVE_BASELINE_TEST' not in header
    assert 'canvas.isHardwareAccelerated()' in header and 'SharedConfig.chatBlurEnabled()' in header
    assert 'NATIVE_BASELINE_TEST' not in method(source,'private void drawFlexyCompactBackground(')
