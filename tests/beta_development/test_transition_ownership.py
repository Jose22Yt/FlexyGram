"""Execute the real Java method body with a synthetic scheduler, no Android or account."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java'


def method(text):
    start = text.index('public void resumeDelayedFragmentAnimation()')
    opening = text.index('{', start)
    depth = 1
    end = opening+1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


def execute(text):
    java = '''
import java.util.*;
class AndroidUtilities {
 static final Set<Runnable> queue = new HashSet<>();
 static void cancelRunOnUIThread(Runnable value) { queue.remove(value); }
}
public class Harness {
 boolean delayedAnimationResumed;
 Runnable delayedOpenAnimationRunnable, waitingForKeyboardCloseRunnable;
 METHOD
 static void require(boolean value, String why) { if (!value) throw new AssertionError(why); }
 public static void main(String[] args) {
  Harness h = new Harness();
  h.resumeDelayedFragmentAnimation();
  require(h.delayedAnimationResumed, "empty resume should be remembered");
  final Runnable replacement = () -> {};
  final Runnable previous = new Runnable() { public void run() {
   require(h.delayedOpenAnimationRunnable == this, "callback must retain ownership at entry");
   h.delayedOpenAnimationRunnable = null;
   // A synchronous fragment callback schedules another transition.
   h.delayedOpenAnimationRunnable = replacement;
   AndroidUtilities.queue.add(replacement);
  }};
  h.delayedOpenAnimationRunnable = previous;
  AndroidUtilities.queue.add(previous);
  h.resumeDelayedFragmentAnimation();
  require(!AndroidUtilities.queue.contains(previous), "old scheduled callback wasn't cancelled");
  require(h.delayedOpenAnimationRunnable == replacement, "replacement callback ownership lost");
  require(AndroidUtilities.queue.contains(replacement), "replacement unexpectedly cancelled");
  h.waitingForKeyboardCloseRunnable = () -> {};
  h.resumeDelayedFragmentAnimation();
  require(h.delayedOpenAnimationRunnable == replacement, "keyboard wait must retain pending callback");
  h.waitingForKeyboardCloseRunnable = null;
  h.delayedOpenAnimationRunnable = () -> {};
  h.resumeDelayedFragmentAnimation();
  require(h.delayedOpenAnimationRunnable == null, "completed callback leaked");
  System.out.println("PASS: reentrant replacement, scheduler, empty, keyboard wait and completion");
 }
}
'''.replace('METHOD', method(text))
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory);(path/'Harness.java').write_text(java)
        tools = Path(os.environ['JAVA_HOME'])/'bin'
        subprocess.run([str(tools/'javac'),str(path/'Harness.java')],check=True,capture_output=True,text=True)
        return subprocess.run([str(tools/'java'),'-cp',directory,'Harness'],capture_output=True,text=True)


class TransitionOwnershipTests(unittest.TestCase):
    def test_real_method_preserves_reentrant_work(self):
        result = execute(SOURCE.read_text())
        self.assertEqual(result.returncode,0,result.stderr)

    def test_historical_method_reproduces_lost_callback(self):
        old = subprocess.check_output(['git','show','19200e843cc9bf31c27a99e7b6775494627b131e:'+str(SOURCE.relative_to(ROOT))],cwd=ROOT,text=True)
        result = execute(old)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('replacement callback ownership lost',result.stderr)
