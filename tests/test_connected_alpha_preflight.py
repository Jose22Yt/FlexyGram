"""Offline unit tests: no real accounts, tokens or Android SDK required."""
from pathlib import Path
import base64
import importlib.util
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "Tools/connected_alpha_preflight.py"
spec = importlib.util.spec_from_file_location("connected_alpha_preflight", SCRIPT)
pre = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = pre
spec.loader.exec_module(pre)


class ConnectedAlphaPreflightTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        files = {
            "settings.gradle": "rootProject.name='exteraless'\n",
            "gradle.properties": "APP_PACKAGE=io.github.jose22yt.flexygram.alpha\n",
            ".gitignore": "local.properties\nTMessagesProj/release.keystore\n",
            ".gitmodules": "[submodule \"x\"]\n",
            "TMessagesProj/build.gradle": """def appId = '6'
def appHash = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
if (properties != null) {
    appId = properties.getProperty('TELEGRAM_APP_ID') ?: System.getenv('TELEGRAM_APP_ID') ?: appId
    appHash = properties.getProperty('TELEGRAM_APP_HASH') ?: System.getenv('TELEGRAM_APP_HASH') ?: appHash
}
""",
            "TMessagesProj/src/main/AndroidManifest.xml": """<manifest><uses-permission android:name="android.permission.INTERNET" />
<application><provider android:authorities="${applicationId}.provider" /></application></manifest>""",
        }
        for name, content in files.items():
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        self.valid = "TELEGRAM_APP_ID=1234567\nTELEGRAM_APP_HASH=0123456789abcdef0123456789abcdef\n"

    def tearDown(self):
        self.temp.cleanup()

    def check(self, env=None, app_id=None):
        return {x.name: x.status for x in pre.preflight(
            self.root, environ=env or {}, application_id=app_id)}

    def test_good_local_properties(self):
        (self.root / "local.properties").write_text(self.valid)
        self.assertEqual(self.check()["credentials"], "PASS")

    def test_missing_credentials_fails(self):
        self.assertEqual(self.check()["credentials"], "FAIL")

    def test_env_only_exposes_original_gradle_bug(self):
        self.assertEqual(self.check({"TELEGRAM_APP_ID":"1234567",
                                     "TELEGRAM_APP_HASH":"0123456789abcdef0123456789abcdef"})["credentials"], "FAIL")

    def test_base64_local_properties(self):
        self.assertEqual(self.check({"LOCAL_PROPERTIES": base64.b64encode(self.valid.encode()).decode()})["credentials"], "PASS")

    def test_bad_base64(self):
        self.assertEqual(self.check({"LOCAL_PROPERTIES": "!not-base64!"})["credentials"], "FAIL")

    def test_invalid_id(self):
        (self.root / "local.properties").write_text(self.valid.replace("1234567", "hello"))
        self.assertEqual(self.check()["credentials"], "FAIL")

    def test_invalid_hash(self):
        (self.root / "local.properties").write_text(self.valid.replace("0123456789abcdef0123456789abcdef", "invalid"))
        self.assertEqual(self.check()["credentials"], "FAIL")

    def test_default_credential_rejected(self):
        (self.root / "local.properties").write_text(self.valid.replace("1234567", "6"))
        self.assertEqual(self.check()["credentials"], "FAIL")

    def test_wrong_package_rejected(self):
        (self.root / "local.properties").write_text(self.valid)
        self.assertEqual(self.check(app_id="com.exteraless.app")["application-id"], "FAIL")

    def test_source_missing(self):
        (self.root / "settings.gradle").unlink()
        self.assertEqual(self.check()["source"], "FAIL")

    def test_internet_missing(self):
        p = self.root / "TMessagesProj/src/main/AndroidManifest.xml"
        p.write_text(p.read_text().replace("android.permission.INTERNET", "android.permission.CAMERA"))
        self.assertEqual(self.check()["internet"], "FAIL")

    def test_fixed_authority_warns(self):
        p = self.root / "TMessagesProj/src/main/AndroidManifest.xml"
        p.write_text(p.read_text().replace("${applicationId}.provider", "com.exteraless.app.provider"))
        self.assertEqual(self.check()["authorities"], "WARN")

    def test_gitignore_guard(self):
        (self.root / ".gitignore").write_text("local.properties\n")
        self.assertEqual(self.check()["gitignore"], "FAIL")


if __name__ == "__main__":
    unittest.main()
