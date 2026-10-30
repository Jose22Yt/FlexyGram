/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.text.TextUtils;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.FileLoader;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.tgnet.TLRPC;

/**
 * Dialog-list-only smart snippet. Reads already loaded MessageObject metadata:
 * no media decoding, thumbnails, URL fetches or message database queries.
 */
public final class SignatureSmartPreviews {
    private static final String PREFS="flexy_signature_smart_previews";
    private static volatile int cachedMode=-1;
    private SignatureSmartPreviews(){}
    public static int mode(){
        int result=cachedMode;
        if(result>=0)return result;
        synchronized(SignatureSmartPreviews.class){
            if(cachedMode<0){
                int stored=ApplicationLoader.applicationContext.getSharedPreferences(PREFS,Context.MODE_PRIVATE)
                        .getInt("palette",SignatureSmartPreviewPalette.ADAPTIVE);
                cachedMode=stored>=0&&stored<=3?stored:0;
            }
            return cachedMode;
        }
    }
    public static void setMode(int next){
        if(next<0||next>3)throw new IllegalArgumentException("palette mode");
        cachedMode=next;
        ApplicationLoader.applicationContext.getSharedPreferences(PREFS,Context.MODE_PRIVATE)
                .edit().putInt("palette",next).apply();
    }
    /**
     * Telegram stores ordinary dialog previews as singleton ArrayLists in
     * MessagesController.dialogMessage; null is NOT the normal non-album case.
     * Only multi-message albums should retain the native grouped caption.
     */
    public static boolean allowsSingleMessagePreview(java.util.List<?> groupedMessages) {
        return groupedMessages == null || groupedMessages.size() <= 1;
    }
    public static int kind(MessageObject message) {
        if (message == null || message.messageOwner == null || message.hasHighlightedWords()
                || message.needDrawBluredPreview()) return SignatureSmartPreviewPalette.NONE;
        TLRPC.Message owner = message.messageOwner;
        if (owner.media != null && owner.media.ttl_seconds != 0) return 0;
        // Never expose hidden spoilers/restricted messages as unprotected text.
        if (owner.entities != null) for (TLRPC.MessageEntity entity : owner.entities) {
            if (entity instanceof TLRPC.TL_messageEntitySpoiler) return 0;
        }
        if (owner.action instanceof TLRPC.TL_messageActionChatAddUser
                || owner.action instanceof TLRPC.TL_messageActionChatJoinedByLink)
            return SignatureSmartPreviewPalette.JOINED;
        if (owner.action instanceof TLRPC.TL_messageActionChatDeleteUser)
            return SignatureSmartPreviewPalette.LEFT;
        if (owner.action instanceof TLRPC.TL_messageActionPinMessage)
            return SignatureSmartPreviewPalette.PINNED;
        if (owner.action != null) return 0; // Unknown system events stay native.

        if (owner.media instanceof TLRPC.TL_messageMediaContact) return SignatureSmartPreviewPalette.CONTACT;
        if (owner.media instanceof TLRPC.TL_messageMediaGeo
                || owner.media instanceof TLRPC.TL_messageMediaGeoLive
                || owner.media instanceof TLRPC.TL_messageMediaVenue)
            return SignatureSmartPreviewPalette.LOCATION;
        if (owner.media instanceof TLRPC.TL_messageMediaPoll) return SignatureSmartPreviewPalette.POLL;
        if (message.isVoice()) return SignatureSmartPreviewPalette.VOICE;
        if (message.isMusic()) return SignatureSmartPreviewPalette.MUSIC;
        if (message.isVideo()) return SignatureSmartPreviewPalette.VIDEO;
        if (message.isPhoto()) return SignatureSmartPreviewPalette.PHOTO;
        if (message.isSticker()) return SignatureSmartPreviewPalette.STICKER;
        if (message.isGif()) return SignatureSmartPreviewPalette.GIF;
        if (message.isDocument()) {
            TLRPC.Document doc = message.getDocument();
            return SignatureMiniPillClassifier.documentType(doc == null ? null : FileLoader.getDocumentFileName(doc),
                    doc == null ? null : doc.mime_type);
        }

        // A standalone URL does not require network access or content parsing.
        String text = owner.message;
        if (text != null) {
            String url = text.trim();
            if (!url.isEmpty() && url.indexOf(' ') < 0 && url.indexOf('\n') < 0
                    && url.indexOf('\t') < 0 && (url.startsWith("https://")
                    || url.startsWith("http://") || url.startsWith("www.")))
                return SignatureSmartPreviewPalette.LINK;
        }
        // Actual channel-post flag, not a guess that the author is an admin.
        if (owner.post) return SignatureSmartPreviewPalette.CHANNEL;
        if (owner.edit_date > 0) return SignatureSmartPreviewPalette.EDITED;
        return 0;
    }

    public static String badgeLabel(int kind) {
        switch (kind) {
            case SignatureSmartPreviewPalette.PDF: return "PDF";
            case SignatureSmartPreviewPalette.TXT: return "TXT";
            case SignatureSmartPreviewPalette.ZIP: return "ZIP";
            case SignatureSmartPreviewPalette.RAR: return "RAR";
            case SignatureSmartPreviewPalette.ARCHIVE: return "7Z";
            case SignatureSmartPreviewPalette.APK: return "APK";
            case SignatureSmartPreviewPalette.PNG: return "PNG";
            case SignatureSmartPreviewPalette.JPG: return "JPG";
            case SignatureSmartPreviewPalette.IMAGE_FILE: return "WEBP";
            case SignatureSmartPreviewPalette.GIF: return "GIF";
            case SignatureSmartPreviewPalette.FILE: return LocaleController.getString(R.string.FlexyPillFile);
            case SignatureSmartPreviewPalette.DOCUMENT: return "DOC";
            case SignatureSmartPreviewPalette.SPREADSHEET: return "XLS";
            case SignatureSmartPreviewPalette.PRESENTATION: return "PPT";
            case SignatureSmartPreviewPalette.PHOTO: return LocaleController.getString(R.string.FlexyPillPhoto);
            case SignatureSmartPreviewPalette.VIDEO: return LocaleController.getString(R.string.FlexyPillVideo);
            case SignatureSmartPreviewPalette.MUSIC: return LocaleController.getString(R.string.FlexyPillMusic);
            case SignatureSmartPreviewPalette.VOICE: return LocaleController.getString(R.string.FlexyPillVoice);
            case SignatureSmartPreviewPalette.LINK: return "WEB";
            case SignatureSmartPreviewPalette.LOCATION: return LocaleController.getString(R.string.FlexyPillLocation);
            case SignatureSmartPreviewPalette.CONTACT: return LocaleController.getString(R.string.FlexyPillContact);
            case SignatureSmartPreviewPalette.STICKER: return LocaleController.getString(R.string.FlexyPillSticker);
            case SignatureSmartPreviewPalette.POLL: return LocaleController.getString(R.string.FlexyPillPoll);
            case SignatureSmartPreviewPalette.JOINED: return LocaleController.getString(R.string.FlexyPillJoined);
            case SignatureSmartPreviewPalette.LEFT: return LocaleController.getString(R.string.FlexyPillLeft);
            case SignatureSmartPreviewPalette.PINNED: return LocaleController.getString(R.string.FlexyPillPinned);
            case SignatureSmartPreviewPalette.EDITED: return LocaleController.getString(R.string.FlexyPillEdited);
            case SignatureSmartPreviewPalette.CHANNEL: return LocaleController.getString(R.string.FlexyPillChannel);
            case SignatureSmartPreviewPalette.ADMIN: return LocaleController.getString(R.string.FlexyPillAdmin);
            case SignatureSmartPreviewPalette.OWNER: return LocaleController.getString(R.string.FlexyPillOwner);
            case SignatureSmartPreviewPalette.EVENT: return LocaleController.getString(R.string.FlexyPillEvent);
            default: return "";
        }
    }

    /** Adjacent native snippet; never put file names inside the colored capsule. */
    public static String snippet(MessageObject message, int kind) {
        if (message == null || message.messageOwner == null) return "";
        TLRPC.Message owner = message.messageOwner;
        if (message.isDocument()) {
            String filename = FileLoader.getDocumentFileName(message.getDocument());
            if (!TextUtils.isEmpty(filename)) return clean(filename);
        }
        if (kind == SignatureSmartPreviewPalette.JOINED
                || kind == SignatureSmartPreviewPalette.LEFT
                || kind == SignatureSmartPreviewPalette.PINNED) {
            return clean(message.messageText == null ? "" : message.messageText.toString());
        }
        if (kind == SignatureSmartPreviewPalette.LINK) {
            String label = label(message, SignatureSmartPreviewPalette.LINK);
            int split = label.indexOf("  ");
            return clean(split >= 0 ? label.substring(split + 2) : label);
        }
        if (!TextUtils.isEmpty(owner.message)) return clean(owner.message);
        if (kind == SignatureSmartPreviewPalette.MUSIC) return clean(message.getMusicTitle());
        if (kind == SignatureSmartPreviewPalette.VOICE) return lineLabel(message, SignatureSmartPreviewPalette.VOICE).replace("🎤  ", "");
        return "";
    }

    private static String clean(String value) {
        if (value == null) return "";
        // One-line only. Drop controls; preserve Unicode names and user text.
        StringBuilder out = new StringBuilder(Math.min(120, value.length()));
        for (int i = 0; i < value.length() && out.length() < 120; i++) {
            char c = value.charAt(i);
            out.append(Character.isISOControl(c) ? ' ' : c);
        }
        return out.toString().trim();
    }

    private static int firstStop(String value,int end,char separator){
        int pos=value.indexOf(separator);
        return pos>=0&&pos<end?pos:end;
    }
    /** A filename/contact may contain control characters; never grow the native preview row. */
    public static String lineLabel(MessageObject message,int kind){
        return label(message,kind).replace('\n',' ').replace('\r',' ').replace('\t',' ');
    }
    public static String label(MessageObject message,int kind){
        if(message==null||message.messageOwner==null)return "";
        switch(kind){
            case SignatureSmartPreviewPalette.VOICE:{
                int seconds=(int)Math.max(0,Math.min(86400,message.getDuration()));
                return "🎤  "+(seconds/60)+":"+(seconds%60<10?"0":"")+(seconds%60);
            }
            case SignatureSmartPreviewPalette.FILE:{
                String file=FileLoader.getDocumentFileName(message.getDocument());
                return "📄  "+(TextUtils.isEmpty(file)?LocaleController.getString(R.string.FlexySmartFile):file);
            }
            case SignatureSmartPreviewPalette.MUSIC:{
                String title=message.getMusicTitle();
                return "♫  "+(TextUtils.isEmpty(title)?LocaleController.getString(R.string.FlexySmartMusic):title);
            }
            case SignatureSmartPreviewPalette.LINK:{
                String url=message.messageOwner.message;
                if(TextUtils.isEmpty(url))return "🔗  "+LocaleController.getString(R.string.FlexySmartLink);
                // The preview is a compact host label, never a network fetch.
                // Discard paths, queries and fragments to keep tracking codes or
                // long tokens out of the main chat list.
                url=url.trim();
                int scheme=url.indexOf("://");
                if(scheme>=0)url=url.substring(scheme+3);
                int end=url.length();
                end=firstStop(url,end,'/');
                end=firstStop(url,end,'?');
                end=firstStop(url,end,'#');
                end=firstStop(url,end,'\n');
                end=firstStop(url,end,'\r');
                url=url.substring(0,end);
                int credentials=url.lastIndexOf('@');
                if(credentials>=0)url=url.substring(credentials+1);
                if(url.length()>52)url=url.substring(0,52);
                return "🔗  "+(url.isEmpty()?LocaleController.getString(R.string.FlexySmartLink):url);
            }
            case SignatureSmartPreviewPalette.LOCATION:
                return "📍  "+LocaleController.getString(R.string.FlexySmartLocation);
            case SignatureSmartPreviewPalette.CONTACT:{
                if(!(message.messageOwner.media instanceof TLRPC.TL_messageMediaContact))return "";
                TLRPC.MessageMedia contact=message.messageOwner.media;
                String name=((contact.first_name==null?"":contact.first_name)+" "+(contact.last_name==null?"":contact.last_name)).trim();
                return "👤  "+(name.isEmpty()?LocaleController.getString(R.string.FlexySmartContact):name);
            }
            case SignatureSmartPreviewPalette.PHOTO:return "▣  "+LocaleController.getString(R.string.FlexySmartPhoto);
            case SignatureSmartPreviewPalette.VIDEO:return "▶  "+LocaleController.getString(R.string.FlexySmartVideo);
            case SignatureSmartPreviewPalette.EVENT:{
                CharSequence event=message.messageText;
                return "♧  "+(TextUtils.isEmpty(event)?LocaleController.getString(R.string.FlexySmartGroupEvent):event.toString());
            }
            default:return "";
        }
    }
}
