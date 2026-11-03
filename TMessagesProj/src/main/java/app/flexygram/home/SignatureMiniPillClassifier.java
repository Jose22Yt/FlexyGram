/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import java.util.Locale;

/** Pure metadata classifier. Never opens, reads or downloads an attachment. */
public final class SignatureMiniPillClassifier {
    private SignatureMiniPillClassifier() {}

    public static int documentType(String filename, String mime) {
        int extensionKind = extensionType(filename == null ? "" : filename.trim());
        String type = mime == null ? "" : mime.trim().toLowerCase(Locale.ROOT);
        int parameters = type.indexOf(';');
        if (parameters >= 0) type = type.substring(0, parameters).trim();
        int mimeKind = mimeType(type);
        // Office/APK files are ZIP containers; preserve their more specific extension.
        if (mimeKind == SignatureSmartPreviewPalette.ZIP && (extensionKind == SignatureSmartPreviewPalette.DOCUMENT
                || extensionKind == SignatureSmartPreviewPalette.SPREADSHEET
                || extensionKind == SignatureSmartPreviewPalette.PRESENTATION
                || extensionKind == SignatureSmartPreviewPalette.APK)) return extensionKind;
        // A concrete MIME is stronger evidence than a misleading filename suffix.
        if (mimeKind != SignatureSmartPreviewPalette.NONE) return mimeKind;
        return extensionKind == SignatureSmartPreviewPalette.NONE ? SignatureSmartPreviewPalette.FILE : extensionKind;
    }

    private static int extensionType(String filename) {
        int dot = filename.lastIndexOf('.');
        String extension = dot >= 0 && dot + 1 < filename.length()
                ? filename.substring(dot + 1).toLowerCase(Locale.ROOT) : "";
        switch (extension) {
            case "pdf": return SignatureSmartPreviewPalette.PDF;
            case "txt": case "log": case "md": case "json": case "xml": return SignatureSmartPreviewPalette.TXT;
            case "zip": return SignatureSmartPreviewPalette.ZIP;
            case "rar": return SignatureSmartPreviewPalette.RAR;
            case "7z": case "tar": case "gz": case "bz2": case "xz": case "tgz": return SignatureSmartPreviewPalette.ARCHIVE;
            case "apk": case "apks": case "xapk": case "apkm": return SignatureSmartPreviewPalette.APK;
            case "png": return SignatureSmartPreviewPalette.PNG;
            case "jpg": case "jpeg": return SignatureSmartPreviewPalette.JPG;
            case "webp": case "avif": case "heic": case "heif": case "bmp": case "tif": case "tiff": case "svg": return SignatureSmartPreviewPalette.IMAGE_FILE;
            case "gif": return SignatureSmartPreviewPalette.GIF;
            case "mp4": case "mkv": case "mov": case "webm": case "avi": case "m4v": case "3gp": case "mpeg": case "mpg": return SignatureSmartPreviewPalette.VIDEO;
            case "mp3": case "flac": case "ogg": case "opus": case "wav": case "m4a": case "aac": case "aiff": case "amr": return SignatureSmartPreviewPalette.MUSIC;
            case "doc": case "docx": case "odt": case "rtf": return SignatureSmartPreviewPalette.DOCUMENT;
            case "xls": case "xlsx": case "ods": case "csv": return SignatureSmartPreviewPalette.SPREADSHEET;
            case "ppt": case "pptx": case "odp": return SignatureSmartPreviewPalette.PRESENTATION;
            default: return SignatureSmartPreviewPalette.NONE;
        }
    }

    private static int mimeType(String mime) {
        switch (mime) {
            case "application/pdf": return SignatureSmartPreviewPalette.PDF;
            case "text/csv": return SignatureSmartPreviewPalette.SPREADSHEET;
            case "application/msword": case "application/rtf":
            case "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            case "application/vnd.oasis.opendocument.text": return SignatureSmartPreviewPalette.DOCUMENT;
            case "application/vnd.ms-excel":
            case "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            case "application/vnd.oasis.opendocument.spreadsheet": return SignatureSmartPreviewPalette.SPREADSHEET;
            case "application/vnd.ms-powerpoint":
            case "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            case "application/vnd.oasis.opendocument.presentation": return SignatureSmartPreviewPalette.PRESENTATION;
            case "application/json": case "application/xml": return SignatureSmartPreviewPalette.TXT;
            case "application/zip": case "application/x-zip-compressed": return SignatureSmartPreviewPalette.ZIP;
            case "application/vnd.rar": case "application/x-rar-compressed": return SignatureSmartPreviewPalette.RAR;
            case "application/x-7z-compressed": case "application/gzip": case "application/x-gzip":
            case "application/x-tar": case "application/x-bzip2": case "application/x-xz": return SignatureSmartPreviewPalette.ARCHIVE;
            case "application/vnd.android.package-archive": return SignatureSmartPreviewPalette.APK;
            case "image/png": return SignatureSmartPreviewPalette.PNG;
            case "image/jpeg": return SignatureSmartPreviewPalette.JPG;
            case "image/gif": return SignatureSmartPreviewPalette.GIF;
            default: break;
        }
        if (mime.startsWith("audio/")) return SignatureSmartPreviewPalette.MUSIC;
        if (mime.startsWith("video/")) return SignatureSmartPreviewPalette.VIDEO;
        if (mime.startsWith("image/")) return SignatureSmartPreviewPalette.IMAGE_FILE;
        if (mime.startsWith("text/")) return SignatureSmartPreviewPalette.TXT;
        return SignatureSmartPreviewPalette.NONE;
    }

    public static boolean isFileKind(int kind) {
        switch (kind) {
            case SignatureSmartPreviewPalette.FILE: case SignatureSmartPreviewPalette.PDF:
            case SignatureSmartPreviewPalette.TXT: case SignatureSmartPreviewPalette.ZIP:
            case SignatureSmartPreviewPalette.RAR: case SignatureSmartPreviewPalette.ARCHIVE:
            case SignatureSmartPreviewPalette.APK: case SignatureSmartPreviewPalette.PNG:
            case SignatureSmartPreviewPalette.JPG: case SignatureSmartPreviewPalette.IMAGE_FILE:
            case SignatureSmartPreviewPalette.DOCUMENT: case SignatureSmartPreviewPalette.SPREADSHEET:
            case SignatureSmartPreviewPalette.PRESENTATION: return true;
            default: return false;
        }
    }

    /** Accept web targets only, without opening them or inspecting their contents. */
    public static boolean isWebLink(String value) {
        if (value == null || value.length() > 8192) return false;
        int start;
        if (value.regionMatches(true, 0, "https://", 0, 8)) start = 8;
        else if (value.regionMatches(true, 0, "http://", 0, 7)) start = 7;
        else if (value.regionMatches(true, 0, "www.", 0, 4) && value.length() > 4) start = 0;
        else return false;
        if (value.length() <= start) return false;
        char first = value.charAt(start);
        if (first == '/' || first == '?' || first == '#' || first == ':') return false;
        for (int i = start; i < value.length(); i++) {
            char c = value.charAt(i);
            if (Character.isWhitespace(c) || Character.isISOControl(c)) return false;
        }
        return true;
    }

    /** Only call with sender roles already confirmed by Telegram's locally loaded participant data. */
    public static int senderRole(boolean confirmedOwner, boolean confirmedAdmin) {
        return confirmedOwner ? SignatureSmartPreviewPalette.OWNER
                : confirmedAdmin ? SignatureSmartPreviewPalette.ADMIN : SignatureSmartPreviewPalette.NONE;
    }

    /** A filename alone cannot reliably prove that an image is a wallpaper. */
    public static boolean canIdentifyWallpaperFromExtensionOnly() { return false; }
}
