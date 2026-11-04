"""Presentation timing and actual ASM call rewriting; never changes this machine's animation settings."""
from pathlib import Path
import os, shutil, subprocess
import pytest
from test_render_work_reuse import JAVA, ROOT, probe


def test_fixed_point_zero_one_and_system_compensation(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.animation.FastMotionTiming;
public class Probe {public static void main(String[] args){
 if(FastMotionTiming.SCALE!=.01d||FastMotionTiming.duration(300)!=3||FastMotionTiming.delay(200)!=2)throw new AssertionError();
 for(float s:new float[]{.01f,.5f,1,1.5f,5,6})for(long nominal:new long[]{100,150,200,300,500,1000}){
  long value=FastMotionTiming.animatorDuration(nominal,s);
  if(value<1||Math.abs(value*s-nominal*.01d)>Math.max(s,.01)+.0001)throw new AssertionError("scale "+s);
 }
 if(FastMotionTiming.duration(0)!=0||FastMotionTiming.duration(-1)!=-1)throw new AssertionError("zero/native sentinel");
 for(float s:new float[]{0,-1,Float.NaN,Float.POSITIVE_INFINITY})if(FastMotionTiming.animatorDuration(300,s)!=3)throw new AssertionError("invalid scale");
 if(FastMotionTiming.animatorDuration(Long.MAX_VALUE,Float.MIN_VALUE)<0)throw new AssertionError("overflow");
}}'''},[JAVA/'app/flexygram/animation/FastMotionTiming.java'])


def test_disabled_policy_uses_system_clock_but_does_not_double_scale_android_animators(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.animation.FastMotionTiming;
public class Probe {public static void main(String[]args){
 FastMotionTiming.setSystemScaleProvider(()->5d);FastMotionTiming.setEnabled(false);
 if(FastMotionTiming.duration(300)!=1500||FastMotionTiming.delay(100)!=500)throw new AssertionError("native manual clock");
 if(FastMotionTiming.animatorDuration(300,5)!=300||FastMotionTiming.animatorDelay(100,5)!=100)throw new AssertionError("native framework double scaling");
 if(Math.abs(FastMotionTiming.frameDelta(.016f)-.0032f)>.00001f)throw new AssertionError("native spring clock");
 FastMotionTiming.setSystemScaleProvider(()->0d);if(FastMotionTiming.duration(300)!=1||FastMotionTiming.delay(100)!=0||FastMotionTiming.frameDelta(.016f)!=0)throw new AssertionError("disabled Android animations");
 FastMotionTiming.setEnabled(true);if(FastMotionTiming.duration(300)!=3||FastMotionTiming.frameDelta(.016f)!=.016f)throw new AssertionError("fast restored");
}}'''},[JAVA/'app/flexygram/animation/FastMotionTiming.java'])


def test_actual_animated_float_finishes_at_its_fixed_deadline_without_idle_redraw(tmp_path):
    files={
      'android/animation/TimeInterpolator.java':'package android.animation;public interface TimeInterpolator{float getInterpolation(float t);}',
      'android/os/SystemClock.java':'package android.os;public class SystemClock{public static long now;public static long elapsedRealtime(){return now;}}',
      'android/view/View.java':'package android.view;public class View{public void invalidate(){}}',
      'androidx/core/math/MathUtils.java':'package androidx.core.math;public class MathUtils{public static float clamp(float n,float a,float b){return Math.max(a,Math.min(b,n));}}',
      'org/telegram/messenger/AndroidUtilities.java':'package org.telegram.messenger;public class AndroidUtilities{public static float lerp(float a,float b,float t){return a+(b-a)*t;}}',
      'org/telegram/ui/Components/CubicBezierInterpolator.java':'package org.telegram.ui.Components;public class CubicBezierInterpolator{public static final android.animation.TimeInterpolator DEFAULT=t->t;}',
      'Probe.java':'''import org.telegram.ui.Components.AnimatedFloat;import android.os.SystemClock;
public class Probe {public static void main(String[]args){int[] invalid={0};AnimatedFloat a=new AnimatedFloat((Runnable)()->invalid[0]++);a.setDuration(300);a.set(0);a.set(1);
 if(!a.isInProgress()||a.getDuration()!=300)throw new AssertionError("public nominal duration");
 SystemClock.now=3;if(a.getValue()!=1||a.isInProgress())throw new AssertionError("3ms target");int idle=invalid[0];
 for(int i=0;i<1000;i++)a.getValue();if(invalid[0]!=idle)throw new AssertionError("idle redraws");
 a.setDelay(200);a.set(0);SystemClock.now=4;if(a.getValue()!=1)throw new AssertionError("early delay");
 SystemClock.now=8;if(a.getValue()!=0||a.isInProgress())throw new AssertionError("delay+transition deadline");
 a.set(1,true);if(a.getValue()!=1||a.isInProgress())throw new AssertionError("force");
}}'''}
    probe(tmp_path,files,[JAVA/'org/telegram/ui/Components/AnimatedFloat.java',JAVA/'app/flexygram/animation/FastMotionTiming.java'])


def test_actual_bytecode_visitor_routes_only_animation_calls_and_preserves_super_and_timers(tmp_path):
    jar=os.environ.get('FLEXY_ASM_JAR')
    if not jar or not Path(jar).is_file():pytest.skip('Set FLEXY_ASM_JAR to the existing Gradle ASM jar')
    if not shutil.which('javac'):pytest.skip('JDK required')
    files={
      'android/animation/Animator.java':'package android.animation;public class Animator{public int starts;public void start(){starts++;}}',
      'android/animation/ValueAnimator.java':'package android.animation;public class ValueAnimator extends Animator{}',
      'android/view/ViewPropertyAnimator.java':'package android.view;public class ViewPropertyAnimator{public int starts;public long duration,delay;public ViewPropertyAnimator setDuration(long n){duration=n;return this;}public ViewPropertyAnimator setStartDelay(long n){delay=n;return this;}public void start(){starts++;}}',
      'android/view/animation/Animation.java':'package android.view.animation;public class Animation{}',
      'android/view/View.java':'package android.view;public class View{public final ViewPropertyAnimator a=new ViewPropertyAnimator();public long posted;public int legacy;public ViewPropertyAnimator animate(){return a;}public void postDelayed(Runnable r,long n){posted=n;}public void startAnimation(android.view.animation.Animation a){legacy++;}}',
      'androidx/dynamicanimation/animation/DynamicAnimation.java':'package androidx.dynamicanimation.animation;public class DynamicAnimation{public int starts;public void start(){starts++;}}',
      'androidx/dynamicanimation/animation/SpringAnimation.java':'package androidx.dynamicanimation.animation;public class SpringAnimation extends DynamicAnimation{}',
      'app/flexygram/animation/FastMotion.java':'''package app.flexygram.animation;public class FastMotion{
 public static int starts,properties,durations,delays,legacy,springs;
 public static void start(android.animation.Animator a){starts++;a.start();}
 public static void start(android.view.ViewPropertyAnimator a){a.start();}
 public static android.view.ViewPropertyAnimator viewAnimator(android.view.ViewPropertyAnimator a){properties++;return a;}
 public static android.view.ViewPropertyAnimator duration(android.view.ViewPropertyAnimator a,long n){durations++;return a.setDuration(n);}
 public static android.view.ViewPropertyAnimator delay(android.view.ViewPropertyAnimator a,long n){delays++;return a.setStartDelay(n);}
 public static void startAnimation(android.view.View v,android.view.animation.Animation a){legacy++;v.startAnimation(a);}
 public static void startSpring(androidx.dynamicanimation.animation.DynamicAnimation a){springs++;a.start();}
}''',
      'Fixture.java':'''public class Fixture extends android.animation.ValueAnimator{
 public void start(){super.start();}
 public static void go(android.animation.ValueAnimator a,android.view.View v,androidx.dynamicanimation.animation.SpringAnimation s){a.start();v.animate().setDuration(300).setStartDelay(100).start();v.postDelayed(()->{},4000);v.startAnimation(new android.view.animation.Animation());s.start();}
}''',
      'MotionAsmProbe.java':'''import java.nio.file.*;import org.objectweb.asm.*;import app.flexygram.motionbuild.FastMotionVisitor;
public class MotionAsmProbe {
 static boolean inherits(String owner,String base){try{return Class.forName(base).isAssignableFrom(Class.forName(owner.replace('/','.')));}catch(Exception ignored){return false;}}
 static class Loader extends ClassLoader{Loader(){super(MotionAsmProbe.class.getClassLoader());}Class<?> define(byte[] b){return defineClass(null,b,0,b.length);}}
 public static void main(String[]args)throws Exception{
  byte[] original=Files.readAllBytes(Path.of(args[0]));ClassWriter writer=new ClassWriter(0);new ClassReader(original).accept(new FastMotionVisitor(writer,MotionAsmProbe::inherits),0);
  Class<?> c=new Loader().define(writer.toByteArray());var a=new android.animation.ValueAnimator();var view=new android.view.View();var spring=new androidx.dynamicanimation.animation.SpringAnimation();
  c.getMethod("go",android.animation.ValueAnimator.class,android.view.View.class,androidx.dynamicanimation.animation.SpringAnimation.class).invoke(null,a,view,spring);
  if(a.starts!=1||view.a.starts!=1||view.legacy!=1||spring.starts!=1||view.posted!=4000)throw new AssertionError("native behavior/timer changed");
  if(app.flexygram.animation.FastMotion.starts!=1||app.flexygram.animation.FastMotion.properties!=1||app.flexygram.animation.FastMotion.durations!=1||app.flexygram.animation.FastMotion.delays!=1||app.flexygram.animation.FastMotion.legacy!=1||app.flexygram.animation.FastMotion.springs!=1)throw new AssertionError("missing hook");
  android.animation.ValueAnimator own=(android.animation.ValueAnimator)c.getConstructor().newInstance();own.start();if(own.starts!=1||app.flexygram.animation.FastMotion.starts!=1)throw new AssertionError("super call recursed");
 }
}'''}
    paths=[]
    for name,text in files.items():
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);paths.append(p)
    visitor=ROOT/'buildSrc/src/main/java/app/flexygram/motionbuild/FastMotionVisitor.java'
    r=subprocess.run(['javac','-cp',jar,'-d',str(tmp_path),*map(str,paths),str(visitor)],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    r=subprocess.run(['java','-cp',str(tmp_path)+os.pathsep+jar,'MotionAsmProbe',str(tmp_path/'Fixture.class')],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
