/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.text.TextUtils;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.FileLoader;
import org.telegram.messenger.MessageObject;
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
        // Captions are user-written text and should retain the native preview.
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
    public static String label(MessageObject message,int kind){
        if(message==null||message.messageOwner==null)return "";
        switch(kind){
            case SignatureSmartPreviewPalette.VOICE:{
                int seconds=(int)Math.max(0,Math.min(86400,message.getDuration()));
                return "🎤  "+(seconds/60)+":"+(seconds%60<10?"0":"")+(seconds%60);
            }
            case SignatureSmartPreviewPalette.FILE:{
                String file=FileLoader.getDocumentFileName(message.getDocument());
                return "📄  "+(TextUtils.isEmpty(file)?"Documento":file);
            }
            case SignatureSmartPreviewPalette.MUSIC:{
                String title=message.getMusicTitle();
                return "♫  "+(TextUtils.isEmpty(title)?"Música":title);
            }
            case SignatureSmartPreviewPalette.LINK:{
                String url=message.messageOwner.message;
                if(TextUtils.isEmpty(url))return "🔗  Enlace";
                // No network request. Limit to the first line of the existing caption.
                int end=url.indexOf('\n');
                if(end>=0)url=url.substring(0,end);
                return "🔗  "+url;
            }
            case SignatureSmartPreviewPalette.PHOTO:return "▣  Foto";
            case SignatureSmartPreviewPalette.VIDEO:return "▶  Vídeo";
            case SignatureSmartPreviewPalette.EVENT:{
                CharSequence event=message.messageText;
                return "♧  "+(TextUtils.isEmpty(event)?"Evento del grupo":event.toString());
            }
            default:return "";
        }
    }
}
