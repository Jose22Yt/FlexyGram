"""Regressions from the supplied Home/header screenshots. No device or FPS claims."""
from test_render_work_reuse import ROOT, JAVA, probe
from test_composer_layout import method
import importlib.util
import re
import xml.etree.ElementTree as ET


def test_signature_actions_do_not_use_the_obsolete_native_glass_touch_mask(tmp_path):
    source=(JAVA/'org/telegram/ui/ActionBar/ActionBar.java').read_text()
    dispatch=method(source,'public boolean dispatchTouchEvent(MotionEvent ev)')
    probe(tmp_path,{'Probe.java':'''class MotionEvent{static final int ACTION_DOWN=0;int action;int getAction(){return action;}float getX(){return 200;}float getY(){return 20;}}
class View{}class Base{int dispatches;public boolean dispatchTouchEvent(MotionEvent e){dispatches++;return true;}}
public class Probe extends Base{
 static class Header{boolean enabled;boolean active(){return enabled;}}
 static class Bounds{boolean contains(int x,int y){return false;}}
 static class Glass{Bounds getBounds(){return new Bounds();}}
 View chatAvatarContainer=new View();boolean glassMode=true;Header signatureHeader=new Header();
 Glass glassDrawable,glassDrawableBack,glassDrawableMenu;
 static View findChildUnder(Probe p,int x,int y,View exclude){return null;}
 DISPATCH
 public static void main(String[]a){Probe p=new Probe();MotionEvent down=new MotionEvent();
 if(p.dispatchTouchEvent(down)||p.dispatches!=0)throw new AssertionError("classic glass mask changed");
 p.signatureHeader.enabled=true;
 if(!p.dispatchTouchEvent(down)||p.dispatches!=1)throw new AssertionError("signature action discarded");
 p.signatureHeader.enabled=false;
 if(p.dispatchTouchEvent(down)||p.dispatches!=1)throw new AssertionError("stale active state");
 p.glassMode=false;if(!p.dispatchTouchEvent(down)||p.dispatches!=2)throw new AssertionError();
 }}'''.replace('DISPATCH',dispatch)})


def test_shortcut_only_folder_keeps_native_ids_without_a_visible_gap(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/FilterTabsView.java').read_text()
    methods='\n'.join(method(source,sig) for sig in [
        'private int tabTotalWidth(', 'public void setShortcutOnly(', 'private void updateTabsWidths('])
    probe(tmp_path,{'Probe.java':'''import java.util.*;public class Probe{
 static class Sparse{Map<Integer,Integer> data=new HashMap<>();int get(int k,int d){return data.getOrDefault(k,d);}void put(int k,int v){data.put(k,v);}void clear(){data.clear();}}
 static class Tab{int id,counter,width;boolean shortcutOnly;Tab(int id,int w){this.id=id;width=w;}int getWidth(boolean store){return shortcutOnly?0:width;}}
 ArrayList<Tab> tabs=new ArrayList<>();Sparse idToPosition=new Sparse(),positionToX=new Sparse(),positionToWidth=new Sparse(),positionToCount=new Sparse();int allTabsWidth,additionalTabWidth=7,listViewPaddingH=4;
 int dp(float n){return Math.round(n);}float getTabPadding(){return 12;}
 Tab getTab(int position){return position<0||position>=tabs.size()?null:tabs.get(position);}
 METHODS
 public static void main(String[]args){Probe p=new Probe();
 for(int i=0;i<3;i++){p.tabs.add(new Tab(i,60+i*10));p.idToPosition.put(i,i);p.allTabsWidth+=60+i*10+12;}
 int width=p.allTabsWidth;p.setShortcutOnly(1);p.setShortcutOnly(1);p.setShortcutOnly(99);p.updateTabsWidths();
 if(p.tabs.size()!=3||p.idToPosition.get(2,-1)!=2||p.tabs.get(1).id!=1)throw new AssertionError("native indices changed");
 if(p.allTabsWidth!=width-82||p.positionToWidth.get(1,-1)!=0)throw new AssertionError("shortcut width counted");
 if(p.positionToX.get(1,-1)!=p.positionToX.get(2,-1))throw new AssertionError("visible gap after shortcut");
 if(p.tabs.get(0).shortcutOnly||p.tabs.get(2).shortcutOnly)throw new AssertionError("other folders hidden");
 }}'''.replace('METHODS',methods)})


def test_glossy_is_the_only_fresh_install_alias_and_remembered_default(tmp_path):
    android='{http://schemas.android.com/apk/res/android}'
    app=ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').getroot().find('application')
    enabled=[a for a in app.findall('activity-alias') if a.get(android+'enabled')=='true']
    assert len(enabled)==1 and enabled[0].get(android+'name')=='org.telegram.messenger.FlexyGlossyIcon'
    assert enabled[0].get(android+'icon')==app.get(android+'icon')=='@mipmap/ic_flexy_glossy'
    source=(JAVA/'org/telegram/ui/LauncherIconController.java').read_text()
    remembered=method(source,'public static LauncherIcon getRememberedIcon()')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 enum LauncherIcon{FLEX_GLOSSY,FLEX_NEON,BLUE}static LauncherIcon resolvedIcon;
 static class Context{static final int MODE_PRIVATE=0;String saved="";Context getSharedPreferences(String f,int m){return this;}String getString(String k,String d){return saved;}}
 static class ApplicationLoader{static Context applicationContext=new Context();}
 METHOD
 public static void main(String[]args){
 if(getRememberedIcon()!=LauncherIcon.FLEX_GLOSSY)throw new AssertionError();
 ApplicationLoader.applicationContext.saved="BLUE";if(getRememberedIcon()!=LauncherIcon.BLUE)throw new AssertionError("explicit selection lost");
 ApplicationLoader.applicationContext.saved="invalid";if(getRememberedIcon()!=LauncherIcon.FLEX_GLOSSY)throw new AssertionError();
 resolvedIcon=LauncherIcon.FLEX_NEON;if(getRememberedIcon()!=LauncherIcon.FLEX_NEON)throw new AssertionError("resolved override lost");
 }}'''.replace('METHOD',remembered)})


def test_settings_reuses_existing_divider_and_plain_chat_rows():
    setting=(JAVA/'app/flexygram/home/HomeStyleSettingsActivity.java').read_text()
    assert setting.index('styleRow=addRow(')<setting.index('dividerRow=addRow(')
    assert 'getHideDividers().setConfigBool' in setting and 'AppearanceConfig.invalidateDividerStyle()' in setting
    assert 'Theme.applyCommonTheme()' in setting
    rows=(JAVA/'org/telegram/ui/Cells/DialogCell.java').read_text()
    assert 'EssentialDialogPainter' not in rows and 'if (useSeparator)' in rows
    assert 'Theme.dividerPaint.setColor(Theme.getDividerColor(resourcesProvider))' in rows
    assert 'if (homeDivider) Theme.dividerPaint.setColor(dividerColor)' in rows
    native=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    assert 'Math.max(-getIdleSearchFieldHeight(), totalOffset - searchOffset)' in native
    chrome=(JAVA/'app/flexygram/home/IosHomeHeader.java').read_text()
    assert 'R.string.Edit' in chrome and 'IosOriginalAssets.HOME_COMPOSE' in chrome
    search=(JAVA/'app/flexygram/home/IosHomeSearch.java').read_text()
    assert 'R.string.Search' in search
    # The root shares the native search/action-mode progress; no second animator or per-frame hierarchy rebuild.
    animation=native[native.index('if(iosHomeHeader!=null){'):native.index('            super.dispatchDraw(canvas);',native.index('if(iosHomeHeader!=null){'))]
    assert all(token not in animation for token in ['requestLayout','addView','removeView','new ','measureText'])


def test_beta_preflight_accepts_current_beta_but_rejects_invalid_source_identity(tmp_path):
    spec=importlib.util.spec_from_file_location('current_beta_verifier',ROOT/'tools/beta_release/verify_beta_apk.py')
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    verifier.ROOT=tmp_path
    props=tmp_path/'gradle.properties'
    def check(package,name,code):
        props.write_text(f'APP_PACKAGE={package}\nBETA_VERSION_NAME={name}\nBETA_VERSION_CODE={code}\n')
        return verifier.expected_version()
    assert check('com.flexygram.messenger','1.0.0-beta.14',1303)==(1303,'1.0.0-beta.14')
    for package,name,code in [('other','1.0.0-beta.14',1303),('com.flexygram.messenger','alpha',1303),('com.flexygram.messenger','1.0.0-beta.0',1303),('com.flexygram.messenger','1.0.0-beta.14',1)]:
        try:check(package,name,code)
        except ValueError:pass
        else:raise AssertionError('invalid Beta identity/version accepted')


def test_positional_resource_fixes_preserve_real_formatter_output(tmp_path):
    import json
    fixture=json.loads((ROOT/'tests/fixtures/home14_resource_formats.json').read_text())
    before=[];after=[]
    for name,original in fixture.items():
        current={item.get('name'):item.text for item in ET.parse(ROOT/name).getroot().findall('string')}
        for key,value in original.items():
            before.append(value);after.append(current[key])
    assert len(before)==51
    probe(tmp_path,{'Probe.java':'''public class Probe{public static void main(String[]args){
 String[]before=BEFORE,after=AFTER;Object[]values=new Object[]{101,202,303,404,505,606};
 for(int i=0;i<before.length;i++){
 String old=String.format(java.util.Locale.ROOT,before[i],values),now=String.format(java.util.Locale.ROOT,after[i],values);
 if(!old.equals(now))throw new AssertionError("resource arguments changed: "+before[i]);
 }
 }}'''.replace('BEFORE','new String[]{'+','.join(json.dumps(v) for v in before)+'}').replace('AFTER','new String[]{'+','.join(json.dumps(v) for v in after)+'}')})


def test_dragging_pinned_chats_preserves_the_visible_saved_row(tmp_path):
    native=(JAVA/'org/telegram/ui/Adapters/DialogsAdapter.java').read_text()
    move=method(native,'public void moveDialogs(RecyclerListView recyclerView, int fromPosition, int toPosition)')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
class RecyclerListView{}class TLRPC{static class Dialog{long id;int pinnedNum;Dialog(long id,int n){this.id=id;pinnedNum=n;}}}
class MessagesController{static MessagesController instance=new MessagesController();static MessagesController getInstance(int a){return instance;}static class DialogFilter{Map<Long,Integer> pinnedDialogs=new HashMap<>();}DialogFilter[]selectedDialogFilter={new DialogFilter(),new DialogFilter()};}
public class Probe{
 static class Parent{ArrayList<TLRPC.Dialog> source=new ArrayList<>();
 ArrayList<TLRPC.Dialog> getDialogsArray(int a,int type,int folder,boolean frozen){return source;}
 ArrayList<TLRPC.Dialog> getControllerDialogsArray(int a,int type,int folder,boolean frozen){return source;}}
 Parent parentFragment=new Parent();int currentAccount,dialogsType,folderId;int fixPosition(int p){return p;}
 void updateList(Object o){}
 MOVE
 public static void main(String[]args){for(int type:new int[]{0,7,8}){
 Probe p=new Probe();p.dialogsType=type;TLRPC.Dialog first=new TLRPC.Dialog(10,3),saved=new TLRPC.Dialog(1,2),last=new TLRPC.Dialog(20,1);
 p.parentFragment.source.addAll(Arrays.asList(first,saved,last));
 if(type!=0){var pins=MessagesController.instance.selectedDialogFilter[type==8?1:0].pinnedDialogs;pins.put(10L,3);pins.put(1L,2);pins.put(20L,1);}
 p.moveDialogs(new RecyclerListView(),0,2);
 if(!p.parentFragment.source.equals(Arrays.asList(last,saved,first)))throw new AssertionError("controller order unchanged");
 var visible=p.parentFragment.getDialogsArray(0,type,0,false);
 if(visible.size()!=3||visible.get(0)!=last||visible.get(1)!=saved||visible.get(2)!=first)throw new AssertionError("drag reversed after refresh");
 if(saved.pinnedNum!=2)throw new AssertionError("saved changed");
 if(type==0&&(first.pinnedNum!=1||last.pinnedNum!=3))throw new AssertionError("pinned numbers not swapped");
 if(type!=0&&MessagesController.instance.selectedDialogFilter[type==8?1:0].pinnedDialogs.get(1L)!=2)throw new AssertionError("saved folder pin changed");
 }}
}'''.replace('MOVE',move)})
