"""Guard the official FlexyGram settings menu, upstream credits and localizations.

These are source/resource checks, not proof of a successful Android launch.
"""
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
JAVA = ROOT / "TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraSettingsActivity.java"
RES = ROOT / "TMessagesProj/src/main/res"
SOURCE_URL = "https://github.com/Jose22Yt/FlexyGram"
UPSTREAM_URL = "https://github.com/exteraless/exteraless"


class FlexySettingsIdentity(unittest.TestCase):
    def setUp(self):
        self.java = JAVA.read_text(encoding="utf-8")

    def test_official_links_replace_upstream_promotional_links(self):
        self.assertIn(SOURCE_URL, self.java)
        self.assertNotIn('openByUserName("exteraless"', self.java)
        self.assertNotIn('openByUserName("the8055u"', self.java)
        self.assertNotIn('openByUserName("BlueprintDsgn"', self.java)
        self.assertNotIn('"@exteraless"', self.java)
        self.assertNotIn('designerRow', self.java)
        self.assertNotIn('designStudioRow', self.java)
        self.assertIn(UPSTREAM_URL, self.java)  # only as an accessible credit
        self.assertIn("https://github.com/Jose22Yt/FlexyGram/blob/main/LICENSE", self.java)

    def test_channel_is_noninteractive_until_a_real_address_exists(self):
        self.assertIn('channelRow = addRow("flexyOfficialChannel")', self.java)
        self.assertIn("holder.getAdapterPosition() != channelRow", self.java)
        self.assertIn("R.string.FlexySettingsComingSoon", self.java)
        self.assertNotIn("else if (position == channelRow)", self.java)

    def test_information_and_composer_are_independent_from_native_composer(self):
        for expected in (
            'informationHeaderRow = addRow("flexyInformationHeader")',
            'aboutFlexyGramRow = addRow("flexyAbout")',
            'creditsRow = addRow("flexyCredits")',
            "showFlexyAbout();",
            "showFlexyCredits();",
            "R.string.FlexySettingsComposerRow",
        ):
            self.assertIn(expected, self.java)
        self.assertNotIn("R.string.FlexyComposerSettings), R.drawable.msg_discussion", self.java)
        self.assertTrue((RES / "values/flexygram_composer.xml").is_file())

    def test_localized_sections_and_attribution_are_present(self):
        keys = {
            "FlexySettingsOfficial",
            "FlexySettingsOfficialChannel",
            "FlexySettingsComingSoon",
            "FlexySettingsInformation",
            "FlexySettingsAbout",
            "FlexySettingsCredits",
            "FlexySettingsAboutBody",
            "FlexySettingsCreditsBody",
            "FlexySettingsLicenseAction",
            "FlexySettingsUpstreamAction",
            "FlexySettingsComposerRow",
        }
        for directory in ("values", "values-es", "values-ru"):
            path = RES / directory / "flexygram_settings_info.xml"
            with self.subTest(locale=directory):
                root = ET.parse(path).getroot()
                entries = {element.get("name"): (element.text or "")
                           for element in root.findall("string")}
                self.assertEqual(set(entries), keys)
                self.assertIn("Exteraless", entries["FlexySettingsCreditsBody"])
                self.assertIn("the8055u", entries["FlexySettingsCreditsBody"])
                self.assertIn("BlueprintDsgn", entries["FlexySettingsCreditsBody"])
                self.assertIn("GPL-3.0", entries["FlexySettingsCreditsBody"])
                self.assertTrue(entries["FlexySettingsComposerRow"].strip())
                for key in keys:
                    self.assertIn(f"R.string.{key}", self.java)


if __name__ == "__main__":
    unittest.main()
