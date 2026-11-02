"""Current native-context controller model; host frame double, never device/FPS evidence."""
from pathlib import Path
import shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2]
class NativeContextPhysics(unittest.TestCase):
 def test_actual_springs_preserve_velocity_on_handoff_and_interrupted_close(self):
  with tempfile.TemporaryDirectory() as folder:
   folder=Path(folder)
   files={
    'android/os/SystemClock.java':'package android.os;public class SystemClock{public static double now=1;public static long uptimeMillis(){return (long)now;}}',
    'android/view/View.java':'''package android.view;public class View{static java.util.ArrayList<Runnable> queue=new java.util.ArrayList<>();public void removeCallbacks(Runnable r){queue.removeIf(v->v==r);}public void postOnAnimation(Runnable r){queue.add(r);}public void invalidate(){}public Object getParent(){return null;}public static void frame(){var pending=new java.util.ArrayList<>(queue);queue.clear();for(var r:pending)r.run();}}''',
    'android/view/Choreographer.java':'''package android.view;public class Choreographer{public interface FrameCallback{void doFrame(long t);}static Choreographer instance=new Choreographer();static java.util.ArrayList<FrameCallback> queue=new java.util.ArrayList<>();public static Choreographer getInstance(){return instance;}public void postFrameCallback(FrameCallback c){queue.add(c);}public void removeFrameCallback(FrameCallback c){queue.removeIf(v->v==c);}public static void frame(long t){var pending=new java.util.ArrayList<>(queue);queue.clear();for(var c:pending)c.doFrame(t);}}''',
    'app/flexygram/bubbles/interaction/BubbleInteractionSettings.java':'package app.flexygram.bubbles.interaction;public class BubbleInteractionSettings{public static boolean motionEnabled(){return true;}}'
   }
   for name in ['app/exteraless/player/Spring','app/flexygram/bubbles/interaction/BubbleTapMotion','app/flexygram/bubbles/interaction/SelectedBubbleMotion','app/flexygram/bubbles/interaction/DampedSpringCurve']:
    files[name+'.java']=(ROOT/'TMessagesProj/src/main/java'/str(name+'.java')).read_text()
   files['PhysicsProbe.java']=(ROOT/'tools/native_context/PhysicsProbe.java').read_text()
   for name,text in files.items():
    path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
   java=shutil.which('java');self.assertIsNotNone(java)
   compile=[shutil.which('javac')] if shutil.which('javac') else [java,'-m','jdk.compiler/com.sun.tools.javac.Main']
   result=subprocess.run(compile+['-d',str(folder),*[str(folder/name) for name in files]],capture_output=True,text=True)
   self.assertEqual(0,result.returncode,result.stderr)
   result=subprocess.run([java,'-cp',str(folder),'PhysicsProbe'],capture_output=True,text=True)
   self.assertEqual(0,result.returncode,result.stdout+result.stderr)
   print(result.stdout.strip())
if __name__=='__main__':unittest.main()
