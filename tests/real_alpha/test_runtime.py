"""Execute actual realAlpha Java wrappers with explicit Android/controller doubles.
No native LaunchActivity rendering, JNI, Android runtime, account or network is executed.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'TMessagesProj/src/realAlpha/java/org/telegram/ui/realalpha'
STUBS = {
'android/annotation/TargetApi.java': 'package android.annotation; public @interface TargetApi { int value(); }',
'android/os/Build.java': 'package android.os; public class Build { public static class VERSION { public static int SDK_INT=37; }}',
'android/os/Bundle.java': 'package android.os; public class Bundle {}',
'android/content/Intent.java': '''package android.content; public class Intent { public static final String ACTION_MAIN="main"; public String action; public Intent(Object c,Class<?> type){} public Intent setAction(String v){action=v;return this;} }''',
'android/window/OnBackInvokedCallback.java': 'package android.window; public interface OnBackInvokedCallback { void onBackInvoked(); }',
'android/window/OnBackInvokedDispatcher.java': '''package android.window; public class OnBackInvokedDispatcher { public static int PRIORITY_DEFAULT=0; public OnBackInvokedCallback callback; public void registerOnBackInvokedCallback(int p,OnBackInvokedCallback c){callback=c;} public void unregisterOnBackInvokedCallback(OnBackInvokedCallback c){if(callback==c)callback=null;} }''',
'android/app/Activity.java': '''package android.app; public class Activity { public final android.window.OnBackInvokedDispatcher dispatcher=new android.window.OnBackInvokedDispatcher(); public android.window.OnBackInvokedDispatcher getOnBackInvokedDispatcher(){return dispatcher;} }''',
'org/telegram/messenger/BuildConfig.java': '''package org.telegram.messenger; public class BuildConfig { public static String APPLICATION_ID="io.github.jose22yt.flexygram.realalpha",FLEXYGRAM_VARIANT="realAlpha",FLEXYGRAM_POLICY_SCOPE="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:realAlpha",APP_HASH=""; public static int APP_ID=0; public static boolean ISOLATED_DIAGNOSTIC=true; public static boolean FLEXYGRAM_CAP_AUTHENTICATION,FLEXYGRAM_CAP_TELEGRAMTRANSPORT,FLEXYGRAM_CAP_PUSH,FLEXYGRAM_CAP_TRANSLATION,FLEXYGRAM_CAP_PLUGINS,FLEXYGRAM_CAP_SESSIONRESTORE; }''',
'org/telegram/messenger/ApplicationLoader.java': '''package org.telegram.messenger; public class ApplicationLoader { public static int initializations; public static void postInitApplication(){initializations++;} }''',
 'org/telegram/messenger/NativeLoader.java': 'package org.telegram.messenger; public class NativeLoader { public static boolean available=true;public static boolean loaded(){return available;} }',
 'org/telegram/messenger/AccountInstance.java': 'package org.telegram.messenger; public class AccountInstance { public static boolean available=true; public static AccountInstance getInstance(int n){return new AccountInstance();} public Object getMessagesController(){return available?new Object():null;} public Object getMessagesStorage(){return available?new Object():null;} public Object getConnectionsManager(){return available?new Object():null;} }',
'org/telegram/messenger/UserConfig.java': '''package org.telegram.messenger; public class UserConfig { public static int MAX_ACCOUNT_COUNT=3,selectedAccount=0; private static final UserConfig[] slots={new UserConfig(),new UserConfig(),new UserConfig()}; public long id,clientUserId; public Object user; public boolean active; public static UserConfig getInstance(int n){return slots[n];} public boolean isClientActivated(){return active;} public Object getCurrentUser(){return user;} public long getClientUserId(){return user!=null?id:0;} }''',
'org/telegram/ui/ActionBar/BaseFragment.java': 'package org.telegram.ui.ActionBar; public class BaseFragment {}',
'org/telegram/ui/ActionBar/INavigationLayout.java': '''package org.telegram.ui.ActionBar; public interface INavigationLayout { class NavigationParams { public BaseFragment fragment; public NavigationParams(BaseFragment f){fragment=f;} } }''',
'org/telegram/ui/DialogsActivity.java': 'package org.telegram.ui; public class DialogsActivity extends org.telegram.ui.ActionBar.BaseFragment { public DialogsActivity(android.os.Bundle b){} }',
'org/telegram/ui/ChatActivity.java': 'package org.telegram.ui; public class ChatActivity extends org.telegram.ui.ActionBar.BaseFragment {}',
'org/telegram/ui/LoginActivity.java': 'package org.telegram.ui; public class LoginActivity extends org.telegram.ui.ActionBar.BaseFragment {}',
'org/telegram/ui/SessionsActivity.java': 'package org.telegram.ui; public class SessionsActivity extends org.telegram.ui.ActionBar.BaseFragment {}',
'org/telegram/ui/LaunchActivity.java': '''package org.telegram.ui;
 public class LaunchActivity extends android.app.Activity {
 public android.content.Intent intent; public android.os.Bundle restored; public int backCalls,newIntents,created,destroyed,cancelled,external; public static final int RESULT_CANCELED=0;
 public void onActivityResult(int request,int result,android.content.Intent data){if(result==RESULT_CANCELED)cancelled++;}
 public void startActivityForResult(android.content.Intent i,int r,android.os.Bundle b){external++;}
 public void startActivities(android.content.Intent[] i,android.os.Bundle b){external++;}
 public void setIntent(android.content.Intent i){intent=i;}
 protected void onCreate(android.os.Bundle b){created++;restored=b;}
 protected org.telegram.ui.ActionBar.BaseFragment getClientNotActivatedFragment(){return new LoginActivity();}
 public boolean needPresentFragment(org.telegram.ui.ActionBar.INavigationLayout l,org.telegram.ui.ActionBar.INavigationLayout.NavigationParams p){return true;}
 public boolean needAddFragmentToStack(org.telegram.ui.ActionBar.BaseFragment f,org.telegram.ui.ActionBar.INavigationLayout l){return true;}
 public void onNewIntent(android.content.Intent i){newIntents++;}
 public void onBackPressed(){backCalls++;}
 protected void onDestroy(){destroyed++;}
 }''',
}
HARNESS = r'''package org.telegram.ui.realalpha;
import org.telegram.messenger.*;
import org.telegram.ui.*;
import org.telegram.ui.ActionBar.*;
public class RuntimeHarness {
 static void need(boolean v){if(!v)throw new AssertionError();}
 static void denied(Runnable r){try{r.run();}catch(IllegalStateException e){need(!e.toString().contains("SYNTHETIC_SECRET"));need(e.getCause()==null);return;}throw new AssertionError("not denied");}
 static class Accounts implements RealAlphaBootstrap.Accounts {
   int runs; boolean identity; int selected=0; int count=3; Runnable during=()->{};
   public void initialize(){runs++;during.run();}
   public int count(){return count;} public int selected(){return selected;}
   public boolean containsIdentity(int n){return n==2&&identity;}
 }
 public static void main(String[] argv)throws Exception {
 String test=argv[0]; Accounts a=new Accounts(); RealAlphaBootstrap b=new RealAlphaBootstrap();
 switch(test){
 case "closed": RealAlphaPolicy.requireClosedBuild();break;
 case "identity": BuildConfig.APPLICATION_ID="io.github.jose22yt.flexygram.beta.development";denied(RealAlphaPolicy::requireClosedBuild);break;
 case "variant": BuildConfig.FLEXYGRAM_VARIANT="diagnostic";denied(RealAlphaPolicy::requireClosedBuild);break;
 case "scope": BuildConfig.FLEXYGRAM_POLICY_SCOPE="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:betaDevelopment";denied(RealAlphaPolicy::requireClosedBuild);break;
 case "apiId": BuildConfig.APP_ID=6;denied(RealAlphaPolicy::requireClosedBuild);break;
 case "apiHash": BuildConfig.APP_HASH="SYNTHETIC_SECRET";denied(RealAlphaPolicy::requireClosedBuild);break;
 case "isolation": BuildConfig.ISOLATED_DIAGNOSTIC=false;denied(RealAlphaPolicy::requireClosedBuild);break;
 case "capabilities":
  for(String name:new String[]{"AUTHENTICATION","TELEGRAMTRANSPORT","PUSH","TRANSLATION","PLUGINS","SESSIONRESTORE"}){
   java.lang.reflect.Field field=BuildConfig.class.getField("FLEXYGRAM_CAP_"+name);
   field.setBoolean(null,true);denied(RealAlphaPolicy::requireClosedBuild);field.setBoolean(null,false);
  } break;
 case "initializeOnce": b.ensure(a);b.ensure(a);need(a.runs==1);break;
 case "priorIdentity": a.identity=true;denied(()->b.ensure(a));need(a.runs==0);break;
 case "identityAfterInit": a.during=()->a.identity=true;denied(()->b.ensure(a));a.identity=false;denied(()->b.ensure(a));need(a.runs==1);break;
 case "reentry": a.during=()->b.ensure(a);denied(()->b.ensure(a));denied(()->b.ensure(a));need(a.runs==1);break;
 case "failure": a.during=()->{throw new IllegalStateException("SYNTHETIC_SECRET");};denied(()->b.ensure(a));denied(()->b.ensure(a));need(a.runs==1);break;
 case "linkage": a.during=()->{throw new UnsatisfiedLinkError("SYNTHETIC_SECRET");};denied(()->b.ensure(a));denied(()->b.ensure(a));break;
 case "invalidSlot": a.selected=-1;denied(()->b.ensure(a));need(a.runs==0);break;
 case "emptySlots": a.count=0;denied(()->b.ensure(a));need(a.runs==0);break;
 case "readyContamination": b.ensure(a);a.identity=true;denied(()->b.ensure(a));break;
 case "staleIdentity": UserConfig.getInstance(2).clientUserId=123;denied(()->new RealAlphaActivity().onCreate(null));break;
 case "missingJNI": NativeLoader.available=false;denied(()->new RealAlphaActivity().onCreate(null));break;
 case "missingControllers": AccountInstance.available=false;denied(()->new RealAlphaActivity().onCreate(null));break;
 case "externalIntents": {RealAlphaActivity owner=new RealAlphaActivity();owner.startActivityForResult(null,12,null);owner.startActivities(new android.content.Intent[0],null);need(owner.external==0&&owner.cancelled==1);break;}
 case "nativeRoot": {RealAlphaActivity owner=new RealAlphaActivity();owner.onCreate(new android.os.Bundle());need(owner.getClientNotActivatedFragment().getClass()==DialogsActivity.class);need(owner.created==1&&owner.restored==null);need(android.content.Intent.ACTION_MAIN.equals(owner.intent.action));break;}
 case "routeDeny": {RealAlphaActivity owner=new RealAlphaActivity(); for(BaseFragment f:new BaseFragment[]{new ChatActivity(),new LoginActivity(),new SessionsActivity(),null}){
 need(!owner.needPresentFragment(null,new INavigationLayout.NavigationParams(f)));need(!owner.needAddFragmentToStack(f,null));}need(owner.needPresentFragment(null,new INavigationLayout.NavigationParams(new DialogsActivity(null))));break;}
 case "intents": {RealAlphaActivity owner=new RealAlphaActivity();owner.onNewIntent(null);need(owner.newIntents==0);break;}
 case "back": {RealAlphaActivity owner=new RealAlphaActivity();owner.onCreate(null);owner.dispatcher.callback.onBackInvoked();need(owner.backCalls==1);owner.onDestroy();need(owner.dispatcher.callback==null&&owner.destroyed==1);break;}
 case "legacyBack": {android.os.Build.VERSION.SDK_INT=24;RealAlphaActivity owner=new RealAlphaActivity();owner.onCreate(null);need(owner.dispatcher.callback==null);owner.onBackPressed();need(owner.backCalls==1);owner.onDestroy();break;}
 case "recreation": {RealAlphaActivity owner=new RealAlphaActivity();owner.onCreate(null);owner.onDestroy();RealAlphaActivity next=new RealAlphaActivity();next.onCreate(new android.os.Bundle());need(ApplicationLoader.initializations==1&&next.created==1&&next.restored==null);next.onDestroy();break;}
 default:throw new AssertionError("unknown test");
 }
 System.out.println("PASS "+test+" HOST_DOUBLES_ONLY");
 }
}'''

class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        home=Path(os.environ['JAVA_HOME'])
        cls.temp=tempfile.TemporaryDirectory(); cls.folder=Path(cls.temp.name)
        for name,content in STUBS.items():
            p=cls.folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
        p=cls.folder/'org/telegram/ui/realalpha/RuntimeHarness.java';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(HARNESS)
        files=list(cls.folder.rglob('*.java'))+list(SRC.glob('*.java'))
        files += [ROOT/'TMessagesProj/src/main/java/org/telegram/messenger'/f for f in ['BuildVariantPolicy.java','DiagnosticPolicy.java']]
        cls.classes=cls.folder/'classes';cls.java=home/'bin/java'
        result=subprocess.run([str(home/'bin/javac'),'--release','8','-d',str(cls.classes),*map(str,files)],capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stderr)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,case):
        p=subprocess.run([str(self.java),'-cp',str(self.classes),'org.telegram.ui.realalpha.RuntimeHarness',case],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn('HOST_DOUBLES_ONLY',p.stdout)

for _case in ['closed','identity','variant','scope','apiId','apiHash','isolation','capabilities','initializeOnce','priorIdentity','identityAfterInit','reentry','failure','linkage','invalidSlot','emptySlots','readyContamination','nativeRoot','routeDeny','intents','back','legacyBack','recreation','missingJNI','missingControllers','externalIntents','staleIdentity']:
    setattr(RuntimeTests,'test_'+_case,lambda self,c=_case:self.run_case(c))
