"""Host regression checks for the real Java blur class, using small Android doubles.

Requires javac/java (21). These verify buffer sizing and drawable state, not GPU
rendering or frame times. No Android SDK, Gradle or external corpus is required.
"""
import pathlib
import shutil
import subprocess
import tempfile

import pytest


STUBS = {
    "android.graphics.Rect": """
        public int left, top, right, bottom;
        public Rect() {} public Rect(Rect r) { set(r.left,r.top,r.right,r.bottom); }
        public void set(int l,int t,int r,int b) {left=l;top=t;right=r;bottom=b;}
    """,
    "android.graphics.Bitmap": """
        public static int allocations; private int w,h;
        public enum Config { ARGB_8888 }
        public static Bitmap createBitmap(int w,int h,Config c) {
            if(w<=0||h<=0) throw new IllegalArgumentException("empty bitmap");
            Bitmap b=new Bitmap(); b.w=w;b.h=h;allocations++;return b;
        }
        public int getWidth(){return w;} public int getHeight(){return h;}
        public void eraseColor(int c){} public void recycle(){}
    """,
    "android.graphics.Canvas": """
        public static final int ALL_SAVE_FLAG=31;
        public Canvas(){} public Canvas(Bitmap b){}
        public void save(){} public void restore(){}
        public void saveLayerAlpha(float l,float t,float r,float b,int a,int f){}
        public void translate(float x,float y){} public void scale(float x,float y){}
        public void scale(float x,float y,float px,float py){}
        public void drawPaint(Paint p){} public void drawColor(int c){}
        public void drawBitmap(Bitmap b,float x,float y,Paint p){}
    """,
    "android.graphics.Paint": """
        public static final int FILTER_BITMAP_FLAG=2;
        public Paint(){} public Paint(int f){}
        public void setColor(int c){} public void setAlpha(int a){}
    """,
    "android.graphics.Color": "public static final int BLACK=0xff000000, TRANSPARENT=0;",
    "android.graphics.drawable.Drawable": """
        private final android.graphics.Rect bounds=new android.graphics.Rect();
        public android.graphics.Rect getBounds(){return bounds;}
        public void setBounds(int l,int t,int r,int b){bounds.set(l,t,r,b);}
        public void setBounds(android.graphics.Rect r){setBounds(r.left,r.top,r.right,r.bottom);}
        public void draw(android.graphics.Canvas c){}
    """,
    "android.view.View": """
        public int width=1080,height=1920;
        public android.graphics.drawable.Drawable background;
        public int getMeasuredWidth(){return width;} public int getMeasuredHeight(){return height;}
        public float getAlpha(){return 1;} public void invalidate(){}
        public void setTag(int k,Object v){} public void draw(android.graphics.Canvas c){}
        public android.graphics.drawable.Drawable getBackground(){return background;}
    """,
    "org.telegram.messenger.AndroidUtilities": """
        public static int statusBarHeight=24; public static int dp(int x){return x;}
        public static void runOnUIThread(Runnable r){r.run();}
    """,
    "org.telegram.messenger.DispatchQueue": """
        public DispatchQueue(String s){} public void cleanupQueue(){} public void recycle(){}
        public void postRunnable(Runnable r){r.run();}
    """,
    "org.telegram.messenger.FileLog": "public static void e(Throwable t){throw new AssertionError(t);}",
    "org.telegram.messenger.Utilities": "public static void stackBlurBitmap(android.graphics.Bitmap b,int r){}",
    "org.telegram.ui.ActionBar.Theme": """
        public interface ResourcesProvider {} public static int key_windowBackgroundWhite=1;
        public static int getColor(int k,ResourcesProvider p){return -1;}
        public static android.graphics.drawable.Drawable getCachedWallpaperNonBlocking(){return null;}
    """,
    "org.telegram.ui.ChatActivity": """
        public static class ThemeDelegate implements org.telegram.ui.ActionBar.Theme.ResourcesProvider {
            public android.graphics.drawable.Drawable getWallpaperDrawable(){return null;}
        }
    """,
}

HARNESS = """
import android.graphics.*;
import android.graphics.drawable.Drawable;
import android.view.View;
import org.telegram.ui.Components.BlurBehindDrawable;
public class BlurRegression {
    static void require(boolean ok,String message) {if(!ok)throw new AssertionError(message);}
    public static void main(String[] args) {
        View parent=new View(), behind=new View();
        behind.background=new Drawable();
        behind.background.setBounds(3,5,17,29);
        BlurBehindDrawable blur=new BlurBehindDrawable(behind,parent,1,null);
        blur.setAnimateAlpha(false);
        blur.draw(new Canvas());
        int initial=Bitmap.allocations;
        require(initial==4,"initial pair of capture and rendering buffers");
        for(int i=0;i<100;i++)blur.checkSizes();
        require(Bitmap.allocations==initial,"stable sizes must reuse buffers");
        Rect bounds=behind.background.getBounds();
        require(bounds.left==3&&bounds.top==5&&bounds.right==17&&bounds.bottom==29,
            "wallpaper bounds must survive capture");
        parent.width=720; parent.height=1280; blur.checkSizes();
        require(Bitmap.allocations==initial+4,"resize must replace both buffer pairs");
        blur.checkSizes(); require(Bitmap.allocations==initial+4,"reuse resized buffers");
        parent.width=1; parent.height=1; behind.background=null;
        blur.checkSizes(); // Small views and no wallpaper must not crash.
        for(int[] size:new int[][]{{0,100},{100,0}}) {
            parent.width=size[0];parent.height=size[1];
            BlurBehindDrawable empty=new BlurBehindDrawable(behind,parent,1,null);
            empty.setAnimateAlpha(false);
            int before=Bitmap.allocations; empty.draw(new Canvas());
            require(Bitmap.allocations==before,"unmeasured axis must skip capture");
        }
        System.out.println("buffer reuse, resize, bounds, tiny/empty sizes and null wallpaper passed");
    }
}
"""


@pytest.mark.skipif(not shutil.which("javac") or not shutil.which("java"), reason="JDK required")
def test_blur_buffer_lifecycle():
    root = pathlib.Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="flexygram-blur-") as directory:
        temp = pathlib.Path(directory)
        sources = []
        for name, body in STUBS.items():
            package, _, cls = name.rpartition(".")
            path = temp / (name.replace(".", "/") + ".java")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"package {package}; public class {cls} {{ {body} }}")
            sources.append(str(path))
        harness = temp / "BlurRegression.java"
        harness.write_text(HARNESS)
        sources += [str(harness), str(root / "TMessagesProj/src/main/java/org/telegram/ui/Components/BlurBehindDrawable.java")]
        subprocess.run(["javac", "-d", str(temp), *sources], check=True, capture_output=True, text=True)
        subprocess.run(["java", "-cp", str(temp), "BlurRegression"], check=True, capture_output=True, text=True)
