"""Host evidence for source selection, diagnostic identity, bounded journal and privacy.
No Android app, native loader or device gesture is executed by these tests.
"""
import hashlib,importlib.util,json,os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DIAG=ROOT/'TMessagesProj/src/startupDiagnostic/java'
spec=importlib.util.spec_from_file_location('prepare_startup',ROOT/'tools/real_alpha/prepare_startup_sources.py')
prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)
spec=importlib.util.spec_from_file_location('runtime_stubs',Path(__file__).with_name('test_runtime.py'))
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
HARNESS='''package org.telegram.ui.realalpha;
import java.io.*;
import org.telegram.messenger.*;
public class ProbeHostHarness {
 static void need(boolean value){if(!value)throw new AssertionError();}
 static void diagnostic(){BuildConfig.APPLICATION_ID="io.github.jose22yt.flexygram.realalpha.startupdiagnostic";BuildConfig.BUILD_TYPE="startupDiagnostic";}
 static class Accounts implements RealAlphaBootstrap.Accounts {
  public void initialize(){throw new IllegalStateException("SYNTHETIC_SECRET",new NullPointerException("phone=SYNTHETIC_SECRET"));}
  public int count(){return 3;} public int selected(){return 0;} public boolean containsIdentity(int n){return false;}
 }
 public static void main(String[] args)throws Exception {
  String mode=args[0];File folder=new File(args[1]);
  if(mode.equals("sanitizer")) {
   Throwable t=new IllegalStateException("SYNTHETIC_SECRET",new NullPointerException("SYNTHETIC_SECRET"));
   t.setStackTrace(new StackTraceElement[]{new StackTraceElement("org.telegram.ui.LaunchActivity","SYNTHETIC_SECRET","/private/SYNTHETIC_SECRET",123),new StackTraceElement("private.SYNTHETIC_SECRET","secret","secret",1)});
   String safe=StartupFailureSanitizer.encode(t);
   need(safe.contains("NULL_POINTER")&&safe.contains("LAUNCH:123")&&!safe.contains("SYNTHETIC_SECRET")&&!safe.contains("private"));
  } else if(mode.equals("linkage")) {
   String safe=StartupFailureSanitizer.encode(new UnsatisfiedLinkError("/private/SYNTHETIC_SECRET"));
   need(safe.contains("UNSATISFIED_LINK")&&!safe.contains("SYNTHETIC_SECRET"));
  } else if(mode.equals("causesBounded")) {
   Throwable a=new RuntimeException("secret"),b=new RuntimeException("secret",a);a.initCause(b);
   need(StartupFailureSanitizer.encode(a).split(";").length==6);
  } else if(mode.equals("noOpOriginal")) {
   StartupTrace.attach(new android.content.Context(folder));StartupTrace.begin(StartupTrace.Stage.APPLICATION_ATTACH);
   StartupTrace.failure(new RuntimeException("SYNTHETIC_SECRET"));need(folder.list().length==0);
  } else if(mode.equals("identity")) {
   diagnostic();RealAlphaPolicy.requireClosedBuild();need(StartupTrace.enabled());
   BuildConfig.BUILD_TYPE="debug";need(!StartupTrace.enabled());
   try{RealAlphaPolicy.requireClosedBuild();throw new AssertionError();}catch(IllegalStateException expected){}
  } else if(mode.equals("bootstrapEvidence")) {
   diagnostic();StartupTrace.attach(new android.content.Context(folder));
   try{new RealAlphaBootstrap().ensure(new Accounts());throw new AssertionError();}
   catch(IllegalStateException e){need(e.getCause()==null&&!e.toString().contains("SYNTHETIC_SECRET"));}
   String report=StartupTrace.read();need(report.contains("CAUSE=1:NULL_POINTER")&&!report.contains("SYNTHETIC_SECRET"));
  } else if(mode.equals("boundedJournal")) {
   diagnostic();StartupTrace.attach(new android.content.Context(folder));StartupTrace.begin(StartupTrace.Stage.APPLICATION_ATTACH);
   for(int i=0;i<2000;i++)StartupTrace.stage(StartupTrace.Stage.APP_NATIVE_BEGIN);
   need(StartupTrace.read().length()<=16384&&StartupTrace.read().endsWith("APP_NATIVE_BEGIN\\n"));
  } else if(mode.equals("journalUnavailable")) {
   diagnostic();StartupTrace.attach(new android.content.Context(null));
   StartupTrace.stage(StartupTrace.Stage.APPLICATION_ENTER);StartupTrace.failure(new RuntimeException("SYNTHETIC_SECRET"));
   need(StartupTrace.read().equals("NO_STAGE_RECORD"));
  } else if(mode.equals("rejectCorruptJournal")) {
   diagnostic();StartupTrace.attach(new android.content.Context(folder));
   try(FileOutputStream out=new FileOutputStream(new File(folder,"startup-sanitized-v1.txt"))){out.write("phone=SYNTHETIC_SECRET/123".getBytes());}
   need(StartupTrace.read().equals("INVALID_DIAGNOSTIC_CONTENT"));
  } else throw new AssertionError();
 }
}'''
class StartupDiagnosticsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.base=Path(cls.temp.name)
  cls.generated=cls.base/'generated';prepare.generate(cls.generated)
  files=[]
  for name,text in runtime.STUBS.items():
   if name=='org/telegram/messenger/BuildConfig.java':text=text.replace('public static int APP_ID=0;', 'public static String BUILD_TYPE="debug"; public static int APP_ID=0;')
   p=cls.base/'stubs'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);files.append(p)
  extras={'android/content/Context.java':'''package android.content; public class Context { private java.io.File folder; public Context(java.io.File f){folder=f;} public java.io.File getNoBackupFilesDir(){return folder;} }''',
  'android/util/AtomicFile.java':'''package android.util; public class AtomicFile {private java.io.File f; public AtomicFile(java.io.File value){f=value;} public java.io.File getBaseFile(){return f;} public byte[] readFully()throws java.io.IOException{return java.nio.file.Files.readAllBytes(f.toPath());} public java.io.FileOutputStream startWrite()throws java.io.IOException{return new java.io.FileOutputStream(f);} public void finishWrite(java.io.FileOutputStream s)throws java.io.IOException{s.close();} public void failWrite(java.io.FileOutputStream s){try{s.close();}catch(Exception ignored){}} }''',
  'org/telegram/ui/realalpha/ProbeHostHarness.java':HARNESS}
  for name,text in extras.items():
   p=cls.base/'stubs'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);files.append(p)
  files+=list((cls.generated/'org/telegram/ui/realalpha').glob('*.java'))
  files+=[ROOT/'TMessagesProj/src/main/java/org/telegram/messenger'/n for n in ['BuildVariantPolicy.java','DiagnosticPolicy.java']]
  files+=list((DIAG/'org/telegram/messenger').glob('*.java'))
  cls.jdk=Path(os.environ['JAVA_HOME']);cls.classes=cls.base/'classes'
  p=subprocess.run([str(cls.jdk/'bin/javac'),'--release','8','-d',str(cls.classes),*map(str,files)],capture_output=True,text=True)
  if p.returncode:raise RuntimeError(p.stderr)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def run_case(self,name):
  with tempfile.TemporaryDirectory()as d:
   p=subprocess.run([str(self.jdk/'bin/java'),'-cp',str(self.classes),'org.telegram.ui.realalpha.ProbeHostHarness',name,d],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stdout+p.stderr)
 def test_exact_overlay_leaves_shared_sources_untouched(self):
  config=json.loads((ROOT/'tools/real_alpha/startup-overlays.json').read_text())
  for row in config['files']:
   self.assertEqual(hashlib.sha256((ROOT/row['source']).read_bytes()).hexdigest(),row['source_sha256'])
   p=self.generated/row['source'].split('/java/',1)[1]
   self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['output_sha256'])
 def test_overlay_rejects_modified_baseline(self):
  from unittest.mock import patch
  config=json.loads((ROOT/'tools/real_alpha/startup-overlays.json').read_text())
  with tempfile.TemporaryDirectory() as d:
   fake=Path(d);first=config['files'][0]
   manifest=fake/'tools/real_alpha/startup-overlays.json';manifest.parent.mkdir(parents=True);manifest.write_text(json.dumps(config))
   source=fake/first['source'];source.parent.mkdir(parents=True);source.write_text('mutated baseline')
   with patch.object(prepare,'ROOT',fake),self.assertRaises(ValueError):prepare.generate(fake/'output')
   self.assertEqual(source.read_text(),'mutated baseline')
 def test_manifest_separates_reporter_and_probe(self):
  import xml.etree.ElementTree as ET
  a='{http://schemas.android.com/apk/res/android}';root=ET.parse(ROOT/'TMessagesProj/src/startupDiagnostic/AndroidManifest.xml').getroot()
  activities=root.find('application').findall('activity')
  probe=next(n for n in activities if n.get(a+'name').endswith('RealAlphaActivity'))
  self.assertEqual(probe.get(a+'exported'),'false');self.assertEqual(probe.get(a+'process'),':startup_probe')
  self.assertFalse(probe.findall('intent-filter'))
  source=(DIAG/'org/telegram/ui/realalpha/diagnostics/StartupReportActivity.java').read_text()
  self.assertIn('getHistoricalProcessExitReasons(getPackageName(),0,8)',source)
  for forbidden in ['getTraceInputStream','getDescription','ACTION_SEND','CrashLog.take','getSuppressed']:
   self.assertNotIn(forbidden,source)
for case in ['sanitizer','linkage','causesBounded','noOpOriginal','identity','bootstrapEvidence','boundedJournal','rejectCorruptJournal','journalUnavailable']:
 setattr(StartupDiagnosticsTests,'test_'+case,lambda self,c=case:self.run_case(c))
