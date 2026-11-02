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
        if (owner.restriction_reason != null && !owner.restriction_reason.isEmpty()) return 0;
        // Never expose hidden spoilers/restricted messages as unprotected text.
        if (owner.entities != null) for (TLRPC.MessageEntity entity : owner.entities) {
            if (entity instanceof TLRPC.TL_messageEntitySpoiler) return 0;
        }
        if (owner.action instanceof TLRPC.TL_messageActionChatAddUser
                || owner.action instanceof TLRPC.TL_messageActionChatJoinedByLink)
            return SignatureSmartPreviewPalette.JOINED;
        if (owner.action instanceof TLRPC.TL_messageActionChatDeleteUser) {
            long departed=((TLRPC.TL_messageActionChatDeleteUser)owner.action).user_id;
            return owner.from_id!=null && owner.from_id.user_id==departed
                    ? SignatureSmartPreviewPalette.LEFT : SignatureSmartPreviewPalette.EVENT;
        }
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
        if (message.isAyuDeleted()) return SignatureSmartPreviewPalette.DELETED;
        int role = senderRole(message);
        if (role != 0) return role;
        // Actual channel-post flag, not a guess that the author is an admin.
        if (owner.post) return SignatureSmartPreviewPalette.CHANNEL;
        if (owner.edit_date > 0) return SignatureSmartPreviewPalette.EDITED;
        return 0;
    }

    /** Cached Telegram participant records only; never performs a load/request. */
    public static int senderRole(MessageObject message) {
        if (message == null || message.messageOwner == null || message.getDialogId() >= 0
                || message.messageOwner.from_id == null || message.messageOwner.from_id.user_id == 0) return 0;
        long sender = message.messageOwner.from_id.user_id, chat = -message.getDialogId();
        org.telegram.messenger.MessagesController controller =
                org.telegram.messenger.MessagesController.getInstance(message.currentAccount);
        TLRPC.ChannelParticipant participant = controller.getAdminInChannel(sender, chat);
        if (participant instanceof TLRPC.TL_channelParticipantCreator) return SignatureSmartPreviewPalette.OWNER;
        if (participant instanceof TLRPC.TL_channelParticipantAdmin) return SignatureSmartPreviewPalette.ADMIN;
        TLRPC.ChatFull full = controller.getChatFull(chat);
        if (full != null && full.participants != null) {
            for (TLRPC.ChatParticipant p : full.participants.participants) {
                if (p.user_id != sender) continue;
                if (p instanceof TLRPC.TL_chatParticipantCreator) return SignatureSmartPreviewPalette.OWNER;
                if (p instanceof TLRPC.TL_chatParticipantAdmin) return SignatureSmartPreviewPalette.ADMIN;
                break;
            }
        }
        return 0;
    }
    public static int secondaryKind(MessageObject message, int primary) {
        if (message == null || message.messageOwner == null) return 0;
        int kind = message.isAyuDeleted() ? SignatureSmartPreviewPalette.DELETED : senderRole(message);
        if (kind == 0 && message.messageOwner.edit_date > 0) kind = SignatureSmartPreviewPalette.EDITED;
        if (kind == 0 && message.messageOwner.post) kind = SignatureSmartPreviewPalette.CHANNEL;
        return kind == primary ? 0 : kind;
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
            case SignatureSmartPreviewPalette.DELETED: return LocaleController.getString(R.string.FlexyPillDeleted);
            case SignatureSmartPreviewPalette.OWNER: return LocaleController.getString(R.string.FlexyPillOwner);
            case SignatureSmartPreviewPalette.EVENT: return LocaleController.getString(R.string.FlexyPillEvent);
            default: return "";
        }
    }

    public static int iconKind(int kind) {
        switch (kind) {
            case SignatureSmartPreviewPalette.ZIP:
            case SignatureSmartPreviewPalette.RAR:
            case SignatureSmartPreviewPalette.ARCHIVE:
                return 10;
            case SignatureSmartPreviewPalette.VOICE:
                return 2;
            case SignatureSmartPreviewPalette.MUSIC:
                return 3;
            case SignatureSmartPreviewPalette.LINK:
                return 4;
            case SignatureSmartPreviewPalette.EVENT:
            case SignatureSmartPreviewPalette.JOINED:
            case SignatureSmartPreviewPalette.LEFT:
            case SignatureSmartPreviewPalette.PINNED:
                return 5;
            case SignatureSmartPreviewPalette.PHOTO:
            case SignatureSmartPreviewPalette.PNG:
            case SignatureSmartPreviewPalette.JPG:
            case SignatureSmartPreviewPalette.IMAGE_FILE:
                return 6;
            case SignatureSmartPreviewPalette.VIDEO:
            case SignatureSmartPreviewPalette.GIF:
                return 7;
            case SignatureSmartPreviewPalette.LOCATION:
                return 8;
            case SignatureSmartPreviewPalette.CONTACT:
                return 9;
            default:
                return 1;
        }
    }

    public static String snippet(MessageObject message, int kind) {
        return snippet(message, kind, null);
    }

    public static String snippet(MessageObject message, int kind, java.util.List<?> groupMessages) {
        if (message == null || message.messageOwner == null) return "";
        TLRPC.Message owner = message.messageOwner;
        if (message.isDocument()) {
            TLRPC.Document document = message.getDocument();
            String filename = document == null ? null : FileLoader.getDocumentFileName(document);
            if (!TextUtils.isEmpty(filename)) {
                String safe = filename.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ');
                if (safe.length() > 120) safe = safe.substring(0, 88) + "…" + safe.substring(safe.length() - 31);
                return clean(safe);
            }
            boolean isArchive = (kind == SignatureSmartPreviewPalette.ZIP || kind == SignatureSmartPreviewPalette.RAR || kind == SignatureSmartPreviewPalette.ARCHIVE);
            return LocaleController.getString(isArchive ? R.string.FlexySmartArchive : R.string.FlexySmartFile);
        }
        if (kind == SignatureSmartPreviewPalette.VOICE) {
            int seconds = (int) Math.max(0, Math.min(86400, message.getDuration()));
            String time = (seconds / 60) + ":" + (seconds % 60 < 10 ? "0" : "") + (seconds % 60);
            return time + "  |||ı|ı||ı|";
        }
        if (kind == SignatureSmartPreviewPalette.MUSIC) {
            String title = message.getMusicTitle();
            if (!TextUtils.isEmpty(title)) return clean(title);
            return LocaleController.getString(R.string.FlexySmartMusic);
        }
        if (kind == SignatureSmartPreviewPalette.LINK) {
            String label = label(message, SignatureSmartPreviewPalette.LINK);
            int split = label.indexOf("  ");
            return clean(split >= 0 ? label.substring(split + 2) : label);
        }
        if (kind == SignatureSmartPreviewPalette.PHOTO) {
            if (groupMessages != null && groupMessages.size() > 1) {
                return String.format(LocaleController.getString(R.string.FlexySmartPhotosCount), groupMessages.size());
            }
            return LocaleController.getString(R.string.FlexySmartPhoto);
        }
        if (kind == SignatureSmartPreviewPalette.VIDEO) {
            int seconds = (int) Math.max(0, Math.min(86400, message.getDuration()));
            if (seconds > 0) {
                return LocaleController.getString(R.string.FlexySmartVideo) + " · " + (seconds / 60) + ":" + (seconds % 60 < 10 ? "0" : "") + (seconds % 60);
            }
            return LocaleController.getString(R.string.FlexySmartVideo);
        }
        if (kind == SignatureSmartPreviewPalette.LOCATION) {
            return LocaleController.getString(R.string.FlexySmartLocation);
        }
        if (kind == SignatureSmartPreviewPalette.CONTACT) {
            if (owner.media instanceof TLRPC.TL_messageMediaContact) {
                TLRPC.MessageMedia contact = owner.media;
                String name = ((contact.first_name == null ? "" : contact.first_name) + " " + (contact.last_name == null ? "" : contact.last_name)).trim();
                if (!TextUtils.isEmpty(name)) return clean(name);
            }
            return LocaleController.getString(R.string.FlexySmartContact);
        }
        if (kind == SignatureSmartPreviewPalette.JOINED) {
            CharSequence event = message.messageText;
            return clean(!TextUtils.isEmpty(event) ? event.toString() : LocaleController.getString(R.string.FlexySmartJoined));
        }
        if (kind == SignatureSmartPreviewPalette.LEFT) {
            CharSequence event = message.messageText;
            return clean(!TextUtils.isEmpty(event) ? event.toString() : LocaleController.getString(R.string.FlexySmartLeft));
        }
        if (kind == SignatureSmartPreviewPalette.PINNED) {
            CharSequence event = message.messageText;
            return clean(!TextUtils.isEmpty(event) ? event.toString() : LocaleController.getString(R.string.FlexySmartPinned));
        }
        if (kind == SignatureSmartPreviewPalette.EVENT) {
            CharSequence event = message.messageText;
            return clean(TextUtils.isEmpty(event) ? LocaleController.getString(R.string.FlexySmartGroupEvent) : event.toString());
        }
        if (!TextUtils.isEmpty(owner.message)) return clean(owner.message);
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
