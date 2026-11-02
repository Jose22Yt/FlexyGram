"""Host and source regressions. No claim of a complete Android build or physical reproduction."""
from pathlib import Path
import re, subprocess, tempfile, xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
J = ROOT/'TMessagesProj/src/main/java'
def src(path): return (J/path).read_text()

def test_glass_counter_and_single_foreground_outline():
    s = src('app/flexygram/header/SignatureChatHeader.java')
    glass = s[s.index('nativeGlassDrawn = bar.drawSignatureNativeGlass'):]
    assert glass.index('drawUnread(canvas);') < glass.index('return;')
    assert 'if (!fusionActive() || nativeGlassDrawn) return;' in s
    assert 'Theme.dialogs_countTextPaint.setColor(previousColor)' in s
    assert 'geometry.countVisible = geometry.separateCount = false' not in s

def test_fusion_counter_geometry_executes_real_java_for_both_directions():
    code = '''import app.flexygram.header.fusion.SignatureFusionGeometry;
public class UnreadGeometryProbe {
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[] args){
  var g=new SignatureFusionGeometry.Layout(); Object back=g.back, badge=g.unread;
  int cases=0;
  for(float d:new float[]{1,1.5f,2,3})for(int w:new int[]{240,320,360,412,600})
   for(boolean rtl:new boolean[]{false,true})for(boolean call:new boolean[]{false,true})
    for(boolean portrait:new boolean[]{false,true})for(int mode=0;mode<3;mode++)for(int digits=0;digits<4;digits++){
     float number=digits*9*d, extra=number<=0||mode==0?0:mode==2?Math.max(28*d,number+8*d)+3*d:number+16*d;
     if(portrait)SignatureFusionGeometry.updatePortrait(g,w*d,d,rtl,call,extra);
     else SignatureFusionGeometry.update(g,w*d,d,rtl,call,extra);
     SignatureFusionGeometry.placeUnread(g,mode==0?0:number,mode,d);
     check(g.back==back&&g.unread==badge);check(g.back.height()==48*d);
     check(g.back.width()>=48*d);check(g.more.width()==48*d);if(call)check(g.call.width()==48*d);
     check(g.separateUnread==(mode==2&&number>0));
     if(g.separateUnread){check(g.unread.height()>=28*d);check(rtl?g.unread.right<g.backVisual.left:g.unread.left>g.backVisual.right);}
     if(g.fits){check(g.text.width()>=48*d);check(rtl?g.center.right<=g.back.left:g.center.left>=g.back.right);}
     cases++;
    }
  SignatureFusionGeometry.update(g,412,1,false,true);check(!g.separateUnread);check(g.unread.width()==0);
  System.out.println("PASS "+cases+" counter geometries; no Android runtime");
 }}'''
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'UnreadGeometryProbe.java';p.write_text(code)
        folder=J/'app/flexygram/header/fusion'
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(folder/'SignatureFusionGeometry.java'),str(folder/'SignatureFusionFade.java'),str(p)],check=True,capture_output=True,text=True)
        result=subprocess.check_output(['java','-cp',tmp,'UnreadGeometryProbe'],text=True)
        assert 'PASS 1920' in result

def test_native_glass_source_can_survive_explicit_setting_changes():
    chat=src('org/telegram/ui/ChatActivity.java')
    constructor=chat[chat.index('public ChatActivity(Bundle args)'):chat.index('navbarContentDrawableFactory = new',chat.index('public ChatActivity(Bundle args)'))]
    assert 'if (LiteMode.isEnabled(LiteMode.FLAG_LIQUID_GLASS))' not in constructor
    assert 'SharedConfig.chatBlurEnabled()' in constructor  # keep master blur/capability gate
    lite=src('org/telegram/messenger/LiteMode.java')
    setter=lite[lite.index('public static void setAllFlags'):lite.index('public static void updatePresets')]
    assert 'previous != flags' in setter and 'dispatchPowerPolicyListeners' in setter
    assert 'onPowerSaverAppliedListeners.contains(callback)' in lite
    bar=src('org/telegram/ui/ActionBar/ActionBar.java')
    assert '!canvas.isHardwareAccelerated()' in bar and '!org.telegram.messenger.SharedConfig.chatBlurEnabled()' in bar
    assert 'signatureGlassUnread.draw(canvas)' in bar
    assert 'if (signatureUnreadGlassRadius == radius) return;' in bar
    assert 'if (glassRadius != radius)' in src('org/telegram/ui/MainTabsLayout.java')

def test_launcher_nested_selector_remains_touch_enabled_and_errors_do_not_select():
    assert 'isEnabled(RecyclerView.ViewHolder h){return true;}' in src('app/flexygram/settings/signature/SignatureLauncherSettingsActivity.java')
    recycler=src('org/telegram/ui/Components/RecyclerListView.java')
    assert 'child.setEnabled(((SelectionAdapter) getAdapter()).isEnabled(holder))' in recycler
    icons=src('org/telegram/ui/Cells/AppIconsSelectorCell.java')
    assert icons.index('catch (IllegalArgumentException | SecurityException rejected)')<icons.index('holderView.setSelected(true, true)')
    controller=src('org/telegram/ui/LauncherIconController.java')
    assert 'pm.setComponentEnabledSettings(changes)' in controller and 'PackageManager.DONT_KILL_APP' in controller
    manifest=ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml')
    ns='{http://schemas.android.com/apk/res/android}'
    aliases={a.get(ns+'name'):a for a in manifest.findall('./application/activity-alias')}
    for key in re.findall(r'^        [A-Z_]+\("(\w+)"',controller,re.M):
        alias=aliases['org.telegram.messenger.'+key]
        assert alias.get(ns+'exported')=='true'
        assert alias.get(ns+'targetActivity')=='org.telegram.ui.LaunchActivity'
    enabled=[k for k,a in aliases.items() if a.get(ns+'enabled')=='true']
    assert enabled==['org.telegram.messenger.FlexyNeonIcon']

def test_dock_is_a_clipped_native_rendernode_not_a_translucency_simulation():
    host=src('org/telegram/ui/MainTabsActivity.java')
    assert 'new BlurredBackgroundSourceRenderNode(iBlur3SourceColor)' in host
    assert 'iBlur3SourceTabGlass.setBlur(dp(14))' in host
    assert 'tabsViewWrapper.getMeasuredHeight()' in host
    assert 'canvas.clipRect(0,0,tabsViewWrapper.getWidth(),tabsViewWrapper.getHeight())' in host
    assert 'viewPager.draw(canvas)' in host and 'child == viewPager && SharedConfig.chatBlurEnabled()' in host
    assert 'hash.add(tabsGlassRevision)' in host
    assert 'Bitmap.createBitmap' not in host
    assert 'postInvalidateOnAnimation' not in host
    layout=src('org/telegram/ui/MainTabsLayout.java')
    assert 'canvas.isHardwareAccelerated()' in layout and 'glassBackground.draw(canvas)' in layout
    assert 'surface.draw(canvas)' in layout and 'drawable.setCallback(this)' in layout

def test_search_is_independent_and_removes_only_the_duplicate_destination():
    config=src('app/flexygram/navigation/LiquidNavigationConfig.java')
    assert 'p.getBoolean("separate_search", false)' in config
    assert '.filter(id -> id != LiquidNavigationDestinations.SEARCH)' in config
    host=src('org/telegram/ui/MainTabsActivity.java')
    assert 'tabsViewWrapper.addView(separateSearchButton' in host
    assert 'separateSearchButton.setOnClickListener(v -> openChatsSearch())' in host
    assert 'separateSearchButton.setContentDescription' in host
    assert 'dockParams.rightMargin = LocaleController.isRTL ? 0 : reservedSearch' in host
    assert 'separateSearchButton.setVisibility(separate ? View.VISIBLE : View.GONE)' in host
    dialogs=src('org/telegram/ui/DialogsActivity.java')
    assert 'actionBar.isSearchFieldVisible()) return' in dialogs
    assert 'separateSearchHidTopItem' in dialogs

def test_theme_refreshes_retained_tabs_and_original_glare_key_is_preserved():
    host=src('org/telegram/ui/MainTabsActivity.java')
    assert 'AndroidUtilities.cancelRunOnUIThread(refreshTabsTheme)' in host
    assert 'AndroidUtilities.runOnUIThread(refreshTabsTheme)' in host
    assert 'dockGlassColors.updateColors()' in host
    filters=src('org/telegram/ui/Components/FilterTabsView.java')
    update=filters[filters.index('    public void updateColors()'):filters.index('    protected void onMeasure',filters.index('    public void updateColors()'))]
    assert 'selectorDrawable.setColor' in update and 'Theme.getColor(selectorColorKey, resourcesProvider)' in update
    for path in ['TMessagesProj/src/main/kotlin/app/exteraless/appearance/AppearanceConfig.kt','TMessagesProj/src/main/java/app/flexygram/effects/GlareMode.java','TMessagesProj/src/main/java/org/telegram/ui/Components/blur3/StaticOutlineStroke.java']:
        assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show','bf96667efac14d0cbbf6677471890a366c3ef3c0:'+path],cwd=ROOT)

def test_transformed_reaction_preview_does_not_use_source_row_clip():
    chat=src('org/telegram/ui/ChatActivity.java')
    assert 'if (!movingSelectedPreview && (cell == null || !cell.getTransitionParams().animateBackgroundBoundsInner))' in chat
    # Reproduces the coordinate error without claiming a physical screenshot match:
    # source row y=230, transformed preview y=160: the original clip removed 70px at its top.
    parent_top,source_top,shift,height=0,230,-70,400
    old_clip=max(parent_top,source_top);preview_top=source_top+shift
    assert old_clip-preview_top==70
    assert max(parent_top,preview_top)==preview_top
    assert 'canvas.clipRect(viewClipLeft, viewClipTop, viewClipRight, viewClipBottom)' in chat
    assert 'selectedBubbleMotion.spatialOffset' in chat  # original motion remains

def test_private_references_are_not_tracked_and_new_strings_match():
    tracked=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True)
    assert not any(name in tracked for name in ['51721.jpg','51722.jpg','51724.png','51726.jpg','51728.jpg','referencias_privadas/'])
    names=[]
    for folder in ['values','values-es','values-ru']:
        values=list(ET.parse(ROOT/'TMessagesProj/src/main/res'/folder/'flexy_port_fixes.xml').getroot())
        assert all(v.text for v in values)
        names.append({v.get('name') for v in values})
    assert names[0]==names[1]==names[2]

def test_actual_policy_setter_and_listener_dispatch_allow_detach_during_callback():
    source=src('org/telegram/messenger/LiteMode.java')
    def method(anchor):
        a=source.index(anchor);i=source.index('{',a)+1;level=1
        while level:
            level+=(source[i]=='{')-(source[i]=='}');i+=1
        return source[a:i]
    code='''import java.util.*;
public class PolicyProbe {
 static class Utilities{interface Callback<T>{void run(T value);}}
 static class AndroidUtilities{static void runOnUIThread(Runnable r){r.run();}}
 static HashSet<Utilities.Callback<Boolean>> onPowerSaverAppliedListeners=new HashSet<>();
 static int value,writes,updates;static boolean lastPowerSaverApplied;
 static int getValue(boolean ignored){return value;}static void savePreference(){writes++;}
 static void onFlagsUpdate(int a,int b){updates++;}
 '''+method('public static void setAllFlags(')+method('private static void dispatchPowerPolicyListeners(')+'''
 public static void main(String[]args){
  Utilities.Callback<Boolean> self=new Utilities.Callback<>(){public void run(Boolean b){onPowerSaverAppliedListeners.remove(this);}};
  int[] calls={0};Utilities.Callback<Boolean> alive=b->calls[0]++;
  onPowerSaverAppliedListeners.add(self);onPowerSaverAppliedListeners.add(alive);
  setAllFlags(7);if(calls[0]!=1||updates!=1||value!=7)throw new AssertionError();
  setAllFlags(7);if(calls[0]!=1||updates!=1)throw new AssertionError();
  setAllFlags(0);if(calls[0]!=2||updates!=2||value!=0)throw new AssertionError();
  System.out.println("PASS changed-only dispatch and listener self-removal; UI host double");
 }}'''
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'PolicyProbe.java';path.write_text(code)
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(path)],check=True,capture_output=True,text=True)
        assert 'PASS' in subprocess.check_output(['java','-cp',tmp,'PolicyProbe'],text=True)
