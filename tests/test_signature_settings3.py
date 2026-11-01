"""Signature Settings 3.0 source/ownership regressions; not full APK or device acceptance."""
import hashlib,json,re,subprocess,tempfile,xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT/'TMessagesProj/src/main/java'
S=JAVA/'app/flexygram/settings/signature'
BASE='3c7a20a229d425c8f3b5ea1740ccb6d8b3361fea'
def source(path):return (JAVA/path).read_text()
def original(path):return subprocess.check_output(['git','show',BASE+':TMessagesProj/src/main/java/'+path],cwd=ROOT,text=True)
def method(text,anchor):
 start=text.index(anchor);end=text.index('{',start)+1;level=1;i=end
 while level:
  level+=(text[i]=='{')-(text[i]=='}');i+=1
 return text[start:i]
def test_exact_root_order_and_single_vector_family():
 text=(S/'Settings3Registry.java').read_text()
 rows=re.findall(r'new Entry\("(\w+)",R.string.Settings3Group_(\w+),R.string.Settings3_\w+,R.string.Settings3Desc_\w+,R.drawable.(\w+)\)',text)
 assert [r[0]for r in rows]==['chat','home','universal','ayu','plugins','flexyfiles','files','navigation','studio','about']
 assert [r[1]for r in rows]==['personal']*3+['functions']*6+['information']
 assert all(icon.startswith('settings3_')for _,_,icon in rows)
 assert rows[1][2]==rows[8][2]=='settings3_stack'
def test_root_no_colored_tiles_or_intermediate_registry():
 cell=(S/'Settings2Cell.java').read_text();root=(S/'SignatureSettingsActivity.java').read_text()
 assert 'GradientDrawable' not in cell and 'Color.WHITE' not in cell
 assert 'icon.setBackground(null)' in cell
 assert 'icon.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider))' in cell
 assert 'Settings3Registry.all()' in root and 'SignatureSettingsRegistry.children' not in root
 assert 'Theme.key_windowBackgroundWhiteBlackText' in source('tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java')
def test_direct_chat_preview_order_and_no_nested_scroll_views():
 text=method((S/'SignatureDirectSettingsActivity.java').read_text(),'private void build()')
 chat=text[text.index('case "chat":'):text.index('case "home":')]
 assert chat.index('new app.flexygram.header.HeaderSettingsActivity')<chat.index('new app.flexygram.bubbles.BubbleSettingsActivity')<chat.index('new app.flexygram.composer.FlexyComposerSettingsActivity')
 assert 'links(' not in chat
 for cls in ['BaseNekoSettingsActivity','BaseNekoXSettingsActivity']:
  bridge=method(source('tw/nekomimi/nekogram/settings/'+cls+'.java'),'prepareSettings3(')
  assert 'createView(' not in bridge and 'new Recycler' not in bridge and 'setAdapter(' not in bridge
 assert 'setItemAnimator(null)' in (S/'SignatureDirectSettingsActivity.java').read_text()
def test_original_editor_click_logic_is_unchanged():
 for path in ['app/flexygram/header/HeaderSettingsActivity.java','app/flexygram/bubbles/BubbleSettingsActivity.java','app/flexygram/composer/FlexyComposerSettingsActivity.java','app/flexygram/navigation/BottomTabsSettingsActivity.java']:
  assert method(source(path),'protected void onItemClick(')==method(original(path),'protected void onItemClick(')
 # The original sticker reset is surfaced as a direct row, with the rest of its click handler unchanged.
 path='app/exteraless/settings/OpenExteraChatsActivity.java'
 new=method(source(path),'protected void onItemClick(').replace('\n        if(position==settings3ResetStickerRow && position>=0){resetStickerSize();return;}','')
 # Smart Previews 2 replaces only the old visual picker with the canonical Home section.
 expected=method(original(path),'protected void onItemClick(')
 start=expected.index('        } else if (position == smartPreviewsRow) {')
 end=expected.index('        } else if (position == flexyContextPanelRow)',start)
 expected=expected[:start]+expected[end:]
 assert new==expected
 assert 'smartPreviewsRow = addRow(' not in source(path)
 assert 'new app.flexygram.home.SmartPreviewsSettingsActivity()' in source('app/flexygram/settings/signature/SignatureDirectSettingsActivity.java')
def test_original_extra_callbacks_are_reused_without_logic_changes():
 for cls in ['NekoGeneralSettingsActivity','NekoChatSettingsActivity','NekoExperimentalSettingsActivity']:
  path='tw/nekomimi/nekogram/settings/'+cls+'.java';new=source(path);old=original(path)
  anchor='cellGroup.callBackSettingsChanged = (key, newValue) ->'
  assert method(new,anchor)==method(old,anchor)
  assert 'createSettings3Adapter(context)' in method(new,'public View createView(')
def test_position_lifecycle_and_hidden_controls_are_preserved():
 for path in ['app/flexygram/header/HeaderSettingsActivity.java','app/flexygram/bubbles/BubbleSettingsActivity.java','app/flexygram/navigation/BottomTabsSettingsActivity.java','app/flexygram/bubbles/interaction/BubbleInteractionSettingsActivity.java','app/flexygram/bubbles/deletion/MessageAnimationsActivity.java']:
  assert 'getAdapterPosition()' not in method(source(path),'boolean isEnabled(')
 text=(S/'SignatureDirectSettingsActivity.java').read_text()
 assert 'PasscodeHelper.isSettingsHidden()' in text
 assert text.index('listView.setAdapter(null)')<text.index('combined.close()')
 assert 'onActivityResultFragment' in text and 'onRequestPermissionsResultFragment' in text
 assert 'settings3Scroll' in text
 assert method(text,'public View createView(').index('scrollState=layoutManager.onSaveInstanceState()')<method(text,'public View createView(').index('release()')
 for cls in ['BaseNekoSettingsActivity','BaseNekoXSettingsActivity']:
  body=method(source('tw/nekomimi/nekogram/settings/'+cls+'.java'),'void releaseSettings3()')
  assert 'onFragmentDestroy()' in body and 'listView=null' in body and 'fragmentView=null' in body
 assert 'unregisterAdapterDataObserver' in (S/'NativeSectionsAdapter.java').read_text()
def test_flexyfiles_and_storage_have_distinct_owners():
 registry=(S/'Settings3Registry.java').read_text()
 assert 'new SignatureFlexyFilesActivity()' in registry
 assert 'f.useSignatureSettingsPage("general","files"' in registry
 assert 'FlexyFiles.enabled(!app.flexygram.files.FlexyFiles.enabled())' in (S/'SignatureFlexyFilesActivity.java').read_text()
 assert 'case "flexyfilesEnabled":case "flexyfilesHelp":return Settings3Registry.open("flexyfiles")' in (S/'SignatureSettingsRegistry.java').read_text()
 assert 'ghostRow = isSettings3Embedded() ? -1' in source('app/exteraless/settings/OpenExteraAyuMomentsActivity.java')
def test_no_new_settings_store_or_idle_work_in_new_components():
 for name in ['NativeSectionsAdapter','NativeSettingsSection','Settings3LinksSection','Settings3Registry','SignatureDirectSettingsActivity','SignatureFlexyFilesActivity']:
  text=(S/(name+'.java')).read_text()
  for forbidden in ['getSharedPreferences(','.putBoolean(','.putInt(','new Thread(','postDelayed(','postInvalidateOnAnimation(','RenderEffect','setDrawBlurBackground','rebuildAllFragmentViews']:
   assert forbidden not in text,(name,forbidden)
def test_localization_license_and_vector_provenance():
 sets=[]
 for locale in ['values','values-es','values-ru']:
  root=E.parse(ROOT/'TMessagesProj/src/main/res'/locale/'flexy_settings3.xml').getroot();names=[x.get('name')for x in root]
  assert len(names)==len(set(names));sets.append(set(names))
 assert sets[0]==sets[1]==sets[2]
 third=ROOT/'third_party/remixicon/settings3'
 assert 'Apache License' in (third/'LICENSE').read_text()
 for item in json.loads((third/'sources.json').read_text()):
  assert hashlib.sha256((third/(item['name']+'.svg')).read_bytes()).hexdigest()==item['sha256']
  vector=E.parse(ROOT/'TMessagesProj/src/main/res/drawable'/('settings3_'+item['name']+'.xml')).getroot()
  assert vector.tag=='vector' and not any(x.tag=='gradient'for x in vector.iter())
 assert (ROOT/'TMessagesProj/src/main/assets/licenses/remixicon-apache-2.0.txt').read_bytes()==(third/'LICENSE').read_bytes()
def test_union_scope_real_java_contract():
 code='''import app.flexygram.settings.signature.*; public class Probe{public static void main(String[]x){var home=new Settings2Policy.Rows("appearance","chat_list|avatars|folders");if(!home.named("avatarCorners")||!home.anonymous())throw new AssertionError();var single=new Settings2Policy.Rows("appearance","fonts");if(single.named("avatarCorners"))throw new AssertionError();home.reset();if(home.anonymous())throw new AssertionError();var others=new Settings2Policy.Rows("other","advanced");if(others.named("ayuMoments"))throw new AssertionError();var stickers=new Settings2Policy.Rows("chats","stickers");if(!stickers.named("settings3StickerReset"))throw new AssertionError();}}'''
 with tempfile.TemporaryDirectory()as tmp:
  p=Path(tmp)/'Probe.java';p.write_text(code)
  subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(S/'Settings2Policy.java'),str(p)],check=True,capture_output=True)
  subprocess.run(['java','-cp',tmp,'Probe'],check=True,capture_output=True)

def test_navigation_simple_controls_are_direct_and_shared_with_original_editor():
 path='app/exteraless/settings/OpenExteraAppNavigationActivity.java';new=source(path);old=original(path)
 start=old.index('        if (id == ID_TABLET_MODE)',old.index('private void onItemClick(UItem'))
 end=old.index('        if (id == ID_ADD_DIVIDER)',start)
 expected=old[start:end].replace('showChoice(', 'showChoice(host,').replace('update();','changed.run();').replace('getParentActivity()', 'host.getParentActivity()').replace('getNotificationCenter()', 'host.getNotificationCenter()').replace('getParentLayout()', 'host.getParentLayout()').replace('            return;','            return true;')
 assert expected in method(new,'private static boolean applyNativeControl(')
 assert 'if(!menuOnly)' in method(new,'private void fillItems(')
 assert 'OpenExteraAppNavigationActivity.NativeControls()' in (S/'SignatureDirectSettingsActivity.java').read_text()
 assert 'OpenExteraAppNavigationActivity(true)' in (S/'Settings3LinksSection.java').read_text()

def test_global_widgets_are_not_placed_in_home_and_search_uses_canonical_target():
 text=(S/'SignatureLegacyExtras.java').read_text()
 for key in ['SwitchStyle','SliderStyle','IconReplacements','CenterActionBarTitleType']:assert '"'+key+'"' in method(text,'public static String categoryForKey(String key,String source)')
 page=(S/'SignatureDirectSettingsActivity.java').read_text()
 assert 'category.equals(SignatureLegacyExtras.categoryForKey(' in page
 assert '"general_extra","advanced_extra","appearance_extra"' in page
 helper=source('tw/nekomimi/nekogram/helpers/SettingsHelper.java')
 assert helper.count('Settings3Registry.searchTarget(fragment,key)')==2
