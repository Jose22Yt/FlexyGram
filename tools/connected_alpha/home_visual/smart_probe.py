"""Actual DialogCell drawing/thumbnail methods; theme, mode and services are doubles."""
from pathlib import Path

def method(source,anchor):
    start=source.index(anchor);end=source.index('{',start)+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]

def write_probe(source,root):
    java=root/'TMessagesProj/src/main/java'
    actual=(java/'org/telegram/ui/Cells/DialogCell.java').read_text()
    methods='\n'.join(method(actual,a) for a in [
        'private void drawSmartPreviewBackground(', 'private CharSequence applyThumbs(',
        'public static class ThumbnailSpan ', 'public static class FixedWidthSpan '])
    code='''import android.graphics.*;import android.text.*;import android.text.style.*;import android.view.View;
import org.robolectric.RuntimeEnvironment;import app.flexygram.home.*;
public class SmartPreviewCellProbe extends View {
 int smartPreviewKind,messageLeft=24,thumbsCount,thumbSize=20;
 StaticLayout messageLayout;Object resourcesProvider;
 final SignatureSmartPreviewPalette smartPreviewPalette=new SignatureSmartPreviewPalette();
 final Paint smartPreviewPaint=new Paint(3);
 static final int[] SMART_VOICE_BARS={5,9,13,6,11,7,4};
 public static class LocaleController {static boolean isRTL;}
 public static class Theme {static int key_actionBarTabLine=1,key_windowBackgroundWhite=2;
 static int surface=0xfff8f8fa,accent=0xff239c72;
 static int getColor(int key,Object provider){return key==1?accent:surface;}}
 static int dp(float n){return Math.round(n);}
 SmartPreviewCellProbe(){super(RuntimeEnvironment.getApplication());}
 void bind(String text,int kind,boolean rtl,float font,int width,int height,int thumbs){
  smartPreviewKind=kind;LocaleController.isRTL=rtl;thumbsCount=thumbs;
  TextPaint paint=new TextPaint(3);paint.setTextSize(14*font);paint.setColor(0xff253547);
  CharSequence label=applyThumbs(text);
  label=TextUtils.ellipsize(label,paint,Math.max(20,width-90),TextUtils.TruncateAt.END);
  messageLayout=StaticLayout.Builder.obtain(label,0,label.length(),paint,width-48)
   .setMaxLines(1).setIncludePad(false).setTextDirection(rtl?TextDirectionHeuristics.RTL:TextDirectionHeuristics.LTR).build();
  measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.EXACTLY));layout(0,0,width,height);
 }
 Bitmap render(float alpha){Bitmap b=Bitmap.createBitmap(getWidth(),getHeight(),Bitmap.Config.ARGB_8888);drawSmartPreviewBackground(new Canvas(b),26,alpha);return b;}
}
'''
    code=code.replace('\n}\n','\n'+methods+'\n}\n')
    (source/'SmartPreviewCellProbe.java').write_text(code)
    package=source/'app/flexygram/home';package.mkdir(parents=True,exist_ok=True)
    (package/'SignatureSmartPreviewPalette.java').write_bytes((java/'app/flexygram/home/SignatureSmartPreviewPalette.java').read_bytes())
    (package/'SignatureSmartPreviews.java').write_text('package app.flexygram.home;public class SignatureSmartPreviews{public static int value;public static int mode(){return value;}}')
    (source/'SmartPreviewsVisualTest.java').write_bytes(Path(__file__).with_name('SmartPreviewsVisualTest.java.in').read_bytes())
