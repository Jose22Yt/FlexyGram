"""Execute actual old/new Activity back methods with a rejecting transition host."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta'
BASE='40c80878b18cdc50f49d44eb4fb26a31b9b0cf6a'

def method(text,signature):
 start=text.index(signature);opening=text.index('{',start);end=opening+1;depth=1
 while depth:
  depth+=(text[end]=='{')-(text[end]=='}');end+=1
 return text[start:end]

class BackRegression(unittest.TestCase):
 def test_back_during_transition_original_fails_corrected_queues(self):
  old=subprocess.check_output(['git','show',BASE+':'+str((SOURCE/'BetaPreviewActivity.java').relative_to(ROOT))],cwd=ROOT,text=True)
  new=(SOURCE/'BetaPreviewActivity.java').read_text();tools=Path(os.environ['JAVA_HOME'])/'bin'
  for original,text in [(True,old),(False,new)]:
   body=method(text,'public void onBackPressed()')
   if not original:body+='\n'+method(text,'private void requestClose()')
   code='''package org.telegram.ui.beta;
import java.util.*;
class Parent {public void onBackPressed(){}}
public class BackHarness extends Parent {
 static class Conversation {}
 static class Navigation {
  boolean busy=true;int closed;
  List<Integer> stack=new ArrayList<>(List.of(0,1));
  List<Integer> getFragmentStack(){return stack;}
  Object getLastFragment(){return new Conversation();}
  void onBackPressed(){if(busy)return;closed++;stack.remove(stack.size()-1);}
 }
 static class Frames implements LatestNavigation.Scheduler {
  List<Runnable> rows=new ArrayList<>();
  public void postFrame(Runnable r){rows.add(r);}public void cancel(Runnable r){rows.remove(r);}
 }
 Navigation navigation=new Navigation();Frames frames=new Frames();
 FIELD
 BODY
 public static void main(String[]args){
  BackHarness owner=new BackHarness();owner.onBackPressed();
  if(owner.navigation.closed!=0)throw new AssertionError("premature close");
  owner.navigation.busy=false;
  while(!owner.frames.rows.isEmpty())owner.frames.rows.remove(0).run();
  if(owner.navigation.closed!=1)throw new AssertionError("BACK_DURING_OPEN_WAS_LOST");
 }
}'''
   field='LatestNavigation requests=new LatestNavigation(frames,()->navigation.busy);'if original else'''BetaNavigation requests=new BetaNavigation(frames,new BetaNavigation.Host(){
    public boolean busy(){return navigation.busy;}
    public boolean perform(BetaNavigation.Destination d){navigation.onBackPressed();return navigation.closed==1;}
    public void observeFrame(java.util.function.Consumer<Boolean> complete){complete.accept(true);}
    public void cancelObservation(){}
   },new NavigationEvents(64,System::nanoTime));'''
   with tempfile.TemporaryDirectory()as d:
    root=Path(d);(root/'BackHarness.java').write_text(code.replace('FIELD',field).replace('BODY',body))
    result=subprocess.run([str(tools/'javac'),'-d',d,*[str(SOURCE/(n+'.java'))for n in ['LatestNavigation','NavigationEvents','BetaNavigation']],str(root/'BackHarness.java')],capture_output=True,text=True,timeout=30)
    self.assertEqual(result.returncode,0,result.stderr)
    result=subprocess.run([str(tools/'java'),'-cp',d,'org.telegram.ui.beta.BackHarness'],capture_output=True,text=True,timeout=15)
    if original:self.assertNotEqual(result.returncode,0);self.assertIn('BACK_DURING_OPEN_WAS_LOST',result.stderr)
    else:self.assertEqual(result.returncode,0,result.stderr)
