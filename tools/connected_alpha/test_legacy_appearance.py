"""User-requested retirement of the two obsolete Exteraless Appearance groups."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
JAVA = ROOT / "TMessagesProj/src/main/java"
APP = JAVA / "app/exteraless/settings/OpenExteraAppearanceActivity.java"
HELPER = JAVA / "app/exteraless/appearance/ChatHeaderUiHelper.java"
HEADER = JAVA / "app/flexygram/header/HeaderConfig.java"
KOTLIN = ROOT / "TMessagesProj/src/main/kotlin/app/exteraless/appearance/AppearanceConfig.kt"


class LegacyAppearanceRetirement(unittest.TestCase):
    def test_exact_review(self):
        from legacy_appearance_contract import verify_current
        verify_current()

    def test_both_screenshot_groups_are_absent_from_live_appearance(self):
        source = APP.read_text()
        for forbidden in (
            'addRow("matteMd3Header")', 'addRow("md3Styles")',
            'addRow("iosStyles")', 'addRow("matteIosHeader")',
            'toggleAllMd3Styles', 'toggleAllIosStyles',
            'TYPE_EXPANDABLE_SWITCH', 'TYPE_ROUND_CHECK',
            'AppearanceConfig.iosChatHeader.setConfigBool',
            'HeaderConfig.style(enable)', 'md3ChatHeaderRow',
            'iosChatHeaderRow',
        ):
            self.assertNotIn(forbidden, source, forbidden)
        for preserved in (
            'avatarCornersPreviewRow', 'chatListPreviewRow', 'foldersPreviewRow',
            'folderThemeAccentRow', 'appearanceHeaderRow', 'sectionsHeaderRow',
            'blurHeaderRow', 'pillStackRow', 'glassOutlineRow',
        ):
            self.assertIn(preserved + ' = addRow(', source, preserved)
        self.assertIn('extends app.flexygram.settings.SignatureMatteSettingsActivity', source)

    def test_retired_preferences_do_not_reset_signature_choice_or_player(self):
        source = KOTLIN.read_text()
        header = HEADER.read_text()
        self.assertIn('retireConflictingLegacyStyles()', source)
        self.assertIn('if (!org.telegram.messenger.BuildConfig.CONNECTED_ALPHA)', source)
        for property_name in (
            'newChatHeaderStyle', 'newNavigationBarStyle',
            'iosNavigationBarStyle', 'iosChatHeader',
        ):
            self.assertIn('if (' + property_name + '.Bool()) ' +
                          property_name + '.setConfigBool(false)', source)
        self.assertNotIn('md3Player.setConfigBool(false)', source)
        self.assertNotIn('md3MiniPlayer.setConfigBool(false)', source)
        self.assertIn('style instanceof Integer', header)
        self.assertIn('BuildConfig.CONNECTED_ALPHA ? 0 : legacy', header)
        self.assertIn('prefs().edit().putInt("style", currentStyle)', header)

    def test_real_header_helper_ignores_legacy_m3_pref_in_connected_alpha(self):
        """JDK-compile and execute the exact production helper with tiny Android doubles."""
        stubs = {
            'org/telegram/messenger/BuildConfig.java':
                'package org.telegram.messenger;public class BuildConfig{public static boolean CONNECTED_ALPHA=true;}',
            'org/telegram/messenger/AndroidUtilities.java':
                'package org.telegram.messenger;public class AndroidUtilities{'
                'public static int dp(float x){return Math.round(x);}'
                'public static float computePerceivedBrightness(int color){return .8f;}}',
            'org/telegram/ui/ActionBar/Theme.java':
                'package org.telegram.ui.ActionBar;public class Theme{public static int key_windowBackgroundGray=3;}',
            'org/telegram/ui/ActionBar/ActionBar.java':
                'package org.telegram.ui.ActionBar;public class ActionBar{'
                'public static final int VISIBLE=0; public int getVisibility(){return 0;}'
                'public int getMeasuredHeight(){return 46;}public int getBackgroundColor(){return 0;}'
                'public boolean isActionModeShowed(){return false;}'
                'public void setDrawGlassMiddlePill(boolean x){}'
                'public void setGlassShadowAlpha(float x){}}',
            'org/telegram/ui/Components/ChatActivityTopPanelLayout.java':
                'package org.telegram.ui.Components;public class ChatActivityTopPanelLayout{'
                'public Meta getMetadata(){return new Meta();}'
                'public static class Meta{public float getTotalVisibility(){return 0f;}}}',
            'org/telegram/ui/Components/ChatAvatarContainer.java':
                'package org.telegram.ui.Components;public class ChatAvatarContainer{'
                'public void setGlassMode(){}public void setAvatarSizeInDp(int n){}}',
            'org/telegram/ui/Components/chat/layouts/ChatActivityFadeView.java':
                'package org.telegram.ui.Components.chat.layouts;public class ChatActivityFadeView{'
                'public int zone,height; public void setFadeTopAlpha(int x){}'
                'public void setFadeZoneTop(int x){zone=x;}'
                'public void setTopFadeColor(int c){}'
                'public void setFadeHeightTop(int x){height=x;}}',
            'app/exteraless/appearance/AppearanceConfig.java':
                'package app.exteraless.appearance;public class AppearanceConfig{'
                'public static boolean newChatHeaderStyle(){return true;}'
                'public static final int CORNER_TYPE_DEFAULT=0,CORNER_TYPE_FORUM=1;'
                'public static int getAvatarCorners(int size,int kind,boolean stories){return size/2;}}',
            'HeaderRetirementProbe.java':
                'import app.exteraless.appearance.ChatHeaderUiHelper;'
                'import org.telegram.messenger.BuildConfig;'
                'import org.telegram.ui.ActionBar.ActionBar;'
                'import org.telegram.ui.Components.chat.layouts.ChatActivityFadeView;'
                'public class HeaderRetirementProbe{public static void main(String[]a){'
                'ChatActivityFadeView v=new ChatActivityFadeView();'
                'if(ChatHeaderUiHelper.isMaterial3ChatHeaderStyle())throw new AssertionError("old MD3 active");'
                'ChatHeaderUiHelper.setupChatTopFade(v,new ActionBar(),0,46);'
                'if(v.height!=48||v.zone!=46)throw new AssertionError("Signature top fade overridden");'
                'BuildConfig.CONNECTED_ALPHA=false;'
                'if(!ChatHeaderUiHelper.isMaterial3ChatHeaderStyle()||'
                'ChatHeaderUiHelper.getChatTopFadeHeight()!=78)throw new AssertionError("legacy fallback");'
                'System.out.println("PASS production connected-alpha header protection");}}'
        }
        with tempfile.TemporaryDirectory() as folder:
            source_dir = Path(folder)
            files = [str(HELPER)]
            for name, body in stubs.items():
                dest = source_dir / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(body)
                files.append(str(dest))
            result = subprocess.run(['javac', '-d', folder, *files],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(['java', '-cp', folder, 'HeaderRetirementProbe'],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('PASS production', result.stdout)


if __name__ == '__main__':
    unittest.main()
