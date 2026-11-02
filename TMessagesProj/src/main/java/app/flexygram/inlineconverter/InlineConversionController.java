/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.inlineconverter;

import android.os.SystemClock;
import android.text.Spanned;
import android.text.style.ClickableSpan;
import android.text.style.CharacterStyle;
import android.text.style.TypefaceSpan;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import java.lang.ref.WeakReference;
import java.util.*;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.Utilities;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.TextStyleSpan;
import org.telegram.ui.Components.URLSpanMono;

/** Lazy per-cell coordinator. No drawing hook, background service, network, or message mutation. */
public final class InlineConversionController {
    private static final InlineConversionCache CACHE=new InlineConversionCache();
    private final View anchor;
    private final Theme.ResourcesProvider theme;
    private final float slop;
    private final WeakReference<InlineConversionController> weak;
    private List<InlineConversionMatch> body=Collections.emptyList(),caption=Collections.emptyList();
    private int generation,revision=-1;
    private String preparedKey;
    private Runnable task;
    private InlineConversionMatch pressed;
    private boolean pressedCaption;
    private float downX,downY;
    private long downTime;
    private InlineConversionPopover popover;
    public InlineConversionController(View anchor,Theme.ResourcesProvider theme){this.anchor=anchor;this.theme=theme;slop=ViewConfiguration.get(anchor.getContext()).getScaledTouchSlop();weak=new WeakReference<>(this);}
    public static void clearCache(){CACHE.clear();}
    private static final class Input {
        final String text;final int[][] excluded;
        Input(CharSequence value){
            if(value==null||value.length()>InlineConversionScanner.MAX_CHARS){text="";excluded=new int[0][];return;}
            text=value.toString();ArrayList<int[]> ranges=new ArrayList<>();
            if(value instanceof Spanned){Spanned spans=(Spanned)value;
                CharacterStyle[] styles=spans.getSpans(0,value.length(),CharacterStyle.class);
                if(styles.length>128){excluded=new int[][]{{0,value.length()}};return;}
                for(CharacterStyle style:styles){
                    boolean block=style instanceof ClickableSpan||style instanceof URLSpanMono||style instanceof TypefaceSpan;
                    if(style instanceof TextStyleSpan){int flags=((TextStyleSpan)style).getStyleFlags();block|=(flags&(TextStyleSpan.FLAG_STYLE_MONO|TextStyleSpan.FLAG_STYLE_CODE|TextStyleSpan.FLAG_STYLE_SPOILER))!=0;}
                    if(block)ranges.add(new int[]{spans.getSpanStart(style),spans.getSpanEnd(style)});
                }
            }
            excluded=ranges.toArray(new int[0][]);
        }
        String key(){return text+"\u0000"+Arrays.deepToString(excluded);}
    }
    public void prepare(CharSequence text,CharSequence captionText,int account,long dialog,int message,int editDate){
        InlineConversionConfig.Snapshot config=InlineConversionConfig.get();
        if(!config.enabled){release();return;}
        Input a=new Input(text),b=new Input(captionText);
        Locale locale=LocaleController.getInstance().getCurrentLocale();if(locale==null)locale=Locale.getDefault();
        String scope=account+":"+dialog+":"+message+":"+editDate+":"+locale.toLanguageTag()+":"+config.revision+":";
        String key=scope+a.key()+"\u0001"+b.key();
        if(key.equals(preparedKey))return;
        release();preparedKey=key;revision=config.revision;
        final int token=generation;final Locale region=locale;
        final WeakReference<InlineConversionController> owner=weak;
        task=()->{
            List<InlineConversionMatch> first=read(scope+a.key(),a,region),second=read(scope+b.key(),b,region);
            AndroidUtilities.runOnUIThread(()->{
                InlineConversionController c=owner.get();
                if(c==null||c.generation!=token||!c.anchor.isAttachedToWindow()||!InlineConversionConfig.get().enabled||InlineConversionConfig.get().revision!=config.revision)return;
                c.task=null;c.body=first;c.caption=second;
            });
        };
        Utilities.globalQueue.postRunnable(task);
    }
    private static List<InlineConversionMatch> read(String key,Input input,Locale locale){
        List<InlineConversionMatch> value=CACHE.get(key);
        if(value==null){
            android.os.Trace.beginSection("Flexy.inline.scan");
            try{value=InlineConversionScanner.scan(input.text,locale,input.excluded);}
            finally{android.os.Trace.endSection();}
            if(InlineConversionConfig.get().enabled)CACHE.put(key,value);
        }
        return value;
    }
    public boolean stale(){return revision!=InlineConversionConfig.get().revision;}
    public void observe(MotionEvent event){
        int action=event.getActionMasked();
        if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_CANCEL||event.getPointerCount()!=1||action==MotionEvent.ACTION_MOVE&&(Math.abs(event.getX()-downX)>slop||Math.abs(event.getY()-downY)>slop))cancelGesture();
    }
    public void cancelGesture(){pressed=null;}
    private InlineConversionMatch hit(int offset,boolean isCaption){
        for(InlineConversionMatch match:isCaption?caption:body)if(offset>=match.start&&offset<match.end&&InlineConversionConfig.get().accepts(match))return match;
        return null;
    }
    public boolean touch(MotionEvent event,int offset,boolean isCaption,int messageDate){
        if(!InlineConversionConfig.get().enabled||stale()){cancelGesture();return false;}
        int action=event.getActionMasked();
        if(action==MotionEvent.ACTION_DOWN){
            pressed=hit(offset,isCaption);pressedCaption=isCaption;downX=event.getX();downY=event.getY();downTime=SystemClock.uptimeMillis();return pressed!=null;
        }
        if(action==MotionEvent.ACTION_UP&&pressed!=null){
            InlineConversionMatch match=pressed;cancelGesture();
            if(isCaption==pressedCaption&&hit(offset,isCaption)==match&&SystemClock.uptimeMillis()-downTime<ViewConfiguration.getLongPressTimeout()){
                if(popover!=null)popover.dismiss();
                android.os.Trace.beginSection("Flexy.inline.open");
                try{popover=new InlineConversionPopover(anchor,theme);popover.show(match,messageDate,event.getX(),event.getY());}
                finally{android.os.Trace.endSection();}
            }
            return true;
        }
        return false;
    }
    public void release(){
        generation++;cancelGesture();preparedKey=null;revision=-1;body=caption=Collections.emptyList();
        if(task!=null){Utilities.globalQueue.cancelRunnable(task);task=null;}
        if(popover!=null){popover.dismiss();popover=null;}
    }
}
