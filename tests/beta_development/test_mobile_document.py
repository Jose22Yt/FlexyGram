"""Future mobile export: real Java code with explicit Android doubles, never a phone test.
Requires JDK21 and pinned PR24 tools. No skips; this session could not execute it.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from client_android_doubles import STUBS

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta'
HARNESS = r'''package org.telegram.ui.beta;
import java.io.*;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.atomic.*;
import android.app.Activity;
import android.content.*;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import org.telegram.ui.ActionBar.ActionBarLayout;
import org.telegram.ui.Cells.TextSettingsCell;

public class MobileDocumentHarness {
 static void need(boolean value,String why){if(!value)throw new AssertionError(why);}
 static Object field(Object owner,String name)throws Exception{
  java.lang.reflect.Field f=BetaPreviewActivity.class.getDeclaredField(name);f.setAccessible(true);return f.get(owner);
 }
 static ActionBarLayout nav(BetaPreviewActivity owner)throws Exception{return (ActionBarLayout)field(owner,"navigation");}
 static TextSettingsCell button(BetaPreviewActivity owner)throws Exception{
  for(View view:((LinearLayout)nav(owner).getLastFragment().getFragmentView()).children)
   if(view instanceof TextSettingsCell&&"Exportar diagnósticos".equals(((TextSettingsCell)view).text))return (TextSettingsCell)view;
  throw new AssertionError("export button missing");
 }
 interface Condition {boolean done()throws Exception;}
 static void await(Condition condition)throws Exception{
  long until=System.nanoTime()+5000000000L;
  while(System.nanoTime()<until){
   Runnable next;while((next=Activity.ui.poll())!=null)next.run();
   if(condition.done())return;
   Thread.sleep(5);
  }
  throw new AssertionError("host completion timeout");
 }
 static File prepare(File root,NavigationEvents events,int id)throws Exception{
  AtomicReference<File> result=new AtomicReference<>();AtomicReference<Throwable> error=new AtomicReference<>();
  Thread worker=new Thread(()->{try{result.set(BetaDiagnosticsDocument.prepare(root,events,id,ProbeState.Value.READY,ProbeState.Outcome.READY));}catch(Throwable e){error.set(e);}});
  worker.start();worker.join(5000);need(!worker.isAlive(),"writer hung");
  if(error.get()!=null)throw new IOException("synthetic prepare rejected");
  return result.get();
 }
 public static void main(String[] args)throws Exception{
  File root=new File(args[1]);root.mkdirs();
  if(args[0].startsWith("zip")||args[0].equals("copy_fail")){
   AtomicLong clock=new AtomicLong(1);NavigationEvents events=new NavigationEvents(256,clock::getAndIncrement);
   events.instant(NavigationEvents.Op.startup);File first=prepare(root,events,1);
   if(args[0].equals("zip")){
    events.instant(NavigationEvents.Op.chat_open);events.instant(NavigationEvents.Op.chat_close);
    File last=prepare(root,events,2);System.out.print(last.getName());return;
   }
   if(args[0].equals("copy_fail")){
    byte[] bytes=Files.readAllBytes(first.toPath());
    try{BetaDiagnosticsDocument.copy(root,first.getName(),new OutputStream(){public void write(int v)throws IOException{throw new IOException("SYNTHETIC_PRIVATE_VALUE");}});throw new AssertionError("storage failure swallowed");}
    catch(IOException expected){}
    need(Arrays.equals(bytes,Files.readAllBytes(first.toPath())),"failed copy consumed source");return;
   }
   File batch=new File(new File(root,"beta-observer"),events.session()+"_1");
   File tampered=new File(batch,args[0].equals("zip_header")?"observer.json":"events.jsonl");
   Files.write(tampered.toPath(),"{\"password\":\"SYNTHETIC_PRIVATE_VALUE\"}".getBytes("UTF-8"));
   events.instant(NavigationEvents.Op.theme_dark);
   try{prepare(root,events,2);throw new AssertionError("private payload exported");}catch(IOException expected){}
   File candidate=new File(new File(root,"beta-mobile-export"),events.session()+"_2.zip");
   need(!candidate.exists()&&!new File(candidate.getPath()+".partial").exists(),"invalid archive published");
   need(first.isFile()&&tampered.isFile(),"private sources deleted");return;
  }
  System.setProperty("java.io.tmpdir",root.getAbsolutePath());
  BetaPreviewActivity owner=new BetaPreviewActivity();
  try{
   owner.onCreate(null);ActionBarLayout layout=nav(owner);
   ((LinearLayout)layout.getLastFragment().getFragmentView()).children.get(1).performClick();
   View.frame();layout.busy=false;
   if(args[0].equals("idle")){
    need(!new File(owner.getFilesDir(),"beta-mobile-export").exists(),"idle file work");
    need(ContentResolver.opens==0&&owner.picker==null,"idle provider/picker work");
    need(layout.getFragmentStack().size()==2,"idle navigation changed");return;
   }
   if(args[0].equals("picker_fail"))owner.pickerUnavailable=true;
   button(owner).performClick();
   final BetaPreviewActivity original=owner;
   if(args[0].equals("leave_settings")){
    layout.closeLastFragment(false);
    await(()->!(Boolean)field(original,"documentBusy"));
    need(owner.picker==null&&field(owner,"pendingDocument")!=null,"late picker interrupted navigation");return;
   }
   if(args[0].equals("picker_fail")){
    await(()->!(Boolean)field(original,"documentBusy"));
    need(field(owner,"pendingDocument")!=null&&ContentResolver.opens==0,"picker failure lost private retry");
    need(!button(owner).value.contains("SYNTHETIC_PRIVATE_VALUE"),"private exception exposed");return;
   }
   await(()->original.picker!=null);
   need(Intent.ACTION_CREATE_DOCUMENT.equals(owner.picker.action)&&"application/zip".equals(owner.picker.type),"wrong picker");
   need(owner.picker.categories.contains(Intent.CATEGORY_OPENABLE)&&Boolean.TRUE.equals(owner.picker.extras.get(Intent.EXTRA_LOCAL_ONLY)),"local document selection absent");
   String name=(String)field(owner,"pendingDocument");
   File source=new File(new File(owner.getFilesDir(),"beta-mobile-export"),name);
   byte[] bytes=Files.readAllBytes(source.toPath());
   long id=(Long)field(owner,"exportId");
   if(args[0].equals("cancel")){
    owner.onActivityResult(owner.pickerCode,Activity.RESULT_CANCELED,null);
    need(ContentResolver.opens==0&&source.isFile(),"cancel wrote provider/deleted source");
    need(name.equals(field(owner,"pendingDocument")),"cancel dropped retry");
    button(owner).performClick();
    need((Long)field(owner,"exportId")==id&&Arrays.equals(bytes,Files.readAllBytes(source.toPath())),"cancel retry drained again");return;
   }
   if(args[0].equals("recreate")){
    Bundle saved=new Bundle();owner.saveState(saved);int request=owner.pickerCode;owner.onDestroy();
    owner=new BetaPreviewActivity();owner.onCreate(saved);layout=nav(owner);
    need(name.equals(field(owner,"pendingDocument")),"recreation lost pending filename");
    owner.pickerCode=request;
   } else if(args[0].equals("rebuild")){
    layout.rebuildAllFragmentViews(true,true);
    need(!button(owner).enabled,"rebuilt button lost busy state");
   }
   if(args[0].equals("open_fail"))ContentResolver.failOpen=true;
   if(args[0].equals("write_fail"))ContentResolver.failWrite=true;
   if(args[0].equals("close_fail"))ContentResolver.failClose=true;
   if(args[0].equals("invalid_uri")){
    owner.onActivityResult(owner.pickerCode,Activity.RESULT_OK,new Intent().setData(Uri.parse("https://not-contacted.invalid/private")));
    need(ContentResolver.opens==0&&name.equals(field(owner,"pendingDocument")),"remote destination accepted");return;
   }
   owner.onActivityResult(owner.pickerCode,Activity.RESULT_OK,new Intent().setData(Uri.parse("content://synthetic/document")));
   final BetaPreviewActivity current=owner;
   await(()->!(Boolean)field(current,"documentBusy"));
   need(source.isFile()&&Arrays.equals(bytes,Files.readAllBytes(source.toPath())),"source not preserved");
   need(ContentResolver.opens==1&&"wt".equals(ContentResolver.mode),"provider not explicit");
   if(args[0].endsWith("_fail")){
    need(name.equals(field(owner,"pendingDocument"))&&!button(owner).value.startsWith("Guardado"),"provider failure falsely claimed success");
   }else{
    need(field(owner,"pendingDocument")==null&&Arrays.equals(bytes,ContentResolver.saved),"successful copy differs from private source");
   }
   need(!button(owner).value.contains("SYNTHETIC_PRIVATE_VALUE"),"exception leaked");
  }finally{owner.onDestroy();}
 }
}
'''

class MobileDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory()
        cls.folder=Path(cls.temporary.name)
        cls.tools=Path(os.environ['JAVA_HOME'])/'bin'
        for name,content in STUBS.items():
            target=cls.folder/name
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(content)
        beta=cls.folder/'org/telegram/ui/beta'
        beta.mkdir(parents=True)
        for source in SOURCE.glob('*.java'):
            (beta/source.name).write_bytes(source.read_bytes())
        (beta/'MobileDocumentHarness.java').write_text(HARNESS)
        result=subprocess.run([str(cls.tools/'javac'),'--release','8','-d',str(cls.folder/'classes'),
                               *map(str,cls.folder.rglob('*.java'))],
                              capture_output=True,text=True,timeout=45)
        if result.returncode:
            raise AssertionError(result.stderr)
    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def run_case(self,mode,root=None):
        if root is None:
            with tempfile.TemporaryDirectory() as temporary:
                return self.run_case(mode,Path(temporary))
        result=subprocess.run([str(self.tools/'java'),'-cp',str(self.folder/'classes'),
                               'org.telegram.ui.beta.MobileDocumentHarness',mode,str(root)],
                              capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stderr,'')
        self.assertNotIn('SYNTHETIC_PRIVATE_VALUE',result.stdout)
        return result.stdout

    def test_zip_real_writer_is_compatible_with_existing_importer(self):
        sys.path.insert(0,str(ROOT/'tools/personal_beta'))
        import import_events
        analyzer,_=import_events.load_reviewed(Path(os.environ['FLEXYGRAM_DIAGNOSTICS_SOURCE']))
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            name=self.run_case('zip',root)
            archive=root/'beta-mobile-export'/name
            with zipfile.ZipFile(archive) as exported:
                self.assertIsNone(exported.testzip())
                self.assertEqual(len(exported.namelist()),5)
                self.assertEqual(set(json.loads(exported.read('diagnostic.json'))),
                                 {'schema','kind','probe','probe_outcome','runtime_certified'})
                destination=root/'extracted'
                exported.extractall(destination)
            batches=[p for p in destination.iterdir() if p.is_dir()]
            result=import_events.assemble(analyzer,batches)
            self.assertEqual(result['quality'],'COMPLETE_EVENT_SAMPLE_ONLY')
            self.assertEqual(result['interactions']['operations']['startup']['presented'],1)
            self.assertEqual(result['interactions']['operations']['chat_open']['presented'],1)
            self.assertEqual(result['interactions']['operations']['chat_close']['presented'],1)

    def test_cancel_preserves_private_archive_and_retry_does_not_redrain(self):self.run_case('cancel')
    def test_storage_open_error_retains_private_retry_without_exception_text(self):self.run_case('open_fail')
    def test_storage_write_error_retains_private_retry_without_exception_text(self):self.run_case('write_fail')
    def test_storage_close_error_is_not_reported_as_success(self):self.run_case('close_fail')
    def test_background_preparation_does_not_open_picker_after_leaving_settings(self):self.run_case('leave_settings')
    def test_picker_unavailable_is_safe_and_retryable(self):self.run_case('picker_fail')
    def test_recreated_activity_delivers_result_for_existing_snapshot(self):self.run_case('recreate')
    def test_settings_rebuild_keeps_pending_button_state(self):self.run_case('rebuild')
    def test_non_content_uri_is_rejected_without_opening_transport(self):self.run_case('invalid_uri')
    def test_success_preserves_private_sources_and_writes_exact_zip(self):self.run_case('save')
    def test_idle_does_no_export_io_or_provider_work(self):self.run_case('idle')
    def test_copy_io_failure_never_consumes_private_source(self):self.run_case('copy_fail')
    def test_private_unknown_header_never_reaches_archive(self):self.run_case('zip_header')
    def test_private_unknown_event_never_reaches_archive(self):self.run_case('zip_event')


if __name__=='__main__':unittest.main()
