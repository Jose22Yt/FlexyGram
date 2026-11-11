"""Run production mini-pill classification against Telegram metadata doubles, without downloads."""
from pathlib import Path
import re
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'TMessagesProj/src/main/java'
HOME = JAVA / 'app/flexygram/home'


def execute(tmp_path, extra, probe):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    preview = (HOME / 'SignatureSmartPreviews.java').read_text()
    strings = sorted(set(re.findall(r'R.string.(\w+)', preview)))
    sources = {
        'android/content/SharedPreferences.java': '''package android.content;public class SharedPreferences {public int getInt(String k,int d){return d;}public Editor edit(){return new Editor();}public class Editor{public Editor putInt(String k,int v){return this;}public void apply(){}}}''',
        'android/content/Context.java': '''package android.content;public class Context{public static final int MODE_PRIVATE=0;public SharedPreferences getSharedPreferences(String n,int m){return new SharedPreferences();}}''',
        'android/text/TextUtils.java': '''package android.text;public class TextUtils{public static boolean isEmpty(CharSequence v){return v==null||v.length()==0;}}''',
        'org/telegram/messenger/ApplicationLoader.java': '''package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();}''',
        'org/telegram/messenger/R.java': 'package org.telegram.messenger;public class R{public static class string{' + ''.join(f'public static final int {s}={i};' for i,s in enumerate(strings)) + '}}',
        'org/telegram/messenger/LocaleController.java': 'package org.telegram.messenger;public class LocaleController{public static String getString(int id){return new String[]{' + ','.join('"'+s+'"' for s in strings) + '}[id];}}',
        'org/telegram/messenger/FileLoader.java': '''package org.telegram.messenger;public class FileLoader{public static String getDocumentFileName(org.telegram.tgnet.TLRPC.Document d){return d==null?null:d.name;}}''',
        'org/telegram/tgnet/TLRPC.java': '''package org.telegram.tgnet;import java.util.*;public class TLRPC{
 public static class Peer{public long user_id;}
 public static class Message {public MessageMedia media;public MessageAction action;public Peer from_id;public String message="";public boolean post;public int edit_date;public List<Object> restriction_reason=new ArrayList<>();public List<MessageEntity> entities=new ArrayList<>();}
 public static class MessageMedia{public int ttl_seconds;public Document document;public WebPage webpage;public String first_name,last_name;}
 public static class WebPage{public String url;}
 public static class TL_messageMediaPhoto extends MessageMedia{}
 public static class TL_messageMediaDocument extends MessageMedia{}
 public static class TL_messageMediaWebPage extends MessageMedia{}
 public static class TL_messageMediaEmpty extends MessageMedia{}
 public static class TL_messageMediaContact extends MessageMedia{}
 public static class TL_messageMediaGeo extends MessageMedia{}
 public static class TL_messageMediaGeoLive extends MessageMedia{}
 public static class TL_messageMediaVenue extends MessageMedia{}
 public static class TL_messageMediaPoll extends MessageMedia{}
 public static class Document{public String name="",mime_type="";}
 public static class TL_documentEmpty extends Document{}
 public static class MessageAction{}
 public static class TL_messageActionEmpty extends MessageAction{}
 public static class TL_messageActionChatAddUser extends MessageAction{}
 public static class TL_messageActionChatJoinedByLink extends MessageAction{}
 public static class TL_messageActionChatDeleteUser extends MessageAction{public long user_id;}
 public static class TL_messageActionPinMessage extends MessageAction{}
 public static class MessageEntity{public int offset,length;public String url;}
 public static class TL_messageEntitySpoiler extends MessageEntity{}
 public static class TL_messageEntityUrl extends MessageEntity{}
 public static class TL_messageEntityTextUrl extends MessageEntity{}
 public static class ChannelParticipant{}
 public static class TL_channelParticipantCreator extends ChannelParticipant{}
 public static class TL_channelParticipantAdmin extends ChannelParticipant{}
 public static class ChatParticipant{public long user_id;}
 public static class TL_chatParticipantCreator extends ChatParticipant{}
 public static class TL_chatParticipantAdmin extends ChatParticipant{}
 public static class Participants{public List<ChatParticipant> participants=new ArrayList<>();}
 public static class ChatFull{public Participants participants;}
}''',
        'org/telegram/messenger/MessageObject.java': '''package org.telegram.messenger;import org.telegram.tgnet.TLRPC;
public class MessageObject{
 public TLRPC.Message messageOwner=new TLRPC.Message();public int currentAccount;public long dialog=10;
 public CharSequence messageText="native snippet";public boolean highlighted,concealed,voice,music,video,photo,sticker,gif,round,deleted;
 public String musicTitle="";public double duration;
 public boolean hasHighlightedWords(){return highlighted;}public boolean needDrawBluredPreview(){return concealed;}
 public boolean isVoice(){return voice;}public boolean isMusic(){return music;}public boolean isVideo(){return video;}
 public boolean isPhoto(){return photo;}public boolean isAnyKindOfSticker(){return sticker;}public boolean isRoundVideo(){return round;}
 public boolean isGif(){return gif;}public boolean isAyuDeleted(){return deleted;}
 // A webpage's document intentionally leaks through these native-style convenience methods.
 public TLRPC.Document getDocument(){return messageOwner.media==null?null:messageOwner.media.document;}
 public boolean isDocument(){return getDocument()!=null&&!video&&!music&&!voice&&!sticker;}
 public double getDuration(){return duration;}public String getMusicTitle(){return musicTitle;}public long getDialogId(){return dialog;}
}''',
        'org/telegram/messenger/MessagesController.java': '''package org.telegram.messenger;import org.telegram.tgnet.TLRPC;
public class MessagesController{public static TLRPC.ChannelParticipant participant;public static TLRPC.ChatFull full;
public static MessagesController getInstance(int a){return new MessagesController();}
public TLRPC.ChannelParticipant getAdminInChannel(long u,long c){return participant;}public TLRPC.ChatFull getChatFull(long c){return full;}}''',
        'Probe.java': probe,
    }
    sources.update(extra)
    files = []
    for name, content in sources.items():
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
        files.append(file)
    actual = [HOME / (n+'.java') for n in ['SignatureMiniPillClassifier', 'SignatureSmartPreviewPalette', 'SignatureSmartPreviews']]
    result = subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',str(tmp_path),*map(str,files),*map(str,actual)],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run(['java','-cp',str(tmp_path),'Probe'],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr


PREFIX = '''import app.flexygram.home.*;import static app.flexygram.home.SignatureSmartPreviewPalette.*;
import org.telegram.messenger.*;import org.telegram.tgnet.TLRPC;
public class Probe{
 static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
 static void kind(MessageObject m,int k){check(SignatureSmartPreviews.kind(m)==k,"expected kind "+k+" got "+SignatureSmartPreviews.kind(m));}
 static MessageObject doc(String name,String mime){MessageObject m=new MessageObject();m.messageOwner.media=new TLRPC.TL_messageMediaDocument();m.messageOwner.media.document=new TLRPC.Document();m.messageOwner.media.document.name=name;m.messageOwner.media.document.mime_type=mime;return m;}
'''


def test_real_attachments_and_webpage_metadata_cannot_be_confused(tmp_path):
    execute(tmp_path, {}, PREFIX+'''public static void main(String[]args){
 MessageObject m=doc("report.pdf","application/pdf");kind(m,PDF);
 check(SignatureSmartPreviews.snippet(m,PDF).equals("report.pdf"),"filename retained");
 m.messageOwner.media=new TLRPC.TL_messageMediaWebPage();m.messageOwner.media.document=new TLRPC.Document();
 m.messageOwner.media.document.name="site.pdf";m.messageOwner.media.document.mime_type="application/pdf";
 m.messageOwner.message="https://example.org/article.pdf?token=secret";kind(m,LINK);
 check(SignatureSmartPreviews.snippet(m,LINK).equals("example.org"),"web document is a link; no filename or query leak");
 m.photo=m.video=m.gif=true;kind(m,LINK); // Same result even if native preview convenience predicates match.
 m.messageOwner.message="hello world";kind(m,NONE);
 m.messageOwner.media=new TLRPC.TL_messageMediaEmpty();kind(m,NONE);
 m.messageOwner.media=null;m.messageOwner.message="admin PDF archivo.mp3 mensaje eliminado";kind(m,NONE);
 m.messageOwner.action=new TLRPC.TL_messageActionEmpty();kind(m,NONE);
 m.messageOwner.action=new TLRPC.MessageAction();kind(m,NONE);
 m=doc("clip.mp4","video/mp4");m.round=true;kind(m,VIDEO);
 check(!SignatureSmartPreviews.snippet(m,VIDEO).equals("clip.mp4"),"round video is not a generic filename");
 m=doc("sticker.webm","video/webm");m.sticker=m.video=true;kind(m,STICKER);
 m=doc("animation.mp4","video/mp4");m.gif=m.video=true;kind(m,GIF);
 m=doc("voice.ogg","audio/ogg");m.voice=true;m.duration=84;kind(m,VOICE);
 check(SignatureSmartPreviews.snippet(m,VOICE).contains("1:24"),"voice duration");
 m=doc("track.ogg","audio/ogg");kind(m,MUSIC);
 m=doc("image.heic","image/heic");kind(m,IMAGE_FILE);
 m=new MessageObject();m.messageOwner.media=new TLRPC.TL_messageMediaPhoto();kind(m,PHOTO);
 m=doc("","application/octet-stream");kind(m,FILE);
 m.messageOwner.media.document=null;kind(m,NONE);
 m.messageOwner.media.document=new TLRPC.TL_documentEmpty();kind(m,NONE);
 m=doc("report.pdf","application/pdf");m.messageOwner.media.ttl_seconds=10;kind(m,NONE);
 m.messageOwner.media.ttl_seconds=0;m.messageOwner.entities.add(new TLRPC.TL_messageEntitySpoiler());kind(m,NONE);
 m.messageOwner.entities.clear();m.messageOwner.restriction_reason.add("restricted");kind(m,NONE);
 m.messageOwner.restriction_reason.clear();m.concealed=true;kind(m,NONE);
 m.concealed=false;m.highlighted=true;kind(m,NONE);
 m.highlighted=false;m.deleted=true;m.messageOwner.message="old caption";kind(m,DELETED);
 check(SignatureSmartPreviews.snippet(m,DELETED).contains("old caption"),"deleted caption retained with state");
 }}''')


def test_mime_filename_precedence_and_distinct_semantic_icons(tmp_path):
    execute(tmp_path, {}, PREFIX+'''public static void main(String[]args){
 String[][] metadata={{"report.PDF ","application/octet-stream"},{"misleading.txt"," Application/PDF; version=1.7 "},{"report.docx","application/zip"},{"app.apks","application/zip"},{"","audio/opus"},{"","video/quicktime"},{"image.avif","application/octet-stream"},{"archive.tar.gz","application/gzip"},{"sheet","text/csv"},{"slides","application/vnd.openxmlformats-officedocument.presentationml.presentation"},{"report.pdf.exe","application/octet-stream"}};
 int[] expected={PDF,PDF,DOCUMENT,APK,MUSIC,VIDEO,IMAGE_FILE,ARCHIVE,SPREADSHEET,PRESENTATION,FILE};
 for(int i=0;i<expected.length;i++)check(SignatureMiniPillClassifier.documentType(metadata[i][0],metadata[i][1])==expected[i],"metadata "+i);
 check(SignatureMiniPillClassifier.documentType(null,null)==FILE,"unknown actual attachment only");
 java.util.Set<Integer> icons=new java.util.HashSet<>();
 for(int k:new int[]{FILE,PDF,TXT,VOICE,MUSIC,PHOTO,VIDEO,GIF,STICKER,LINK,ADMIN,OWNER,DELETED,POLL,APK,DOCUMENT,SPREADSHEET,PRESENTATION})
  check(icons.add(SignatureSmartPreviews.iconKind(k)),"distinct icon for "+k);
 for(int k:new int[]{VOICE,MUSIC,VIDEO,GIF,LINK,DELETED})check(!SignatureMiniPillClassifier.isFileKind(k),"not filename clipping");
 for(String url:new String[]{"https://example.com/a.pdf","HTTP://example.com","www.example.com","https://例子.测试/"})check(SignatureMiniPillClassifier.isWebLink(url),"valid URL");
 for(String url:new String[]{"hola.pdf","report.mp3","javascript:alert(1)","https://","http:// /x","www."})check(!SignatureMiniPillClassifier.isWebLink(url),"not a URL "+url);
 }}''')


def test_url_entities_roles_and_service_events_use_confirmed_metadata(tmp_path):
    execute(tmp_path, {}, PREFIX+'''public static void main(String[]args){
 MessageObject m=new MessageObject();m.messageOwner.message="😊 abre el informe";
 TLRPC.TL_messageEntityTextUrl e=new TLRPC.TL_messageEntityTextUrl();e.offset=3;e.length=4;e.url="https://example.org/report.pdf";m.messageOwner.entities.add(e);kind(m,LINK);
 check(SignatureSmartPreviews.snippet(m,LINK).equals("example.org"),"hidden link's domain, not its label");
 e.offset=Integer.MAX_VALUE;kind(m,NONE);e.offset=-1;kind(m,NONE);e.offset=3;e.length=Integer.MAX_VALUE;kind(m,NONE);
 m.messageOwner.entities.clear();m.messageOwner.message="example.org/report.pdf";
 TLRPC.TL_messageEntityUrl bare=new TLRPC.TL_messageEntityUrl();bare.length=m.messageOwner.message.length();m.messageOwner.entities.add(bare);kind(m,LINK);
 check(SignatureSmartPreviews.snippet(m,LINK).equals("example.org"),"bare domain confirmed by Telegram");
 m.messageOwner.entities.clear();kind(m,NONE); // No guessing from ordinary text without URL metadata.
 m.messageOwner.media=new TLRPC.TL_messageMediaWebPage();m.messageOwner.media.webpage=new TLRPC.WebPage();m.messageOwner.media.webpage.url="https://preview.example/picture.jpg";kind(m,LINK);
 m.messageOwner.media=null;m.messageOwner.from_id=new TLRPC.Peer();m.messageOwner.from_id.user_id=42;m.dialog=-7;kind(m,NONE);
 MessagesController.participant=new TLRPC.TL_channelParticipantAdmin();kind(m,ADMIN);
 MessagesController.participant=new TLRPC.TL_channelParticipantCreator();kind(m,OWNER);
 MessagesController.participant=null;m.messageOwner.post=true;kind(m,CHANNEL);
 m.messageOwner.post=false;m.messageOwner.edit_date=123;kind(m,EDITED);
 m.messageOwner.action=new TLRPC.TL_messageActionChatAddUser();kind(m,JOINED);
 TLRPC.TL_messageActionChatDeleteUser delete=new TLRPC.TL_messageActionChatDeleteUser();delete.user_id=42;m.messageOwner.action=delete;kind(m,LEFT);
 delete.user_id=44;kind(m,EVENT);
 m.messageOwner.action=new TLRPC.TL_messageActionPinMessage();kind(m,PINNED);
 }}''')


def test_label_fidelity_and_light_dark_palette_contrast(tmp_path):
    execute(tmp_path, {}, PREFIX+'''public static void main(String[]args){
 MessageObject m=doc("😀".repeat(100)+".pdf","application/pdf");
 String name=SignatureSmartPreviews.snippet(m,PDF);
 check(name.endsWith(".pdf")&&name.length()<=120,"long filename keeps its extension");
 for(int i=0;i<name.length();i++){
  if(Character.isHighSurrogate(name.charAt(i)))check(i+1<name.length()&&Character.isLowSurrogate(name.charAt(++i)),"no split surrogate");
  else check(!Character.isLowSurrogate(name.charAt(i)),"no orphan surrogate");
 }
 int[] colors=new int[3];
 for(int mode:new int[]{ADAPTIVE,MATTE,MULTICOLOR})for(int surface:new int[]{0xffffffff,0xff121820})
  for(int accent:new int[]{0xff2299dd,0xffe6c900,0xff008800})for(int kind=1;kind<=DELETED;kind++){
   SignatureSmartPreviewPalette.resolveColors(kind,mode,accent,surface,colors);
   check(SignatureSmartPreviewPalette.contrast(colors[0],colors[1])>=4.5,"text contrast for kind "+kind);
   check(SignatureSmartPreviewPalette.contrast(colors[0],colors[2])>=3.0,"icon contrast for kind "+kind);
  }
 }}''')


def test_every_mini_icon_has_cached_geometry_and_inherits_live_ink(tmp_path):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    sources = {
        'app/flexygram/icons/ExactIcons.java':'package app.flexygram.icons;public class ExactIcons{public static boolean isEnabled(){return false;}public static android.graphics.drawable.Drawable direct(int id){return null;}}',
        'app/flexygram/icons/IosOriginalAssets.java':'package app.flexygram.icons;public class IosOriginalAssets{public static final int[] PREVIEW=new int[28];}',
        'android/graphics/drawable/Drawable.java':'package android.graphics.drawable;public class Drawable{public void setTint(int c){}public void setAlpha(int a){}public void setBounds(int a,int b,int c,int d){}public void draw(android.graphics.Canvas c){}}',
        'android/graphics/Path.java': '''package android.graphics;public class Path{public enum Direction{CW}public int points;public void moveTo(float x,float y){points++;}public void lineTo(float x,float y){points++;}public void close(){points++;}public void quadTo(float a,float b,float c,float d){points++;}public void cubicTo(float a,float b,float c,float d,float e,float f){points++;}public void addRect(float a,float b,float c,float d,Direction dir){points++;}}''',
        'android/graphics/Paint.java': '''package android.graphics;public class Paint{public static final int ANTI_ALIAS_FLAG=1;public enum Style{STROKE}public enum Cap{ROUND}public enum Join{ROUND}public static class FontMetricsInt{}int color,alpha=255;public Paint(int flags){}public void setStyle(Style s){}public void setStrokeWidth(float v){}public void setStrokeCap(Cap c){}public void setStrokeJoin(Join j){}public void setColor(int c){color=c;}public int getColor(){return color;}public void setAlpha(int a){alpha=a;}public int getAlpha(){return alpha;}}''',
        'android/graphics/Canvas.java': '''package android.graphics;public class Canvas{public Path path;public int color,alpha;public void save(){}public void restore(){}public void translate(float x,float y){}public void scale(float x,float y){}public void drawPath(Path p,Paint ink){path=p;color=ink.getColor();alpha=ink.getAlpha();}}''',
        'android/text/style/ReplacementSpan.java': '''package android.text.style;public abstract class ReplacementSpan{public abstract int getSize(android.graphics.Paint p,CharSequence t,int s,int e,android.graphics.Paint.FontMetricsInt fm);public abstract void draw(android.graphics.Canvas c,CharSequence t,int s,int e,float x,int top,int y,int bottom,android.graphics.Paint p);}''',
        'org/telegram/messenger/AndroidUtilities.java': '''package org.telegram.messenger;public class AndroidUtilities{public static float density=1;public static int dp(float n){return Math.round(n);}}''',
        'Probe.java': '''import app.flexygram.home.SignaturePreviewIcon;import android.graphics.*;
public class Probe{public static void main(String[]args){Canvas c=new Canvas();Paint ink=new Paint(1);java.util.Set<Path> paths=new java.util.HashSet<>();for(int i=1;i<=27;i++){SignaturePreviewIcon.draw(c,i,0,0,14,ink);if(c.path.points==0||!paths.add(c.path))throw new AssertionError("missing icon "+i);Path first=c.path;for(int color:new int[]{0xffffffff,0xff171717}){ink.setColor(color);ink.setAlpha(128);SignaturePreviewIcon.draw(c,i,0,0,14,ink);if(c.path!=first||c.color!=color||c.alpha!=128)throw new AssertionError("cache/tint");}}}}''',
    }
    files=[]
    for name,content in sources.items():
        file=tmp_path/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(content);files.append(file)
    result=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',str(tmp_path),*map(str,files),str(HOME/'SignaturePreviewIcon.java')],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    result=subprocess.run(['java','-cp',str(tmp_path),'Probe'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
