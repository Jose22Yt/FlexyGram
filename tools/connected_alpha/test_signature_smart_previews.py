"""Host JVM checks against the actual Signature Smart Previews production classes.

No mock rendering or performance claims: Android DialogCell/device acceptance is
a separate step. The classifier does not open media or download thumbnails.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/"TMessagesProj/src/main/java"
PALETTE=JAVA/"app/flexygram/home/SignatureSmartPreviewPalette.java"
CLASSIFIER=JAVA/"app/flexygram/home/SignatureSmartPreviews.java"
DIALOG=JAVA/"org/telegram/ui/Cells/DialogCell.java"
SETTINGS=JAVA/"app/exteraless/settings/OpenExteraChatsActivity.java"


class SmartPreviews(unittest.TestCase):
    def test_compiled_production_palette_and_classifier(self):
        doubles={
            "android/content/SharedPreferences.java": '''package android.content; public interface SharedPreferences {
                int getInt(String key,int fallback); Editor edit();
                interface Editor { Editor putInt(String key,int n); void apply(); }
            }''',
            "android/content/Context.java": '''package android.content;
                public class Context { public static final int MODE_PRIVATE=0;
                private final java.util.Map<String,Integer> prefs=new java.util.HashMap<>();
                public SharedPreferences getSharedPreferences(String name,int mode) {
                    return new SharedPreferences() {
                        public int getInt(String key,int fallback){return prefs.getOrDefault(key,fallback);}
                        public Editor edit(){return new Editor(){
                            public Editor putInt(String key,int v){prefs.put(key,v);return this;}
                            public void apply(){} };} }; }
                }''',
            "android/text/TextUtils.java": '''package android.text;public class TextUtils{
                public static boolean isEmpty(CharSequence s){return s==null||s.length()==0;} }''',
            "org/telegram/messenger/ApplicationLoader.java": '''package org.telegram.messenger;
                public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();}''',
            "org/telegram/messenger/FileLoader.java": '''package org.telegram.messenger;
                public class FileLoader{public static String getDocumentFileName(org.telegram.tgnet.TLRPC.Document d){
                    return d==null?"":d.file_name;} }''',
            "org/telegram/tgnet/TLRPC.java": '''package org.telegram.tgnet;
                public final class TLRPC {
                    public static class Document {public String file_name;}
                    public static class Message { public Media media;public String message;
                        public Object action;public java.util.ArrayList<Object> restriction_reason=new java.util.ArrayList<>();}
                    public static class Media { public int ttl_seconds; }
                    public static class TL_messageMediaWebPage extends Media{}
                    public static class TL_messageActionChatAddUser{}
                    public static class TL_messageActionChatJoinedByLink{}
                }''',
            "org/telegram/messenger/MessageObject.java": '''package org.telegram.messenger;
                import org.telegram.tgnet.TLRPC;
                public class MessageObject {
                    public final TLRPC.Message messageOwner=new TLRPC.Message();
                    public CharSequence messageText;
                    public boolean highlighted,voice,music,file,video,photo,empty=true;
                    public double duration;public String musicTitle;
                    public TLRPC.Document document=new TLRPC.Document();
                    public boolean hasHighlightedWords(){return highlighted;}
                    public boolean isVoice(){return voice;}
                    public boolean isMusic(){return music;}
                    public boolean isDocument(){return file;}
                    public boolean isVideo(){return video;}
                    public boolean isPhoto(){return photo;}
                    public boolean isMediaEmpty(){return empty;}
                    public double getDuration(){return duration;}
                    public TLRPC.Document getDocument(){return document;}
                    public String getMusicTitle(){return musicTitle;}
                }''',
            "SmartPreviewProbe.java": '''import app.flexygram.home.*;
                import org.telegram.messenger.MessageObject;
                import org.telegram.tgnet.TLRPC;
                public class SmartPreviewProbe {
                    static void ok(boolean good,String why){if(!good)throw new AssertionError(why);}
                    static MessageObject m(){return new MessageObject();}
                    static void verify(int expected,MessageObject msg){
                        ok(SignatureSmartPreviews.kind(msg)==expected,"kind "+expected);
                    }
                    public static void main(String[] args){
                        MessageObject voice=m();voice.voice=true;voice.duration=83;
                        verify(SignatureSmartPreviewPalette.VOICE,voice);
                        ok(SignatureSmartPreviews.label(voice,2).contains("1:23"),"voice duration");
                        MessageObject music=m();music.music=true;music.musicTitle="Track";
                        verify(3,music);ok(SignatureSmartPreviews.label(music,3).contains("Track"),"title");
                        MessageObject file=m();file.file=true;file.document.file_name="report.pdf";
                        verify(1,file);ok(SignatureSmartPreviews.label(file,1).contains("report.pdf"),"document name");
                        MessageObject photo=m();photo.photo=true;verify(6,photo);
                        MessageObject video=m();video.video=true;verify(7,video);
                        MessageObject group=m();group.messageOwner.action=new TLRPC.TL_messageActionChatAddUser();
                        group.messageText="Joined group";verify(5,group);
                        MessageObject link=m();link.messageOwner.media=new TLRPC.TL_messageMediaWebPage();
                        link.messageOwner.message="https://example.com";verify(4,link);
                        link.messageOwner.message="Please visit https://example.com";verify(0,link);
                        MessageObject simpleLink=m();simpleLink.messageOwner.message="https://example.com";
                        verify(4,simpleLink);
                        simpleLink.messageOwner.message="Just a text";verify(0,simpleLink);
                        voice.highlighted=true;verify(0,voice);voice.highlighted=false;
                        voice.messageOwner.message="Caption";verify(0,voice);
                        voice.messageOwner.message="";voice.messageOwner.media=new TLRPC.Media();
                        voice.messageOwner.media.ttl_seconds=15;verify(0,voice);
                        SignatureSmartPreviews.setMode(SignatureSmartPreviewPalette.MATTE);
                        ok(SignatureSmartPreviews.mode()==2,"mode stored");
                        SignatureSmartPreviews.setMode(SignatureSmartPreviewPalette.OFF);
                        ok(SignatureSmartPreviews.mode()==3,"off");
                        for(int mode=0;mode<=2;mode++){
                            for(int type=1;type<=7;type++){
                                for(int surface:new int[]{0xfff7f7f9,0xff141b25,0xff777777}){
                                    SignatureSmartPreviewPalette palette=new SignatureSmartPreviewPalette();
                                    ok(palette.update(type,mode,0xff189c6d,surface),"cache initial");
                                    ok(!palette.update(type,mode,0xff189c6d,surface),"cache stable");
                                    ok(SignatureSmartPreviewPalette.contrast(palette.background(),palette.foreground())>=4.5,
                                        "WCAG contrast mode="+mode+" type="+type);
                                    ok((palette.background()>>>24)==255,"opaque background");
                                }
                            }
                        }
                        System.out.println("PASS: real palette and classifier, theme modes, file/audio/link/event/caption/TTL");
                    }}'''
        }
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)
            java=[str(PALETTE),str(CLASSIFIER)]
            for name,body in doubles.items():
                path=source/name;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(body,encoding="utf-8");java.append(str(path))
            a=subprocess.run(["javac","-d",folder,*java],text=True,capture_output=True)
            self.assertEqual(a.returncode,0,a.stderr)
            b=subprocess.run(["java","-cp",folder,"SmartPreviewProbe"],text=True,capture_output=True)
            self.assertEqual(b.returncode,0,b.stderr)
            self.assertIn("PASS:",b.stdout)

    def test_dialog_cell_integration_preserves_native_list_and_layout(self):
        s=DIALOG.read_text()
        self.assertIn("SignatureSmartPreviews.kind(message)",s)
        self.assertIn("drawSmartPreviewBackground(canvas,top,1f-updateHelper.typingProgres)",s)
        self.assertIn("smartPreviewPalette.foreground()",s)
        self.assertIn("smartPreviewKind=0",s)
        self.assertIn("draftMessage == null && !draftVoice",s)
        self.assertIn("!hasTags()",s)
        self.assertIn("spoilers.isEmpty()",s)
        self.assertNotIn("new Bitmap",s[s.index("drawSmartPreviewBackground"):s.index("drawSmartPreviewBackground")+1200])
        self.assertNotIn("ValueAnimator",s[s.index("drawSmartPreviewBackground"):s.index("drawSmartPreviewBackground")+1200])
        self.assertIn("messageLayout = new StaticLayout(",s)
        self.assertIn("AnimatedEmojiSpan.drawAnimatedEmojis(canvas, messageLayout",s)

    def test_settings_picker_and_localizations(self):
        s=SETTINGS.read_text()
        for x in ('smartPreviewsRow = addRow("flexySmartPreviews")',
                  'SignatureSmartPreviews.setMode(selected)',
                  'SignatureSmartPreviews.setMode(selected)'):
            self.assertIn(x,s)
        for locale in ("values","values-es","values-ru"):
            p=ROOT/"TMessagesProj/src/main/res"/locale/"flexygram_smart_previews.xml"
            tree=ET.parse(p)
            names={c.attrib["name"] for c in tree.getroot()}
            self.assertEqual(len(names),5)

    def test_exact_review(self):
        from smart_previews1278_contract import verify_current
        verify_current()


if __name__=="__main__":
    unittest.main()
