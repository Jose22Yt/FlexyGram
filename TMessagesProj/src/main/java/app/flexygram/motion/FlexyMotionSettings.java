/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Looper;

/** One immutable in-memory snapshot. Read disk once; setters are main-thread local and atomic. */
public final class FlexyMotionSettings {
    private static final String FILE="flexy_motion_engine", PROFILE="profile", REDUCE_MOTION="reduce_motion";
    public static final class State {
        public final FlexyMotionProfile profile;
        public final boolean reduceMotion;
        public final float speed,stiffness,damping,pressedScale;
        State(FlexyMotionProfile p,boolean reduced,float speed,float stiffness,float damping,float scale){profile=p;reduceMotion=reduced;this.speed=speed;this.stiffness=stiffness;this.damping=damping;pressedScale=scale;}
        public boolean instant(){return reduceMotion||profile==FlexyMotionProfile.FLASH;}
    }
    private static volatile State state;
    private static SharedPreferences prefs;
    private FlexyMotionSettings(){}
    private static float bounded(float x,float low,float high,float fallback){return Float.isFinite(x)?Math.max(low,Math.min(high,x)):fallback;}
    public static State state(Context c){
        State s=state;if(s!=null)return s;
        synchronized(FlexyMotionSettings.class){if(state==null){prefs=c.getApplicationContext().getSharedPreferences(FILE,Context.MODE_PRIVATE);FlexyMotionProfile p=FlexyMotionProfile.parse(prefs.getString(PROFILE,"FLOW"));state=new State(p,prefs.getBoolean(REDUCE_MOTION,false),bounded(prefs.getFloat("speed",1),.5f,2,1),bounded(prefs.getFloat("stiffness",Math.max(200,p.stiffness)),200,1000,560),bounded(prefs.getFloat("damping",p.dampingRatio),.55f,1.2f,.92f),bounded(prefs.getFloat("press",p.pressedScale),.94f,1, .975f));}return state;}
    }
    private static void change(Context c,State s){
        if(Looper.myLooper()!=Looper.getMainLooper())throw new IllegalStateException("main thread");
        State previous=state(c);
        if(previous.profile==s.profile&&previous.reduceMotion==s.reduceMotion&&previous.speed==s.speed&&previous.stiffness==s.stiffness&&previous.damping==s.damping&&previous.pressedScale==s.pressedScale)return;
        state=s;
        prefs.edit().putString(PROFILE,s.profile.name()).putBoolean(REDUCE_MOTION,s.reduceMotion).putFloat("speed",s.speed).putFloat("stiffness",s.stiffness).putFloat("damping",s.damping).putFloat("press",s.pressedScale).apply();
        FlexyFrameMotion.settingsChanged();
    }
    public static FlexyMotionProfile profile(Context c){return state(c).profile;}
    public static boolean reduceMotion(Context c){return state(c).reduceMotion;}
    public static FlexyMotionProfile effectiveProfile(Context c){State s=state(c);return s.instant()?FlexyMotionProfile.FLASH:s.profile;}
    public static void setProfile(Context c,FlexyMotionProfile p){if(p==null)throw new IllegalArgumentException("profile");State s=state(c);change(c,new State(p,s.reduceMotion,1,Math.max(200,p.stiffness),p.dampingRatio,p.pressedScale));}
    public static void setReduceMotion(Context c,boolean enabled){State s=state(c);change(c,new State(s.profile,enabled,s.speed,s.stiffness,s.damping,s.pressedScale));}
    public static void tune(Context c,float speed,float stiffness,float damping,float press){State s=state(c);change(c,new State(s.profile,s.reduceMotion,bounded(speed,.5f,2,1),bounded(stiffness,200,1000,560),bounded(damping,.55f,1.2f,.92f),bounded(press,.94f,1,.975f)));}
}
