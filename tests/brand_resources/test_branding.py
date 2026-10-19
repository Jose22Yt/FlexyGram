"""Source-level checks for FlexyGram's proposed visible brand resources.

No Android build, network, credentials or app execution is involved.
"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "TMessagesProj/src/main/res"
MANIFEST = ROOT / "TMessagesProj/src/diagnostic/AndroidManifest.xml"
ANDROID = "{http://schemas.android.com/apk/res/android}"
LOCALES = (
    "values", "values-ar", "values-de", "values-es", "values-it",
    "values-ko", "values-nl", "values-pt-rBR"
)
ICON_ASSETS = (
    "drawable/flexygram_brand_background.xml",
    "drawable-night/flexygram_brand_background.xml",
    "drawable/flexygram_brand_mark.xml",
    "drawable-night/flexygram_brand_mark.xml",
    "drawable/flexygram_brand_monochrome.xml",
    "mipmap-anydpi-v26/ic_launcher_flexygram_candidate.xml",
    "mipmap-anydpi-v26/ic_launcher_flexygram_candidate_round.xml",
)


class BrandResourcesTests(unittest.TestCase):
    def test_localized_product_names_are_consistent(self):
        for locale in LOCALES:
            with self.subTest(locale=locale):
                strings = ET.parse(RES / locale / "strings.xml").getroot()
                names = {}
                for node in strings.findall("string"):
                    if node.get("name") in ("AppName", "AppNameBeta"):
                        self.assertNotIn(node.get("name"), names)
                        names[node.get("name")] = "".join(node.itertext()).strip()
                self.assertEqual(names, {
                    "AppName": "FlexyGram",
                    "AppNameBeta": "FlexyGram Beta",
                })

    def test_diagnostic_application_and_launcher_are_unchanged(self):
        app = ET.parse(MANIFEST).getroot().find("application")
        self.assertIsNotNone(app)
        self.assertEqual(app.get(ANDROID + "label"), "FlexyGram Diagnostic")
        self.assertEqual(app.get(ANDROID + "icon"), "@mipmap/ic_launcher_exteraless")
        self.assertEqual(app.get(ANDROID + "roundIcon"), "@mipmap/ic_launcher_exteraless_round")
        enabled_launchers = []
        for alias in app.findall("activity-alias"):
            if alias.get(ANDROID + "enabled", "true") != "true":
                continue
            for intent in alias.findall("intent-filter"):
                actions = {e.get(ANDROID + "name") for e in intent.findall("action")}
                categories = {e.get(ANDROID + "name") for e in intent.findall("category")}
                if ("android.intent.action.MAIN" in actions and
                        "android.intent.category.LAUNCHER" in categories):
                    enabled_launchers.append(alias)
                    break
        self.assertEqual(len(enabled_launchers), 1)
        self.assertEqual(enabled_launchers[0].get(ANDROID + "name"),
                         "org.telegram.messenger.ExteralessIcon")

    def test_identity_candidate_assets_exist_and_parse(self):
        for name in ICON_ASSETS:
            with self.subTest(asset=name):
                self.assertEqual(ET.parse(RES / name).getroot().tag.rsplit("}", 1)[-1],
                                 "adaptive-icon" if "mipmap-" in name
                                 else "vector" if "mark.xml" in name or "monochrome.xml" in name
                                 else "shape")

    def test_adaptive_round_and_standard_reference_the_same_layers(self):
        expected = {
            "background": "@drawable/flexygram_brand_background",
            "foreground": "@drawable/flexygram_brand_mark",
            "monochrome": "@drawable/flexygram_brand_monochrome",
        }
        for name in ("ic_launcher_flexygram_candidate.xml",
                     "ic_launcher_flexygram_candidate_round.xml"):
            icon = ET.parse(RES / "mipmap-anydpi-v26" / name).getroot()
            self.assertEqual(
                {child.tag.rsplit("}", 1)[-1]: child.get(ANDROID + "drawable")
                 for child in icon},
                expected,
            )

    def test_monochrome_mark_has_f_cutout_and_vectors_have_consistent_viewport(self):
        mono = ET.parse(RES / "drawable/flexygram_brand_monochrome.xml").getroot()
        self.assertEqual(mono.get(ANDROID + "viewportWidth"), "108")
        self.assertEqual(mono.get(ANDROID + "viewportHeight"), "108")
        mono_paths = mono.findall("path")
        self.assertEqual(len(mono_paths), 1)
        self.assertEqual(mono_paths[0].get(ANDROID + "fillType"), "evenOdd")
        self.assertIn("M43,41", mono_paths[0].get(ANDROID + "pathData"))
        for qualifier in ("drawable", "drawable-night"):
            mark = ET.parse(RES / qualifier / "flexygram_brand_mark.xml").getroot()
            self.assertEqual(mark.get(ANDROID + "viewportWidth"), "108")
            self.assertEqual(mark.get(ANDROID + "viewportHeight"), "108")
            self.assertEqual(len(mark.findall("path")), 2)

    def test_account_labels_resolve_to_updated_brand_without_touching_auth_xml(self):
        auth = ET.parse(RES / "xml/auth.xml").getroot()
        self.assertEqual(auth.get(ANDROID + "label"), "@string/AppName")
        self.assertEqual(auth.get(ANDROID + "accountType"),
                         "@string/flexygram_account_type")


if __name__ == "__main__":
    unittest.main()
