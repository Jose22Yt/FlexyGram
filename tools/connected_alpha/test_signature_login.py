"""Native authentication preserved; no test account, phone, code or session in fixtures."""
import hashlib
from pathlib import Path
import re
import subprocess
import unittest
from xml.etree import ElementTree as ET
from login_parity import BASE,PATCH_PATHS,restore_login_presentation
from measure_login import stats,frame_times
ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'

class SignatureLoginTests(unittest.TestCase):
 def test_every_reviewed_presentation_file_restores_exact_original(self):
  for path in PATCH_PATHS:
   actual=(ROOT/path).read_bytes();before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
   self.assertEqual(restore_login_presentation(path,actual),before,path)
   mutated=actual.replace(b'public ',b'private ',1)
   try: result=restore_login_presentation(path,mutated)
   except ValueError:continue
   self.assertNotEqual(result,before,path)
 def test_native_auth_transport_and_consent_call_sites_preserved(self):
  path='TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java'
  before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
  after=(ROOT/path).read_text()
  # Normalize only the authorized UI title expression before comparing native storage/API call sites.
  after=after.replace("org.telegram.messenger.BuildConfig.CONNECTED_ALPHA ? R.string.FlexySignatureName : R.string.NagramX", "R.string.NagramX")
  # Protocol constructors, request flags, request submission, state storage and permission APIs.
  for pattern in (r'TLRPC\.TL_\w+',r'ConnectionsManager\.RequestFlag\w+',r'\.sendRequest\(',r'\.cancelRequest\(',r'\.requestPermissions\(',r'\.(?:put|get)(?:String|Int|Boolean|Long)\([^\n]+'):
   self.assertEqual(re.findall(pattern,before),re.findall(pattern,after),pattern)
  self.assertIn('private boolean syncContacts = false;',after)
  for text in ('syncContacts = savedInstanceState.getInt("syncContacts", 0) == 1;', 'syncContacts = !syncContacts;', 'UserConfig.getInstance(currentAccount).syncContacts = syncContacts;'):
   self.assertIn(text,after)
  self.assertEqual(re.findall(r'views\[[A-Z_]+\] = new [^;]+;',before),re.findall(r'views\[[A-Z_]+\] = new [^;]+;',after))
 def test_signature_welcome_returns_before_legacy_graphics_and_has_no_render_loop(self):
  source=(JAVA/'org/telegram/ui/IntroActivity.java').read_text()
  branch=source.index('if (isSignatureWelcome()) return createSignatureWelcome(context);')
  self.assertLess(branch,source.index('new TextureView'))
  view=(JAVA/'app/flexygram/login/SignatureWelcomeView.java').read_text()
  for expensive in ('TextureView','EGLThread','postInvalidate','ValueAnimator','Handler','Timer','postDelayed','onDraw('):self.assertNotIn(expensive,view)
  self.assertIn('new LoginActivity(), true',source)
  self.assertIn('ConnectionsManager.getInstance(currentAccount).updateDcSettings();',source)
  self.assertIn('new LanguageSelectActivity()',source)
 def test_actual_welcome_callbacks_block_repeated_and_cross_action_taps(self):
  source=(JAVA/'org/telegram/ui/IntroActivity.java').read_text()
  begin=source.index('        signatureWelcome = new app.flexygram.login.SignatureWelcomeView(')
  statement=source[begin:source.index('        fragmentView = signatureWelcome;',begin)]
  statement=statement.replace('app.flexygram.login.SignatureWelcomeView','FakeWelcome')
  fixture="""public class WelcomeGateProbe {
   static class Button {boolean enabled=true;void setEnabled(boolean v){enabled=v;}}
   static class LoginActivity {} static class LanguageSelectActivity {}
   static class FakeWelcome {Button startButton=new Button();Runnable start,language;FakeWelcome(int context,Runnable a,Runnable b){start=a;language=b;}}
   boolean startPressed,accept=true;int calls;FakeWelcome signatureWelcome;
   boolean presentFragment(Object value,boolean remove){calls++;return accept;}
   boolean presentFragment(Object value){return presentFragment(value,false);}
   void create(int context){_STATEMENT_}
   static void check(boolean value){if(!value)throw new AssertionError();}
   public static void main(String[] args){
    WelcomeGateProbe first=new WelcomeGateProbe();first.create(0);first.signatureWelcome.start.run();first.signatureWelcome.start.run();first.signatureWelcome.language.run();check(first.calls==1);check(!first.signatureWelcome.startButton.enabled);
    WelcomeGateProbe lang=new WelcomeGateProbe();lang.create(0);lang.signatureWelcome.language.run();lang.signatureWelcome.language.run();lang.signatureWelcome.start.run();check(lang.calls==1);
    WelcomeGateProbe failure=new WelcomeGateProbe();failure.accept=false;failure.create(0);failure.signatureWelcome.start.run();check(!failure.startPressed&&failure.signatureWelcome.startButton.enabled);failure.signatureWelcome.language.run();check(!failure.startPressed&&failure.calls==2);
   }
  }""".replace('_STATEMENT_',statement)
  import tempfile
  with tempfile.TemporaryDirectory() as temp:
   runner=Path(temp)/'WelcomeGateProbe.java';runner.write_text(fixture)
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',temp,str(runner)],check=True,capture_output=True)
   subprocess.run(['java','-cp',temp,'WelcomeGateProbe'],check=True,capture_output=True)
 def test_shared_icon_is_resolved_without_replacing_work1_artwork(self):
  identity=(JAVA/'app/flexygram/login/SignatureIdentity.java').read_text()
  self.assertIn('getIdentifier("ic_flexy_blue", "mipmap"',identity)
  self.assertNotIn('exteraless_icon',identity)
  self.assertIn('R.drawable.msg_send',identity)
  self.assertEqual(subprocess.check_output(['git','diff',BASE,'--','TMessagesProj/src/main/res/mipmap*','TMessagesProj/src/main/AndroidManifest.xml'],cwd=ROOT),b'')
 def test_candidate_scope_and_frozen_work1_files(self):
  from login_contract import PATHS
  changes=set(subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines())
  changes.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines())
  self.assertFalse(changes-PATHS,changes-PATHS)
  prefixes=['TMessagesProj/build.gradle','TMessagesProj/src/main/java/app/flexygram/composer','TMessagesProj/src/main/java/app/flexygram/home','TMessagesProj/src/main/java/app/flexygram/bubbles','TMessagesProj/src/main/java/app/flexygram/settings','TMessagesProj/src/main/java/app/exteraless/appicons','TMessagesProj/src/main/java/app/exteraless/settings','TMessagesProj/src/main/java/org/telegram/ui/ActionBar/MessageDrawable.java','TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java','TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java','TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java','TMessagesProj/jni','TMessagesProj/chaquopy','tools/alpha_local_installer']
  self.assertEqual(subprocess.check_output(['git','diff',BASE,'--',*prefixes],cwd=ROOT),b'')
 def test_variant_identity_override_preserves_internal_keys_and_legal_resources(self):
  root=ET.parse(ROOT/'TMessagesProj/src/connectedAlpha/res/values/flexygram_identity.xml').getroot()
  self.assertEqual({x.get('name'):x.text for x in root},{'NagramX':'FlexyGram'})
  for locale in ('values','values-es','values-ru'):
   path=f'TMessagesProj/src/main/res/{locale}/flexygram_settings_info.xml'
   self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT))
 def test_manual_upstream_updater_is_blocked_before_network_or_disk(self):
  s=(JAVA/'app/exteraless/updater/GitHubUpdater.java').read_text()
  fetch=s[s.index('public static void fetch('):s.index('public static long lastCheck(')]
  self.assertLess(fetch.index('if (BuildConfig.CONNECTED_ALPHA)'),fetch.index('new Thread'))
  download=s[s.index('public static void download('):]
  self.assertLess(download.index('if (BuildConfig.CONNECTED_ALPHA)'),download.index('new File'))
  sheet=(JAVA/'app/exteraless/updater/UpdaterSheet.java').read_text()
  self.assertIn('R.string.FlexyAlphaDeliveryInfo',sheet)
  self.assertIn('https://github.com/Jose22Yt/FlexyGram/actions',sheet)
 def test_metrics_nearest_rank_and_framestats_parser(self):
  self.assertEqual(stats(list(range(1,21))),{'samples':20,'median_ms':10.5,'p95_ms':19})
  self.assertIsNone(stats([])['p95_ms'])
  text='Flags,IntendedVsync,FrameCompleted,\n0,1000000,18000000,\n1,1000000,30000000,\n0,0,2,\n0,5,9223372036854775807,\n'
  self.assertEqual(frame_times(text),[17])
  s=(ROOT/'tools/connected_alpha/measure_login.py').read_text()
  for forbidden in ('pm clear','logcat','uiautomator','screencap','dumpheap'):self.assertNotIn(forbidden,s)
  self.assertIn("'performance_superiority':'NOT_ESTABLISHED'",s)

if __name__=='__main__':unittest.main()
