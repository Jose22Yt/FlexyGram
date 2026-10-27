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
    public static int kind(MessageObject message){
        if(message==null||message.messageOwner==null||message.hasHighlightedWords())return 0;
        if(message.messageOwner.media!=null&&message.messageOwner.media.ttl_seconds!=0)return 0;
        // Never reveal the contents of an intentionally concealed spoiler by
        // converting it into a plain text URL/document preview.
        if (message.messageOwner.entities != null) {
            for (TLRPC.MessageEntity entity : message.messageOwner.entities) {
                if (entity instanceof TLRPC.TL_messageEntitySpoiler) return 0;
            }
        }
        if(message.messageOwner.action instanceof TLRPC.TL_messageActionChatAddUser
                ||message.messageOwner.action instanceof TLRPC.TL_messageActionChatJoinedByLink){
            return SignatureSmartPreviewPalette.EVENT;
        }
        // A standalone URL with a Telegram webpage preview is still a LINK.
        // Non-standalone prose, link captions and media captions keep native
        // text/spoilers/formatting; never parse URLs by network.
        String text=message.messageOwner.message;
        boolean standaloneUrl=false;
        if(text!=null){
            String value=text.trim();
            standaloneUrl=!value.isEmpty()&&!value.contains(" ")&&value.indexOf((char)10)<0 && value.indexOf((char)9)<0
                    &&(value.startsWith("https://")||value.startsWith("http://")||value.startsWith("www."));
        }
        if(message.messageOwner.media instanceof TLRPC.TL_messageMediaWebPage && standaloneUrl)
            return SignatureSmartPreviewPalette.LINK;
        // A caption is native user text even for media messages without a
        // fully resolved media object (e.g. preloading, synthetic test doubles).
        if(!TextUtils.isEmpty(message.messageOwner.message)
                && (message.isVoice() || message.isMusic() || message.isDocument()
                    || message.isVideo() || message.isPhoto()))return 0;
        if(message.messageOwner.media!=null
                &&!TextUtils.isEmpty(message.messageOwner.message))return 0;
        if(message.isVoice())return SignatureSmartPreviewPalette.VOICE;
        if(message.isMusic())return SignatureSmartPreviewPalette.MUSIC;
        if(message.isDocument())return SignatureSmartPreviewPalette.FILE;
        if(message.isVideo())return SignatureSmartPreviewPalette.VIDEO;
        if(message.isPhoto())return SignatureSmartPreviewPalette.PHOTO;
        if(standaloneUrl && (message.messageOwner.media==null || message.isMediaEmpty()))
            return SignatureSmartPreviewPalette.LINK;
        return 0;
    }
    private static int firstStop(String value,int end,char separator){
        int pos=value.indexOf(separator);
        return pos>=0&&pos<end?pos:end;
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
                if(url.length()>52)url=url.substring(0,52);
                return "🔗  "+(url.isEmpty()?LocaleController.getString(R.string.FlexySmartLink):url);
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
