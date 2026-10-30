/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import java.util.Locale;

/** Pure metadata classifier. Never opens, reads or downloads an attachment. */
public final class SignatureMiniPillClassifier {
    private SignatureMiniPillClassifier() {}

    public static int documentType(String filename, String mime) {
        String extension = "";
        if (filename != null) {
            int dot = filename.lastIndexOf('.');
            if (dot >= 0 && dot + 1 < filename.length()) {
                extension = filename.substring(dot + 1).toLowerCase(Locale.ROOT);
            }
        }
        switch (extension) {
            case "pdf": return SignatureSmartPreviewPalette.PDF;
            case "txt": case "log": case "md": return SignatureSmartPreviewPalette.TXT;
            case "zip": return SignatureSmartPreviewPalette.ZIP;
            case "rar": return SignatureSmartPreviewPalette.RAR;
            case "7z": return SignatureSmartPreviewPalette.ARCHIVE;
            case "tar": case "gz": return SignatureSmartPreviewPalette.FILE;
            case "apk": case "apks": case "xapk": return SignatureSmartPreviewPalette.APK;
            case "png": return SignatureSmartPreviewPalette.PNG;
            case "jpg": case "jpeg": return SignatureSmartPreviewPalette.JPG;
            case "webp": return SignatureSmartPreviewPalette.IMAGE_FILE;
            case "gif": return SignatureSmartPreviewPalette.GIF;
            case "mp4": case "mkv": case "mov": case "webm": return SignatureSmartPreviewPalette.VIDEO;
            case "mp3": case "flac": case "ogg": case "wav": case "m4a": return SignatureSmartPreviewPalette.MUSIC;
            case "doc": case "docx": case "odt": case "rtf": return SignatureSmartPreviewPalette.DOCUMENT;
            case "xls": case "xlsx": case "ods": case "csv": return SignatureSmartPreviewPalette.SPREADSHEET;
            case "ppt": case "pptx": case "odp": return SignatureSmartPreviewPalette.PRESENTATION;
            default: break;
        }
        if (mime != null) {
            switch (mime.toLowerCase(Locale.ROOT)) {
                case "application/pdf": return SignatureSmartPreviewPalette.PDF;
                case "text/plain": return SignatureSmartPreviewPalette.TXT;
                case "application/zip": return SignatureSmartPreviewPalette.ZIP;
                case "application/vnd.android.package-archive": return SignatureSmartPreviewPalette.APK;
                case "image/png": return SignatureSmartPreviewPalette.PNG;
                case "image/jpeg": return SignatureSmartPreviewPalette.JPG;
                case "image/gif": return SignatureSmartPreviewPalette.GIF;
                case "audio/mpeg": return SignatureSmartPreviewPalette.MUSIC;
                case "video/mp4": return SignatureSmartPreviewPalette.VIDEO;
                default: break;
            }
        }
        return SignatureSmartPreviewPalette.FILE;
    }

    /** Only call with sender roles already confirmed by Telegram's locally loaded participant data. */
    public static int senderRole(boolean confirmedOwner, boolean confirmedAdmin) {
        return confirmedOwner ? SignatureSmartPreviewPalette.OWNER
                : confirmedAdmin ? SignatureSmartPreviewPalette.ADMIN : SignatureSmartPreviewPalette.NONE;
    }

    /** A filename alone cannot reliably prove that an image is a wallpaper. */
    public static boolean canIdentifyWallpaperFromExtensionOnly() { return false; }
}
