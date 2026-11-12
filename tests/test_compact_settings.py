"""Execute production routing/dispatch on the JVM; these are not APK/device tests."""
import hashlib
import re
import xml.etree.ElementTree as E
from pathlib import Path
from test_render_work_reuse import probe, JAVA
from test_composer_layout import method

ROOT = Path(__file__).resolve().parents[1]
S = JAVA / 'app/flexygram/settings/signature'


def resources(*sources):
    return 'package org.telegram.messenger;public class R{' + ''.join(
        'public static class ' + kind + '{' + ''.join(
            'public static final int ' + name + '=' + str(i + 1) + ';'
            for i, name in enumerate(sorted(set(re.findall(r'R\.' + kind + r'\.(\w+)', '\n'.join(sources)))))) + '}'
        for kind in ['string', 'drawable']) + '}'


def test_compact_plan_routes_are_stable_and_immutable(tmp_path):
    plan = (S / 'CompactSettingsPlan.java').read_text()
    files = {'app/flexygram/settings/signature/CompactSettingsPlan.java': plan,
             'org/telegram/messenger/R.java': resources(plan),
             'app/flexygram/settings/signature/PlanProbe.java': '''package app.flexygram.settings.signature;
public class PlanProbe{public static void main(String[] args){
 if(CompactSettingsPlan.pages("home").length!=7||CompactSettingsPlan.pages("chat").length!=8)throw new AssertionError("unbounded overview");
 var copy=CompactSettingsPlan.pages("home");copy[0]=null;if(CompactSettingsPlan.pages("home")[0]==null)throw new AssertionError("mutable shared plan");
 String[][] cases={{"home","scroll_effects","motion"},{"home","avatars","avatars"},{"home","folders","folders"},{"home","layout","list"},{"home","smart_previews","pills"},{"home","visible","visible"},{"home","appearance_extra_ng","extras"},{"chat","media_extra_nc","media"},{"chat","stickers_extra_nx","stickers"},{"chat","post_appearance","messages"},{"chat","menus","menus"}};
 for(String[] c:cases)if(!CompactSettingsPlan.segment(c[0],c[1]).equals(c[2]))throw new AssertionError(java.util.Arrays.toString(c));
 for(String category:new String[]{"home","chat"}){
  var icons=new java.util.HashSet<Integer>();for(var p:CompactSettingsPlan.pages(category)){if(!icons.add(p.icon))throw new AssertionError("repeated icon");if(CompactSettingsPlan.page(category,p.id)!=p)throw new AssertionError();}
 }
 try{CompactSettingsPlan.page("home","missing");throw new AssertionError("invalid restore accepted");}catch(IllegalArgumentException expected){}
}}'''}
    files['Probe.java']='public class Probe{public static void main(String[]args){app.flexygram.settings.signature.PlanProbe.main(args);}}'
    probe(tmp_path, files, [])


def test_only_the_open_section_creates_editors_and_all_old_controls_remain_reachable(tmp_path):
    text = (S / 'SignatureDirectSettingsActivity.java').read_text()
    body = method(text, 'private void build()')
    # Run the real dispatch with counted editor factories. No native editor is
    # allowed to be created for an overview, including the expensive previews.
    classes = re.findall(r'new (app\.[\w.]+)\(', body)
    files = {}
    for cls in set(classes):
        package, name = cls.rsplit('.', 1)
        files[cls.replace('.', '/') + '.java'] = ('package ' + package + ';public class ' + name +
            '{public ' + name + '(){}public ' + name + '(boolean b){}}')
    # Nested NativeControls needs its actual outer class shape.
    files.pop('app/exteraless/settings/OpenExteraAppNavigationActivity/NativeControls.java', None)
    files['app/exteraless/settings/OpenExteraAppNavigationActivity.java'] = 'package app.exteraless.settings;public class OpenExteraAppNavigationActivity{public static class NativeControls{}}'
    source = '''import org.telegram.messenger.R;import java.util.*;import app.exteraless.settings.OpenExteraAppNavigationActivity;
public class Probe{
 String category,segment="";int overviewCalls;List<String> rows=new ArrayList<>();
 boolean include(String id){return segment.equals(id);}void overview(){overviewCalls++;}
 void add(Object o){rows.add(o.getClass().getSimpleName());} <T>T scope(T o,String source,String routes){rows.add(source+":"+routes);return o;}
 void extra(String source,String... routes){rows.add(source+":"+String.join("|",routes));}
 void links(String[] ids,int[] titles,int[] icons){}
 static class OpenExteraChatsActivity{static final int SCREEN_SIGNATURE_MESSAGES=1,SCREEN_MENUS=2,SCREEN_MEDIA=3,SCREEN_SIGNATURE_STICKERS=4,SCREEN_CHATS=5,SCREEN_HIDING=6;OpenExteraChatsActivity(int screen){}}
 static class OpenExteraAppearanceActivity{}static class OpenExteraGeneralActivity{}static class OpenExteraOtherActivity{}static class SignatureLauncherSettingsActivity{}static class GhostModeActivity{}static class OpenExteraAyuMomentsActivity{}
 BODY
 void open(String category,String segment){this.category=category;this.segment=segment;rows.clear();overviewCalls=0;build();}
 void expect(String row){if(!rows.contains(row))throw new AssertionError(category+":"+segment+" lost "+row);}
 public static void main(String[]args){Probe p=new Probe();
 for(String cat:new String[]{"home","chat"}){p.open(cat,"");if(p.overviewCalls!=1||!p.rows.isEmpty())throw new AssertionError("eager editors");}
 p.open("home","list");p.expect("HomeListSettingsActivity");p.expect("appearance:chat_list");p.expect("chats:chat_list");if(p.rows.contains("SmartPreviewsSettingsActivity"))throw new AssertionError("eager preview");
 p.open("home","motion");if(!p.rows.equals(List.of("ScrollEffectsSettingsActivity")))throw new AssertionError("scroll controls lost");
 p.open("home","pills");if(!p.rows.equals(List.of("SmartPreviewsSettingsActivity")))throw new AssertionError(p.rows.toString());
 for(String route:new String[]{"avatars","folders"}){p.open("home",route);p.expect("appearance:"+route);}
 p.open("home","visible");p.expect("chats:visible");p.open("home","extras");p.expect("ng:appearance_extra");p.expect("nx:appearance_extra");
 p.open("chat","messages");p.expect("chats:messages|post_appearance");p.expect("nc:messages_extra");
 p.open("chat","menus");p.expect("chats:menus");
 for(String route:new String[]{"media","stickers"}){p.open("chat",route);p.expect("chats:"+route);for(String source:new String[]{"ng","nc","nx"})p.expect(source+":"+route+"_extra");}
 String[][] special={{"glare","GlareSettingsSection"},{"members","MemberLensSettingsSection"},{"conversion","InlineConversionSettingsSection"},{"animations","MessageAnimationsActivity"}};
 for(String[] c:special){p.open("chat",c[0]);if(!p.rows.equals(List.of(c[1])))throw new AssertionError("wrong special editor");}
 }}'''.replace('BODY', body)
    files['Probe.java'] = source
    files['org/telegram/messenger/R.java'] = resources(body)
    probe(tmp_path, files, [])


def test_icons_are_distinct_real_assets_and_localization_is_complete():
    plan = (S / 'CompactSettingsPlan.java').read_text()
    direct = (S / 'SignatureDirectSettingsActivity.java').read_text()
    overview = method(direct, 'private void overview()')
    # Compare actual packaged image contents, not merely aliases with different names.
    for text in [plan[plan.index('CHAT='):plan.index('static boolean')]+overview,
                 plan[plan.index('HOME='):plan.index('CHAT=')]]:
        names = re.findall(r'R.drawable.(\w+)', text)
        digests = []
        for name in names:
            matches = list((ROOT/'TMessagesProj/src/main/res').glob('drawable*/'+name+'.*'))
            assert matches, name
            digests.append(hashlib.sha256(matches[0].read_bytes()).digest())
        assert len(digests)==len(set(digests)), 'two entries draw the same icon'
    keys = set()
    for path in [S/'CompactSettingsPlan.java', JAVA/'app/flexygram/home/SmartPreviewsSettingsActivity.java']:
        keys.update(re.findall(r'R.string.(Compact\w+)', path.read_text()))
    for locale in ['values','values-es','values-ru']:
        strings = E.parse(ROOT/'TMessagesProj/src/main/res'/locale/'flexy_settings_compact.xml').getroot()
        names = [x.get('name') for x in strings]
        assert len(names)==len(set(names))
        assert keys <= set(names)


def test_mini_pill_picker_is_lazy_and_legacy_links_open_sections():
    text = (JAVA/'app/flexygram/home/SmartPreviewsSettingsActivity.java').read_text()
    rows = method(text, 'protected void updateRows()')
    assert 'previewRow=showPreview?addRow():-1' in rows
    assert 'TYPE_RADIO' not in text
    assert 'createSingleChoiceDialog' in text
    legacy = (S/'SignatureSettingsRegistry.java').read_text()
    assert 'Settings3Registry.openRoute(id)' in method(legacy, 'public static BaseFragment open(')
    assert 'Settings3Registry.searchPage(SignatureLegacyExtras.categoryForKey(key)' in method(legacy,'public static BaseFragment legacy(')
    save = method((S/'SignatureDirectSettingsActivity.java').read_text(), 'public void saveSelfArgs(')
    restore = method((S/'SignatureDirectSettingsActivity.java').read_text(), 'public void restoreSelfArgs(')
    assert 'settings3Segment' in save and 'settings3Segment' in restore


def test_reopening_preview_reconnects_a_recycled_holder(tmp_path):
    text = (JAVA/'app/flexygram/home/SmartPreviewsSettingsActivity.java').read_text()
    bind = method(text, 'public void onBindViewHolder(').replace('@Override ', '')
    probe(tmp_path, {'Probe.java': '''class View{}class SmartPreviewsDemoView extends View{int themes;void updateColors(){themes++;}}
class TextSettingsCell extends View{void setTextAndValue(String s,String v,boolean d){}}
class RecyclerView{static class ViewHolder{View itemView;ViewHolder(View v){itemView=v;}}}
class LocaleController{static String getString(int id){return "";}}class R{static class string{static int CompactHidePreview,CompactPreview;}}
class SignatureSmartPreviews{static int mode(){return 1;}}
public class Probe{int previewRow=2,styleRow=0;boolean showPreview;SmartPreviewsDemoView preview;
String getActionBarTitle(){return "";}int label(int mode){return mode;}
BIND
public static void main(String[]args){Probe p=new Probe();SmartPreviewsDemoView view=new SmartPreviewsDemoView();var holder=new RecyclerView.ViewHolder(view);
p.onBindViewHolder(holder,2,false);if(p.preview!=view)throw new AssertionError();p.preview=null;
// RecyclerView can return the same holder without invoking onCreateViewHolder.
p.onBindViewHolder(holder,2,false);if(p.preview!=view||view.themes!=2)throw new AssertionError("recycled preview disconnected");}}
'''.replace('BIND', bind)}, [])
