/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;
import android.view.View;

/** Pixel-domain property driver. External finger writes remain authoritative; no second clock. */
public final class FlexyBoundSpring {
    public interface Reader { float get(); }
    private final View owner;
    private final Reader reader;
    private final FlexyFrameMotion.Listener writer;
    private FlexyFrameMotion motion;
    public FlexyBoundSpring(View owner,Reader reader,FlexyFrameMotion.Listener writer){
        if(owner==null||reader==null||writer==null)throw new IllegalArgumentException("property");
        this.owner=owner;this.reader=reader;this.writer=writer;
    }
    private FlexyFrameMotion motion(){
        if(motion==null){
            motion=new FlexyFrameMotion(owner,reader.get(),writer,.5f,30f);
            motion.setOnSettingsChanged(()->{
                float value=reader.get();
                if(!motion.isRunning()||value!=motion.current())motion.snapTo(value);
            });
        }
        return motion;
    }
    public void animateToFinalPosition(float target){
        FlexyFrameMotion m=motion();float value=reader.get();
        if(!m.isRunning()||value!=m.current())m.snapTo(value);
        m.animateTo(target);
    }
    public void cancel(){if(motion!=null){motion.snapTo(reader.get());motion.cancel();}}
    public void dispose(){if(motion!=null){motion.dispose();motion=null;}}
}
