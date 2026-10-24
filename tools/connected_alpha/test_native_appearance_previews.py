"""Regression guards for lightweight, native appearance previews.

Static host checks only: these do not assert that the APK was built or visually accepted.
"""
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
APPEARANCE = ROOT / "TMessagesProj/src/main/java/app/exteraless/appearance"
RES = ROOT / "TMessagesProj/src/main/res"


class NativeAppearancePreviews(unittest.TestCase):
    def read(self, name):
        return (APPEARANCE / name).read_text(encoding="utf-8")

    def test_folder_previews_use_the_production_signature_tabs_without_blur(self):
        code = self.read("FoldersPreviewCell.java")
        production = (ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Components/FilterTabsView.java").read_text()
        self.assertIn("new FilterTabsView(context, resourcesProvider)", code)
        self.assertIn("tabsView.setSignatureHome(true)", code)
        self.assertIn("public void setSignatureHome(boolean enabled)", production)
        self.assertNotIn("BlurredBackground", code)
        self.assertNotIn("backgroundSource", code)
        self.assertNotIn("ObjectAnimator", code)
        self.assertIn("rebuildTabs(false)", code)
        self.assertIn("tabsView.updateColors()", code)

    def test_avatar_preview_uses_production_drawable_and_live_setting(self):
        code = self.read("AvatarCornersPreviewCell.java")
        production = (ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Components/AvatarDrawable.java").read_text()
        self.assertIn("new AvatarDrawable()", code)
        self.assertIn("avatarDrawable.setRoundRadius(", code)
        self.assertIn("AppearanceConfig.getAvatarCorners(AndroidUtilities.dp(56))", code)
        self.assertIn("public void setRoundRadius(int roundRadius)", production)
        self.assertIn("new ImageView(context)", code)
        self.assertIn("new TextView(context)", code)
        self.assertNotIn("drawRoundRect(", code)
        self.assertNotIn("BlurredBackground", code)
        self.assertNotIn("ObjectAnimator", code)
        self.assertIn("setTextColor(Theme.getColor(Theme.key_chats_name))", code)
        self.assertIn("setTextColor(Theme.getColor(Theme.key_chats_message))", code)

    def test_real_home_toolbar_assets_and_native_action_bar(self):
        code = self.read("ChatListPreviewCell.java")
        self.assertIn("new ActionBar(context)", code)
        self.assertIn("R.drawable.flexy_home_search", code)
        self.assertIn("R.drawable.flexy_home_more", code)
        self.assertNotIn("R.drawable.ic_ab_other", code)
        self.assertIn("new SignatureHomePainter()", code)
        self.assertIn("SignatureHomeStyle.controlDiameter(", code)
        self.assertIn("painter.control(canvas,", code)
        self.assertIn("dark, false, item.getAlpha()", code)
        self.assertIn("setDrawGlassTitle(false)", code)
        self.assertIn("doNotDrawGlassMenu = true", code)
        for icon in ("flexy_home_search.xml", "flexy_home_more.xml"):
            self.assertTrue((RES / "drawable" / icon).exists())

    def test_sample_is_translated_without_using_private_chat_data(self):
        keys = []
        for lang in ("values", "values-es", "values-ru"):
            root = ET.parse(RES / lang / "flexygram_appearance_preview.xml").getroot()
            names = [node.attrib["name"] for node in root.findall("string")]
            self.assertEqual(names, ["FlexyAppearancePreviewMessage"])
            value = root.find("string").text
            self.assertTrue(value and value.strip())
            keys.append(value)
        self.assertEqual(len(set(keys)), 3)


if __name__ == "__main__":
    unittest.main()
