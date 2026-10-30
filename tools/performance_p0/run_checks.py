#!/usr/bin/env python3
"""Compile production deltas and exact baseline code with isolated API doubles. No APK/device claims."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
JAVA = ROOT/'TMessagesProj/src/main/java'
BASE = '0030904ae2e41d7720f43b7906c6a302ed339839'

STUBS = {
'android/os/Build.java': 'package android.os;public class Build {public static class VERSION {public static int SDK_INT=37;}}',
'android/os/SystemClock.java': 'package android.os;public class SystemClock {public static long now;public static long uptimeMillis(){return now;}}',
'android/view/View.java': '''package android.view;import java.util.*;public class View {
public static final float REQUESTED_FRAME_RATE_CATEGORY_HIGH=-4,REQUESTED_FRAME_RATE_CATEGORY_DEFAULT=Float.NaN;
public float rate=Float.NaN;public int votes,invalidations,removes;public View parent;public final List<Runnable> callbacks=new ArrayList<>();
public float getRequestedFrameRate(){return rate;}public void setRequestedFrameRate(float value){votes++;rate=value;}
public void invalidate(){invalidations++;}public Object getParent(){return parent;}
public void removeCallbacks(Runnable r){removes++;callbacks.removeIf(v->v==r);}public void postOnAnimation(Runnable r){callbacks.add(r);}}''',
'android/graphics/Rect.java': 'package android.graphics;public class Rect{public int left,top,right,bottom;public Rect(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}}',
'android/graphics/RectF.java': '''package android.graphics;public class RectF {public static int queries;public float left,top,right,bottom;public void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}public float centerX(){queries++;return(left+right)*.5f;}public float centerY(){queries++;return(top+bottom)*.5f;}public float width(){queries++;return right-left;}public float height(){queries++;return bottom-top;}}''',
'android/graphics/Path.java': '''package android.graphics;import java.util.*;public class Path{
public int rewinds;public final List<float[]> points=new ArrayList<>();public final List<String> commands=new ArrayList<>();
void add(String op,float...f){commands.add(op+Arrays.toString(f));}public void rewind(){rewinds++;points.clear();commands.clear();}
public void moveTo(float x,float y){points.add(new float[]{x,y});add("M",x,y);}public void lineTo(float x,float y){points.add(new float[]{x,y});add("L",x,y);}
public void cubicTo(float a,float b,float c,float d,float e,float f){points.add(new float[]{e,f});add("C",a,b,c,d,e,f);}public void close(){if(!points.isEmpty())points.add(points.get(0));add("Z");}
public void computeBounds(RectF b,boolean exact){if(points.isEmpty()){b.set(0,0,0,0);return;}float l=Float.MAX_VALUE,t=l,r=-l,d=-l;for(float[]p:points){l=Math.min(l,p[0]);t=Math.min(t,p[1]);r=Math.max(r,p[0]);d=Math.max(d,p[1]);}b.set(l,t,r,d);}}''',
'android/graphics/PathMeasure.java': '''package android.graphics;public class PathMeasure {Path p;public void setPath(Path p,boolean c){this.p=p;}public float getLength(){float n=0;for(int i=1;i<p.points.size();i++)n+=length(i);return n;}float length(int i){float[]a=p.points.get(i-1),b=p.points.get(i);return(float)Math.hypot(b[0]-a[0],b[1]-a[1]);}public boolean nextContour(){return false;}public void getPosTan(float d,float[]out,float[]tan){for(int i=1;i<p.points.size();i++){float len=length(i);if(d<=len||i==p.points.size()-1){float q=len==0?0:Math.min(1,d/len);float[]a=p.points.get(i-1),b=p.points.get(i);out[0]=a[0]+(b[0]-a[0])*q;out[1]=a[1]+(b[1]-a[1])*q;return;}d-=len;}}public void getSegment(float a,float b,Path dst,boolean move){dst.add("S",a,b);}}''',
'android/graphics/Shader.java':'package android.graphics;public class Shader{public enum TileMode{CLAMP}}',
'android/graphics/LinearGradient.java':'package android.graphics;public class LinearGradient extends Shader {public LinearGradient(float a,float b,float c,float d,int[]colors,float[]stops,TileMode mode){}}',
'android/graphics/Paint.java':'''package android.graphics;public class Paint{public static final int ANTI_ALIAS_FLAG=1;public enum Style{FILL,STROKE}public Paint(int i){}public void setStyle(Style s){}public void setColor(int c){}public void setStrokeWidth(float w){}}''',
'android/graphics/Canvas.java':'''package android.graphics;public class Canvas{public int save(){return 1;}public void clipPath(Path p){}public void clipRect(float a,float b,float c,float d){}public java.util.List<String> bars=new java.util.ArrayList<>();public void drawRoundRect(float a,float b,float c,float d,float e,float f,Paint p){bars.add(java.util.Arrays.toString(new float[]{a,b,c,d,e,f}));}public void drawPath(Path p,Paint q){}public void restoreToCount(int i){}}''',
'android/graphics/drawable/Drawable.java':'package android.graphics.drawable;public class Drawable{public void setBounds(int a,int b,int c,int d){}public void draw(android.graphics.Canvas c){}}',
'org/telegram/messenger/AndroidUtilities.java':'package org.telegram.messenger;public class AndroidUtilities{public static float density=1,screenRefreshRate=60,screenRefreshTime=1000f/60;}',
'app/flexygram/navigation/LiquidNavigationConfig.java':'''package app.flexygram.navigation;public class LiquidNavigationConfig{public enum Parameter{INTENSITY,OUTLINE,REFLECTION,REFRACTION}public static boolean adaptive;public static boolean adaptiveQuality(){return adaptive;}public static int opacity(){return 70;}public static int value(Parameter p){return 50;}}'''
}

STUBS.update({
'android/content/Context.java':'package android.content;public class Context {public static final String DISPLAY_SERVICE="display";}',
'android/os/Looper.java':'package android.os;public class Looper {public static Looper getMainLooper(){return new Looper();}}',
'android/os/Handler.java':'package android.os;public class Handler {public Handler(Looper l){}}',
'android/view/Display.java':'package android.view;public class Display{public float rate=60;public float getRefreshRate(){return rate;}public int getDisplayId(){return 1;}}',
'android/view/WindowManager.java':'package android.view;public class WindowManager{public final Display display=new Display();public Display getDefaultDisplay(){return display;}}',
'android/hardware/display/DisplayManager.java':'package android.hardware.display;public class DisplayManager{public interface DisplayListener{void onDisplayChanged(int id);void onDisplayAdded(int id);void onDisplayRemoved(int id);}public int registrations,removals;public void registerDisplayListener(DisplayListener l,android.os.Handler h){registrations++;}public void unregisterDisplayListener(DisplayListener l){removals++;}}',
'android/app/Activity.java':'package android.app;public class Activity extends android.content.Context{public final android.hardware.display.DisplayManager manager=new android.hardware.display.DisplayManager();public final android.view.WindowManager windows=new android.view.WindowManager();public Object getSystemService(String name){return manager;}public android.view.WindowManager getWindowManager(){return windows;}}'
})

HARNESS = '''import java.util.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
import app.flexygram.performance.*;import app.flexygram.navigation.*;import app.flexygram.bubbles.*;import app.flexygram.bubbles.interaction.*;
import android.graphics.*;import android.view.View;import android.os.*;
public class PerformanceHarness {
static int checks;static void check(boolean v){checks++;if(!v)throw new AssertionError("check "+checks);}
public static void main(String[]args)throws Exception{
// All selected/active combinations, retaining zero/login and every activated account.
for(int selected=0;selected<10;selected++)for(int mask=0;mask<1024;mask++){
 boolean[]seen=new boolean[10];for(int i=0;i<10;i++){int a=StartupAccounts.accountAt(i,selected,10);check(!seen[a]);seen[a]=true;check(a==BaselineStartupAccounts.accountAt(i,selected,10));check(StartupAccounts.needsControllers(a,selected,(mask&(1<<a))!=0)==(a==0||a==selected||(mask&(1<<a))!=0));}}
int directCalls=10,eligible=0;for(int a=0;a<10;a++)if(StartupAccounts.needsControllers(a,0,a==0))eligible++;
// Pending bursts collapse; a new event during execution is retained; enqueue failure is retryable.
List<Runnable>queue=new ArrayList<>();int[]calls={0};CoalescedTask[]task=new CoalescedTask[1];task[0]=new CoalescedTask(queue::add,()->{calls[0]++;if(calls[0]==1)task[0].request();});
for(int i=0;i<1000;i++)task[0].request();check(queue.size()==1);queue.remove(0).run();check(calls[0]==1&&queue.size()==1);queue.remove(0).run();check(calls[0]==2&&queue.isEmpty());
AtomicBoolean reject=new AtomicBoolean(true);CoalescedTask retry=new CoalescedTask(r->{if(reject.getAndSet(false))throw new IllegalStateException();queue.add(r);},()->{});try{retry.request();throw new AssertionError();}catch(IllegalStateException expected){}retry.request();check(queue.size()==1);queue.clear();
ConcurrentLinkedQueue<Runnable>parallel=new ConcurrentLinkedQueue<>();CoalescedTask concurrent=new CoalescedTask(parallel::add,()->{});List<Thread>threads=new ArrayList<>();for(int i=0;i<12;i++){Thread t=new Thread(()->{for(int j=0;j<1000;j++)concurrent.request();});threads.add(t);t.start();}for(Thread t:threads)t.join();check(parallel.size()==1);
// Frequent cache hits must not extend the timestamp of the last actual query.
long lastQuery=-1;int reads=0;for(long now=0;now<=12000;now+=100){if(NetworkSnapshotAge.expired(now,lastQuery)){reads++;lastQuery=now;}}check(reads==3);check(NetworkSnapshotAge.expired(100,200));check(!NetworkSnapshotAge.expired(5000,0));check(NetworkSnapshotAge.expired(5001,0));
// API guard, previous NaN/custom request restoration, no repeated votes, another owner's request.
View v=new View();ScrollFrameRateHint hint=new ScrollFrameRateHint(v);Build.VERSION.SDK_INT=34;hint.setScrolling(true);check(v.votes==0);Build.VERSION.SDK_INT=35;hint.setScrolling(true);hint.setScrolling(true);check(v.rate==-4&&v.votes==1);hint.setScrolling(false);check(Float.isNaN(v.rate)&&v.votes==2);v.rate=90;hint.setScrolling(true);hint.setScrolling(false);check(v.rate==90);hint.setScrolling(true);v.rate=120;hint.setScrolling(false);check(v.rate==120);
// Display subscription is activity-scoped; actual Hz (including fractional modes) updates the shared budget.
android.app.Activity activity=new android.app.Activity();RefreshRateMonitor monitor=new RefreshRateMonitor(activity);monitor.start();monitor.start();check(activity.manager.registrations==1);for(float hz:new float[]{60,90,120,144,119.88f}){activity.windows.display.rate=hz;monitor.onDisplayChanged(1);check(org.telegram.messenger.AndroidUtilities.screenRefreshRate==hz);check(org.telegram.messenger.AndroidUtilities.screenRefreshTime==1000f/hz);}activity.windows.display.rate=Float.NaN;monitor.onDisplayChanged(1);check(Float.isFinite(org.telegram.messenger.AndroidUtilities.screenRefreshTime));monitor.stop();monitor.stop();check(activity.manager.removals==1);activity.windows.display.rate=30;monitor.onDisplayChanged(1);check(org.telegram.messenger.AndroidUtilities.screenRefreshRate!=30);
// Exact command equivalence to baseline lens for all six changed geometry parameters.
LiquidLensRenderer lens=new LiquidLensRenderer();BaselineLiquidLensRenderer oldLens=new BaselineLiquidLensRenderer();
for(int i=0;i<300;i++){float x=i%20,y=i%13,w=70+i%40,h=35+i%15,s=(i%10)*.03f,d=(i%3)-1;oldLens.prepare(x,y,w,h,s,d);lens.prepare(x,y,w,h,s,d);check(oldLens.shape().commands.equals(lens.shape().commands));}
int oldRewinds=oldLens.shape().rewinds,newRewinds=lens.shape().rewinds;for(int i=0;i<1000;i++){oldLens.prepare(100,30,90,42,0,0);lens.prepare(100,30,90,42,0,0);}int oldBuilds=oldLens.shape().rewinds-oldRewinds,newBuilds=lens.shape().rewinds-newRewinds;check(oldBuilds==1000&&newBuilds==1);LiquidNavigationConfig.adaptive=true;lens.prepare(100,30,90,42,0,0);check(lens.shape().rewinds-newRewinds==1);
// Partial contour samples are identical; bounds normalization happens once per rebuild.
int oldQueries=0,newQueries=0;for(int i=0;i<100;i++){Path p=new Path();float w=80+i*2,h=25+i%30;p.moveTo(0,0);p.lineTo(w,0);p.lineTo(w,h);p.lineTo(-4,h);p.lineTo(0,h-5);p.close();Rect r=new Rect(0,0,(int)w,(int)h);for(int side=1;side<=4;side++){org.telegram.messenger.AndroidUtilities.density=1+(i%4)*.5f;SignatureBorderPath b=new SignatureBorderPath();BaselineSignatureBorderPath before=new BaselineSignatureBorderPath();RectF.queries=0;Path old=before.get(p,side,r,10,0,0,2,0,0,0);oldQueries+=RectF.queries;RectF.queries=0;Path now=b.get(p,side,r,10,0,0,2,0,0,0);newQueries+=RectF.queries;check(old.commands.equals(now.commands));check(b.get(p,side,r,10,0,0,2,0,0,0)==now);}}
check(newQueries<oldQueries);
// Resting/recycled cells preserve Work2 idle guarantees; the approved new spring has a different response curve.
View beforeView=new View(),nowView=new View();beforeView.parent=new View();nowView.parent=new View();BaselineBubbleTapMotion beforeMotion=new BaselineBubbleTapMotion(beforeView);BubbleTapMotion motion=new BubbleTapMotion(nowView);for(int i=0;i<1000;i++){beforeMotion.reset();motion.reset();}check(nowView.invalidations==0&&beforeView.invalidations==1000);
for(int hz:new int[]{60,90,120,144}){SystemClock.now=0;beforeMotion.press(.04f,.7f,280);motion.press(.04f,.7f,280);check(motion.scale()<1f&&motion.scale()>.99f);beforeMotion.release();motion.release();for(int n=1;n<=hz;n++){SystemClock.now=Math.round(n*1000f/hz);beforeMotion.run();motion.run();check(Float.isFinite(motion.scale())&&motion.scale()>.94f&&motion.scale()<1.04f);}check(motion.scale()==1f);motion.reset();motion.run();check(motion.scale()==1&&!motion.pressed());}
motion.press(.02f,.3f,180);motion.release();motion.reset();int count=nowView.invalidations;motion.run();check(nowView.invalidations==count&&nowView.callbacks.isEmpty());
System.out.println("{\\"assertions\\":"+checks+",\\"startup_loop_controller_calls_one_active\\":{\\"before\\":"+directCalls+",\\"after\\":"+eligible+"},\\"burst_1000_queued_checks\\":1,\\"stationary_lens_builds_1000_prepares\\":{\\"before\\":"+oldBuilds+",\\"after\\":"+newBuilds+"},\\"contour_bounds_queries\\":{\\"before\\":"+oldQueries+",\\"after\\":"+newQueries+"},\\"idle_cell_invalidations_1000_resets\\":{\\"before\\":1000,\\"after\\":0},\\"device_fps\\":null,\\"evidence\\":\\"ISOLATED_OPERATION_COUNTS_NOT_DEVICE_TIMING\\"}");
}}
'''


def sources():
    names = ['app/flexygram/performance/StartupAccounts.java','app/flexygram/performance/CoalescedTask.java',
             'app/flexygram/performance/ScrollFrameRateHint.java','app/flexygram/navigation/LiquidLensRenderer.java',
             'app/flexygram/bubbles/SignatureBorderPath.java','app/flexygram/bubbles/interaction/BubbleTapMotion.java','app/flexygram/performance/NetworkSnapshotAge.java','app/flexygram/performance/RefreshRateMonitor.java']
    # The retired Home lens is retained only as historical PR132 benchmark evidence.
    # No lens code executes in the current Home bar.
    result={name:((JAVA/name).read_text() if (JAVA/name).is_file() else subprocess.check_output(['git','show','3db6f7a87d147b84a628af7352299173424ce4f7:TMessagesProj/src/main/java/'+name],cwd=ROOT,text=True)) for name in names}
    for helper in ['app/exteraless/player/Spring.java','app/flexygram/bubbles/interaction/DampedSpringCurve.java']:
        result[helper]=(JAVA/helper).read_text()
    for name in [names[0],names[3],names[4],names[5]]:
        old=subprocess.check_output(['git','show',BASE+':TMessagesProj/src/main/java/'+name],cwd=ROOT,text=True)
        cls=Path(name).stem
        result[name.replace(cls,'Baseline'+cls)]=old.replace(cls,'Baseline'+cls)
    return result


def startup_probes(temp):
    relative='TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java'
    before=subprocess.check_output(['git','show',BASE+':'+relative],cwd=ROOT,text=True)
    after=(ROOT/relative).read_text()
    names=[]
    for name,source in [('BeforeStartupProbe',before),('AfterStartupProbe',after)]:
        start=source.index('        UserConfig.getInstance(0).loadConfig();')
        end=source.index('        PushListenerController.reconcilePushRegistration();',start)
        block=source[start:end]
        text="""import java.util.*;public class CLASS {
static int selected,mask,cache,puts,unsent;static Set<Integer>controllers=new HashSet<>();static int[]loads;
static class TLRPC{static class User{}}
static class UserConfig{static int MAX_ACCOUNT_COUNT=10,selectedAccount;int id;UserConfig(int i){id=i;}static UserConfig getInstance(int i){return new UserConfig(i);}void loadConfig(){loads[id]++;if(id==0)selectedAccount=selected;}boolean isClientActivated(){return(mask&(1<<id))!=0;}TLRPC.User getCurrentUser(){return isClientActivated()?new TLRPC.User():null;}}
static class MessagesController{static MessagesController getInstance(int i){if(loads[i]==0)throw new AssertionError();controllers.add(i);return new MessagesController();}void putUser(TLRPC.User u,boolean b){puts++;}}
static class ConnectionsManager{static ConnectionsManager getInstance(int i){return new ConnectionsManager();}int getCurrentTime(){return 0;}}
static class SharedConfig{static String pushStringStatus;}
static class SendMessagesHelper{static SendMessagesHelper getInstance(int i){return new SendMessagesHelper();}void checkUnsentMessages(){unsent++;}}
static boolean prepareDialogs=true;
static void prepareSelectedDialogs(){if((mask&(1<<selected))==0||loads[selected]==0)throw new AssertionError();cache++;}
static void exercise(){ BLOCK }
public static void main(String[]args){for(selected=0;selected<10;selected++)for(mask=0;mask<1024;mask++){cache=puts=unsent=0;controllers.clear();loads=new int[10];exercise();for(int a=0;a<10;a++)if(loads[a]!=(a==0?ZERO:1))throw new AssertionError("config count");if(puts!=Integer.bitCount(mask)||unsent!=puts)throw new AssertionError("active user work");if(cache!=((mask&(1<<selected))!=0?1:0))throw new AssertionError("local cache scheduling");for(int a=0;a<10;a++)if(controllers.contains(a)!=EXPECTED)throw new AssertionError("controller eligibility");}}
}
""".replace('CLASS',name).replace('BLOCK',block).replace('ZERO','2' if name.startswith('Before') else '1').replace('EXPECTED','true' if name.startswith('Before') else '(a==0||a==selected||(mask&(1<<a))!=0)')
        path=temp/(name+'.java');path.write_text(text);names.append(str(path))
    subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(temp/'classes'),'-d',str(temp/'classes'),*names],check=True)
    for name in ['BeforeStartupProbe','AfterStartupProbe']:
        subprocess.run(['java','-cp',str(temp/'classes'),name],check=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/performance-p0/operation-results.json')
    parser.add_argument('--android-jar',type=Path)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='flexy-performance-p0-') as directory:
        temp=Path(directory);written=[]
        for name,text in {**STUBS,**sources(),'PerformanceHarness.java':HARNESS}.items():
            path=temp/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);written.append(str(path))
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',str(temp/'classes'),*written],check=True)
        result=subprocess.check_output(['java','-cp',str(temp/'classes'),'PerformanceHarness'],text=True)
        report=json.loads(result)
        report["retired_home_lens_scope"]="HISTORICAL_PR132_ONLY_NOT_CURRENT_HOME"
        startup_probes(temp)
        report["actual_startup_loop_matrix"]="PASS_10240_STATES_EACH_REVISION_ISOLATED_DOUBLES"
        cell=(JAVA/'org/telegram/ui/Cells/DialogCell.java').read_text()
        start=cell.index('    private static final int[] SMART_VOICE_BARS')
        end=cell.index('    private void drawSmartPreviewBackground',start)
        geometry=cell[start:end]
        baseline=subprocess.check_output(['git','show',BASE+':TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java'],cwd=ROOT,text=True)
        def bars(text,start):
            a=text.index(start);loop=text.index('for(int i=0;i<SMART_VOICE_BARS.length;i++)',a);brace=text.index('{',loop);depth=0
            for i in range(brace,len(text)):
                if text[i]=='{':depth+=1
                elif text[i]=='}':
                    depth-=1
                    if depth==0:return text[a:i+1]
            raise ValueError('No waveform loop')
        before_bars=bars(baseline,'            float barWidth=dp(1f);')
        after_bars=bars(cell,'            prepareSmartVoiceGeometry();')
        voice='import org.telegram.messenger.AndroidUtilities;import android.graphics.*;public class VoiceGeometryProbe {static int calls;static int dp(float v){calls++;return (int)Math.ceil(v*AndroidUtilities.density);}' + geometry
        voice+='final Canvas canvas=new Canvas();final Paint smartPreviewPaint=new Paint(1);void beforeDraw(float right){float waveX=0,cy=20;'+before_bars+'}void afterDraw(float right){float waveX=0,cy=20;'+after_bars+'}'
        voice+="""
public static void main(String[]a){for(float density:new float[]{.75f,1f,1.25f,1.5f,2f,3.5f}){AndroidUtilities.density=density;VoiceGeometryProbe p=new VoiceGeometryProbe();for(float width:new float[]{0,4,10,50,1000}){p.canvas.bars.clear();p.beforeDraw(width);String old=p.canvas.bars.toString();p.canvas.bars.clear();p.afterDraw(width);if(!old.equals(p.canvas.bars.toString()))throw new AssertionError("geometry changed");}for(int i=0;i<SMART_VOICE_BARS.length;i++)if(p.smartVoiceHeights[i]!=(int)Math.ceil((SMART_VOICE_BARS[i]*.65f)*density))throw new AssertionError();}AndroidUtilities.density=1;VoiceGeometryProbe p=new VoiceGeometryProbe();calls=0;for(int i=0;i<1000;i++){p.canvas.bars.clear();p.beforeDraw(1000);}int before=calls;calls=0;for(int i=0;i<1000;i++){p.canvas.bars.clear();p.afterDraw(1000);}if(before!=22000||calls!=10)throw new AssertionError("operation counts");}
}"""
        path=temp/'VoiceGeometryProbe.java';path.write_text(voice)
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(temp/'classes'),'-d',str(temp/'classes'),str(path)],check=True)
        subprocess.run(['java','-cp',str(temp/'classes'),'VoiceGeometryProbe'],check=True)
        hot=cell[cell.index('            prepareSmartVoiceGeometry();'):cell.index('    private void drawSmartPreviewBackground')+cell[cell.index('    private void drawSmartPreviewBackground'):].index('    public') if '    public' in cell[cell.index('    private void drawSmartPreviewBackground'):] else len(cell)]
        assert 'float h=smartVoiceHeights[i]' in hot and 'float x=waveX+smartVoiceSpacing*i' in hot
        report['voice_bar_dp_calls_1000_full_width_draws']={'before':22000,'after':10,'density_change_rebuilds':True}
        if args.android_jar:
            api=temp/'api';api.mkdir()
            inputs=[str(JAVA/name) for name in sources() if 'Baseline' not in name and (JAVA/name).is_file()]
            # Minimal project-only dependencies, not a replacement for the Android platform API.
            inputs += [str(temp/'org/telegram/messenger/AndroidUtilities.java'),str(temp/'app/flexygram/navigation/LiquidNavigationConfig.java')]
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-classpath',str(args.android_jar),'-d',str(api),*inputs],check=True)
            report['official_android_api_compile']='PASS_NOT_FULL_APP'
        else:report['official_android_api_compile']='NOT_RUN'
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))


if __name__=='__main__':main()
