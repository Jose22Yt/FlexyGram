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
 if(CompactSettingsPlan.pages("home").length!=6||CompactSettingsPlan.pages("chat").length!=8)throw new AssertionError("unbounded overview");
 var copy=CompactSettingsPlan.pages("home");copy[0]=null;if(CompactSettingsPlan.pages("home")[0]==null)throw new AssertionError("mutable shared plan");
 String[][] cases={{"home","avatars","avatars"},{"home","folders","folders"},{"home","layout","list"},{"home","smart_previews","pills"},{"home","visible","visible"},{"home","appearance_extra_ng","extras"},{"chat","media_extra_nc","media"},{"chat","stickers_extra_nx","stickers"},{"chat","post_appearance","messages"},{"chat","menus","menus"},{"universal","general_network","network"},{"universal","general_notifications","notifications"},{"universal","general_maps","maps"},{"universal","general_behavior","general"},{"universal","general_extra_ng","extras"},{"universal","advanced_extra_nx","advanced"},{"universal","surfaces","effects"},{"navigation","bottom_tabs","tabs"},{"navigation","navigation_extra_ng","extras"},{"navigation","gestures","gestures"},{"ayu","ayu_saving","saving"},{"ayu","ayu_tools","tools"},{"ayu","ayu_maintenance","maintenance"},{"plugins","translation_options","translation"}};
 for(String[] c:cases)if(!CompactSettingsPlan.segment(c[0],c[1]).equals(c[2]))throw new AssertionError(java.util.Arrays.toString(c));
 for(String category:new String[]{"home","chat","universal","navigation","ayu","plugins"}){
  var icons=new java.util.HashSet<Integer>();for(var p:CompactSettingsPlan.pages(category)){if(!icons.add(p.icon))throw new AssertionError("repeated icon");if(CompactSettingsPlan.page(category,p.id)!=p)throw new AssertionError();}
 }
 try{CompactSettingsPlan.page("home","missing");throw new AssertionError("invalid restore accepted");}catch(IllegalArgumentException expected){}
 try{CompactSettingsPlan.page("home","motion");throw new AssertionError("retired effect page accepted");}catch(IllegalArgumentException expected){}
}}'''}
    files['Probe.java']='public class Probe{public static void main(String[]args){app.flexygram.settings.signature.PlanProbe.main(args);}}'
    probe(tmp_path, files, [])


def test_only_the_open_section_creates_editors_and_retained_controls_remain_reachable(tmp_path):
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
 for(String cat:new String[]{"home","chat","universal","navigation","ayu","plugins"}){p.open(cat,"");if(p.overviewCalls!=1||!p.rows.isEmpty())throw new AssertionError("eager editors");}
 p.open("home","list");p.expect("HomeListSettingsActivity");p.expect("appearance:chat_list");p.expect("chats:chat_list");if(p.rows.contains("SmartPreviewsSettingsActivity"))throw new AssertionError("eager preview");
 p.open("home","pills");if(!p.rows.equals(List.of("SmartPreviewsSettingsActivity")))throw new AssertionError(p.rows.toString());
 for(String route:new String[]{"avatars","folders"}){p.open("home",route);p.expect("appearance:"+route);}
 p.open("home","visible");p.expect("chats:visible");p.open("home","extras");p.expect("ng:appearance_extra");p.expect("nx:appearance_extra");
 p.open("chat","messages");p.expect("chats:messages|post_appearance");p.expect("nc:messages_extra");
 p.open("chat","menus");p.expect("chats:menus");
 for(String route:new String[]{"media","stickers"}){p.open("chat",route);p.expect("chats:"+route);for(String source:new String[]{"ng","nc","nx"})p.expect(source+":"+route+"_extra");}
 String[][] special={{"glare","GlareSettingsSection"},{"members","MemberLensSettingsSection"},{"conversion","InlineConversionSettingsSection"},{"animations","MessageAnimationsActivity"}};
 for(String[] c:special){p.open("chat",c[0]);if(!p.rows.equals(List.of(c[1])))throw new AssertionError("wrong special editor");}
 for(String[] c:new String[][]{{"general","general_behavior"},{"network","general_network"},{"notifications","general_notifications"},{"maps","general_maps"},{"profile","profile"},{"archive","archive"}}){p.open("universal",c[0]);p.expect("general:"+c[1]);}
 for(String route:new String[]{"fonts","effects"}){p.open("universal",route);p.expect("appearance:"+route);}
 p.open("universal","launcher");p.expect("SignatureLauncherSettingsActivity");
 p.open("universal","advanced");p.expect("other:advanced");p.expect("ng:advanced_extra");p.expect("nx:advanced_extra");
 p.open("universal","extras");p.expect("ng:general_extra|appearance_extra");
 p.open("navigation","tabs");p.expect("BottomTabsSettingsActivity");p.open("navigation","controls");p.expect("NativeControls");
 p.open("navigation","gestures");p.expect("chats:gestures");p.open("navigation","extras");p.expect("ng:navigation_extra");p.expect("nx:navigation_extra");
 p.open("ayu","ghost");p.expect("GhostModeActivity");for(String route:new String[]{"privacy","saving","tools","maintenance"}){p.open("ayu",route);p.expect("ayu:ayu_"+route);}
 p.open("plugins","translation");p.expect("general:translation_options");
 }}'''.replace('BODY', body)
    files['Probe.java'] = source
    files['org/telegram/messenger/R.java'] = resources(body)
    probe(tmp_path, files, [])


def test_restoring_removed_effect_section_returns_home_overview(tmp_path):
    plan = (S / 'CompactSettingsPlan.java').read_text()
    restore = method((S / 'SignatureDirectSettingsActivity.java').read_text(), 'public void restoreSelfArgs(').replace('@Override ', '')
    files = {
        'app/flexygram/settings/signature/CompactSettingsPlan.java': plan,
        'org/telegram/messenger/R.java': resources(plan),
        'app/flexygram/settings/signature/RestoreProbe.java': '''package app.flexygram.settings.signature;
class Bundle{java.util.Map<String,String>values=new java.util.HashMap<>();Object scroll=new Object();String getString(String k,String d){return values.getOrDefault(k,d);}Object getParcelable(String k){return scroll;}}
class Settings3Registry{static void entry(String value){if(!value.equals("home")&&!value.equals("chat"))throw new IllegalArgumentException();}}
class NativeScreen{int restores;public void restoreSelfArgs(Bundle b){restores++;}}
public class RestoreProbe extends NativeScreen{String category,segment;Object scrollState;
RESTORE
public static void main(String[]args){RestoreProbe screen=new RestoreProbe();Bundle state=new Bundle();
state.values.put("settings3Category","home");state.values.put("settings3Segment","motion");screen.restoreSelfArgs(state);
if(!screen.category.equals("home")||!screen.segment.isEmpty()||screen.scrollState!=state.scroll||screen.restores!=1)throw new AssertionError("retired section was not restored safely");
for(String[]c:new String[][]{{"home","list"},{"home","pills"},{"chat","animations"}}){state.values.put("settings3Category",c[0]);state.values.put("settings3Segment",c[1]);screen.restoreSelfArgs(state);if(!screen.category.equals(c[0])||!screen.segment.equals(c[1])||screen.scrollState!=state.scroll)throw new AssertionError("retained state changed");}
}}
'''.replace('RESTORE', restore),
        'Probe.java': 'public class Probe{public static void main(String[]args){app.flexygram.settings.signature.RestoreProbe.main(args);}}',
    }
    probe(tmp_path, files, [])


def test_icons_are_distinct_real_assets_and_localization_is_complete():
    plan = (S / 'CompactSettingsPlan.java').read_text()
    direct = (S / 'SignatureDirectSettingsActivity.java').read_text()
    overview = method(direct, 'private void overview()')
    # Compare actual packaged image contents, not merely aliases with different names.
    blocks = dict(re.findall(r'private static final Page\[\] (\w+)=\{(.*?)\n    \};', plan, re.S))
    for category, block in blocks.items():
        specialized = re.search(r'if\(category.equals\("'+category.lower()+r'"\)\)links\((.*?);', overview)
        text = block + (specialized[1] if specialized else "")
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


def test_system_partition_preserves_every_general_control_and_group_children(tmp_path):
    policy = (S/'Settings2Policy.java').read_text()
    probe(tmp_path, {
        'app/flexygram/settings/signature/Settings2Policy.java': policy,
        'Probe.java': '''import app.flexygram.settings.signature.Settings2Policy;public class Probe{public static void main(String[]args){
 String[] parts={"general_behavior","general_network","general_notifications","general_maps"};
 for(var entry:Settings2Policy.inventory().entrySet())if(entry.getKey().startsWith("general:")&&entry.getValue().equals("general")){
  String key=entry.getKey().substring(8);int owners=0;
  for(String part:parts){var rows=new Settings2Policy.Rows("general",part);boolean accepted=rows.named(key);if(accepted)owners++;if(rows.anonymous()!=accepted)throw new AssertionError("orphan child: "+key);}
  if(owners!=1||!new Settings2Policy.Rows("general","general").named(key))throw new AssertionError("lost or duplicated: "+key);
 }
 if(!Settings2Policy.matches("general","general_network","DnsType")||!Settings2Policy.matches("general","general_network","CustomDoH"))throw new AssertionError("network aliases");
 if(Settings2Policy.matches("general","general_notifications","SaveToChatSubfolder"))throw new AssertionError("storage moved");
 var saving=new Settings2Policy.Rows("ayu","ayu_saving");if(!saving.named("MessageSavingSaveMedia")||!saving.anonymous())throw new AssertionError("media group lost");if(saving.named("ayuDangerHeader")||saving.anonymous())throw new AssertionError("destructive controls leaked");
 if(!Settings2Policy.matches("ayu","ayu_tools","databaseImport")||!Settings2Policy.matches("ayu","ayu_maintenance","ayuClearDatabase"))throw new AssertionError("database controls lost");
 }}'''}, [])


def test_every_ayu_named_control_has_one_section_and_callbacks_are_unchanged():
    # Resolve real ConfigItem keys from Kotlin, so changing a key cannot silently
    # remove an existing toggle from the new filtered section.
    ayu = (JAVA/'app/exteraless/settings/OpenExteraAyuMomentsActivity.java').read_text()
    rows = method(ayu,'protected void updateRows()')
    kotlin = (ROOT/'TMessagesProj/src/main/kotlin/xyz/nextalone/nagram/NaConfig.kt').read_text()
    keys = re.findall(r'addRow\("(\w+)"',rows)
    for getter in re.findall(r'addRow\(NaConfig.INSTANCE.get(\w+)\(\).getKey\(\)\)',rows):
        name = getter[0].lower()+getter[1:]
        match = re.search(r'val '+name+r'\s*=\s*addConfig\(\s*"(\w+)"',kotlin)
        assert match, name
        keys.append(match[1])
    policy = (S/'Settings2Policy.java').read_text()
    for key in keys:
        assert len(re.findall(r'own\("ayu:'+key+r'","ayu_\w+"\)',policy))==1,key
    # All changes stay in the composite host; database transfer/confirmation
    # callbacks, which include privacy-sensitive actions, are reused verbatim.
    import subprocess
    assert ayu == subprocess.check_output(['git','show','9037e41cf:TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraAyuMomentsActivity.java'],cwd=ROOT,text=True)


def test_all_root_categories_have_compact_or_already_short_destinations():
    plan = (S/'CompactSettingsPlan.java').read_text()
    registered = re.findall(r'new Entry\("(\w+)"',(S/'Settings3Registry.java').read_text())
    assert set(registered)=={'home','chat','universal','navigation','ayu','plugins','files','flexyfiles','studio','about'}
    for category in set(registered)-{'files','flexyfiles','studio','about'}:
        assert 'case "'+category+'":return '+category.upper()+'.clone()' in plan
    for category, path, keys in [
        ('flexyfiles',S/'SignatureFlexyFilesActivity.java',['flexyfilesEnabled','flexyfilesHelp']),
        ('studio',JAVA/'app/flexygram/studio/FlexyStudioActivity.java',['flexystudioExport','flexystudioImport','flexystudioShare'])]:
        assert re.findall(r'addRow\("(\w+)"',method(path.read_text(),'protected void updateRows()'))==keys,category
    policy=(S/'Settings2Policy.java').read_text()
    assert set(re.findall(r'own\("general:(\w+)", "files"\)',policy))=={'settings2FilesHeader','flexyfilesEnabled','flexyfilesHelp','savePath','saveToChatSubfolder','storageHeader'}


def test_search_and_old_routes_reach_exact_sections_in_all_categories(tmp_path):
    registry = (S/'Settings3Registry.java').read_text()
    plan = (S/'CompactSettingsPlan.java').read_text()
    files={
        'org/telegram/messenger/R.java':resources(registry,plan),
        'org/telegram/ui/ActionBar/BaseFragment.java':'package org.telegram.ui.ActionBar;public class BaseFragment{}',
        'app/flexygram/settings/signature/Settings3Registry.java':registry,
        'app/flexygram/settings/signature/CompactSettingsPlan.java':plan,
        'app/flexygram/settings/signature/Settings2Policy.java':(S/'Settings2Policy.java').read_text(),
        'tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java':'''package tw.nekomimi.nekogram.settings;public class BaseNekoSettingsActivity extends org.telegram.ui.ActionBar.BaseFragment{public String route;public String getSignatureSettingsRoute(){return route;}public void useSignatureSettingsPage(String source,String route,int title){this.route=route;}}''',
        'tw/nekomimi/nekogram/settings/BaseNekoXSettingsActivity.java':'''package tw.nekomimi.nekogram.settings;public class BaseNekoXSettingsActivity extends org.telegram.ui.ActionBar.BaseFragment{public String getSignatureSettingsRoute(){return "general_extra";}}''',
        'app/flexygram/settings/signature/SignatureLegacyExtras.java':'''package app.flexygram.settings.signature;public class SignatureLegacyExtras{public static String canonicalRouteForKey(String key){return null;}public static String categoryForKey(String key){return "universal";}public static String routeForKey(String key){return "appearance_extra";}}''',
        'app/flexygram/settings/signature/SignatureSettingsRegistry.java':'package app.flexygram.settings.signature;public class SignatureSettingsRegistry{public static org.telegram.ui.ActionBar.BaseFragment open(String route){return Settings3Registry.openRoute(route);}}',
        'app/flexygram/settings/signature/SignatureDirectSettingsActivity.java':'''package app.flexygram.settings.signature;public class SignatureDirectSettingsActivity extends tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity{public String category,segment;public SignatureDirectSettingsActivity(String c){category=c;segment="";}public SignatureDirectSettingsActivity(String c,String s){category=c;segment=s;}}''',
    }
    names=set(re.findall(r'(?:new |instanceof )((?:app|tw)\.[\w.]+)',registry))
    names.update(['app.flexygram.settings.signature.SignatureFlexyFilesActivity','app.flexygram.settings.signature.SignatureLauncherSettingsActivity'])
    for cls in names:
        path=cls.replace('.','/')+'.java'
        if path in files:
            continue
        package,name=cls.rsplit('.',1)
        files[path]='package '+package+';public class '+name+' extends tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity{}'
    files['Probe.java']='''import app.flexygram.settings.signature.*;import org.telegram.ui.ActionBar.BaseFragment;
public class Probe{
 static void expect(BaseFragment f,String category,String segment){if(!(f instanceof SignatureDirectSettingsActivity))throw new AssertionError("not a section");var page=(SignatureDirectSettingsActivity)f;if(!category.equals(page.category)||!segment.equals(page.segment))throw new AssertionError(page.category+":"+page.segment+" expected "+category+":"+segment);}
 public static void main(String[]args){
 var general=new app.exteraless.settings.OpenExteraGeneralActivity();general.route="general";
 for(String[] c:new String[][]{{"DnsType","network"},{"CustomDoH","network"},{"pushStatus","notifications"},{"batteryOptimization","notifications"},{"mapPreview","maps"},{"formatTimeWithSeconds","general"}})expect(Settings3Registry.searchTarget(general,c[0]),"universal",c[1]);
 general.route="general_network";expect(Settings3Registry.searchTarget(general,"IPv6"),"universal","network");
 expect(Settings3Registry.openRoute("profile"),"universal","profile");expect(Settings3Registry.openRoute("fonts"),"universal","fonts");expect(Settings3Registry.openRoute("general_extra_ng"),"universal","extras");expect(Settings3Registry.openRoute("navigation_extra_nx"),"navigation","extras");
 expect(Settings3Registry.searchTarget(new app.flexygram.navigation.BottomTabsSettingsActivity(),"anything"),"navigation","tabs");
 var ayu=new app.exteraless.settings.OpenExteraAyuMomentsActivity();for(String[] c:new String[][]{{"AskBeforeOpeningStory","privacy"},{"EnableSaveDeletedMessages","saving"},{"databaseImport","tools"},{"ayuClearDatabase","maintenance"}})expect(Settings3Registry.searchTarget(ayu,c[0]),"ayu",c[1]);
 ayu.route="ayu_tools";expect(Settings3Registry.searchTarget(ayu,"databaseExport"),"ayu","tools");
 expect(Settings3Registry.searchTarget(new app.flexygram.settings.signature.SignatureLauncherSettingsActivity(),"settings2Launcher"),"universal","launcher");
 expect(Settings3Registry.searchTarget(new tw.nekomimi.nekogram.settings.BaseNekoXSettingsActivity(),"SwitchStyle"),"universal","extras");
 }}'''
    probe(tmp_path,files,[])
