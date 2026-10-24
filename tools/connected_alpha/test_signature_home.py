"""Home-only integration, executable geometry and preservation of native actions."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from check_source import restore_home_presentation
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
HOME = ROOT/'TMessagesProj/src/main/java/app/flexygram/home'
BASE = 'b478f02ad8a3cee5a17f58d3909c4961a3555651'
BEHAVIOR_PINS = [['TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java', 'public boolean onBackPressed(boolean invoked)', 'ef0d8520c293203771cf6dce64443535af55b8af421c98af7fb7608938187dee'], ['TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java', 'private void showSearch(boolean show, boolean startFromDownloads, boolean animated, boolean forceNotOnlyDialogs)', 'c45d18f08ac0856ef7263f76f0efca6f24816d6a41c1f151ebb13c1c36af6b27'], ['TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java', 'private void showItemOptions()', 'd1585a5057df3bf62c98b2d35693b886bd3d27e7a9c5a47f09afd41e32de8e7c'], ['TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java', 'searchItem.setOnClickListener(v ->', 'f62e4321e99bb040c811e74f776b813549d6b067d5ba99b422b6bdddff10189e'], ['TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java', 'optionsItem.setOnClickListener(v ->', 'b2d4dc2feef550352173956855f900c014cf0a2eaa6bb1859089f1756d9337e5'], ['TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java', 'optionsItem.setOnLongClickListener(v ->', 'aeb00035111504987380d7c1c4af064ac774322b3edca08df5a7f2152288faa6'], ['TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java', 'searchItem.setOnLongClickListener(v ->', '1ad1b7af1c04807064b2ffed43a94330ced5a2b07856fb83e4a01e67f2519b90'], ['TMessagesProj/src/main/java/org/telegram/ui/Components/FilterTabsView.java', 'public void scrollToTab(Tab tab, int position)', 'ee5911ac63d71b313b9a43bcb4c73e30bc7a8f7a77d7f11cbb66b1a4b59f1ccc'], ['TMessagesProj/src/main/java/org/telegram/ui/Components/FilterTabsView.java', 'listView.setOnItemClickListener(', '8de15f6bb08be11968b649dd9a98be43befad05cbb55e493a67ab459827b4e65'], ['TMessagesProj/src/main/java/org/telegram/ui/Components/FilterTabsView.java', 'listView.setOnItemLongClickListener(', '87c191e1b55cbd898652bd21f37444ea3f36a08b6b460cf9c1d850e2e3158057']]

def body(source, anchor):
    start = source.index(anchor)
    pos = source.index('{', start)
    depth = 1
    while depth:
        pos += 1
        if source[pos] == '{': depth += 1
        elif source[pos] == '}': depth -= 1
    return source[start:pos+1]

class SignatureHomeTests(unittest.TestCase):
    def test_visual_patch_restores_exact_original_and_rejects_native_mutation(self):
        path=ROOT/'TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java'
        data=path.read_bytes()
        restored=restore_home_presentation(data)
        expected='6cb070e30b4ec5c435d9a0fc6da09ac534575694214673b9eba8f9bf251b0768'
        self.assertEqual(hashlib.sha256(restored).hexdigest(),expected)
        # An unrelated change must either fail patch application or fail parity.
        mutated=data.replace(b'public boolean onBackPressed(boolean invoked)',
                             b'public boolean onBackPressed(boolean unrelated)',1)
        try:
            result=restore_home_presentation(mutated)
        except ValueError:
            return
        self.assertNotEqual(hashlib.sha256(result).hexdigest(),expected)

    def test_original_search_menu_back_and_filter_actions_unchanged(self):
        for path, anchor, expected in BEHAVIOR_PINS:
            with self.subTest(anchor=anchor):
                actual = body((ROOT/path).read_text(), anchor)
                self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(), expected)

    def test_home_scope_and_native_special_states(self):
        s=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java').read_text()
        scope=body(s,'public boolean isSignatureHome()')
        for condition in ('!onlySelect','DIALOGS_TYPE_DEFAULT','folderId == 0','communityId == 0','searchString == null'):
            self.assertIn(condition,scope)
        dispatch=body(s,'protected void dispatchDraw(Canvas canvas) {\n                // Only the main screen')
        for condition in ('!inPreviewMode','progressToActionMode == 0','!isActionModeShowed()',
                          'searchAnimationProgress == 0','getRightSlidingProgress() == 0'):
            self.assertIn(condition, dispatch)
        self.assertIn('setDrawGlassTitle(!home)',dispatch)
        self.assertIn('doNotDrawGlassMenu = home',dispatch)
        self.assertIn('super.dispatchDraw(canvas)',dispatch)
        self.assertIn('!isSignatureHome() && !NaConfig',body(s,'private boolean shouldShowIdleSearchField()'))
        shared = body(s, '// Home paints cheap individual pills;')
        self.assertIn('if (!isSignatureHome())', shared)
        self.assertIn('iBlur3FactoryLiquidGlass.create(filterTabsView', shared)

    def test_native_category_row_and_separators(self):
        s=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/Components/FilterTabsView.java').read_text()
        self.assertIn('Math.max(30f, FolderIconHelper.getTabPadding())',s)
        self.assertIn('!signatureHome && trueTabsWidth < width',s)
        self.assertIn('if (signatureHome) return;',body(s,'private void drawSelector('))
        self.assertIn('super.dispatchDraw(canvas);',body(s,'protected void dispatchDraw('))
        self.assertIn('LinearLayoutManager.HORIZONTAL',s)
        self.assertIn('info.setSelected(',s)
        self.assertIn('itemTouchHelper.attachToRecyclerView(listView)',s)
        adapter=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/Adapters/DialogsAdapter.java').read_text()
        self.assertIn('cell.useSeparator = parentFragment != null && parentFragment.isSignatureHome() && nextDialog != null;',adapter)

    def test_original_thin_vector_resources(self):
        a='{http://schemas.android.com/apk/res/android}'
        for name in ('search','more'):
            path=ROOT/f'TMessagesProj/src/main/res/drawable/flexy_home_{name}.xml'
            self.assertIn('GPL-3.0-or-later',path.read_text())
            root=ET.parse(path).getroot()
            self.assertEqual(root.get(a+'width'),'24dp')
            p=root.find('path')
            self.assertEqual(p.get(a+'strokeLineCap'),'round')
            self.assertEqual(p.get(a+'fillColor'),'@android:color/transparent')

    def test_painter_has_no_extra_effect_or_animation_engine(self):
        s=(HOME/'SignatureHomePainter.java').read_text()
        for forbidden in ('RenderEffect','BlurMaskFilter','saveLayer','ValueAnimator','setShadowLayer','Bitmap','Handler','postDelayed'):
            self.assertNotIn(forbidden,s)
        for anchor in ('public void control(', 'public void category(', 'private void surface('):
            self.assertNotIn('new ',body(s,anchor))

    def test_executable_geometry_selection_and_rapid_state_changes(self):
        java=shutil.which('java')
        self.assertIsNotNone(java,'Java required; geometry validation must not silently skip')
        source='''import app.flexygram.home.SignatureHomeStyle;
public class HomePolicyProbe {
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[] args){
  for(float d:new float[]{.75f,1,1.5f,2,2.75f,3,4}) {
   check(SignatureHomeStyle.controlDiameter(48*d,56*d,d)==36*d);
   for(int width=0;width<=600;width++)for(int height=0;height<=200;height+=10){
    float size=SignatureHomeStyle.controlDiameter(width,height,d);
    check(size>=0 && size<=36*d && size<=Math.max(0,Math.min(width,height)-8*d));
    float pill=SignatureHomeStyle.categoryHeight(height,d);
    check(pill>=0 && pill<=30*d && pill<=Math.max(0,height-4*d));
   }
  }
  for(int i=0;i<=10000;i++){
   float p=i/10000f;
   float selected=SignatureHomeStyle.selection(4,4,3,true,p);
   float previous=SignatureHomeStyle.selection(3,4,3,true,p);
   check(Math.abs(selected+previous-1)<.00001f);
   check(SignatureHomeStyle.selection(9,4,3,true,p)==0);
   check(SignatureHomeStyle.selection(4,4,3,false,p)==1);
  }
  check(SignatureHomeStyle.selection(4,4,3,true,2)==1);
  check(SignatureHomeStyle.selection(4,4,3,true,-1)==0);
 }
}'''
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'HomePolicyProbe.java';path.write_text(source)
            subprocess.run([java,'-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,
                            str(HOME/'SignatureHomeStyle.java'),str(path)],check=True,capture_output=True)
            subprocess.run([java,'-cp',tmp,'HomePolicyProbe'],check=True,capture_output=True)

    def test_no_work1_composer_branding_native_or_installer_changes(self):
        allowed={
            'TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java',
            'TMessagesProj/src/main/java/org/telegram/ui/Components/FilterTabsView.java',
            'TMessagesProj/src/main/java/org/telegram/ui/Adapters/DialogsAdapter.java',
            'TMessagesProj/src/main/java/app/flexygram/home/SignatureHomeStyle.java',
            'TMessagesProj/src/main/java/app/flexygram/home/SignatureHomePainter.java',
            'TMessagesProj/src/main/res/drawable/flexy_home_search.xml',
            'TMessagesProj/src/main/res/drawable/flexy_home_more.xml',
            'TMessagesProj/build.gradle','.github/workflows/pr.yml',
            '.github/workflows/connected-alpha-arm64.yml',
            'tools/connected_alpha/test_signature_home.py',
            'tools/connected_alpha/test_signature_custom.py',
            'tools/connected_alpha/check_source.py',
            'tools/connected_alpha/signature_home_dialogs.patch',
            'tools/connected_alpha/home_visual/run.py',
            'tools/connected_alpha/home_visual/pom.xml',
            'tools/connected_alpha/home_visual/HomeVisualTest.java.in',
            # Follow-up preview-only PR #72, no native Home or composer modifications.
            'TMessagesProj/src/main/java/app/exteraless/appearance/AvatarCornersPreviewCell.java',
            'TMessagesProj/src/main/java/app/exteraless/appearance/ChatListPreviewCell.java',
            'TMessagesProj/src/main/java/app/exteraless/appearance/FoldersPreviewCell.java',
            'TMessagesProj/src/main/res/values/flexygram_appearance_preview.xml',
            'TMessagesProj/src/main/res/values-es/flexygram_appearance_preview.xml',
            'TMessagesProj/src/main/res/values-ru/flexygram_appearance_preview.xml',
            'tools/connected_alpha/test_native_appearance_previews.py',
            'tools/connected_alpha/test_integrated_approved_composer.py',
            # User-approved official branding links, secondary legal attribution,
            # and relocating the existing composer shortcut under Chats > Text input.
            'TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraSettingsActivity.java',
            'TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraChatsActivity.java',
            'TMessagesProj/src/main/res/values/flexygram_settings_info.xml',
            'TMessagesProj/src/main/res/values-es/flexygram_settings_info.xml',
            'TMessagesProj/src/main/res/values-ru/flexygram_settings_info.xml',
            'tools/connected_alpha/test_flexy_settings_identity.py',
        }
        # Independent General/Appearance candidate; exact delta guarded against Alpha1267.
        from test_signature_matte import CANDIDATE_PATHS
        allowed.update(CANDIDATE_PATHS)
        changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
        self.assertTrue(changed)
        self.assertEqual(set(changed)-allowed,set())
        gradle=subprocess.check_output(['git','diff',BASE,'--','TMessagesProj/build.gradle'],cwd=ROOT,text=True)
        additions=[l for l in gradle.splitlines() if l.startswith('+') and not l.startswith('+++')]
        self.assertEqual(additions,['+def verCode = 1267',"+        versionNameSuffix = '-alpha2-integrated-signature'"])

if __name__=='__main__':unittest.main()
