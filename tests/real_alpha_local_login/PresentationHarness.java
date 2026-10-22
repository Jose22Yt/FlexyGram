package org.telegram.ui.realalpha.local;
import org.telegram.ui.*;import org.telegram.ui.ActionBar.*;import org.telegram.ui.realalpha.*;import android.os.Handler;
public final class PresentationHarness {
 static void need(boolean b){if(!b)throw new AssertionError("PRESENTATION_CONTRACT");}
 public static void main(String[] args)throws Exception{
  System.load(args[2]);RealAlphaActivity a=new RealAlphaActivity(new java.io.File(args[1]));org.telegram.messenger.ApplicationLoader.applicationContext=a;
  DialogsActivity root=new DialogsActivity();root.parentLayout=new ActionBarLayout(a);LaunchActivity.last=root;RealAlphaLocalLoginHost h=a.localLab;h.attachEntry();String test=args[0];
  if(test.equals("construction"))LoginActivity.failConstruction=true;
  if(test.equals("binding"))LoginActivity.failBinding=true;
  if(test.equals("fragment"))LoginActivity.rejectCreation=true;
  if(test.equals("view"))LoginActivity.failView=true;
  if(test.equals("transition"))ActionBarLayout.transition=true;
  root.getActionBar().createMenu().getItem(904301).click();AlertDialog.choice.onClick(null,test.equals("app")?1:0);
  if(test.equals("cancelled"))h.close();
  if(test.equals("foreignRoot"))LaunchActivity.last=new DialogsActivity();
  Handler.drain(false);Handler.drain(true);
  if(LoginActivity.nullPageFailure)throw new AssertionError("REPRODUCED_CREATE_VIEW_NULL_PAGE");
  if(test.equals("sms")||test.equals("app")){
   need(LaunchActivity.last instanceof LoginActivity);LoginActivity login=(LoginActivity)LaunchActivity.last;need(login.phoneShown()&&h.owns(login));
   need(!a.needPresentFragment(root.parentLayout,new INavigationLayout.NavigationParams(new LoginActivity(0))));
   need(!a.needAddFragmentToStack(new LoginActivity(0),root.parentLayout));
   login.onFragmentDestroy();need(!h.owns(login));
  }else if(test.equals("cancelled")||test.equals("foreignRoot")){need(!(LaunchActivity.last instanceof LoginActivity));}
  else {String code=test.equals("construction")?"LOCAL_SCREEN_CONSTRUCTION":test.equals("binding")?"LOCAL_PAGE_BINDING":test.equals("fragment")?"FRAGMENT_CREATION":test.equals("view")?"VIEW_CREATION":"NAVIGATION_TRANSITION";need(LaunchActivity.last==root&&AlertDialog.lastMessage.contains("PRESENTATION:"+code));}
  h.close();need(org.telegram.tgnet.ConnectionsManager.sends==0&&org.telegram.tgnet.ConnectionsManager.initializations==0);
  System.out.println("HOST_LOCAL_INTEGRATION_NOT_ANDROID");
 }
}
