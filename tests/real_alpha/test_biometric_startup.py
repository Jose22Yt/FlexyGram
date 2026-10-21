"""Execute the real launch condition/controller methods with a permission-enforcing host double.
This reproduces the permission failure, not an Android device or Keystore implementation.
"""
from pathlib import Path
import hashlib,json,os,re,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2]
BASE='cce67ce7023e8231cd1c244c60f0305c455c160c'
LAUNCH='TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java'

def launch_block(source):
    end=source.index('            FingerprintController.checkKeyReady();')
    start=source.rfind('        if (Build.VERSION.SDK_INT',0,end)
    return source[start:source.index('\n        }',end)+10]

def controller_methods():
    source=(ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/FingerprintController.java').read_text()
    return source[source.index('    public static void checkKeyReady()'):source.index('    public static boolean isKeyReady()')]

class BiometricStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name)
        current=(ROOT/LAUNCH).read_text()
        baseline=subprocess.check_output(['git','show',BASE+':'+LAUNCH],cwd=ROOT,text=True)
        source='''public class BiometricStartupHarness {
 static class Build { static class VERSION { static int SDK_INT; } static class VERSION_CODES { static final int M=23; } }
 static class BuildConfig { static String FLEXYGRAM_VARIANT; static boolean ISOLATED_DIAGNOSTIC,FLEXYGRAM_CAP_AUTHENTICATION,FLEXYGRAM_CAP_TELEGRAMTRANSPORT; }
 static int biometricCalls,keyReads,generated; static boolean permission;
 static class ApplicationLoader { static Object applicationContext; }
 static class AndroidUtilities { static boolean isKeyguardSecure(){return true;} }
 static class Utilities { static Queue globalQueue=new Queue(); static class Queue { void postRunnable(Runnable r){r.run();} } }
 static class BiometricManager {
  static final int BIOMETRIC_SUCCESS=0; static class Authenticators { static final int BIOMETRIC_STRONG=15; }
  static BiometricManager from(Object o){return new BiometricManager();}
  int canAuthenticate(int mode){biometricCalls++;if(!permission)throw new SecurityException("SYNTHETIC_USE_BIOMETRIC_REQUIRED");return 0;}
 }
 static class FingerprintController {
  static boolean isKeyReady(){keyReads++;return false;}
  static void generateNewKey(boolean notify){generated++;}
'''+controller_methods()+'''
 }
 static void current(){
'''+launch_block(current)+'''
 }
 static void baseline(){
'''+launch_block(baseline)+'''
 }
 public static void main(String[] a){
  Build.VERSION.SDK_INT=Integer.parseInt(a[1]);BuildConfig.FLEXYGRAM_VARIANT=a[2];
  BuildConfig.ISOLATED_DIAGNOSTIC=Boolean.parseBoolean(a[3]);BuildConfig.FLEXYGRAM_CAP_AUTHENTICATION=Boolean.parseBoolean(a[4]);BuildConfig.FLEXYGRAM_CAP_TELEGRAMTRANSPORT=Boolean.parseBoolean(a[5]);permission=Boolean.parseBoolean(a[6]);
  boolean security=false;try{if(a[0].equals("baseline"))baseline();else current();}catch(SecurityException expected){security=true;}
  System.out.println(security+":"+biometricCalls+":"+keyReads+":"+generated);
 }
}'''
        p=cls.folder/'BiometricStartupHarness.java';p.write_text(source);cls.java=Path(os.environ['JAVA_HOME'])/'bin/java'
        subprocess.run([str(cls.java.with_name('javac')),'-d',str(cls.folder),str(p)],check=True,capture_output=True,text=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,mode='current',sdk=37,variant='realAlpha',isolated=True,auth=False,transport=False,permission=False):
        values=[mode,str(sdk),variant,*[str(x).lower() for x in [isolated,auth,transport,permission]]]
        return subprocess.check_output([str(self.java),'-cp',str(self.folder),'BiometricStartupHarness',*values],text=True).strip()
    def test_baseline_reproduces_permission_security_failure(self):
        for sdk in [24,32,37]:
            with self.subTest(sdk=sdk):self.assertEqual(self.run_case(mode='baseline',sdk=sdk),'true:1:1:0')
    def test_realalpha_offline_skips_entire_biometric_key_path(self):
        for sdk in [24,32,37]:
            with self.subTest(sdk=sdk):self.assertEqual(self.run_case(sdk=sdk),'false:0:0:0')
    def test_other_variants_preserve_the_original_call(self):
        for variant in ['diagnostic','betaDevelopment','production','unknown']:
            for sdk in [24,32,37]:
                with self.subTest(variant=variant,sdk=sdk):
                    self.assertEqual(self.run_case(variant=variant,sdk=sdk),'true:1:1:0')
                    self.assertEqual(self.run_case(variant=variant,sdk=sdk,permission=True),'false:1:1:1')
    def test_variant_name_alone_cannot_skip_an_open_policy(self):
        for flags in [dict(isolated=False),dict(auth=True),dict(transport=True)]:
            with self.subTest(flags=flags):self.assertEqual(self.run_case(**flags),'true:1:1:0')
    def test_pre23_original_sdk_gate_is_unchanged(self):
        for variant in ['realAlpha','production']:self.assertEqual(self.run_case(sdk=22,variant=variant),'false:0:0:0')
    def test_fault_line_maps_to_the_observed_instrumented_line(self):
        text=subprocess.check_output(['git','show',BASE+':'+LAUNCH],cwd=ROOT,text=True)
        lines=text.splitlines();self.assertEqual(lines[734].strip(),'FingerprintController.checkKeyReady();')
        config=json.loads(subprocess.check_output(['git','show',BASE+':tools/real_alpha/startup-overlays.json'],cwd=ROOT,text=True))
        row=next(x for x in config['files'] if x['source']==LAUNCH)
        shift=sum(len(h['replacement'])-(h['end']-h['start']) for h in row['hunks'] if h['start']<735)
        self.assertEqual(735+shift,737)
        controller=controller_methods();self.assertIn('BiometricManager.from(ApplicationLoader.applicationContext).canAuthenticate',controller)
    def test_manifests_and_fingerprint_controller_remain_identical(self):
        paths=['TMessagesProj/src/main/AndroidManifest.xml','TMessagesProj/src/realAlpha/AndroidManifest.xml','TMessagesProj/src/startupDiagnostic/AndroidManifest.xml','TMessagesProj/src/main/java/org/telegram/messenger/FingerprintController.java']
        for path in paths:
            with self.subTest(path=path):self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT))
