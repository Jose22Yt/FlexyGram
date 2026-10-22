"""Exact source excerpts in framework doubles; executes host/navigation/lifecycle, not Android rendering."""
import sys,os
from pathlib import Path
from fixtures import write as base_write,ROOT
import re

def method(text,signature):
 a=text.index(signature);b=text.index('{',a)
 masked=re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/',lambda m:' '*len(m.group()),text)
 depth=1
 for c in range(b+1,len(text)):
  depth+=(masked[c]=='{')-(masked[c]=='}')
  if depth==0:return text[a:c+1]
 raise ValueError('UNBALANCED_EXCERPT')

def write(root):
 result=base_write(root)
 def put(p,s):(root/p).write_text(s)
 login=(ROOT/'build/generated/flexygram-local-login/java/org/telegram/ui/LoginActivity.java').read_text()
 activity=(ROOT/'build/generated/flexygram-local-login/realAlpha/org/telegram/ui/realalpha/RealAlphaActivity.java').read_text()
 layout=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
 base=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/BaseFragment.java').read_text()
 # Source selected by a test only, to prove the PR52 regression without modifying the checkout.
 if os.environ.get('PRESENTATION_BASELINE_LOOP')=='1':
  import subprocess,tempfile
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java';p.parent.mkdir(parents=True)
   p.write_bytes((ROOT/'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java').read_bytes())
   for patch in ('patches/native-login-wiring/0002-native-fragment-local-binding.patch','patches/native-login-pages/0004-native-local-pages.patch'):
    data=subprocess.check_output(['git','show','bac8681:'+patch],cwd=ROOT)
    subprocess.run(['git','apply','-'],input=data,cwd=d,check=True,capture_output=True)
   login=p.read_text()
 a=login.index('        for (int a = 0; a < views.length; a++) {\n            SlideView v = views[a];',login.index('public View createView('))
 loop=method(login[a:],'for (int a = 0; a < views.length; a++)')
 declarations='''static class NotificationCenter {static int didUpdateConnectionState,newSuggestionsAvailable;void addObserver(Object o,int id){throw new AssertionError("ORIGINAL_AUTH_OBSERVER");}} NotificationCenter getNotificationCenter(){return new NotificationCenter();}
private static final int VIEW_PHONE_INPUT=0,VIEW_CODE_MESSAGE=1,VIEW_CODE_SMS=2,VIEW_CODE_FLASH_CALL=3,VIEW_CODE_CALL=4,VIEW_REGISTER=5,VIEW_PASSWORD=6,VIEW_NEW_PASSWORD_STAGE_1=9,VIEW_NEW_PASSWORD_STAGE_2=10,VIEW_ADD_EMAIL=12,MODE_LOGIN=0,MODE_CHANGE_PHONE_NUMBER=3,DONE_TYPE_FLOATING=0,DONE_TYPE_ACTION=1;
 public static boolean failConstruction,failBinding,failView,rejectCreation,nullPageFailure;
 private int activityMode=MODE_LOGIN,currentViewNum,currentDoneType;private boolean newAccount,restoringState,preparedLocalMode,preparedLocalFragmentDestroyed;
 private android.view.View cachedFragmentView;private io.github.jose22yt.flexygram.login.local.LocalLoginSession preparedLocalSession;
 public void onResume(){} public SlideView[] views=new SlideView[20]; private final android.view.View backButtonView=new android.view.View(),moreButtonView=new android.view.View();
 static class SlideView extends android.view.View {int shown;boolean needBackButton(){return false;}boolean hasCustomKeyboard(){return false;}void restoreStateParams(android.os.Bundle b){}void onShow(){shown++;}void onHide(){}}
 public boolean phoneShown(){return views[0]!=null && views[0].shown==1;}
 void setCustomKeyboardVisible(boolean b,boolean a){}void showDoneButton(boolean b,boolean a){}
'''
 ctor=method(login,'public LoginActivity(int account)').replace('super();','super(); if(failConstruction) throw new IllegalStateException();')
 binding=method(login,'public void bindClosedLocalPages(').replace('{','{ if(failBinding) throw new IllegalStateException();',1)
 creation=method(login,'public boolean onFragmentCreate()').replace('{','{ if(rejectCreation) return false;',1)
 put('android/view/View.java','package android.view;public class View {public static final int VISIBLE=0,GONE=8;private int visibility=8;public int getVisibility(){return visibility;}public void setVisibility(int v){visibility=v;}public interface OnClickListener{void onClick(View v);}}')
 put('org/telegram/ui/LoginActivity.java','''package org.telegram.ui;import android.view.View;import android.content.Context;import android.os.Bundle;public class LoginActivity extends org.telegram.ui.ActionBar.BaseFragment {'''+declarations+ctor+binding+method(login,'private static boolean localLoginClosed()')+creation+'''
 public View createView(Context context){if(failView)throw new IllegalStateException();Bundle savedInstanceState=null;
 for(int i=0;i<views.length;i++)if(io.github.jose22yt.flexygram.login.local.EphemeralPages.allowedPage(i))views[i]=new SlideView();
 '''+'try {'+loop+'} catch(NullPointerException failure){nullPageFailure=true;throw failure;}'+'''return new View();}}
''')
 # The real pre-admission condition (including transition and delegate order), no permissive replacement.
 start=layout.index('    public boolean presentFragment(NavigationParams params) {')
 end=layout.index('        final EdgeToEdgeSupportMode',start)
 admission=layout[start:end]
 put('org/telegram/ui/ActionBar/INavigationLayout.java','''package org.telegram.ui.ActionBar;public interface INavigationLayout {boolean presentFragment(BaseFragment f);public class NavigationParams{public BaseFragment fragment;public boolean removeLast,noAnimation,preview,checkPresentFromDelegate=true;public ActionBarPopupWindow.ActionBarPopupWindowLayout menuView;public NavigationParams(BaseFragment f){fragment=f;}}}''')
 put('org/telegram/ui/ActionBar/ActionBarPopupWindow.java','package org.telegram.ui.ActionBar;public class ActionBarPopupWindow {public static class ActionBarPopupWindowLayout{}}')
 put('org/telegram/ui/ActionBar/ActionBarLayout.java','''package org.telegram.ui.ActionBar;import org.telegram.ui.*;import org.telegram.ui.realalpha.RealAlphaActivity;import org.telegram.ui.ActionBar.INavigationLayout.NavigationParams;public class ActionBarLayout implements INavigationLayout {
 public static boolean transition;public boolean animationInProgress,startedTracking;public RealAlphaActivity delegate,parentActivity;public ActionBarLayout(RealAlphaActivity a){delegate=parentActivity=a;}
 boolean checkTransitionAnimation(){return transition;}public boolean presentFragment(BaseFragment f){return presentFragment(new NavigationParams(f));}
 '''+admission+'''
 fragment.parentLayout=this;fragment.createView(parentActivity);LaunchActivity.last=fragment;return true;}}
''')
 put('org/telegram/ui/ActionBar/BaseFragment.java','''package org.telegram.ui.ActionBar;public class BaseFragment {private final ActionBar bar=new ActionBar();protected int currentAccount;public INavigationLayout parentLayout;public int getCurrentAccount(){return currentAccount;}public ActionBar getActionBar(){return bar;}public void showDialog(AlertDialog d){}public INavigationLayout getParentLayout(){return parentLayout;}protected boolean allowPresentFragment(){return true;}public boolean onFragmentCreate(){return true;}public android.view.View createView(android.content.Context c){return new android.view.View();}public void onFragmentDestroy(){}'''+method(base,'public boolean presentFragment(BaseFragment fragment)')+'}')
 put('org/telegram/ui/LaunchActivity.java','''package org.telegram.ui;import org.telegram.ui.ActionBar.*;public class LaunchActivity extends android.content.Context {public LaunchActivity(java.io.File f){super(f);}public static BaseFragment last;public static BaseFragment getLastFragment(){return last;}public boolean needPresentFragment(INavigationLayout l,INavigationLayout.NavigationParams p){return true;}public boolean needAddFragmentToStack(BaseFragment f,INavigationLayout l){return true;}}''')
 put('org/telegram/ui/realalpha/RealAlphaActivity.java','''package org.telegram.ui.realalpha;import org.telegram.ui.*;import org.telegram.ui.ActionBar.*;public class RealAlphaActivity extends LaunchActivity {
 public final org.telegram.ui.realalpha.local.RealAlphaLocalLoginHost localLab=new org.telegram.ui.realalpha.local.RealAlphaLocalLoginHost(this);public boolean finishing;public RealAlphaActivity(java.io.File f){super(f);}public boolean isFinishing(){return finishing;}
 '''+method(activity,'public boolean needPresentFragment(')+method(activity,'public boolean needAddFragmentToStack(')+method(activity,'private boolean permitted(')+'}')
 return result
