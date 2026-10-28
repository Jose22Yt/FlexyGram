"""Regression for the physically reported Alpha1279 invisible Smart Previews.

Old code checked groupMessages == null, but DialogCell.update() receives a
singleton list from MessagesController.dialogMessage for ordinary latest files.
This test exercises the exact production Java helper through the existing
test_signature_smart_previews JVM probe, and audits the hotfix scope.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
DIALOG=ROOT/"TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java"
CLASSIFIER=ROOT/"TMessagesProj/src/main/java/app/flexygram/home/SignatureSmartPreviews.java"

class Alpha1279SmartPreviewRegression(unittest.TestCase):
    def test_real_dialog_cell_uses_singleton_guard(self):
        source=DIALOG.read_text()
        self.assertIn("SignatureSmartPreviews.allowsSingleMessagePreview(groupMessages)",source)
        self.assertNotIn("&& groupMessages == null",source)
        self.assertIn("messageString=applyThumbs(label)",source)
        self.assertIn("&& !isForumCell() && !isFolderCell() && !hasTags()",source)
        self.assertIn("smartPreviewKind=candidate",source)
        classifier=CLASSIFIER.read_text()
        self.assertIn("return groupedMessages == null || groupedMessages.size() <= 1;",classifier)

    def test_compiled_jvm_probe_covers_singleton_and_album(self):
        from test_signature_smart_previews import SmartPreviews
        SmartPreviews().test_compiled_production_palette_and_classifier()

    def test_review_refuses_unrecognized_blob(self):
        import smart_previews1279_hotfix_contract as hotfix
        import integration1279_contract as integration
        hotfix.verify_current()
        integration.verify_current()
        name="TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java"
        current=(ROOT/name).read_bytes()
        self.assertEqual(hotfix.original(name),hotfix.restore(name,current))
        self.assertEqual(current+b"// UNREVIEWED",hotfix.restore(name,current+b"// UNREVIEWED"))

if __name__=="__main__":unittest.main()
