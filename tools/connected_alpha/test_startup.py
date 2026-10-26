"""Execute production startup ordering/gates without accounts, native DB or a network.
Host evidence only: latency, first frame and Android performance require a real device.
"""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'

def method(source,signature):
 start=source.index(signature);opening=source.index('{',start);depth=1;i=opening+1
 while depth:
  if source[i]=='{':depth+=1
  elif source[i]=='}':depth-=1
  i+=1
 return source[start:i]

class Startup(unittest.TestCase):
 def test_real_account_order_keeps_zero_first_and_initializes_every_account_once(self):
  runner='''import app.flexygram.performance.StartupAccounts;class OrderProbe{public static void main(String[]args){int checks=0;for(int count=1;count<=100;count++)for(int selected=-1;selected<=count;selected++){boolean[] seen=new boolean[count];for(int i=0;i<count;i++){int account=StartupAccounts.accountAt(i,selected,count);if(account<0||account>=count||seen[account])throw new AssertionError();seen[account]=true;if(i==0&&account!=0)throw new AssertionError();if(i==1&&selected>0&&selected<count&&account!=selected)throw new AssertionError();checks++;}for(boolean b:seen)if(!b)throw new AssertionError();}System.out.println("PASS "+checks+" account order transitions; no Android latency claim");}}'''
  with tempfile.TemporaryDirectory()as tmp:
   f=Path(tmp)/'OrderProbe.java';f.write_text(runner)
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(JAVA/'app/flexygram/performance/StartupAccounts.java'),str(f)],check=True,capture_output=True)
   self.assertIn('PASS',subprocess.check_output(['java','-cp',tmp,'OrderProbe'],text=True))
 def test_actual_prepare_method_defers_to_ui_and_never_uses_another_accounts_cache(self):
  body=method((JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text(),'private static void prepareSelectedDialogs()')
  runner='''import java.util.*;class GateProbe{
 static List<String> calls=new ArrayList<>();static Runnable posted;
 static class android{static class os{static class Looper{static Object main=new Object(),current=main;static Object myLooper(){return current;}static Object getMainLooper(){return main;}}static class Trace{static void beginSection(String name){calls.add("begin");}static void endSection(){calls.add("end");}}}}
 static class AndroidUtilities{static void runOnUIThread(Runnable callback){posted=callback;}}
 static class ApplicationLoader{static void prepareSelectedDialogs(){GateProbe.prepareSelectedDialogs();}}
 static class UserConfig{static int selectedAccount=0;static final int MAX_ACCOUNT_COUNT=10;static UserConfig[] all=new UserConfig[10];boolean active;Object user;static UserConfig getInstance(int i){return all[i];}boolean isClientActivated(){return active;}Object getCurrentUser(){return user;}}
 static class MessagesController{static MessagesController[] all=new MessagesController[10];int account,reads;boolean dialogsLoaded,loading,reseting;List<Integer> dialogs=new ArrayList<>();static MessagesController getInstance(int account){calls.add("controller:"+account);return all[account];}List<Integer> getDialogs(int folder){if(folder!=0)throw new AssertionError();return dialogs;}void loadDialogs(int folder,int offset,int count,boolean cache){if(folder!=0||offset!=0||count!=100||!cache)throw new AssertionError();if(!loading&&!reseting){loading=true;reads++;calls.add("read:"+account);}}}
 static void yes(boolean value){if(!value)throw new AssertionError(calls.toString());}
 public static void main(String[]args){for(int i=0;i<10;i++){UserConfig.all[i]=new UserConfig();MessagesController.all[i]=new MessagesController();MessagesController.all[i].account=i;}
  for(int i=0;i<10;i++){calls.clear();UserConfig.selectedAccount=i;prepareSelectedDialogs();yes(calls.isEmpty());UserConfig.all[i].active=true;prepareSelectedDialogs();yes(calls.isEmpty());UserConfig.all[i].user=new Object();prepareSelectedDialogs();yes(MessagesController.all[i].reads==1);yes(!calls.contains("controller:"+((i+1)%10)));prepareSelectedDialogs();yes(MessagesController.all[i].reads==1);}
  for(int invalid:new int[]{-1,10,999}){calls.clear();UserConfig.selectedAccount=invalid;prepareSelectedDialogs();yes(calls.isEmpty());}
  UserConfig.selectedAccount=4;MessagesController selected=MessagesController.all[4];calls.clear();selected.dialogsLoaded=true;prepareSelectedDialogs();yes(!calls.contains("begin"));selected.dialogsLoaded=false;selected.dialogs.add(1);prepareSelectedDialogs();yes(!calls.contains("begin"));
  calls.clear();android.os.Looper.current=new Object();prepareSelectedDialogs();yes(posted!=null&&calls.isEmpty());android.os.Looper.current=android.os.Looper.main;UserConfig.selectedAccount=7;posted.run();yes(calls.contains("controller:7"));yes(!calls.contains("controller:4"));
  System.out.println("PASS real startup gate; authentication/loading/reset and account separation retained");
 }
''' +body+'}'
  with tempfile.TemporaryDirectory()as tmp:
   f=Path(tmp)/'GateProbe.java';f.write_text(runner)
   result=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(f)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertIn('PASS',subprocess.check_output(['java','-cp',tmp,'GateProbe'],text=True))
 def test_launch_opt_in_and_native_network_state_remain_honest(self):
  app=(JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text();launch=(JAVA/'org/telegram/ui/LaunchActivity.java').read_text()
  self.assertIn('ApplicationLoader.postInitApplication(true);',launch)
  self.assertIn('postInitApplication(false);',method(app,'public static void postInitApplication()'))
  self.assertLess(app.index('UserConfig.getInstance(0).loadConfig();'),app.index('final int startupAccount'))
  self.assertLess(app.index('if (prepareDialogs && a == startupAccount) prepareSelectedDialogs();'),app.index('PushListenerController.reconcilePushRegistration();'))
  state=method(launch,'private void updateCurrentConnectionState(int account)')
  original=subprocess.check_output(['git','show','175b299e0d4faeb246eca8e1be16a362a3a62213:TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java'],cwd=ROOT,text=True)
  self.assertEqual(state,method(original,'private void updateCurrentConnectionState(int account)'))
  native=(JAVA/'org/telegram/messenger/MessagesController.java').read_text()
  self.assertEqual(native,subprocess.check_output(['git','show','175b299e0d4faeb246eca8e1be16a362a3a62213:TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java'],cwd=ROOT,text=True))

 def test_exact_checkpoint_reverses_and_rejects_mutations(self):
  import json
  from startup_contract import restore,original,BASE
  spec=json.loads((ROOT/'tools/connected_alpha/startup_review.json').read_text())
  for path in spec['reviewed']:
   with self.subTest(path=path):
    data=(ROOT/path).read_bytes();before=original(BASE,path) or b''
    self.assertEqual(restore(path,data),before)
    self.assertEqual(restore(path,before),before)
    with self.assertRaises(ValueError):restore(path,data+b'\nUNREVIEWED\n')
 def test_native_sqlite_work_and_cursor_cleanup_are_unchanged_beneath_trace(self):
  source=(JAVA/'org/telegram/messenger/MessagesStorage.java').read_text()
  before=subprocess.check_output(['git','show','175b299e0d4faeb246eca8e1be16a362a3a62213:TMessagesProj/src/main/java/org/telegram/messenger/MessagesStorage.java'],cwd=ROOT,text=True)
  body=method(source,'public void getDialogs(int folderId, int offset, int count, boolean loadDraftsPeersAndFolders)')
  body=body.replace('            android.os.Trace.beginSection("Flexy.dialogs.read_local");\n','')
  body=body.replace('                try {\n                    if (cursor != null) cursor.dispose();\n                } finally {\n                    android.os.Trace.endSection();\n                }','                if (cursor != null) {\n                    cursor.dispose();\n                }')
  self.assertEqual(body,method(before,'public void getDialogs(int folderId, int offset, int count, boolean loadDraftsPeersAndFolders)'))
