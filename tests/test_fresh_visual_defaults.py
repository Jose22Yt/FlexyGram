"""Fresh installs stay native; explicit visual choices and legacy power policy survive reload."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method

PREFS = '''package android.content;import java.util.*;
public class SharedPreferences {
 public final Map<String,Object> data=new HashMap<>();
 public Map<String,?> getAll(){return data;}
 public boolean contains(String k){return data.containsKey(k);}
 public boolean getBoolean(String k,boolean d){return (Boolean)data.getOrDefault(k,d);}
 public int getInt(String k,int d){return (Integer)data.getOrDefault(k,d);}
 public String getString(String k,String d){return (String)data.getOrDefault(k,d);}
 public Editor edit(){return new Editor();}
 public interface OnSharedPreferenceChangeListener{void onSharedPreferenceChanged(SharedPreferences p,String key);}
 public void registerOnSharedPreferenceChangeListener(OnSharedPreferenceChangeListener l){}
 public void unregisterOnSharedPreferenceChangeListener(OnSharedPreferenceChangeListener l){}
 public class Editor{
  public Editor putInt(String k,int v){data.put(k,v);return this;}
  public Editor putBoolean(String k,boolean v){data.put(k,v);return this;}
  public Editor remove(String k){data.remove(k);return this;}
  public void apply(){}
 }
}'''


def test_native_composer_and_enabled_message_motion_preserve_explicit_choices(tmp_path):
    probe(tmp_path, {
        'android/content/SharedPreferences.java': PREFS,
        'app/flexygram/composer/ComposerGeometry.java': 'package app.flexygram.composer;public class ComposerGeometry{public static final int TOUCH_SLOT=44;}',
        'org/telegram/messenger/SharedConfig.java': 'package org.telegram.messenger;public class SharedConfig{public static boolean capable=true;public static boolean canBlurChat(){return capable;}public static boolean chatBlurEnabled(){throw new AssertionError("surface blur must stay independent");}public static boolean animationsEnabled(){return true;}}',
        'org/telegram/messenger/AndroidUtilities.java': 'package org.telegram.messenger;public class AndroidUtilities{public static boolean isAccessibilityScreenReaderEnabled(){return false;}}',
        'android/content/Context.java': '''package android.content;import java.util.*;
public class Context {public static final int MODE_PRIVATE=0;final Map<String,SharedPreferences> files=new HashMap<>();
 public Context getApplicationContext(){return this;}
 public SharedPreferences getSharedPreferences(String f,int mode){return files.computeIfAbsent(f,k->new SharedPreferences());}}''',
        'org/telegram/messenger/ApplicationLoader.java': '''package org.telegram.messenger;public class ApplicationLoader{
 public static final android.content.Context applicationContext=new android.content.Context();}''',
        'app/flexygram/animation/FastMotion.java': '''package app.flexygram.animation;public class FastMotion{
 public static void setEnabled(boolean v){FastMotionTiming.setEnabled(v);}public static double systemScale(){return 1;}}''',
        'Probe.java': '''import app.flexygram.composer.*;import app.flexygram.animation.*;
import app.flexygram.bubbles.interaction.*;import org.telegram.messenger.ApplicationLoader;
public class Probe {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){var c=ApplicationLoader.applicationContext;
 check(!FlexyComposerConfig.compact()&&!FlexyComposerConfig.glass()&&FlexyComposerConfig.referenceIcons());
 check(FlexyComposerConfig.preferences().getBoolean("reference_icons_restored_v1",false));
 FlexyComposerConfig.setStyle(1);FlexyComposerConfig.setGlass(true);FlexyComposerConfig.setReferenceIcons(true);
 check(FlexyComposerConfig.compact()&&FlexyComposerConfig.glass()&&FlexyComposerConfig.referenceIcons());
 FlexyComposerConfig.reset();check(!FlexyComposerConfig.compact()&&!FlexyComposerConfig.glass()&&FlexyComposerConfig.referenceIcons());
 check(BubbleInteractionSettings.style(c)==BubbleInteractionSettings.STYLE_SIGNATURE&&BubbleInteractionSettings.backdropBlur(c));
 BubbleInteractionSettings.setStyle(c,0);BubbleInteractionSettings.reload();check(BubbleInteractionSettings.style(c)==0&&!BubbleInteractionSettings.backdropBlur(c));
 BubbleInteractionSettings.setStyle(c,1);BubbleInteractionSettings.reload();check(BubbleInteractionSettings.style(c)==1);
 BubbleInteractionSettings.resetTap(c);BubbleInteractionSettings.reload();check(BubbleInteractionSettings.style(c)==1);
 org.telegram.messenger.SharedConfig.capable=false;check(!BubbleInteractionSettings.backdropBlur(c));org.telegram.messenger.SharedConfig.capable=true;
 var p=c.getSharedPreferences("flexy_bubble_interaction",0);p.data.clear();p.data.put("tap_panel",false);
 BubbleInteractionSettings.reload();check(BubbleInteractionSettings.style(c)==0&&!BubbleInteractionSettings.backdropBlur(c));
 check(FastMotionTiming.isEnabled());FastMotionConfig.load();check(FastMotionConfig.isEnabled());
 FastMotionConfig.setEnabled(true);FastMotionConfig.load();check(FastMotionConfig.isEnabled());
 FastMotionConfig.setEnabled(false);FastMotionConfig.load();check(!FastMotionConfig.isEnabled());
 }}''',
    }, [JAVA / p for p in ['app/flexygram/composer/FlexyComposerConfig.java',
                           'app/flexygram/composer/ComposerStyle.java',
                           'app/flexygram/animation/FastMotionTiming.java',
                           'app/flexygram/animation/FastMotionConfig.java',
                           'app/flexygram/bubbles/interaction/BubbleInteractionSettings.java']])


def test_native_power_defaults_exclude_glass_but_saved_and_legacy_flags_survive(tmp_path):
    source=(JAVA/'org/telegram/messenger/LiteMode.java').read_text()
    # Execute the production loader including its real flag/preset constants.
    constants=source[source.index('    public static final int FLAG_ANIMATED_STICKERS_KEYBOARD'):source.index('    private static int BATTERY_LOW')]
    body=method(source, 'public static void loadPreference()')
    probe(tmp_path, {
        'android/content/SharedPreferences.java': PREFS,
        'Probe.java': '''import android.content.SharedPreferences;
class SharedConfig{static final int PERFORMANCE_CLASS_LOW=0,PERFORMANCE_CLASS_AVERAGE=1;static int device;static int getDevicePerformanceClass(){return device;}}
class MessagesController{static SharedPreferences p=new SharedPreferences();static SharedPreferences getGlobalMainSettings(){return p;}}
class LiteMode {
 CONSTANTS
 static int BATTERY_LOW=10,BATTERY_MEDIUM=10,BATTERY_HIGH=10,value,powerSaverLevel;static boolean loaded;
 static void onFlagsUpdate(int old,int next){}
 LOADER
}
public class Probe {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){var p=MessagesController.p;
 int effects=LiteMode.FLAG_CHAT_BLUR|LiteMode.FLAG_LIQUID_GLASS;
 LiteMode.PRESET_HIGH|=effects;LiteMode.PRESET_MEDIUM|=effects;LiteMode.PRESET_LOW|=effects;
 for(int device=0;device<3;device++){
  SharedConfig.device=device;p.data.clear();LiteMode.loadPreference();check((LiteMode.value&effects)==0);
  int nativeFlags=device==0?LiteMode.PRESET_LOW:device==1?LiteMode.PRESET_MEDIUM:LiteMode.PRESET_HIGH;
  check((LiteMode.value&~effects)==(nativeFlags&~effects));
  p.data.put("lite_mode6",nativeFlags);LiteMode.loadPreference();check(LiteMode.value==nativeFlags);
 }
 p.data.clear();p.data.put("chatBlur",true);LiteMode.loadPreference();check((LiteMode.value&LiteMode.FLAG_CHAT_BLUR)!=0);
 p.data.clear();p.data.put("lite_mode5",effects);LiteMode.loadPreference();check((LiteMode.value&LiteMode.FLAG_CHAT_BLUR)!=0);
 }}'''.replace('CONSTANTS',constants).replace('LOADER',body),
    })


def test_native_icon_pack_is_identity_and_cupertino_remains_selectable(tmp_path):
    import re
    source=(JAVA/'app/exteraless/icons/BaseIconPacks.java').read_text()
    names=sorted(set(re.findall(r'R\.drawable\.(\w+)',source)))
    resources='package org.telegram.messenger;public class R{public static class string{public static final int Default=1;}public static class drawable{'+''.join(f'public static final int {name}={i+1};' for i,name in enumerate(names))+'}}'
    probe(tmp_path, {
        'org/telegram/messenger/R.java': resources,
        'org/telegram/messenger/LocaleController.java': 'package org.telegram.messenger;public class LocaleController{public static String getString(int id){return "Default";}}',
        'android/util/SparseIntArray.java': '''package android.util;public class SparseIntArray{java.util.Map<Integer,Integer> m=new java.util.HashMap<>();public SparseIntArray(int capacity){}public void put(int k,int v){m.put(k,v);}public int get(int k,int d){return m.getOrDefault(k,d);}}''',
        'xyz/nextalone/nagram/NaConfig.java': '''package xyz.nextalone.nagram;public class NaConfig{public static final NaConfig INSTANCE=new NaConfig();public final Item item=new Item();public Item getIconReplacements(){return item;}public static class Item{int value;public int Int(){return value;}public void setConfigInt(int v){value=v;}}}''',
        'android/content/res/Resources.java': 'package android.content.res;public class Resources{public static class Theme{}}',
        'android/graphics/drawable/Drawable.java': 'package android.graphics.drawable;public class Drawable{}',
        'app/flexygram/icons/ExactIcons.java': 'package app.flexygram.icons;public class ExactIcons{public static android.graphics.drawable.Drawable create(android.content.res.Resources r,int id,int d,android.content.res.Resources.Theme t){return id==1?new android.graphics.drawable.Drawable():null;}}',
        'app/flexygram/icons/CupertinoIconMap.java': 'package app.flexygram.icons;public class CupertinoIconMap{public static int spec(int id){return id==1?1:0;}public static int color(int id){return 0;}}',
        'app/flexygram/icons/CupertinoGlyphDrawable.java': 'package app.flexygram.icons;public class CupertinoGlyphDrawable extends android.graphics.drawable.Drawable{public CupertinoGlyphDrawable(android.content.res.Resources r,int s,int c){}}',
        'Probe.java': '''import app.exteraless.icons.BaseIconPacks;import app.flexygram.icons.CupertinoIcons;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 var r=new android.content.res.Resources();check(BaseIconPacks.getSelected()==0&&BaseIconPacks.getMap(0)==null);
 check(BaseIconPacks.getIcon(123456)==123456&&BaseIconPacks.getName(0).equals("Default"));
 for(int pack:new int[]{0,1,2}){BaseIconPacks.setSelected(pack);check(BaseIconPacks.getSelected()==pack&&CupertinoIcons.create(r,1)==null);}
 BaseIconPacks.setSelected(3);check(BaseIconPacks.getSelected()==3&&CupertinoIcons.create(r,1)!=null&&CupertinoIcons.create(r,-1)==null);
 BaseIconPacks.setSelected(-9);check(BaseIconPacks.getSelected()==0&&CupertinoIcons.create(r,1)==null);
 }}''',
    }, [JAVA/'app/exteraless/icons/BaseIconPacks.java',JAVA/'app/flexygram/icons/CupertinoIcons.java'])
