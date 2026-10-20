"""Actual Java producer/exporter -> reviewed personal importer. Synthetic host only, no Android."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta'
HARNESS=r'''package org.telegram.ui.beta;
import java.io.File;import java.util.*;import java.util.concurrent.atomic.*;import java.util.function.*;
public class ExportBridge {
 static class Frames implements LatestNavigation.Scheduler {
  List<Runnable> rows=new ArrayList<>();public void postFrame(Runnable r){rows.add(r);}public void cancel(Runnable r){rows.remove(r);}void next(){rows.remove(0).run();}
 }
 static class Host implements BetaNavigation.Host {
  Consumer<Boolean> pending;public boolean busy(){return false;}public boolean perform(BetaNavigation.Destination d){return true;}
  public void observeFrame(Consumer<Boolean> c){pending=c;}public void cancelObservation(){pending=null;}
  void frame(){Consumer<Boolean> c=pending;pending=null;c.accept(true);}
 }
 static void save(File root,NavigationEvents events,int batch)throws Exception{
  AtomicBoolean saved=new AtomicBoolean();Thread worker=new Thread(()->saved.set(BetaEventExport.save(root,events,batch)));worker.start();worker.join(5000);
  if(worker.isAlive()||!saved.get())throw new AssertionError("EXPORT_FAILED");
 }
 public static void main(String[] args)throws Exception{
  AtomicLong clock=new AtomicLong(1000000000L);NavigationEvents events=new NavigationEvents(256,clock::getAndIncrement);
  Frames frames=new Frames();Host host=new Host();BetaNavigation nav=new BetaNavigation(frames,host,events);
  nav.startup();host.frame();nav.request(BetaNavigation.Destination.CONVERSATION,false);frames.next();
  save(new File(args[0]),events,1); // pending endpoint spans two real export batches
  host.frame();nav.request(BetaNavigation.Destination.BACK,true);frames.next();host.frame();
  save(new File(args[0]),events,2);
 }
}'''
class PersonalImporterBridge(unittest.TestCase):
 def test_actual_java_two_batch_export_imports_and_keeps_rapid_tap_endpoint(self):
  sys.path.insert(0,str(ROOT/'tools/personal_beta'))
  import import_events
  analyzer,_=import_events.load_reviewed(Path(os.environ['FLEXYGRAM_DIAGNOSTICS_SOURCE']))
  with tempfile.TemporaryDirectory()as d:
   folder=Path(d);(folder/'ExportBridge.java').write_text(HARNESS);tools=Path(os.environ['JAVA_HOME'])/'bin'
   names=['NavigationEvents','LatestNavigation','BetaNavigation','BetaEventExport']
   p=subprocess.run([str(tools/'javac'),'-d',d,*[str(SOURCE/(n+'.java'))for n in names],str(folder/'ExportBridge.java')],capture_output=True,text=True,timeout=30)
   self.assertEqual(p.returncode,0,p.stderr)
   p=subprocess.run([str(tools/'java'),'-cp',d,'org.telegram.ui.beta.ExportBridge',d],capture_output=True,text=True,timeout=15)
   self.assertEqual(p.returncode,0,p.stderr)
   batches=sorted((folder/'beta-observer').iterdir());self.assertEqual(len(batches),2)
   result=import_events.assemble(analyzer,list(reversed(batches)))
   self.assertEqual(result['quality'],'COMPLETE_EVENT_SAMPLE_ONLY')
   self.assertEqual(result['observer_lost_events'],0)
   ops=result['interactions']['operations']
   self.assertEqual(ops['chat_open']['presented'],1);self.assertEqual(ops['chat_close']['presented'],1)
   self.assertEqual(ops['rapid_tap']['presented'],1)
   self.assertEqual(ops['rapid_tap']['incomplete'],0)
