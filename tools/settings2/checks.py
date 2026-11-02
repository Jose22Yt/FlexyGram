#!/usr/bin/env python3
"""Focused migration invariants; no accounts, private inputs, APK or runtime performance claims."""
import re,json,subprocess,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE='3c7a20a229d425c8f3b5ea1740ccb6d8b3361fea';J=ROOT/'TMessagesProj/src/main/java';D=J/'app/flexygram/settings/signature'
def before(path):return subprocess.check_output(['git','show',BASE+':'+str(path)],cwd=ROOT,text=True)
def method(s,anchor):
 start=s.index(anchor);i=s.index('{',start);d=1;j=i+1
 while d:
  if s[j]=='{':d+=1
  elif s[j]=='}':d-=1
  j+=1
 return s[start:j]
class Migration(unittest.TestCase):
 def test_root_is_exact_and_registry_ids_are_unique(self):
  s=(D/'SignatureSettingsRegistry.java').read_text();entries=re.findall(r'new Entry\("([^"]+)","([^"]+)"',s);self.assertEqual(len(entries),len(set(x[0]for x in entries)));self.assertEqual([a for a,b in entries if b=='root'],['appearance','navigation','conversations','studio','files','extensions','general','advanced'])
 def test_every_route_is_reachable_and_graph_is_acyclic(self):
  entries=dict(re.findall(r'new Entry\("([^"]+)","([^"]+)"',(D/'SignatureSettingsRegistry.java').read_text()))
  for key in entries:
   seen=set();at=key
   while at!='root':self.assertNotIn(at,seen,key);seen.add(at);self.assertIn(at,entries,key);at=entries[at]
 def test_all_reference_resources_exist_and_locales_match(self):
  langs=[]
  for locale in ['values','values-es','values-ru']:
   p=ROOT/'TMessagesProj/src/main/res'/locale/'flexy_settings2.xml';r=ET.parse(p).getroot();names=[x.get('name')for x in r];self.assertEqual(len(names),len(set(names)));langs.append(set(names))
  self.assertEqual(langs[0],langs[1]);self.assertEqual(langs[0],langs[2])
  resources=ROOT/'TMessagesProj/src/main/res';drawables={p.stem for p in resources.glob('drawable*/*')}
  for p in D.glob('*.java'):
   for name in re.findall(r'R.drawable.(\w+)',p.read_text()):self.assertIn(name,drawables,p.name)
 def test_no_new_settings_store_or_backend_or_network_code(self):
  for p in D.glob('*.java'):
   s=p.read_text()
   for bad in ['getSharedPreferences(','.putBoolean(','.putInt(','.setConfigBool(','.setConfigInt(','sendRequest(','new Thread(','postInvalidateOnAnimation','setDrawBlurBackground']:
    self.assertNotIn(bad,s,p.name)
 def test_original_preference_handlers_are_byte_identical(self):
  for name in ['OpenExteraGeneralActivity','OpenExteraAppearanceActivity','OpenExteraChatsActivity','OpenExteraOtherActivity']:
   path=Path('TMessagesProj/src/main/java/app/exteraless/settings')/(name+'.java');new=(ROOT/path).read_text();old=before(path)
   for anchor in ['protected void onItemClick(']:
    expected=method(old,anchor)
    if name=='OpenExteraChatsActivity':
     # This task retires exactly the old Smart Preview picker; retain all other callbacks byte-for-byte.
     a=expected.index('        } else if (position == smartPreviewsRow) {')
     b=expected.index('        } else if (position == flexyContextPanelRow)',a)
     expected=expected[:a]+expected[b:]
    self.assertEqual(expected,method(new,anchor).replace('\n        if(position==settings3ResetStickerRow && position>=0){resetStickerSize();return;}',''),name)
 def test_no_changes_to_signature_style_engines_media_auth_jni_or_flexyfiles_backend(self):
  paths=['app/flexygram/files','app/flexygram/header/HeaderConfig.java','app/flexygram/header/HeaderPreviewView.java','app/flexygram/bubbles/BubbleConfig.java','app/flexygram/bubbles/BubblePreviewView.java','app/flexygram/composer/FlexyComposerConfig.java','app/flexygram/composer/ComposerStyle.java','app/flexygram/navigation/LiquidNavigationConfig.java','org/telegram/messenger','org/telegram/tgnet','org/telegram/ui/ChatActivity.java','org/telegram/ui/ActionBar/ActionBarLayout.java']
  changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'--',*[str(Path('TMessagesProj/src/main/java')/p)for p in paths],'TMessagesProj/jni','TMessagesProj/chaquopy','TMessagesProj/build.gradle','config','.github'],cwd=ROOT,text=True).splitlines())
  workflow='.github/workflows/smart-previews2.yml'
  allowed={workflow,'.github/workflows/cherry-tabs.yml','TMessagesProj/src/main/java/app/flexygram/navigation/LiquidNavigationConfig.java','TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java'}
  self.assertFalse(changed-allowed)
  self.assertEqual('22be37697119c5b2a4314fb15875823d1c5e7ed0',subprocess.check_output(['git','hash-object',workflow],cwd=ROOT,text=True).strip())
 def test_studio_has_only_original_three_operations_and_files_is_moved(self):
  s=(J/'app/flexygram/studio/FlexyStudioActivity.java').read_text();rows=method(s,'protected void updateRows()');self.assertEqual(re.findall(r'addRow\("([^"]+)"',rows),['flexystudioExport','flexystudioImport','flexystudioShare']);self.assertIn('tools=files=help=toolsShadow=-1',rows)
  f=(D/'SignatureFilesSettingsActivity.java').read_text();self.assertIn('app.flexygram.files.FlexyFiles.enabled(!app.flexygram.files.FlexyFiles.enabled())',f);self.assertIn('super.onItemClick(v,p,x,y)',f);self.assertIn('notifyItemChanged(enabled)',f)
 def test_native_control_entry_removals_keep_nonclient_behavior(self):
  self.assertNotIn('items.add(SettingCell.Factory.of(100,',(J/'org/telegram/ui/SettingsActivity.java').read_text())
  self.assertIn('BuildConfig.CONNECTED_ALPHA ? -1 : rowCount++',(J/'org/telegram/ui/PrivacySettingsActivity.java').read_text())
  self.assertIn('if (!org.telegram.messenger.BuildConfig.CONNECTED_ALPHA)',(J/'org/telegram/ui/ThemeActivity.java').read_text())
  self.assertIn('if(!org.telegram.messenger.BuildConfig.CONNECTED_ALPHA)count += 3',(J/'org/telegram/ui/LanguageSelectActivity.java').read_text())
 def test_new_menus_retain_clean_titles_and_native_animation_engine(self):
  s=(D/'SignatureSettingsActivity.java').read_text();self.assertIn('actionBar.centerTitle()',s);self.assertIn('listView.setItemAnimator(null)',s);self.assertIn('actionBar.createMenu()',s)
  for p in D.glob('*.java'):
   for bad in ['new SpringAnimation(','FlexyMotion','requestLayout();requestLayout','rebuildAllFragmentViews','System.exit','setContentView']:
    self.assertNotIn(bad,p.read_text(),p.name)
 def test_conditional_native_row_notifications_have_owner_admission(self):
  for cls in ['NekoGeneralSettingsActivity','NekoExperimentalSettingsActivity','NekoChatSettingsActivity']:
   s=(J/'tw/nekomimi/nekogram/settings'/(cls+'.java')).read_text()
   for m in re.finditer(r'private void (check\w+)\(\) \{',s):
    body=method(s,m[0]);
    if 'notifyItemInserted' in body:self.assertIn('signatureSettingsAllows(',body,cls+':'+m[1])
 def test_pure_production_policy_and_aliases(self):
  code='''import app.flexygram.settings.signature.*;public class Probe{public static void main(String[]x){for(var e:Settings2Policy.inventory().entrySet()){if(e.getValue().isEmpty())throw new AssertionError();}if(!"archive".equals(Settings2Policy.aliasOwner("general","HideArchive")))throw new AssertionError();if(!"files".equals(Settings2Policy.aliasOwner("general","SaveToChatSubfolder")))throw new AssertionError();for(String route:new String[]{"files","general","archive","profile"}){var r=new Settings2Policy.Rows("general",route);boolean admitted=r.named("savePath");if(admitted!=route.equals("files"))throw new AssertionError();if(r.anonymous()!=admitted)throw new AssertionError();r.reset();if(r.anonymous())throw new AssertionError();}}}'''
  with tempfile.TemporaryDirectory()as t:
   p=Path(t)/'Probe.java';p.write_text(code);subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',t,str(D/'Settings2Policy.java'),str(p)],check=True,capture_output=True);subprocess.run(['java','-cp',t,'Probe'],check=True,capture_output=True)
 def test_no_overlap_with_pr158_files(self):
  reserved=set(subprocess.check_output(['git','diff','--name-only',BASE+'...0e930b52b78db6578db377a19047ff3bfa72ef24'],cwd=ROOT,text=True).splitlines());changed=set(subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines());self.assertFalse(reserved&changed,reserved&changed)
if __name__=='__main__':unittest.main(verbosity=2)
