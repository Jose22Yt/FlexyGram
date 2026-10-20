"""Run the actual beta queue with a fake frame scheduler; no Android timing claims."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]


class NavigationQueueTests(unittest.TestCase):
    def test_bounded_latest_request_reentrancy_and_lifecycle(self):
        harness='''package org.telegram.ui.beta;
import java.util.*;
public class QueueHarness {
 static void require(boolean b,String why){if(!b)throw new AssertionError(why);}
 static final class Frames implements LatestNavigation.Scheduler {
  final List<Runnable> frames=new ArrayList<>();
  public void postFrame(Runnable r){frames.add(r);}
  public void cancel(Runnable r){frames.remove(r);}
  void step(){frames.remove(0).run();}
 }
 public static void main(String[] args){
  Frames f=new Frames();boolean[] busy={true};int[] result={-1};
  LatestNavigation q=new LatestNavigation(f,()->busy[0]);
  for(int i=0;i<1000;i++){final int value=i;q.submit(()->result[0]=value);}
  require(f.frames.size()==1,"tap queue must stay bounded");
  f.step();require(f.frames.size()==1&&result[0]==-1,"busy transition must defer one frame");
  busy[0]=false;f.step();require(result[0]==999&&f.frames.isEmpty(),"latest interaction must win");
  q.submit(()->{result[0]=1;q.submit(()->result[0]=2);});
  f.step();require(result[0]==1&&f.frames.size()==1,"reentrant request ownership lost");
  f.step();require(result[0]==2&&f.frames.isEmpty(),"replacement not delivered");
  q.submit(()->result[0]=3);q.cancel();require(f.frames.isEmpty()&&result[0]==2,"pause/back must cancel pending navigation");
  q.submit(()->result[0]=4);q.close();q.submit(()->result[0]=5);
  require(f.frames.isEmpty()&&result[0]==2,"closed screen retained pending work");
  LatestNavigation[] owner={null};
  owner[0]=new LatestNavigation(f,()->{owner[0].cancel();return false;});
  owner[0].submit(()->result[0]=6);f.step();
  require(result[0]==2&&f.frames.isEmpty(),"reentrant busy-probe cancellation ran stale work");
  System.out.println("PASS: 1000 interactions, one frame, latest wins, reentry, cancel, close");
 }
}'''
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);target=root/'org/telegram/ui/beta';target.mkdir(parents=True)
            (target/'LatestNavigation.java').write_bytes((ROOT/'TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta/LatestNavigation.java').read_bytes())
            (target/'QueueHarness.java').write_text(harness)
            tools=Path(os.environ['JAVA_HOME'])/'bin'
            subprocess.run([str(tools/'javac'),'-d',d,*map(str,target.glob('*.java'))],check=True,capture_output=True,text=True)
            result=subprocess.run([str(tools/'java'),'-cp',d,'org.telegram.ui.beta.QueueHarness'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
