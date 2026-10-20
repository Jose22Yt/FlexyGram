"""Execute actual UI state codec and stage probe with synthetic platform/Chaquopy doubles."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from client_android_doubles import STUBS
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta'
HARNESS=r'''package org.telegram.ui.beta;
import android.os.Bundle;import android.content.Context;import org.telegram.messenger.NativeLoader;import com.chaquo.python.Python;
public class CodecProbeHarness {
 static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
 public static void main(String[]args){
  if(args[0].equals("state")){
   Bundle b=new Bundle();new BetaUiState(BetaUiState.Route.SETTINGS,true).save(b);
   BetaUiState restored=BetaUiState.restore(b,false);
   check(restored.route==BetaUiState.Route.SETTINGS&&restored.dark,"valid synthetic UI state lost");
   b.putString("flexygram.beta.ui.route","SYNTHETIC_PRIVATE_VALUE");restored=BetaUiState.restore(b,false);
   check(restored.route==BetaUiState.Route.HOME&&!restored.dark,"wrong type accepted");
   b.putInt("flexygram.beta.ui.route",99);check(BetaUiState.restore(b,true).route==BetaUiState.Route.HOME,"unknown route accepted");
   b.putInt("flexygram.beta.ui.version",2);check(BetaUiState.restore(b,true).dark,"unrecognized schema changed live theme");
   b.putString("token","SYNTHETIC_NOT_A_REAL_TOKEN");Bundle out=new Bundle();BetaUiState.restore(b,false).save(out);
   check(out.values.size()==3&&!out.values.containsKey("token"),"unknown input copied");
   check(new ProbeState().value()==ProbeState.Value.IDLE,"runtime success restored from UI state");
   Bundle broken=new Bundle(){@Override public Object get(String key){throw new IllegalArgumentException("SYNTHETIC_PRIVATE_VALUE");}};
   check(BetaUiState.restore(broken,true).route==BetaUiState.Route.HOME,"malformed saved state crashed restoration");
  }else{
   Context c=new Context();NativeLoader.ready=false;
   check(LocalPythonProbe.inspect(c)==ProbeState.Outcome.JNI_UNAVAILABLE,"JNI failure not classified");
   check(Python.entered.getCount()==1,"JNI failure still ran Python");
   NativeLoader.ready=true;Python.failStart=true;
   check(LocalPythonProbe.inspect(c)==ProbeState.Outcome.PYTHON_START_FAILED,"start failure not classified");
   Python.failStart=false;Python.failImport=true;
   check(LocalPythonProbe.inspect(c)==ProbeState.Outcome.PYTHON_IMPORT_FAILED,"import failure not classified");
   Python.failImport=false;Python.release.countDown();
   check(LocalPythonProbe.inspect(c)==ProbeState.Outcome.READY,"local runtime success lost");
   ProbeState owner=new ProbeState();owner.begin();owner.finish(ProbeState.Outcome.JNI_UNAVAILABLE);
   check(owner.value()==ProbeState.Value.FAILED&&owner.outcome()==ProbeState.Outcome.JNI_UNAVAILABLE,"stage state lost");
   owner.close();check(!owner.finish(ProbeState.Outcome.READY),"closed owner updated");
  }
 }
}'''
class UiStateProbeTests(unittest.TestCase):
 def run_case(self,name):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d)
   for path,source in STUBS.items():
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source)
   beta=root/'org/telegram/ui/beta';beta.mkdir(parents=True)
   for p in SOURCE.glob('*.java'):(beta/p.name).write_bytes(p.read_bytes())
   (beta/'CodecProbeHarness.java').write_text(HARNESS);tools=Path(os.environ['JAVA_HOME'])/'bin'
   p=subprocess.run([str(tools/'javac'),'-d',str(root/'classes'),*[str(p)for p in root.rglob('*.java')]],capture_output=True,text=True,timeout=30)
   self.assertEqual(p.returncode,0,p.stderr)
   p=subprocess.run([str(tools/'java'),'-cp',str(root/'classes'),'org.telegram.ui.beta.CodecProbeHarness',name],capture_output=True,text=True,timeout=15)
   self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stdout,'');self.assertEqual(p.stderr,'')
 def test_saved_state_is_primitive_allowlist_and_never_runtime_or_credentials(self):self.run_case('state')
 def test_jni_start_import_and_success_stages_without_private_error_output(self):self.run_case('probe')
