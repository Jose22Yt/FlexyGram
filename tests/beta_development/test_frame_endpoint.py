"""Compile and execute actual View observer with explicit Android doubles, not a device."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta/SceneFrameObserver.java'
TREE='''package android.view;
import java.util.*;
public class ViewTreeObserver {
 public interface OnPreDrawListener {boolean onPreDraw();}
 public List<OnPreDrawListener> rows=new ArrayList<>();public boolean alive=true;
 public boolean isAlive(){return alive;}public void addOnPreDrawListener(OnPreDrawListener r){rows.add(r);}
 public void removeOnPreDrawListener(OnPreDrawListener r){rows.remove(r);}
 public void draw(){for(OnPreDrawListener r:new ArrayList<>(rows))if(!r.onPreDraw())throw new AssertionError("observer blocked draw");}
}'''
VIEW='''package android.view;
import java.util.*;
public class View {
 public ViewTreeObserver tree=new ViewTreeObserver();public boolean visible=true;
 public List<Runnable> frames=new ArrayList<>(),timers=new ArrayList<>();
 public ViewTreeObserver getViewTreeObserver(){return tree;}
 public boolean isAttachedToWindow(){return visible;}public boolean isShown(){return visible;}public boolean hasWindowFocus(){return visible;}
 public int getWidth(){return 10;}public int getHeight(){return 10;}
 public boolean postDelayed(Runnable r,long delay){timers.add(r);return true;}
 public void postOnAnimation(Runnable r){frames.add(r);}public void invalidate(){}
 public boolean removeCallbacks(Runnable r){frames.remove(r);timers.remove(r);return true;}
}'''
HARNESS='''package org.telegram.ui.beta;
import android.view.*;
public class FrameHarness {
 static void require(boolean b,String why){if(!b)throw new AssertionError(why);}
 public static void main(String[]args){
  View v=new View();boolean[] idle={false};int[] yes={0},no={0};
  SceneFrameObserver o=new SceneFrameObserver(v,()->idle[0],b->{if(b)yes[0]++;else no[0]++;});o.start();
  v.tree.draw();require(v.frames.isEmpty()&&yes[0]==0,"busy frame treated as presentation");
  idle[0]=true;v.tree.draw();require(v.frames.size()==1&&yes[0]==0,"predraw treated as final presentation");
  Runnable frame=v.frames.get(0);frame.run();frame.run();
  require(yes[0]==1&&no[0]==0&&v.tree.rows.isEmpty()&&v.timers.isEmpty(),"duplicate endpoint or leaked callbacks");
  o=new SceneFrameObserver(v,()->true,b->{if(b)yes[0]++;else no[0]++;});o.start();v.tree.draw();frame=v.frames.get(0);o.cancel();frame.run();
  require(yes[0]==1&&no[0]==0,"cancelled observer emitted presented");
  o=new SceneFrameObserver(v,()->false,b->{if(!b)no[0]++;});o.start();v.timers.get(0).run();
  require(no[0]==1&&v.frames.isEmpty()&&v.tree.rows.isEmpty(),"timeout did not detach");
  int[] abandoned={0};o=new SceneFrameObserver(v,()->idle[0],b->{if(b==null)abandoned[0]++;else throw new AssertionError("invalidated frame misreported");});
  o.start();idle[0]=true;v.tree.draw();idle[0]=false;v.frames.get(0).run();
  require(abandoned[0]==1&&no[0]==1,"scene invalidation invented timeout");
 }
}'''

class FrameEndpointTests(unittest.TestCase):
 def test_predraw_frame_cancel_and_timeout_real_observer(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);a=root/'android/view';a.mkdir(parents=True)
   (a/'View.java').write_text(VIEW);(a/'ViewTreeObserver.java').write_text(TREE);(root/'FrameHarness.java').write_text(HARNESS)
   tools=Path(os.environ['JAVA_HOME'])/'bin'
   p=subprocess.run([str(tools/'javac'),'-d',d,str(SOURCE),str(a/'View.java'),str(a/'ViewTreeObserver.java'),str(root/'FrameHarness.java')],capture_output=True,text=True,timeout=30)
   self.assertEqual(p.returncode,0,p.stderr)
   p=subprocess.run([str(tools/'java'),'-cp',d,'org.telegram.ui.beta.FrameHarness'],capture_output=True,text=True,timeout=15)
   self.assertEqual(p.returncode,0,p.stderr)
