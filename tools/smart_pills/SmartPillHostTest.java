/* SPDX-License-Identifier: GPL-3.0-or-later */
import app.flexygram.home.SignatureMiniPillClassifier;
import app.flexygram.home.SignatureSmartPreviewPalette;
import app.flexygram.home.SignatureSmartPillLayout;

public final class SmartPillHostTest {
    private static int checks;
    private static void eq(int expected, int actual, String name) {
        checks++;
        if (expected != actual) throw new AssertionError(name + ": " + actual + " expected " + expected);
    }
    private static void yes(boolean ok, String name) {
        checks++;
        if (!ok) throw new AssertionError(name);
    }
    public static void main(String[] args) {
        int[] expected = {
            SignatureSmartPreviewPalette.PDF, SignatureSmartPreviewPalette.TXT,
            SignatureSmartPreviewPalette.ZIP, SignatureSmartPreviewPalette.RAR,
            SignatureSmartPreviewPalette.ARCHIVE, SignatureSmartPreviewPalette.APK,
            SignatureSmartPreviewPalette.PNG, SignatureSmartPreviewPalette.JPG,
            SignatureSmartPreviewPalette.IMAGE_FILE, SignatureSmartPreviewPalette.GIF,
            SignatureSmartPreviewPalette.MUSIC, SignatureSmartPreviewPalette.VIDEO,
            SignatureSmartPreviewPalette.DOCUMENT, SignatureSmartPreviewPalette.SPREADSHEET,
            SignatureSmartPreviewPalette.PRESENTATION
        };
        String[] names = {
            "terms.PDF", "readme.txt", "backup.zip", "archive.rar", "textures.7Z",
            "release.apk", "wall.png", "photo.JPEG", "sticker.webp", "animation.gif",
            "song.flac", "movie.mp4", "proposal.docx", "budget.xlsx", "slides.pptx"
        };
        for (int i = 0; i < names.length; i++) eq(expected[i],
                SignatureMiniPillClassifier.documentType(names[i], null), names[i]);
        eq(SignatureSmartPreviewPalette.PDF,
                SignatureMiniPillClassifier.documentType("unknown", "application/pdf"), "mime");
        eq(SignatureSmartPreviewPalette.FILE,
                SignatureMiniPillClassifier.documentType("unknown.abc", "other/unknown"), "fallback");
        eq(SignatureSmartPreviewPalette.ADMIN,
                SignatureMiniPillClassifier.senderRole(false, true), "known admin");
        eq(SignatureSmartPreviewPalette.OWNER,
                SignatureMiniPillClassifier.senderRole(true, true), "known owner wins");
        eq(SignatureSmartPreviewPalette.NONE,
                SignatureMiniPillClassifier.senderRole(false, false), "unknown role must not invent admin");
        yes(!SignatureMiniPillClassifier.canIdentifyWallpaperFromExtensionOnly(), "wallpaper requires evidence");
        eq(237, SignatureSmartPillLayout.remaining(350f, 35, 20, 40, 18), "bounds");
        eq(0, SignatureSmartPillLayout.remaining(50f, 30, 20, 40, 18), "narrow");
        eq(0, SignatureSmartPillLayout.remaining(Float.NaN, 0, 0, 0, 0), "NaN");
        for (int mode = 0; mode < 3; mode++) {
            for (int type = 1; type <= SignatureSmartPreviewPalette.OWNER; type++) {
                SignatureSmartPreviewPalette p = new SignatureSmartPreviewPalette();
                p.update(type, mode, 0xff438bd0, 0xfff5f6f9);
                yes(SignatureSmartPreviewPalette.contrast(p.foreground(), p.background()) >= 4.49,
                        "light contrast type=" + type + " mode=" + mode);
                p.update(type, mode, 0xff87aaf1, 0xff152030);
                yes(SignatureSmartPreviewPalette.contrast(p.foreground(), p.background()) >= 4.49,
                        "dark contrast type=" + type + " mode=" + mode);
            }
        }
        System.out.println("SmartPillHostTest PASS: " + checks + " assertions");
    }
}
