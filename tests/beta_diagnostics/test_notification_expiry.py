"""Execute the actual Java expiry method with clock/queue doubles; no Android runtime."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
PATH='TMessagesProj/src/main/java/org/telegram/messenger/NotificationCenter.java'
BASE='19200e843cc9bf31c27a99e7b6775494627b131e'


def method(source):
    start=source.index('    private void checkForExpiredNotifications() {')
    end=source.index('\n    public void updateAllowedNotifications(',start)
    return source[start:end]


def harness(body):
    return '''import java.util.*;
public class ExpiryHarness {
    static final long EXPIRE_NOTIFICATIONS_TIME=5017;
    Runnable checkForExpiredNotifications;
    static class SystemClock { static long now; static long elapsedRealtime(){return now;} }
    static class AndroidUtilities {
        static Runnable pending; static long due;
        static void runOnUIThread(Runnable task,long delay){pending=task;due=SystemClock.now+delay;}
    }
    static class AllowedNotifications {long time; AllowedNotifications(long time){this.time=time;}}
    static class Table {
        TreeMap<Integer,AllowedNotifications> rows=new TreeMap<>();
        int size(){return rows.size();}
        int keyAt(int i){return new ArrayList<Integer>(rows.keySet()).get(i);}
        AllowedNotifications valueAt(int i){return rows.get(keyAt(i));}
    }
    Table allowedNotifications=new Table();
    int finished;
    void onAnimationFinish(int key){allowedNotifications.rows.remove(key);finished++;}
''' + body + '''
    public static void main(String[] args){
        ExpiryHarness owner=new ExpiryHarness();
        // Timer fires while a recently added animation is too young to expire.
        SystemClock.now=5000;
        owner.allowedNotifications.rows.put(1,new AllowedNotifications(0));
        owner.allowedNotifications.rows.put(2,new AllowedNotifications(4500));
        owner.checkForExpiredNotifications();
        if(owner.finished!=1 || owner.allowedNotifications.size()!=1) throw new AssertionError("initial expiry changed");
        Runnable callback=AndroidUtilities.pending;
        if(callback==null) throw new AssertionError("callback missing");
        if(args[0].equals("corrected") && owner.checkForExpiredNotifications!=callback) throw new AssertionError("callback not retained for cancellation");
        SystemClock.now=AndroidUtilities.due;
        callback.run();
        if(owner.allowedNotifications.size()!=0 || owner.finished!=2) throw new AssertionError("EXPIRY_CALLBACK_NOT_EXECUTED");
        if(owner.checkForExpiredNotifications!=null) throw new AssertionError("callback reference not cleared");
        System.out.println("SYNTHETIC_EXPIRY_PASS");
    }
}
'''


class NotificationExpiry(unittest.TestCase):
    def test_original_callback_bug_and_actual_corrected_method(self):
        original=subprocess.run(['git','show',BASE+':'+PATH],cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(original.returncode,0,'Full repository base object required')
        before,after=method(original.stdout),method((ROOT/PATH).read_text())
        old='() -> checkForExpiredNotifications = this::checkForExpiredNotifications'
        self.assertIn(old,before)
        self.assertEqual(after,before.replace(old,'checkForExpiredNotifications = this::checkForExpiredNotifications'))
        tools=Path(os.environ.get('JAVA_HOME','/usr'))/'bin'
        self.assertTrue((tools/'javac').is_file(),'JDK21 compiler required; test must not skip')
        for name,source in [('original',before),('corrected',after)]:
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);(root/'ExpiryHarness.java').write_text(harness(source))
                result=subprocess.run([str(tools/'javac'),str(root/'ExpiryHarness.java')],capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stderr)
                result=subprocess.run([str(tools/'java'),'-cp',str(root),'ExpiryHarness',name],capture_output=True,text=True,timeout=30)
                if name=='original':
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn('EXPIRY_CALLBACK_NOT_EXECUTED',result.stderr)
                else:
                    self.assertEqual(result.returncode,0,result.stderr)
                    self.assertIn('SYNTHETIC_EXPIRY_PASS',result.stdout)
