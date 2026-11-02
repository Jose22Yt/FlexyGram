import app.flexygram.inlineconverter.*;
import android.view.*;
import org.telegram.messenger.*;
import java.util.*;

/** Actual controller/config against declared host doubles, not Telegram/Android execution. */
public class ControllerProbe {
    static void check(boolean ok){if(!ok)throw new AssertionError();}
    static void flush(){Utilities.globalQueue.flush();AndroidUtilities.ui.flush();}
    static void prepare(InlineConversionController c,String text,int edit){c.prepare(text,null,0,55,90,edit);}
    static void event(InlineConversionController c,MotionEvent e){c.observe(e);}
    static boolean tap(InlineConversionController c,int offset){var d=new MotionEvent(0,30,30);c.observe(d);boolean down=c.touch(d,offset,false,0);return down&&c.touch(new MotionEvent(1,30,30),offset,false,0);}
    public static void main(String[]args)throws Exception{
        check(!InlineConversionConfig.get().enabled);InlineConversionConfig.set(InlineConversionConfig.ENABLED,true);
        View anchor=new View();var controller=new InlineConversionController(anchor,null);
        switch(args[0]){
            case "edits":{
                prepare(controller,"70 miles",0);Runnable obsolete=Utilities.globalQueue.tasks.get(0);
                prepare(controller,"hello world",1);obsolete.run();AndroidUtilities.ui.flush();check(!tap(controller,1));
                flush();check(!tap(controller,1));prepare(controller,"180 lbs",2);flush();check(tap(controller,1));
                int count=InlineConversionPopover.shown;controller.release();check(!tap(controller,1));check(InlineConversionPopover.shown==count);break;
            }
            case "cancel":{
                prepare(controller,"70 miles",0);Runnable obsolete=Utilities.globalQueue.tasks.get(0);controller.release();check(Utilities.globalQueue.tasks.isEmpty());obsolete.run();AndroidUtilities.ui.flush();check(!tap(controller,1));
                prepare(controller,"70 miles",0);anchor.attached=false;flush();check(!tap(controller,1));anchor.attached=true;controller.release();prepare(controller,"70 miles",0);flush();check(tap(controller,1));break;
            }
            case "gestures":{
                prepare(controller,"70 miles",0);flush();var down=new MotionEvent(0,30,30);controller.observe(down);check(controller.touch(down,1,false,0));
                event(controller,new MotionEvent(2,50,30));check(!controller.touch(new MotionEvent(1,30,30),1,false,0));check(InlineConversionPopover.shown==0);
                controller.observe(down);check(controller.touch(down,1,false,0));controller.cancelGesture();check(!controller.touch(new MotionEvent(1,30,30),1,false,0));
                controller.observe(down);controller.touch(down,1,false,0);android.os.SystemClock.now=600;controller.touch(new MotionEvent(1,30,30),1,false,0);check(InlineConversionPopover.shown==0);
                android.os.SystemClock.now=0;controller.observe(down);controller.touch(down,1,false,0);event(controller,new MotionEvent(3,30,30));check(!controller.touch(new MotionEvent(1,30,30),1,false,0));
                controller.observe(down);controller.touch(down,1,false,0);var multi=new MotionEvent(2,30,30);multi.pointers=2;event(controller,multi);check(!controller.touch(new MotionEvent(1,30,30),1,false,0));break;
            }
            case "settings":{
                prepare(controller,"70 miles",0);flush();InlineConversionConfig.set(InlineConversionConfig.UNITS,false);check(controller.stale());check(!tap(controller,1));
                InlineConversionConfig.set(InlineConversionConfig.TARGET_CURRENCY,"COP");InlineConversionConfig.set(InlineConversionConfig.TARGET_ZONE,"Asia/Tokyo");InlineConversionConfig.set(InlineConversionConfig.SYSTEM,2);
                var field=InlineConversionConfig.class.getDeclaredField("current");field.setAccessible(true);field.set(null,null);var loaded=InlineConversionConfig.get();check(loaded.targetCurrency.equals("COP"));check(loaded.targetZone.equals("Asia/Tokyo"));check(loaded.system==2&&!loaded.units&&loaded.enabled);
                boolean rejected=false;try{InlineConversionConfig.set("session",true);}catch(IllegalArgumentException ok){rejected=true;}check(rejected);check(!tw.nekomimi.nekogram.NekoConfig.store.map.containsKey("session"));
                rejected=false;try{InlineConversionConfig.set(InlineConversionConfig.TARGET_ZONE,"Not/A_Zone");}catch(java.time.DateTimeException ok){rejected=true;}check(rejected);check(InlineConversionConfig.get().targetZone.equals("Asia/Tokyo"));
                InlineConversionConfig.set(InlineConversionConfig.ENABLED,false);check(!tap(controller,1));break;
            }
            case "spans":{
                class Text implements android.text.Spanned{
                    Object span=new android.text.style.ClickableSpan();public int length(){return 8;}public char charAt(int p){return "70 miles".charAt(p);}public CharSequence subSequence(int a,int b){return "70 miles".substring(a,b);}public String toString(){return "70 miles";}
                    public <T>T[] getSpans(int a,int b,Class<T>type){T[] array=(T[])java.lang.reflect.Array.newInstance(type,1);array[0]=type.cast(span);return array;}
                    public int getSpanStart(Object o){return 0;}public int getSpanEnd(Object o){return 8;}
                }
                Text text=new Text();controller.prepare(text,null,0,55,90,0);flush();check(!tap(controller,1));
                text.span=new org.telegram.ui.Components.URLSpanMono();controller.prepare(text,null,0,55,90,1);flush();check(!tap(controller,1));
                var spoiler=new org.telegram.ui.Components.TextStyleSpan();spoiler.flags=256;text.span=spoiler;controller.prepare(text,null,0,55,90,2);flush();check(!tap(controller,1));break;
            }
            default:throw new AssertionError();
        }System.out.println("PASS HOST_DOUBLES "+args[0]);
    }
}
