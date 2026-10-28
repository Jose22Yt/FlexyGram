from native_motion_restore_contract import read_current
"""Current boundary and preservation of native/signing contracts, not device evidence."""
from pathlib import Path
import subprocess,unittest
import alpha1280_contract as audit
ROOT=Path(__file__).resolve().parents[2]
class Alpha1280(unittest.TestCase):
    def test_exact_review_and_all_unknown_mutations_refused(self):
        audit.verify_current()
        for path in audit.spec()['reviewed']:
            raw=read_current(path)+b'\nUNREVIEWED'
            self.assertEqual(raw,audit.restore(path,raw),path)
    def test_version_is_only_change_to_signing_and_build_gates(self):
        for path in ('TMessagesProj/build.gradle','.github/workflows/connected-alpha-arm64.yml','tools/connected_alpha/build_private_apk.py'):
            from alpha1281_contract import restore
            before=audit.original(path);current=restore(path,read_current(path))
            self.assertIn(b'1280',current)
            self.assertEqual(before,current.replace(b'1280',b'1279'),path)
    def test_previous_reviews_and_protocol_storage_files_unchanged(self):
        for path in ('tools/connected_alpha/integration1279_review.json','tools/connected_alpha/signature1278_review.json','tools/connected_alpha/stability1277_review.json','tools/connected_alpha/smart_previews1279_hotfix_review.json','TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java','TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java','TMessagesProj/src/main/java/org/telegram/messenger/MessagesStorage.java','TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java','TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java'):
            self.assertEqual(audit.original(path),read_current(path),path)
    def test_prefetch_and_memory_pressure_have_native_lifecycle_hooks(self):
        s=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java').read_text()
        self.assertIn('super.onUpdateBackgroundDrawable(drawable);\n            ensureSignatureWallpaperBlur();',s)
        app=(ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java').read_text()
        self.assertIn('SignatureWallpaperBlur.trimMemory(level)',app)
        self.assertIn('public void onLowMemory()',app)
if __name__=='__main__':unittest.main()
