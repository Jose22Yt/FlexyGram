"""Alpha1267 preservation, actual row/handler continuity and executable layout/storage policy."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASE = 'c85cfa5cc201b25987d101e47f8ee2f252e6b961'
JAVA = ROOT/'TMessagesProj/src/main/java'
SETTINGS = JAVA/'app/flexygram/settings'
CANDIDATE_PATHS = {
    '.github/workflows/signature-matte-settings.yml', '.github/workflows/pr.yml',
    '.github/workflows/connected-alpha-arm64.yml', 'TMessagesProj/build.gradle',
    'tools/connected_alpha/test_matte_release.py', 'tools/connected_alpha/test_signature_custom.py',
    'TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraGeneralActivity.java',
    'TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraAppearanceActivity.java',
    'TMessagesProj/src/main/java/tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java',
    'TMessagesProj/src/main/java/tw/nekomimi/nekogram/NekoConfig.java',
    'tools/connected_alpha/test_signature_home.py', 'tools/connected_alpha/test_signature_matte.py',
    *['TMessagesProj/src/main/java/app/flexygram/settings/'+p+'.java' for p in (
        'SignatureMatteSettingsActivity', 'MatteTextSettingsCell', 'MatteDetailSettingsCell',
        'MatteExpandableSwitchCell', 'MatteTextCheckCell', 'MatteSettingsLayout', 'FreshInstallSavePath')],
    *['TMessagesProj/src/main/res/'+locale+'/flexygram_matte_settings.xml' for locale in ('values','values-es','values-ru')],
    *['tools/connected_alpha/matte_visual/'+p for p in ('run.py','pom.xml','MatteVisualTest.java.in','stubs.py')],
}

def old(path):
    return subprocess.check_output(['git','show',BASE+':'+str(path)],cwd=ROOT,text=True)

def body(source, anchor):
    start=source.index(anchor); start=source.index('{',start)
    depth=1; end=start+1
    while depth:
        depth += (source[end]=='{') - (source[end]=='}'); end+=1
    return source[start:end]

class SignatureMatteTests(unittest.TestCase):
    def test_exact_candidate_scope_preserves_app_delivery_and_native_previews(self):
        paths=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
        paths+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
        self.assertTrue(set(paths)<=CANDIDATE_PATHS, set(paths)-CANDIDATE_PATHS)
        for directory in ('app/flexygram/composer','app/flexygram/home','app/exteraless/appearance'):
            prefix='TMessagesProj/src/main/java/'+directory
            for path in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--',prefix],cwd=ROOT,text=True).splitlines():
                self.assertEqual((ROOT/path).read_text(),old(path),path)
        self.assertEqual((ROOT/'TMessagesProj/build.gradle').read_text().replace('def verCode = 1269','def verCode = 1267').replace("versionNameSuffix = '-alpha2-signature-matte'","versionNameSuffix = '-alpha2-integrated-signature'"),old('TMessagesProj/build.gradle'))
        from test_matte_release import restore_delivery_workflow
        self.assertEqual(restore_delivery_workflow((ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text()),old('.github/workflows/connected-alpha-arm64.yml'))

    def test_every_existing_row_and_click_handler_is_preserved(self):
        for name in ('General','Appearance'):
            path=f'TMessagesProj/src/main/java/app/exteraless/settings/OpenExtera{name}Activity.java'
            before=old(path);after=(ROOT/path).read_text()
            for signature in ('protected void onItemClick(', 'protected String getKey()'):
                self.assertEqual(body(before,signature),body(after,signature))
            a=body(before,'protected void updateRows()'); b=body(after,'protected void updateRows()')
            # New presentation groups may split cards, but every existing persistent row/key remains.
            for row,key in re.findall(r'(\w+Row) = addRow\("([^"]+)"',a):
                self.assertIn(f'{row} = addRow("{key}"',b)
                self.assertEqual(b.count(f'{row} = addRow('),a.count(f'{row} = addRow('),row)
            self.assertIn('extends app.flexygram.settings.SignatureMatteSettingsActivity',after)
            self.assertIn('class ListAdapter extends MatteListAdapter',after)

    def test_groups_use_independent_existing_preferences_and_order(self):
        s=(JAVA/'app/exteraless/settings/OpenExteraAppearanceActivity.java').read_text()
        rows=body(s,'protected void updateRows()')
        ordered=['avatarsHeaderRow =','chatListHeaderRow =','foldersHeaderRow =','iconsHeaderRow =',
                 'linksHeaderRow =','appearanceHeaderRow =','md3HeaderRow =','iosHeaderRow =',
                 'sectionsHeaderRow =','blurHeaderRow =']
        self.assertEqual([rows.index(k) for k in ordered],sorted(rows.index(k) for k in ordered))
        for method in ('private void toggleAllMd3Styles(', 'private void toggleAllIosStyles('):
            self.assertEqual(body(s,method),body(old('TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraAppearanceActivity.java'),method))
        self.assertNotIn('FlexyComposerSettingsActivity',s)
        for locale in ('values','values-es','values-ru'):
            values={n.attrib['name']:n.text for n in ET.parse(ROOT/f'TMessagesProj/src/main/res/{locale}/flexygram_matte_settings.xml').getroot()}
            self.assertEqual(len(values),7)
            self.assertIn('Material Design 3',values['FlexyMatteMd3Info'])
            self.assertIn('iOS Design',values['FlexyMatteIosInfo'])

    def test_matte_is_opt_in_and_has_no_glass_shadow_or_per_frame_allocations(self):
        s=(SETTINGS/'SignatureMatteSettingsActivity.java').read_text()
        for forbidden in ('setShadowLayer','RenderEffect','Bitmap','ValueAnimator','postDelayed','setConfig','LiteMode.set'):
            self.assertNotIn(forbidden,s)
        self.assertNotIn('new ',body(s,'public void drawBackgroundRect('))
        self.assertIn('Theme.multAlpha(',body(s,'public void drawBackgroundRect('))
        self.assertIn('setDrawGlassTitle(false)',s)
        self.assertIn('doNotDrawGlassMenu = true',s)
        base=(JAVA/'tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java').read_text()
        self.assertIn('return false;',body(base,'protected boolean usesSolidSettingsSurfaces()'))
        self.assertIn('if (!usesSolidSettingsSurfaces()) listView.addOnScrollListener',base)
        self.assertIn('usesSolidSettingsSurfaces() ? new SizeNotifierFrameLayout',base)

    def test_real_layout_and_storage_policies_execute(self):
        source=(SETTINGS/'FreshInstallSavePath.java').read_text()
        method=body(source,'public static boolean eligible(')
        fixture='''import app.flexygram.settings.MatteSettingsLayout;
public class MattePolicyProbe {
 static void check(boolean b){if(!b)throw new AssertionError();}
 static boolean eligible(boolean alpha,boolean emptyPreferences,long firstInstall,long lastUpdate)_METHOD_
 public static void main(String[] a){
  for(float density:new float[]{.75f,1f,1.5f,2f,2.75f,3f,4f})
   for(int width=240;width<=700;width+=10)for(float font:new float[]{1f,1.3f,1.5f,2f,3f}){
    int available=Math.max(0,Math.round((width-42)*density));
    int title=Math.round(240*density*font),value=Math.round(120*density*font),gap=Math.round(8*density);
    boolean stack=MatteSettingsLayout.stackValue(title,value,available,gap);
    check(stack || title+value+gap<=available);
    int height=MatteSettingsLayout.rowHeight(50,Math.round(20*font),stack?Math.round(18*font):0,12,4);
    check(height>=50 && height>=Math.round(20*font)+24);
   }
  check(!MatteSettingsLayout.stackValue(10,0,0,8));
  check(eligible(true,true,10,10));
  check(!eligible(true,true,10,11));check(!eligible(true,false,10,10));
  check(!eligible(false,true,10,10));check(!eligible(true,true,0,0));
  System.out.println("PASS real measurement and conservative fresh-install policies");
 }
}'''.replace('_METHOD_',method)
        with tempfile.TemporaryDirectory() as tmp:
            runner=Path(tmp)/'MattePolicyProbe.java';runner.write_text(fixture)
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(SETTINGS/'MatteSettingsLayout.java'),str(runner)],check=True)
            self.assertIn('PASS real',subprocess.check_output(['java','-cp',tmp,'MattePolicyProbe'],text=True))

    def test_storage_fallback_and_all_existing_configuration_remain_unchanged(self):
        path='TMessagesProj/src/main/java/tw/nekomimi/nekogram/NekoConfig.java'
        after=(ROOT/path).read_text()
        self.assertEqual(after.replace('            app.flexygram.settings.FreshInstallSavePath.pin(getPreferences());\n',''),old(path))
        self.assertIn('configTypeString, "exteraless"',after)
        s=(SETTINGS/'FreshInstallSavePath.java').read_text()
        self.assertIn('!preferences.getAll().isEmpty()',s)
        self.assertIn('"customSavePath", "FlexyGram"',s)
        self.assertNotIn('remove(',s)
        self.assertNotIn('rename',s)

if __name__=='__main__':unittest.main()
