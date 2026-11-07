"""Conversation controls: shipped vectors, stable hit bounds, restored defaults and shared menu blur."""
from test_render_work_reuse import JAVA, ROOT, probe
from test_composer_layout import method
import os,re,shutil,subprocess
from pathlib import Path
import pytest


def test_counter_and_reference_icons_are_repaired_once_then_respect_choices(tmp_path):
    probe(tmp_path,{
 'android/content/SharedPreferences.java':'''package android.content;import java.util.*;public class SharedPreferences{
 public final Map<String,Object> data=new HashMap<>();public int writes;
 public Map<String,?>getAll(){return new HashMap<>(data);}public boolean getBoolean(String k,boolean d){return data.containsKey(k)?(Boolean)data.get(k):d;}public int getInt(String k,int d){return data.containsKey(k)?(Integer)data.get(k):d;}
 public Editor edit(){return new Editor();}public class Editor{
 public Editor putInt(String k,int v){data.put(k,v);return this;}public Editor putBoolean(String k,boolean v){data.put(k,v);return this;}public Editor remove(String k){data.remove(k);return this;}public void apply(){writes++;}}}''',
 'android/content/Context.java':'''package android.content;public class Context{public static final int MODE_PRIVATE=0;private final java.util.Map<String,SharedPreferences> files=new java.util.HashMap<>();public SharedPreferences getSharedPreferences(String f,int mode){return files.computeIfAbsent(f,k->new SharedPreferences());}}''',
 'org/telegram/messenger/ApplicationLoader.java':'''package org.telegram.messenger;public class ApplicationLoader{public static final android.content.Context applicationContext=new android.content.Context();}''',
 'app/exteraless/appearance/AppearanceConfig.java':'''package app.exteraless.appearance;public class AppearanceConfig{static final android.content.SharedPreferences p=new android.content.SharedPreferences();public static android.content.SharedPreferences getPreferences(){return p;}}''',
 'Probe.java':'''import app.flexygram.header.HeaderConfig;import app.flexygram.composer.FlexyComposerConfig;public class Probe{
 public static void main(String[]args){var c=org.telegram.messenger.ApplicationLoader.applicationContext;var h=c.getSharedPreferences("flexygram_header",0);var lower=c.getSharedPreferences("flexygram_composer",0);
 h.data.put("counter",false);h.data.put("counter_mode",2);lower.data.put("iconAppearance",1);
 HeaderConfig.load();if(!HeaderConfig.counter()||HeaderConfig.counterMode()!=1||!FlexyComposerConfig.referenceIcons())throw new AssertionError("repair missing");
 int hw=h.writes,lw=lower.writes;for(int i=0;i<10000;i++){HeaderConfig.load();FlexyComposerConfig.referenceIcons();}if(h.writes!=hw||lower.writes!=lw)throw new AssertionError("repeated writes");
 HeaderConfig.counter(false);HeaderConfig.load();FlexyComposerConfig.setReferenceIcons(false);if(HeaderConfig.counter()||FlexyComposerConfig.referenceIcons())throw new AssertionError("explicit choice overwritten");
 HeaderConfig.counterMode(2);HeaderConfig.load();if(HeaderConfig.counterMode()!=2)throw new AssertionError();
 FlexyComposerConfig.reset();if(!FlexyComposerConfig.referenceIcons())throw new AssertionError("reset uses obsolete icons");
 }}'''
    },[JAVA/'app/flexygram/header/HeaderConfig.java',JAVA/'app/flexygram/composer/FlexyComposerConfig.java',JAVA/'app/flexygram/composer/ComposerStyle.java',JAVA/'app/flexygram/composer/ComposerGeometry.java'])


def test_custom_action_slots_fit_parent_after_resume_and_studio_refresh(tmp_path):
    source=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    expressions=[]
    for sig in ['public void onResume()', 'public void onFlexyStudioApplied(']:
        body=method(source,sig)
        expressions.append(re.search(r'params.rightMargin = ([^;]+);',body)[1])
    probe(tmp_path,{'Probe.java':'''import app.flexygram.header.fusion.SignatureFusionGeometry;
 public class Probe{static boolean signature,centered;static boolean usesSignatureHeader(){return signature;}static boolean isTitleCentered(){return centered;}static class AndroidUtilities{static float density;static int dp(float n){return Math.round(n*density);}}
 public static void main(String[]args){for(float d:new float[]{1,2,3})for(int width:new int[]{360,411,720})for(boolean rtl:new boolean[]{false,true}){
 AndroidUtilities.density=d;signature=true;centered=false;int[]margins={EXPRESSIONS};
 var g=SignatureFusionGeometry.updatePortrait(new SignatureFusionGeometry.Layout(),width*d,d,rtl,true,30*d);
 for(int margin:margins){float parentRight=width*d-margin;if(g.more.right>parentRight||g.call.right>parentRight||g.more.left<0||g.call.left<0)throw new AssertionError("action drawn outside touch parent");}
 if((!rtl&&g.call.right>g.more.left)||(rtl&&g.more.right>g.call.left))throw new AssertionError("overlapping actions");
 signature=false;int[]nativeMargins={EXPRESSIONS};for(int margin:nativeMargins)if(margin!=Math.round(52*d))throw new AssertionError("native layout changed");
 }} }'''.replace('EXPRESSIONS',','.join(expressions))},[JAVA/'app/flexygram/header/fusion/SignatureFusionGeometry.java'])


def test_zero_badge_is_retained_and_unchanged_counts_do_not_remeasure(tmp_path):
    source=(JAVA/'app/flexygram/header/SignatureChatHeader.java').read_text()
    setter=method(source,'public void setCount(int value)')
    probe(tmp_path,{
 'android/graphics/Paint.java':'''package android.graphics;public class Paint{public void set(Paint p){}public float measureText(String s){return s.length()*6;}}''',
 'org/telegram/ui/ActionBar/Theme.java':'''package org.telegram.ui.ActionBar;public class Theme{public static final android.graphics.Paint dialogs_countTextPaint=new android.graphics.Paint();}''',
 'android/text/Layout.java':'''package android.text;public class Layout{public enum Alignment{ALIGN_CENTER}}''',
 'android/text/StaticLayout.java':'''package android.text;public class StaticLayout{public static int allocations;public String text;public StaticLayout(String s,android.graphics.Paint p,int width,Layout.Alignment a,float m,float add,boolean pad){text=s;allocations++;}}''',
 'Probe.java':'''import org.telegram.ui.ActionBar.Theme;public class Probe{
 int unreadCount,changes;android.text.StaticLayout unreadLayout;android.graphics.Paint unreadPaint=new android.graphics.Paint();void changed(){changes++;}
 SETTER
 public static void main(String[]args){Probe p=new Probe();p.setCount(0);if(!p.unreadLayout.text.equals("0"))throw new AssertionError();for(int i=0;i<10000;i++)p.setCount(0);
 if(p.changes!=1||android.text.StaticLayout.allocations!=1)throw new AssertionError("idle text rebuild");
 p.setCount(101);for(int i=102;i<10000;i++)p.setCount(i);if(!p.unreadLayout.text.equals("99+")||p.changes!=2)throw new AssertionError();
 p.setCount(-1);if(!p.unreadLayout.text.equals("0"))throw new AssertionError();
 }}'''.replace('SETTER',setter)
    })


def test_control_decoder_bypasses_drawable_replacements_and_closes_parser(tmp_path):
    probe(tmp_path,{
 'android/content/res/XmlResourceParser.java':'''package android.content.res;public class XmlResourceParser implements AutoCloseable{public boolean closed;public int id;public void close(){closed=true;}}''',
 'android/content/res/Resources.java':'''package android.content.res;public class Resources{public static class Theme{}public static class NotFoundException extends RuntimeException{public NotFoundException(String s,Throwable t){super(s,t);}}public XmlResourceParser parser;public XmlResourceParser getXml(int id){parser=new XmlResourceParser();parser.id=id;return parser;}public android.graphics.drawable.Drawable getDrawable(int id){throw new AssertionError("icon replacement path used");}}''',
 'android/content/Context.java':'''package android.content;public class Context{public final android.content.res.Resources r=new android.content.res.Resources();public android.content.res.Resources getResources(){return r;}public android.content.res.Resources.Theme getTheme(){return new android.content.res.Resources.Theme();}}''',
 'org/xmlpull/v1/XmlPullParserException.java':'''package org.xmlpull.v1;public class XmlPullParserException extends Exception{}''',
 'android/graphics/drawable/Drawable.java':'''package android.graphics.drawable;public class Drawable{public int id;public static boolean fail;public static Drawable createFromXml(android.content.res.Resources r,android.content.res.XmlResourceParser p,android.content.res.Resources.Theme t)throws java.io.IOException,org.xmlpull.v1.XmlPullParserException{if(fail)throw new java.io.IOException();Drawable d=new Drawable();d.id=p.id;return d;}}''',
 'Probe.java':'''import app.flexygram.icons.ConversationControlIcons;public class Probe{public static void main(String[]args){android.content.Context c=new android.content.Context();if(ConversationControlIcons.load(c,77).id!=77||!c.r.parser.closed)throw new AssertionError();android.graphics.drawable.Drawable.fail=true;try{ConversationControlIcons.load(c,78);throw new AssertionError();}catch(android.content.res.Resources.NotFoundException expected){}if(!c.r.parser.closed)throw new AssertionError("parser leak");}}'''
    },[JAVA/'app/flexygram/icons/ConversationControlIcons.java'])


def test_decoder_types_against_real_android_sdk(tmp_path):
    sdk=Path(os.environ.get('ANDROID_HOME',str(ROOT.parent/'.flexygram/android-sdk')))/'platforms/android-37.0/android.jar'
    if not sdk.is_file()or not shutil.which('javac'):pytest.skip('Android SDK and JDK required')
    subprocess.run(['javac','-proc:none','-cp',str(sdk),'-d',str(tmp_path),str(JAVA/'app/flexygram/icons/ConversationControlIcons.java')],check=True,capture_output=True,text=True)


def test_menu_cards_share_selection_blur_and_imports_preserve_explicit_controls():
    chat=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    panel=chat[chat.index('final var panel=new app.flexygram.bubbles.interaction.BubbleActionPanelView'):]
    panel=panel[:panel.index('final var admitted=')]
    assert 'BubbleInteractionSettings.backdropBlur(getParentActivity())' in panel
    assert 'scrimBlur3Factory.create(target, true)' in panel and 'scrimMenuBackground(themeDelegate)' in panel
    assert 'checkBlurEnabled' not in panel and 'captureMessageMenuBlur' not in panel
    backup=(JAVA/'app/flexygram/studio/StudioClientBackup.java').read_text()
    assert 'containsKey("counter")' in backup and 'putBoolean("back_counter_restored_v1",true)' in backup
    assert 'containsKey("iconAppearance")' in backup and 'putBoolean("reference_icons_restored_v1",true)' in backup
