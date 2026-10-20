"""Execute beta Java core, not Android. Synthetic host and monotonic clock; no network."""
from pathlib import Path
import json
import types
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta'

HARNESS=r'''package org.telegram.ui.beta;
import java.io.*;
import java.util.*;
import java.util.concurrent.atomic.*;
import java.util.function.*;
public class ClientHarness {
 static void require(boolean value,String why){if(!value)throw new AssertionError(why);}
 static class Frames implements LatestNavigation.Scheduler {
  List<Runnable> frames=new ArrayList<>();
  public void postFrame(Runnable r){frames.add(r);}
  public void cancel(Runnable r){frames.remove(r);}
  void step(){frames.remove(0).run();}
 }
 static class Host implements BetaNavigation.Host {
  boolean busy, conversation; int opened,closed,themes; Consumer<Boolean> endpoint;
  List<String> calls=new ArrayList<>(); Runnable reentry;
  public boolean busy(){return busy;}
  public boolean perform(BetaNavigation.Destination d){
   require(!busy,"navigation entered while busy");calls.add(d.name());
   if(reentry!=null){Runnable r=reentry;reentry=null;r.run();}
   switch(d){
    case CONVERSATION:opened++;conversation=true;return true;
    case BACK:closed++;conversation=false;return true;
    case DARK:case LIGHT:themes++;return true;
    default:return true;
   }
  }
  public void observeFrame(Consumer<Boolean> completion){endpoint=completion;}
  public void cancelObservation(){endpoint=null;}
  void frame(){Consumer<Boolean> c=endpoint;endpoint=null;if(c!=null)c.accept(true);}
 }
 static String drain(NavigationEvents events)throws Exception {
  AtomicReference<String> result=new AtomicReference<>();AtomicReference<Throwable> error=new AtomicReference<>();
  Thread worker=new Thread(()->{try{StringWriter w=new StringWriter();events.drainTo(w);result.set(w.toString());}catch(Throwable t){error.set(t);}});
  worker.start();worker.join(5000);require(!worker.isAlive(),"export hung");
  if(error.get()!=null)throw new AssertionError(error.get());return result.get();
 }
 public static void main(String[] args)throws Exception{
  AtomicLong clock=new AtomicLong(1000000000L);
  NavigationEvents events=new NavigationEvents(args[0].equals("overflow")?1:256,()->clock.getAndIncrement());
  Frames frames=new Frames();Host host=new Host();BetaNavigation nav=new BetaNavigation(frames,host,events);
  switch(args[0]){
   case "close":
    nav.startup();host.frame();nav.request(BetaNavigation.Destination.CONVERSATION,false);frames.step();
    host.busy=true;nav.request(BetaNavigation.Destination.BACK,true);frames.step();
    require(host.closed==0&&frames.frames.size()==1,"close lost or premature during open");
    host.frame();host.busy=false;frames.step();host.frame();
    require(host.opened==1&&host.closed==1,"consecutive close lost");break;
   case "replace":
    host.busy=true;nav.request(BetaNavigation.Destination.CONVERSATION,false);
    nav.request(BetaNavigation.Destination.CONVERSATION,false);
    require(frames.frames.size()==1,"unbounded tap queue");
    host.busy=false;frames.step();host.frame();
    nav.request(BetaNavigation.Destination.BACK,true);nav.pause();
    require(frames.frames.isEmpty(),"paused navigation retained work");
    nav.request(BetaNavigation.Destination.CONVERSATION,false);require(frames.frames.isEmpty(),"paused request admitted");
    nav.resume();host.reentry=nav::pause;nav.request(BetaNavigation.Destination.CONVERSATION,false);frames.step();
    require(host.endpoint==null,"synchronous pause retained observer");
    nav.close();nav.resume();nav.request(BetaNavigation.Destination.CONVERSATION,false);require(frames.frames.isEmpty(),"closed request admitted");break;
   case "overflow":
    nav.request(BetaNavigation.Destination.CONVERSATION,false);frames.step();host.frame();
    nav.request(BetaNavigation.Destination.BACK,true);frames.step();host.frame();
    require(host.opened==1&&host.closed==1&&events.lostEvents()>0,"observer changed navigation or hid drops");break;
   case "clock":
    events.instant(NavigationEvents.Op.rapid_tap);clock.set(1);events.instant(NavigationEvents.Op.rapid_tap);
    require(events.lostEvents()==3,"clock regression not marked lost");
    AtomicReference<Throwable> rejected=new AtomicReference<>();
    Thread wrong=new Thread(()->{try{events.request(NavigationEvents.Op.startup);}catch(Throwable t){rejected.set(t);}});wrong.start();wrong.join();
    require(rejected.get() instanceof IllegalStateException,"multiple producers admitted");
    try{events.drainTo(new StringWriter());throw new AssertionError("UI export admitted");}catch(IllegalStateException good){}break;
   case "io":
    events.instant(NavigationEvents.Op.startup);
    AtomicReference<Throwable> failed=new AtomicReference<>();
    Thread bad=new Thread(()->{try{events.drainTo(new Writer(){public void write(char[] c,int o,int l)throws IOException{throw new IOException("synthetic");}public void close(){}public void flush(){}});}catch(Throwable t){failed.set(t);}});
    bad.start();bad.join();require(failed.get() instanceof IOException&&events.lostEvents()>0,"failed export claimed complete");break;
   case "theme":
    host.busy=true;nav.request(BetaNavigation.Destination.DARK,false);nav.request(BetaNavigation.Destination.LIGHT,false);
    host.busy=false;frames.step();host.frame();
    require(host.themes==1&&host.calls.equals(List.of("LIGHT")),"superseded theme applied");break;
   case "concurrent":
    java.util.concurrent.CountDownLatch blocked=new java.util.concurrent.CountDownLatch(1),release=new java.util.concurrent.CountDownLatch(1);
    AtomicReference<Throwable> collision=new AtomicReference<>();
    events.instant(NavigationEvents.Op.startup);
    Thread first=new Thread(()->{try{events.drainTo(new Writer(){public void write(char[]c,int o,int l)throws IOException{blocked.countDown();try{if(!release.await(5,java.util.concurrent.TimeUnit.SECONDS))throw new IOException();}catch(InterruptedException e){throw new IOException();}}public void close(){}public void flush(){}});}catch(Throwable e){collision.set(e);}});
    first.start();require(blocked.await(5,java.util.concurrent.TimeUnit.SECONDS),"writer not reached");
    // UI production succeeds while the exporter is deliberately blocked on I/O.
    events.instant(NavigationEvents.Op.rapid_tap);
    Thread second=new Thread(()->{try{events.drainTo(new StringWriter());}catch(Throwable e){collision.set(e);}});second.start();second.join(5000);
    release.countDown();first.join(5000);require(!first.isAlive()&&!second.isAlive()&&collision.get() instanceof IllegalStateException,"concurrent consumers admitted or UI blocked");
    // Those first records were consumed by a deliberately non-retaining writer in the harness.
    events.exportFailed(3);break;
   case "probe":
    ProbeState probe=new ProbeState();require(probe.begin(),"initial probe rejected");
    require(!probe.begin()&&probe.value()==ProbeState.Value.RUNNING,"duplicate runtime work admitted");
    // A new Settings view reads the Activity state instead of a cell captured by a worker.
    require(probe.value()==ProbeState.Value.RUNNING,"recreated view lost in-progress state");
    require(probe.finish(true)&&probe.value()==ProbeState.Value.READY,"result lost");
    probe.close();require(!probe.begin()&&!probe.finish(false),"destroyed Activity admitted result");break;
   case "export":
    events.instant(NavigationEvents.Op.startup);File root=new File(args[1]);
    AtomicReference<Boolean> saved=new AtomicReference<>();
    Thread exporter=new Thread(()->saved.set(BetaEventExport.save(root,events,1)));exporter.start();exporter.join();
    require(Boolean.TRUE.equals(saved.get()),"private export failed");
    File target=new File(new File(root,"beta-observer"),events.session()+"_1");
    require(new File(target,"events.jsonl").isFile()&&new File(target,"observer.json").isFile(),"incomplete export reported complete");
    exporter=new Thread(()->saved.set(BetaEventExport.save(root,events,1)));exporter.start();exporter.join();
    require(!saved.get(),"existing export overwritten");break;
   default:throw new AssertionError("unknown scenario");
  }
  System.out.print(drain(events));System.out.println("LOST="+events.lostEvents());
 }
}'''

class ClientEventsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name)
  cls.tools=Path(os.environ['JAVA_HOME'])/'bin'
  (cls.folder/'ClientHarness.java').write_text(HARNESS)
  names=['NavigationEvents','LatestNavigation','BetaNavigation','ProbeState','BetaEventExport']
  result=subprocess.run([str(cls.tools/'javac'),'-d',str(cls.folder),*[str(SOURCE/(n+'.java'))for n in names],str(cls.folder/'ClientHarness.java')],capture_output=True,text=True,timeout=30)
  if result.returncode:raise AssertionError(result.stderr)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def run_case(self,name):
  with tempfile.TemporaryDirectory()as d:
   result=subprocess.run([str(self.tools/'java'),'-cp',str(self.folder),'org.telegram.ui.beta.ClientHarness',name,d],capture_output=True,text=True,timeout=15)
   self.assertEqual(result.returncode,0,result.stderr)
   rows=[json.loads(line)for line in result.stdout.splitlines()if line.startswith('{')]
   previous=-1;phases={}
   for row in rows:
    self.assertEqual(set(row),{'id','op','phase','timestamp_ns','clock'})
    self.assertRegex(row['id'],r'^[A-Za-z0-9_-]{1,64}$')
    self.assertEqual(row['clock'],'android_monotonic_ns');self.assertGreaterEqual(row['timestamp_ns'],previous);previous=row['timestamp_ns']
    key=row['id'];phases.setdefault(key,[]).append(row['phase'])
   for phases_row in phases.values():
    self.assertEqual(len(phases_row),len(set(phases_row)))
    if 'presented'in phases_row:self.assertLess(phases_row.index('accepted'),phases_row.index('presented'))
   return rows
 def test_close_after_open_waits_and_completes(self):
  rows=self.run_case('close');self.assertEqual([r['phase']for r in rows if r['op']=='chat_close'],['request','accepted','presented'])
 def test_replace_pause_reentry_and_closed_owner(self):
  rows=self.run_case('replace');self.assertTrue(any(r['op']=='transition_interrupt'for r in rows));self.assertFalse(any(r['phase']=='timeout'for r in rows))
 def test_overflow_cannot_change_navigation(self):self.run_case('overflow')
 def test_interoperability_with_pinned_work1_analyzer(self):
  # Consume the exact existing analyzer read-only, never copy/modify it in this PR.
  source=subprocess.check_output(['git','show','db5b9a113d54f552a925ea233c5b199ab95bfcdb:tools/beta_diagnostics/analyze.py'],cwd=ROOT,text=True)
  module=types.ModuleType('work1_pinned_analyzer');exec(compile(source,'work1-pinned-analyzer','exec'),module.__dict__)
  rows=self.run_case('close')+[]
  report=module.interactions('\n'.join(json.dumps(r)for r in rows))
  self.assertEqual(report['status'],'EVENT_SAMPLE')
  self.assertEqual(report['operations']['chat_open']['presented'],1)
  self.assertEqual(report['operations']['chat_close']['presented'],1)
  meta={'schema':1,'client':'FlexyGram','apk_sha256':'0'*64,'source':'synthetic','run_id':'host_interop','repetition':0,
        'conditions':{'event_endpoint':'beta_idle_predraw_frame_v1','observer_lost_events':0}}
  combined=module.report(meta,'io.github.jose22yt.flexygram.beta.development',[],event_text='\n'.join(json.dumps(r)for r in rows))
  self.assertFalse(combined['android_execution_verified_by_analyzer'])
  self.assertEqual(combined['interactions']['operations']['chat_close']['presented'],1)
  rows=self.run_case('replace');report=module.interactions('\n'.join(json.dumps(r)for r in rows))
  self.assertGreater(report['operations']['transition_interrupt']['cancelled'],0)
  self.assertEqual(report['operations']['transition_interrupt']['presented'],0)
  self.assertGreater(report['operations']['chat_open']['incomplete'],0)
  self.assertEqual(report['operations']['chat_open']['timeout'],0)
 def test_rapid_tap_observes_navigation_frame_instead_of_instant_success(self):
  rows=self.run_case('close')
  phases=[row['phase'] for row in rows if row['op']=='rapid_tap']
  self.assertEqual(phases,['request','accepted','presented'])
  chat_close_frame=next(row['timestamp_ns'] for row in rows
                         if row['op']=='chat_close' and row['phase']=='presented')
  tap_frame=next(row['timestamp_ns'] for row in rows
                 if row['op']=='rapid_tap' and row['phase']=='presented')
  self.assertGreater(tap_frame,chat_close_frame,
                     'rapid tap must not complete before navigation endpoint')
 def test_interrupt_reports_logical_cancellation_not_presentation(self):
  rows=self.run_case('replace')
  by_id={}
  for row in rows:
   if row['op']=='transition_interrupt':by_id.setdefault(row['id'],[]).append(row['phase'])
  self.assertTrue(by_id)
  for phases in by_id.values():self.assertEqual(phases,['request','accepted','cancelled'])
 def test_clock_regression_and_thread_ownership(self):self.run_case('clock')
 def test_writer_failure_is_not_loss_free(self):self.run_case('io')
 def test_probe_state_recreated_view_and_destroy(self):self.run_case('probe')
 def test_theme_replacement_uses_only_latest_explicit_target(self):
  rows=self.run_case('theme');self.assertEqual([r['phase']for r in rows if r['op']=='theme_dark'],['request','cancelled'])
  self.assertEqual([r['phase']for r in rows if r['op']=='theme_light'],['request','accepted','presented'])
 def test_blocked_writer_does_not_block_ui_and_second_consumer_rejected(self):self.run_case('concurrent')
 def test_export_is_background_private_and_never_overwrites(self):self.run_case('export')
