"""Pending host regressions for process-local beta post-init, never Android certification."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from client_android_doubles import STUBS

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta'
BASE = '78151d9e8083290dca2617279cab3afb53540de6'
LOADER = r'''package org.telegram.messenger;
public class ApplicationLoader {
 public static boolean initialized;
 public static int calls;
 public static String failureKind="runtime";
 public static void postInitApplication(){
  calls++;
  if(initialized)return;
  initialized=true; // Match the real early flag before the injected failure.
  if(failureKind.equals("runtime"))throw new IllegalStateException("SYNTHETIC_PRIVATE_VALUE");
  if(failureKind.equals("linkage"))throw new UnsatisfiedLinkError("SYNTHETIC_PRIVATE_VALUE");
 }
}'''
HARNESS = r'''package org.telegram.ui.beta;
import android.os.Build;
import android.widget.TextView;
import org.telegram.ui.ActionBar.ActionBarLayout;
import org.telegram.messenger.ApplicationLoader;
public class PostInitHarness {
 static void need(boolean value,String message){if(!value)throw new AssertionError(message);}
 static ActionBarLayout layout(BetaPreviewActivity owner)throws Exception{
  java.lang.reflect.Field field=BetaPreviewActivity.class.getDeclaredField("navigation");
  field.setAccessible(true);return (ActionBarLayout)field.get(owner);
 }
 static boolean blocked(BetaPreviewActivity owner){
  return owner.content instanceof TextView
      && ((TextView)owner.content).text.equals("FlexyGram offline startup stopped: POST_INIT_FAILED");
 }
 public static void main(String[]args)throws Exception{
  if(args[0].equals("ready")){
   int[] runs={0};
   need(BetaPostInit.ensure(()->runs[0]++),"first complete init rejected");
   need(BetaPostInit.ensure(()->{throw new AssertionError("successful init repeated");}),
       "completed state not retained");
   need(runs[0]==1,"successful initialization not exactly once");return;
  }
  if(args[0].equals("reentry")){
   int[] runs={0};
   need(BetaPostInit.ensure(()->{
    runs[0]++;
    need(!BetaPostInit.ensure(()->runs[0]++),"recursive partial init accepted");
   }),"outer init did not complete");
   need(runs[0]==1,"recursive initializer executed");return;
  }
  if(args[0].equals("fatal")){
   Error expected=new AssertionError("synthetic fatal");
   try{BetaPostInit.ensure(()->{throw expected;});throw new AssertionError("fatal swallowed");}
   catch(Error actual){need(actual==expected,"fatal changed");}
   need(!BetaPostInit.ensure(()->{throw new AssertionError("fatal process retried");}),
       "fatal left retryable partial state");return;
  }
  Build.VERSION.SDK_INT=36;
  ApplicationLoader.failureKind=args[0];
  BetaPreviewActivity first=new BetaPreviewActivity();
  try{
   first.onCreate(null);
   need(blocked(first)&&layout(first)==null,"first failure built client UI");
   need(ApplicationLoader.initialized,"fixture did not set early global flag");
  }finally{first.onDestroy();}
  BetaPreviewActivity second=new BetaPreviewActivity();
  try{
   second.onCreate(new android.os.Bundle());
   need(blocked(second)&&layout(second)==null,"POST_INIT_REENTRY_BUILT_PARTIAL_UI");
   need(ApplicationLoader.calls==1,"failed global init was retried");
   second.dispatcher.dispatch();
   need(second.isFinishing(),"failed startup cannot exit using modern Back");
   need(!((TextView)second.content).text.contains("SYNTHETIC_PRIVATE_VALUE"),"private failure leaked");
  }finally{second.onDestroy();}
 }
}'''

class PostInitReentryTests(unittest.TestCase):
    def run_case(self, name, original=False):
        tools = Path(os.environ['JAVA_HOME']) / 'bin'
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for path, content in STUBS.items():
                target = folder / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            (folder / 'org/telegram/messenger/ApplicationLoader.java').write_text(LOADER)
            target = folder / 'org/telegram/ui/beta'
            target.mkdir(parents=True)
            for source in SOURCE.glob('*.java'):
                (target / source.name).write_bytes(source.read_bytes())
            if original:
                old = subprocess.check_output(['git', 'show', BASE + ':' +
                    str((SOURCE / 'BetaPreviewActivity.java').relative_to(ROOT))], cwd=ROOT, text=True)
                (target / 'BetaPreviewActivity.java').write_text(old)
            (target / 'PostInitHarness.java').write_text(HARNESS)
            completed = subprocess.run([str(tools / 'javac'), '-d', str(folder / 'classes'),
                *map(str, folder.rglob('*.java'))], capture_output=True, text=True, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            completed = subprocess.run([str(tools / 'java'), '-cp', str(folder / 'classes'),
                'org.telegram.ui.beta.PostInitHarness', name],
                capture_output=True, text=True, timeout=15)
            if original:
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn('POST_INIT_REENTRY_BUILT_PARTIAL_UI', completed.stderr)
            else:
                self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertNotIn('SYNTHETIC_PRIVATE_VALUE', completed.stdout + completed.stderr)

    def test_runtime_failure_blocks_second_activity_in_same_process(self):
        self.run_case('runtime', original=True)
        self.run_case('runtime')

    def test_linkage_failure_blocks_second_activity_in_same_process(self):
        self.run_case('linkage', original=True)
        self.run_case('linkage')

    def test_success_is_reused_without_repeating_global_initialization(self):
        self.run_case('ready')

    def test_recursive_entry_cannot_build_on_partial_initialization(self):
        self.run_case('reentry')

    def test_unhandled_fatal_propagates_but_remains_fail_closed(self):
        self.run_case('fatal')


if __name__ == '__main__':
    unittest.main()
