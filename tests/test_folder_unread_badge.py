"""Host regression checks for folder counts and live accent/contrast changes."""
import pathlib
import shutil
import subprocess
import tempfile

import pytest

from test_composer_layout import method


@pytest.mark.skipif(not shutil.which("javac") or not shutil.which("java"), reason="JDK required")
def test_folder_unread_badge_count_and_theme():
    root = pathlib.Path(__file__).resolve().parents[1]
    chat = (root / "TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java").read_text()
    bar = (root / "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBar.java").read_text()
    count = method(chat, "private int getCurrentFolderUnreadMessageCount()")
    view = method(bar, "public class UnreadImageView extends AppCompatImageView")
    header = (root / "TMessagesProj/src/main/java/app/flexygram/header/SignatureChatHeader.java").read_text()
    color_state = header[header.index("    private int lastBadgeAccent;"):header.index("    private void drawUnread(Canvas canvas)")]
    native_methods = color_state + method(header, "public void setCount(int value)") + method(header, "private void drawUnread(Canvas canvas)")
    for full, local in (("androidx.core.graphics.ColorUtils", "ColorUtils"), ("android.graphics.Color", "Color"), ("android.text.StaticLayout", "StaticLayout"), ("android.text.Layout", "Layout")):
        native_methods = native_methods.replace(full, local)
    harness = """
import java.util.*;
public class BadgeRegression {
    static class TLRPC { static class Dialog {
        long id; int unread_count;
        Dialog(long id,int count){this.id=id;unread_count=count;}
    }}
    static class DialogObject {static boolean isFolderDialogId(long id){return id==999;}}
    static class MessagesController {
        static class DialogFilter {ArrayList<TLRPC.Dialog> dialogs=new ArrayList<>();}
        Map<Integer,DialogFilter> dialogFiltersById=new HashMap<>();
        Map<Integer,ArrayList<TLRPC.Dialog>> dialogsByFolder=new HashMap<>();
    }
    final MessagesController controller=new MessagesController();
    int dialogFilterId,dialogFolderId;
    MessagesController getMessagesController(){return controller;}
    COUNT
    static class Paint {
        static final int ANTI_ALIAS_FLAG=1;int color;
        Paint(int flags){} void setColor(int c){color=c;}
    }
    static class TextPaint extends Paint {
        TextPaint(int flags){super(flags);}
        void set(TextPaint other){color=other.color;}
        void setTextSize(int size){} void setTypeface(Object face){}
        float measureText(String text){return text.length()*7;}
    }
    static class Color {static final int WHITE=0xffffffff,BLACK=0xff000000;}
    static class ColorUtils {
        static int setAlphaComponent(int color,int alpha){return (color&0xffffff)|(alpha<<24);}
        static double channel(int c){double v=c/255.0;return v<=0.04045?v/12.92:Math.pow((v+0.055)/1.055,2.4);}
        static double luminance(int c){return .2126*channel((c>>16)&255)+.7152*channel((c>>8)&255)+.0722*channel(c&255);}
        static double calculateContrast(int a,int b){double x=luminance(a)+.05,y=luminance(b)+.05;return Math.max(x,y)/Math.min(x,y);}
    }
    static class Theme {static int accent;static int getColor(int key,Object provider){return accent;}static int key_telegram_color=1;static TextPaint dialogs_countTextPaint=new TextPaint(1);}
    static class AndroidUtilities {
        static Object bold(){return null;}static float density=1;static int dp(float n){return Math.round(n);}
    }
    static class RectF {float left,top,right,bottom;void set(float a,float b,float c,float d){left=a;top=b;right=c;bottom=d;}float centerX(){return (left+right)/2;}float centerY(){return (top+bottom)/2;}}
    static class Canvas {
        int background,foreground,draws;String text;
        void drawRoundRect(RectF r,float x,float y,Paint paint){background=paint.color;draws++;}
        void save(){}void restore(){}void translate(float x,float y){}
    }
    static class Layout {enum Alignment {ALIGN_CENTER}}
    static class StaticLayout {
        final String text;final TextPaint paint;final int width;
        StaticLayout(String text,TextPaint paint,int w,Layout.Alignment a,float b,float c,boolean d){this.text=text;this.paint=paint;this.width=w;}
        int getWidth(){return width;}int getHeight(){return 16;}
        void draw(Canvas canvas){canvas.foreground=paint.color;canvas.text=text;}
    }
    static class Context {
        Context getResources(){return this;}Object getTheme(){return null;}
        Object getDrawable(int id,Object theme){return null;}
    }
    static class AppCompatImageView {
        AppCompatImageView(Context c){}void setImageResource(int id){}void setImageDrawable(Object d){}
        Context getContext(){return new Context();}int getMeasuredWidth(){return 100;}
        public void onDraw(Canvas c){}void invalidate(){}
    }
    int accent=0xff316bda;StaticLayout countLayout;
    int getThemedColor(int key){return accent;}
    VIEW
    static class LocaleController {static boolean isRTL;}
    static class Geometry {boolean countVisible=true,separateCount;RectF back=new RectF(),badge=new RectF();}
    class NativeBadge {
        int unreadCount;StaticLayout unreadLayout;Object provider;Geometry geometry=new Geometry();
        Paint badgePaint=new Paint(1);TextPaint unreadPaint=new TextPaint(1);RectF badgeRect=new RectF();
        void changed(){}
        NATIVE
    }
    static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    static ArrayList<TLRPC.Dialog> dialogs(TLRPC.Dialog... d){return new ArrayList<>(List.of(d));}
    public static void main(String[] args) {
        BadgeRegression c=new BadgeRegression();
        c.controller.dialogsByFolder.put(0,dialogs(new TLRPC.Dialog(1,4),new TLRPC.Dialog(2,36),new TLRPC.Dialog(999,80)));
        c.controller.dialogsByFolder.put(1,dialogs(new TLRPC.Dialog(3,80)));
        require(c.getCurrentFolderUnreadMessageCount()==40,"sum messages, not conversations or archive summary");
        c.dialogFolderId=1;require(c.getCurrentFolderUnreadMessageCount()==80,"archive scope");
        MessagesController.DialogFilter filter=new MessagesController.DialogFilter();
        filter.dialogs=dialogs(new TLRPC.Dialog(2,36),new TLRPC.Dialog(3,80),new TLRPC.Dialog(4,-1));
        c.controller.dialogFiltersById.put(5,filter);c.dialogFilterId=5;
        require(c.getCurrentFolderUnreadMessageCount()==116,"custom folder membership, including eligible archived chats");
        filter.dialogs.get(0).unread_count=0;
        require(c.getCurrentFolderUnreadMessageCount()==80,"read state updates");
        filter.dialogs.add(new TLRPC.Dialog(6,Integer.MAX_VALUE));
        require(c.getCurrentFolderUnreadMessageCount()==Integer.MAX_VALUE,"no integer overflow");
        c.dialogFilterId=7;require(c.getCurrentFolderUnreadMessageCount()==0,"removed filter must not show account total");
        UnreadImageView badge=c.new UnreadImageView(new Context());badge.setUnread(40);
        NativeBadge nativeBadge=c.new NativeBadge();nativeBadge.setCount(40);
        int originalSharedTextColor=Theme.dialogs_countTextPaint.color;
        for(int accent:new int[]{0xff102050,0xffffdf20,0xff2288aa,0xff000000,0xffffffff}) {
            c.accent=accent;Theme.accent=accent;Canvas canvas=new Canvas();badge.onDraw(canvas);
            for(boolean separate:new boolean[]{false,true})for(boolean rtl:new boolean[]{false,true}){
                nativeBadge.geometry.separateCount=separate;LocaleController.isRTL=rtl;
                Canvas nativeCanvas=new Canvas();nativeBadge.drawUnread(nativeCanvas);
                require(nativeCanvas.background==accent,"actual Signature header must follow accent in both counter modes");
                require(ColorUtils.calculateContrast(nativeCanvas.foreground,accent)>=4.5,"actual Signature header text contrast");
                require(Theme.dialogs_countTextPaint.color==originalSharedTextColor,"Signature header must not mutate shared paint");
            }
            require(canvas.background==accent,"theme accent must update without changing count");
            require(ColorUtils.calculateContrast(canvas.foreground,accent)>=4.5,"readable badge text");
            require("40".equals(canvas.text),"badge count unchanged by theme");
        }
        require(Theme.dialogs_countTextPaint.color==originalSharedTextColor,"do not mutate shared dialog text paint");
        nativeBadge.setCount(41);Canvas changedCount=new Canvas();nativeBadge.drawUnread(changedCount);
        require(ColorUtils.calculateContrast(changedCount.foreground,c.accent)>=4.5,"new count must restore cached contrast after copying shared paint");
        badge.setUnread(120);Canvas capped=new Canvas();badge.onDraw(capped);require("99+".equals(capped.text),"retain compact display");
        badge.setUnread(-1);Canvas empty=new Canvas();badge.onDraw(empty);require(empty.draws==0,"empty count hidden");
    }
}
""".replace("COUNT", count).replace("VIEW", view).replace("NATIVE", native_methods)
    with tempfile.TemporaryDirectory(prefix="flexygram-badge-") as directory:
        path = pathlib.Path(directory) / "BadgeRegression.java"
        path.write_text(harness)
        result = subprocess.run(["javac", "-d", directory, str(path)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        result = subprocess.run(["java", "-cp", directory, "BadgeRegression"], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
