"""Source-level regressions for the optional FlexyFiles Native 2.0 viewer.

These checks do not claim Android compilation, frame-rate measurements or
physical-device acceptance. The existing SelectedDocument hostile-file probe
remains the authority for ZIP validation and limits.
"""
from pathlib import Path
from xml.etree import ElementTree
import unittest

ROOT = Path(__file__).resolve().parents[2]
JAVA = ROOT / "TMessagesProj/src/main/java/app/flexygram/files"
RES = ROOT / "TMessagesProj/src/main/res"


class NativeViewerContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sheet = (JAVA / "FlexyFilesSheet.java").read_text()
        cls.viewer = (JAVA / "FlexyFilesNativePreview.java").read_text()
        cls.entry = (JAVA / "FlexyFiles.java").read_text()
        cls.core = (JAVA / "core/SelectedDocument.java").read_text()

    def test_same_native_sheet_for_explorer_and_preview(self):
        self.assertIn("extends BottomSheet", self.sheet)
        self.assertIn("new FlexyFilesNativePreview(", self.sheet)
        self.assertIn("browserPanel.setVisibility(View.GONE)", self.sheet)
        self.assertIn("browserPanel.setVisibility(View.VISIBLE)", self.sheet)
        self.assertIn("if (previewing) { leavePreview(); return; }", self.sheet)
        self.assertIn("openPreview(null, sheet.name, ready.size())", self.sheet)
        self.assertIn("this::leavePreview, this::editPreview", self.sheet)
        self.assertNotIn("new FlexyFilesSheet(", self.viewer)

    def test_read_decode_and_chunk_outside_ui_thread(self):
        self.assertIn("tasks.submit(() -> {", self.sheet)
        self.assertIn("selected.read(entry, limit)", self.sheet)
        self.assertIn("new FlexyFilesNativePreview.TextData(SelectedDocument.text(bytes))", self.sheet)
        self.assertIn("AndroidUtilities.runOnUIThread(() -> {", self.sheet)
        self.assertIn("TextAdapter extends RecyclerListView.SelectionAdapter", self.viewer)
        self.assertIn("setItemAnimator(null)", self.viewer)
        self.assertIn("setHasFixedSize(true)", self.viewer)
        self.assertIn("TEXT_CHUNK = 3072", self.viewer)
        self.assertIn("MAX_IMAGE_PIXELS = 32_000_000", self.viewer)
        self.assertIn("options.inSampleSize *= 2", self.viewer)
        self.assertNotIn("new WebView(", self.sheet)
        self.assertNotIn("new WebView(", self.viewer)

    def test_cancellation_and_bounded_retention(self):
        self.assertIn("work.cancel()", self.sheet)
        self.assertIn("tasks.current(token)", self.sheet)
        self.assertIn("previewPanel.release()", self.sheet)
        self.assertIn("work.close()", self.sheet)
        self.assertIn("folderCache.clear()", self.sheet)
        self.assertIn("return size() > 8", self.sheet)
        self.assertIn("result.size() <= 128", self.sheet)
        self.assertIn("SelectedDocument.MAX_TEXT", self.sheet)
        self.assertIn("FlexyFilesNativePreview.MAX_IMAGE_BYTES", self.sheet)
        self.assertIn("MAX_ARCHIVE = 128L * 1024 * 1024", self.core)
        self.assertIn("new FlexyFileEditorActivity(", self.sheet)
        self.assertIn("enabled()", self.entry)

    def test_translations_cover_new_actions(self):
        expected = {
            "FlexyFilesNativeBack", "FlexyFilesNativeEdit", "FlexyFilesNativeImage",
            "FlexyFilesNativeTooLarge", "FlexyFilesNativeUnsupported",
        }
        keys = []
        for language in ("values", "values-es", "values-ru"):
            root = ElementTree.parse(RES / language / "flexyfiles.xml").getroot()
            labels = [node.attrib["name"] for node in root.findall("string")]
            self.assertEqual(len(labels), len(set(labels)), language)
            self.assertTrue(expected.issubset(labels), language)
            self.assertTrue(all(node.text for node in root), language)
            keys.append(set(labels))
        self.assertEqual(keys[0], keys[1])
        self.assertEqual(keys[0], keys[2])


if __name__ == "__main__":
    unittest.main()
