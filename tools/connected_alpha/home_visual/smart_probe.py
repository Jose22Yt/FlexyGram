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
 int smartPreviewKind,messageLeft=24,thumbsCount,thumbSize=20,smartPreviewPrefixEnd,smartPreviewClipLeft=6,smartPreviewClipRight=314;
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
  TextPaint paint=new TextPaint(3);paint.setTextSize(15);paint.setColor(0xff253547);
  SpannableStringBuilder pill=new SpannableStringBuilder("\ufffc");
  pill.setSpan(new SignaturePreviewIcon(Math.max(1,kind)),0,1,Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
  pill.append(text);pill.setSpan(new AbsoluteSizeSpan(Math.round(12*font)),1,pill.length(),Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
  CharSequence label=applyThumbs(pill);smartPreviewPrefixEnd=thumbs>0?1:0;smartPreviewClipRight=width-6;
  label=TextUtils.ellipsize(label,paint,Math.max(20,width-90),kind==1?TextUtils.TruncateAt.MIDDLE:TextUtils.TruncateAt.END);
  messageLayout=StaticLayout.Builder.obtain(label,0,label.length(),paint,width-48)
   .setMaxLines(1).setIncludePad(false).setTextDirection(rtl?TextDirectionHeuristics.RTL:TextDirectionHeuristics.LTR).build();
  measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.EXACTLY));layout(0,0,width,height);
 }
 void bindInline(String sender,String text,boolean rtl,int width){
  smartPreviewKind=4;LocaleController.isRTL=rtl;thumbsCount=0;smartPreviewClipRight=width-6;
  TextPaint paint=new TextPaint(3);paint.setTextSize(15);paint.setColor(0xff253547);
  SpannableStringBuilder value=new SpannableStringBuilder(sender);smartPreviewPrefixEnd=value.length();value.append("\ufffc");
  value.setSpan(new SignaturePreviewIcon(4),smartPreviewPrefixEnd,smartPreviewPrefixEnd+1,Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
  value.append(text);value.setSpan(new AbsoluteSizeSpan(12),smartPreviewPrefixEnd+1,value.length(),Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
  messageLayout=StaticLayout.Builder.obtain(value,0,value.length(),paint,width-48).setMaxLines(1).setIncludePad(false).setTextDirection(rtl?TextDirectionHeuristics.RTL:TextDirectionHeuristics.LTR).build();
  measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(72,MeasureSpec.EXACTLY));layout(0,0,width,72);
 }
 Bitmap renderBackground(){Bitmap b=Bitmap.createBitmap(getWidth(),getHeight(),Bitmap.Config.ARGB_8888);drawSmartPreviewBackground(new Canvas(b),26,1);return b;}
 Bitmap render(float alpha){Bitmap b=Bitmap.createBitmap(getWidth(),getHeight(),Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);drawSmartPreviewBackground(c,26,alpha);if(smartPreviewKind!=0&&SignatureSmartPreviews.mode()!=3){c.save();c.translate(messageLeft,26);messageLayout.getPaint().setColor(smartPreviewPalette.foreground());messageLayout.draw(c);c.restore();}return b;}
}
'''
    code=code.replace('\n}\n','\n'+methods+'\n}\n')
    (source/'SmartPreviewCellProbe.java').write_text(code)
    package=source/'app/flexygram/home';package.mkdir(parents=True,exist_ok=True)
    (package/'SignatureTopicAccent.java').write_bytes((java/'app/flexygram/home/SignatureTopicAccent.java').read_bytes())
    (package/'SignaturePreviewIcon.java').write_bytes((java/'app/flexygram/home/SignaturePreviewIcon.java').read_bytes())
    (package/'SignaturePreviewContext.java').write_bytes((java/'app/flexygram/home/SignaturePreviewContext.java').read_bytes())
    messenger=source/'org/telegram/messenger';messenger.mkdir(parents=True,exist_ok=True)
    (messenger/'AndroidUtilities.java').write_text('package org.telegram.messenger;public class AndroidUtilities {public static int dp(float value){return Math.round(value);}}')
    (package/'SignatureSmartPreviewPalette.java').write_bytes((java/'app/flexygram/home/SignatureSmartPreviewPalette.java').read_bytes())
    (package/'SignatureSmartPreviews.java').write_text('package app.flexygram.home;public class SignatureSmartPreviews{public static int value;public static int mode(){return value;}}')
    (source/'SmartPreviewsVisualTest.java').write_bytes(Path(__file__).with_name('SmartPreviewsVisualTest.java.in').read_bytes())
