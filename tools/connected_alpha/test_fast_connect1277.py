"""Production launch/service/RPC guards, with no live account/network or latency claim."""
from pathlib import Path
import subprocess,tempfile,unittest
from test_startup import method
ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'
class FastConnect1277(unittest.TestCase):
 def java(self,source):
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'Probe.java';p.write_text(source)
   r=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(p)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run(['java','-cp',tmp,'Probe'],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);return r.stdout
 def test_actual_service_loop_preserves_contacts_media_billing_and_all_active_accounts(self):
  body=method((JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text(),'private static void initializeAccountServices()')
  out=self.java('''import java.util.*;class Probe{
  static List<Integer> contacts=new ArrayList<>(),downloads=new ArrayList<>();static int media,billing,sections;
  static class android{static class os{static class Trace{static void beginSection(String s){if(!s.equals("Flexy.startup.account_services"))throw new AssertionError();sections++;}static void endSection(){sections--;}}}}
  static class UserConfig{static final int MAX_ACCOUNT_COUNT=10;static int mask;int account;static UserConfig getInstance(int a){UserConfig u=new UserConfig();u.account=a;return u;}boolean isClientActivated(){return (mask&(1<<account))!=0;}}
  static class MediaController{static void getInstance(){media++;}}
  static class ContactsController{int account;static ContactsController getInstance(int a){ContactsController c=new ContactsController();c.account=a;return c;}void checkAppAccount(){contacts.add(account);}}
  static class DownloadController{static void getInstance(int a){downloads.add(a);}}
  static class BillingController{static BillingController getInstance(){return new BillingController();}void startConnection(){billing++;}}
  '''+body+'''public static void main(String[]args){for(int mask=0;mask<1024;mask++){UserConfig.mask=mask;contacts.clear();downloads.clear();media=billing=0;initializeAccountServices();if(sections!=0||media!=1||billing!=1||contacts.size()!=10||downloads.size()!=Integer.bitCount(mask))throw new AssertionError();for(int a=0;a<10;a++)if(contacts.get(a)!=a||downloads.contains(a)!=((mask&(1<<a))!=0))throw new AssertionError();}System.out.println("PASS 1024 account activation sets; all active sessions retain downloads; contacts/media/billing retained");}}''')
  self.assertIn('PASS 1024',out)
 def test_actual_rpc_prefix_rejects_empty_slots_without_setting_busy_or_refresh_timestamp(self):
  path='TMessagesProj/src/main/java/org/telegram/messenger/DownloadController.java';s=(ROOT/path).read_text();old=subprocess.check_output(['git','show','38e677d60847e117ede1c25731f7b6c4fd2970e2:'+path],cwd=ROOT,text=True)
  addition='''        // This RPC requires a session. An empty slot must not consume a request
        // or set the daily refresh timestamp before a user has authenticated.
        if (!getUserConfig().isClientActivated()) return;
'''
  self.assertEqual(s.replace(addition,'',1),old)
  body=method(s,'public void loadAutoDownloadConfig(boolean force)');prefix=body[:body.index('        TL_account.getAutoDownloadSettings req')]
  self.java('''class Probe{boolean loadingAutoDownloadConfig;int requests;static class Config{boolean active;long autoDownloadConfigLoadTime;boolean isClientActivated(){return active;}}Config config=new Config();Config getUserConfig(){return config;}
  '''+prefix+'''requests++;}
  public static void main(String[]args){for(boolean force:new boolean[]{false,true}){Probe p=new Probe();p.loadAutoDownloadConfig(force);if(p.requests!=0||p.loadingAutoDownloadConfig||p.config.autoDownloadConfigLoadTime!=0)throw new AssertionError();p.config.active=true;p.loadAutoDownloadConfig(force);if(p.requests!=1||!p.loadingAutoDownloadConfig)throw new AssertionError();p.loadAutoDownloadConfig(true);if(p.requests!=1)throw new AssertionError();}Probe p=new Probe();p.config.active=true;p.config.autoDownloadConfigLoadTime=System.currentTimeMillis();p.loadAutoDownloadConfig(false);if(p.requests!=0)throw new AssertionError();p.loadAutoDownloadConfig(true);if(p.requests!=1)throw new AssertionError();}}''')
 def test_native_lazy_accessor_and_protocol_sync_storage_are_unchanged(self):
  p='TMessagesProj/src/main/java/org/telegram/messenger/DownloadController.java';current=(ROOT/p).read_text();old=subprocess.check_output(['git','show','38e677d60847e117ede1c25731f7b6c4fd2970e2:'+p],cwd=ROOT,text=True)
  self.assertEqual(method(current,'public static DownloadController getInstance(int num)'),method(old,'public static DownloadController getInstance(int num)'))
  for suffix in ('org/telegram/messenger/MessagesController.java','org/telegram/messenger/MessagesStorage.java','org/telegram/tgnet/ConnectionsManager.java'):
   p='TMessagesProj/src/main/java/'+suffix
   self.assertEqual((ROOT/p).read_bytes(),subprocess.check_output(['git','show','38e677d60847e117ede1c25731f7b6c4fd2970e2:'+p],cwd=ROOT))

 def test_phase_queries_separate_local_work_from_visible_or_network_readiness(self):
  import sqlite3
  from performance.perfetto import plan
  spec=plan('test.app');sql=spec['startup_phases_sql'].split(';',1)[1]
  db=sqlite3.connect(':memory:')
  db.executescript("CREATE TABLE android_startups(startup_id,startup_type,ts,package);CREATE TABLE slice(track_id,name,ts,dur);CREATE TABLE thread_track(id,utid);CREATE TABLE thread(utid,upid);CREATE TABLE process(upid,name);INSERT INTO process VALUES(1,'test.app'),(2,'other.app');INSERT INTO thread VALUES(1,1),(2,2);INSERT INTO thread_track VALUES(1,1),(2,2);INSERT INTO android_startups VALUES(1,'cold',1000000,'test.app'),(2,'warm',50000000,'test.app');INSERT INTO slice VALUES(1,'Flexy.dialogs.read_local',6000000,14000000),(1,'Flexy.startup.account_services',51000000,2000000),(2,'Flexy.dialogs.read_local',6000000,9999999);")
  rows=db.execute(sql).fetchall();self.assertEqual(len(rows),2);self.assertEqual(rows[0][3:],(5.0,19.0,14.0));self.assertEqual(rows[1][0:3],(2,'warm','Flexy.startup.account_services'))
  self.assertIn('NOT_INFERRED',spec['limits']['local_rows_visible'])
  self.assertIn('REQUIRES_SUCCESSFUL',spec['limits']['useful_connection'])

 def test_new_comparison_requires_real_equivalent_conditions_and_pinned1276(self):
  import copy
  from test_performance import PerformanceLab
  from performance.compare import compare
  reports=copy.deepcopy(PerformanceLab().reports())
  for r,label,sha in zip(reports,('exteraless','alpha1276','candidate'),('1ad6a60a6834ffca722b1a22f4fba27ecb29a061','38e677d60847e117ede1c25731f7b6c4fd2970e2','a'*40)):
   r['label']=label;r['source_commit']=sha;r['environment'].update(build_mode='release',network_profile='same-test-wifi',sync_state='same-pending-updates')
  result=compare(reports,'stability1277');self.assertTrue(result['comparable']);self.assertEqual(result['superiority'],'NOT_AUTOMATICALLY_ESTABLISHED')
  for key in ('network_profile','sync_state','build_mode'):
   bad=copy.deepcopy(reports);bad[-1]['environment'][key]='unverified';self.assertFalse(compare(bad,'stability1277')['comparable'])
  bad=copy.deepcopy(reports);bad[1]['source_commit']='b'*40;self.assertFalse(compare(bad,'stability1277')['comparable'])
  bad=copy.deepcopy(reports);bad[-1]['evidence']='synthetic';self.assertFalse(compare(bad,'stability1277')['comparable'])
