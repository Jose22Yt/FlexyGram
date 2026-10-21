package org.telegram.ui.realalpha.local;
import java.util.*;
import java.util.concurrent.Executor;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.session.AuthenticationController.State;
import io.github.jose22yt.flexygram.login.local.EphemeralPages.*;

import android.os.Handler;
import org.telegram.ui.*;
import org.telegram.ui.realalpha.*;
import org.telegram.ui.ActionBar.*;
public class IntegrationHarness {
 static ClosedRuntime runtime(int slot){String digest=org.telegram.messenger.BuildConfig.FLEXYGRAM_POLICY_SCOPE;return ClosedRuntime.verify(SessionScope.of("realAlpha","io.github.jose22yt.flexygram.realalpha",slot),digest,true,new boolean[6],0,new char[0],"FLEXYGRAM_POLICY:"+digest+":auth=0:transport=0:push=0:translation=0:plugins=0:restore=0");}
 static void yes(boolean b){if(!b)throw new IllegalStateException("LOCAL_INTEGRATION_CONTRACT");}
 static class Worker implements Executor {Deque<Runnable> tasks=new ArrayDeque<>();public void execute(Runnable r){tasks.add(r);}void flush(){int n=0;while(!tasks.isEmpty()){yes(++n<1000);tasks.remove().run();}}}
 static class F {
  Worker w=new Worker();LocalLoginRehearsal flow;View view;
  F(LocalLoginRehearsal.Scenario scenario){flow=new LocalLoginRehearsal(runtime(0),scenario,w,()->1000);yes(flow.initialize());w.flush();yes(flow.owner.snapshot().state==State.READY);view=flow.pages.attach(0,Runnable::run,s->{});}
  void phone(){yes(flow.pages.phone(view,"0000000".toCharArray()));w.flush();}
  void code(){yes(flow.pages.code(view,"000000".toCharArray()));w.flush();}
 }
 static RealAlphaLocalLoginHost host;
 static DialogsActivity root;
 static RealAlphaActivity activity;
 static void setup(String path){activity=new RealAlphaActivity(new java.io.File(path));org.telegram.messenger.ApplicationLoader.applicationContext=activity;root=new DialogsActivity();LaunchActivity.last=root;host=new RealAlphaLocalLoginHost(activity);host.attachEntry();}
 static void choose(int n){root.getActionBar().createMenu().getItem(904301).click();yes(AlertDialog.choice!=null);AlertDialog.choice.onClick(null,n);}
 static void pump(){Handler.drain(false);Handler.drain(true);}
 public static void main(String[] args)throws Exception {
  if(args.length>2&&!args[0].equals("hostJniUnavailable"))System.load(args[2]);
  switch(args[0]){
   case "sms":case "app":{F f=new F(args[0].equals("sms")?LocalLoginRehearsal.Scenario.SMS:LocalLoginRehearsal.Scenario.APP);f.phone();yes(f.flow.pages.parameters(f.view).page==(args[0].equals("sms")?2:1));f.code();yes(f.flow.owner.snapshot().state==State.LOCAL_AUTHORIZED);f.flow.close();break;}
   case "twoFactor":{F f=new F(LocalLoginRehearsal.Scenario.TWO_FACTOR);f.phone();f.code();yes(f.flow.pages.parameters(f.view).page==6);yes(f.flow.pages.loadPassword(f.view));f.w.flush();yes(f.flow.pages.parameters(f.view).passwordReady);yes(f.flow.pages.password(f.view,"FAKE_LOCAL_ONLY".toCharArray()));f.w.flush();yes(f.flow.owner.snapshot().state==State.LOCAL_AUTHORIZED);f.flow.close();break;}
   case "registration":{F f=new F(LocalLoginRehearsal.Scenario.REGISTER);f.phone();f.code();yes(f.flow.pages.parameters(f.view).page==5);yes(f.flow.pages.register(f.view,"Local".toCharArray(),"Fixture".toCharArray()));f.w.flush();yes(f.flow.owner.snapshot().state==State.LOCAL_AUTHORIZED);f.flow.close();break;}
   case "invalidCodeRetry":{F f=new F(LocalLoginRehearsal.Scenario.SMS);f.phone();yes(f.flow.pages.code(f.view,"111111".toCharArray()));f.w.flush();yes(f.flow.pages.parameters(f.view).page==2);f.code();yes(f.flow.owner.snapshot().state==State.LOCAL_AUTHORIZED);break;}
   case "consecutivePresses":{F f=new F(LocalLoginRehearsal.Scenario.SMS);yes(f.flow.pages.phone(f.view,"0000000".toCharArray()));for(int i=0;i<50;i++)yes(!f.flow.pages.phone(f.view,"0000000".toCharArray()));f.w.flush();f.code();yes(f.flow.owner.snapshot().state==State.LOCAL_AUTHORIZED);break;}
   case "cancelPending":{F f=new F(LocalLoginRehearsal.Scenario.SMS);f.flow.pages.phone(f.view,"0000000".toCharArray());f.flow.pages.cancel(f.view);f.w.flush();yes(f.flow.owner.snapshot().state==State.CANCELLED);break;}
   case "recreateView":{F f=new F(LocalLoginRehearsal.Scenario.SMS);f.phone();View old=f.view;f.flow.pages.detach(old);f.view=f.flow.pages.attach(0,Runnable::run,p->{});yes(!f.flow.pages.code(old,"000000".toCharArray()));f.code();yes(f.flow.owner.snapshot().state==State.LOCAL_AUTHORIZED);break;}
   case "noPersistence":{F f=new F(LocalLoginRehearsal.Scenario.SMS);f.phone();f.code();yes(f.flow.pages.commit(f.view));f.w.flush();yes(f.flow.owner.snapshot().state==State.STORAGE_UNCERTAIN);break;}
   case "hostBoundBeforeAdmission":{setup(args[1]);choose(0);pump();yes(LaunchActivity.last instanceof LoginActivity);LoginActivity s=(LoginActivity)LaunchActivity.last;yes(s.binding!=null&&host.owns(s));host.close();pump();yes(!host.owns(s));break;}
   case "hostDestroyedWhileOpening":{setup(args[1]);choose(0);host.close();pump();yes(LaunchActivity.last==root);break;}
   case "hostAccountChanged":{setup(args[1]);choose(0);root.account=1;pump();yes(LaunchActivity.last==root);break;}
   case "hostForeignLoginRejected":{setup(args[1]);yes(!host.owns(new LoginActivity(0)));host.close();break;}
   case "hostExistingAccountRejected":{setup(args[1]);org.telegram.messenger.UserConfig.getInstance(0).active=true;choose(0);pump();yes(LaunchActivity.last==root&&AlertDialog.lastMessage.contains("ACCOUNT_INSPECTION"));host.close();break;}
   case "hostPresentationFailureCloses":{setup(args[1]);root.present=false;choose(0);pump();yes(LaunchActivity.last==root);host.close();break;}
   case "hostReopenAfterDestroy":{setup(args[1]);choose(0);pump();LoginActivity s=(LoginActivity)LaunchActivity.last;s.onFragmentDestroy();pump();LaunchActivity.last=root;choose(1);pump();yes(LaunchActivity.last instanceof LoginActivity&&LaunchActivity.last!=s&&host.owns(LaunchActivity.last));host.close();break;}
   case "hostWorkerRejected":{setup(args[1]);Handler.reject=true;choose(0);yes(LaunchActivity.last==root);Handler.reject=false;host.close();break;}
   case "hostDoubleOpen":{setup(args[1]);choose(0);AlertDialog.choice.onClick(null,1);pump();yes(host.owns(LaunchActivity.last));host.close();break;}
   case "hostNativePolicyMismatch":{setup(args[1]);org.telegram.messenger.BuildConfig.FLEXYGRAM_CAP_TELEGRAMTRANSPORT=true;choose(0);pump();yes(LaunchActivity.last==root&&AlertDialog.lastMessage.contains("LOCAL_LOGIN_UNAVAILABLE"));host.close();break;}
   case "hostJniUnavailable":{setup(args[1]);choose(0);pump();yes(LaunchActivity.last==root&&AlertDialog.lastMessage.contains("NATIVE_ATTESTATION"));host.close();break;}
   case "hostNavigationBeforeReady":{setup(args[1]);choose(0);DialogsActivity other=new DialogsActivity();LaunchActivity.last=other;pump();yes(LaunchActivity.last==other);host.close();break;}
   case "hostRecreationBeforeReady":{setup(args[1]);choose(0);host.close();setup(args[1]);pump();yes(LaunchActivity.last==root);choose(1);pump();yes(host.owns(LaunchActivity.last));host.close();break;}
   case "hostRetainedRootMenuRebound":{setup(args[1]);host.close();activity=new RealAlphaActivity(new java.io.File(args[1]));org.telegram.messenger.ApplicationLoader.applicationContext=activity;host=new RealAlphaLocalLoginHost(activity);host.attachEntry();AlertDialog.choice=null;choose(0);pump();yes(host.owns(LaunchActivity.last));host.close();break;}
   case "hostScreenNoStrongOuterOwner":{setup(args[1]);choose(0);pump();yes(host.owns(LaunchActivity.last));for(java.lang.reflect.Field f:LaunchActivity.last.getClass().getDeclaredFields())yes(f.getType()!=RealAlphaLocalLoginHost.class);host.close();break;}
   default:throw new IllegalArgumentException("UNKNOWN_TEST");
  }
  System.out.println("HOST_LOCAL_INTEGRATION_NOT_ANDROID");
 }
}
