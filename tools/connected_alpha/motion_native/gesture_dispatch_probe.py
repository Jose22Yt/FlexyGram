"""Exact LaunchActivity OnBackAnimationCallback body with real framework events/child continuation.

Activity services/overlay/drawer and notification locker are explicit doubles;
this does not register a platform callback or execute the full Activity/account.
"""
from player_probe import method

def write(put,root):
 s=(root/'TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java').read_text()
 callback=method(s,'                onBackAnimationCallback =  new OnBackAnimationCallback()')
 callback=callback.replace('onBackAnimationCallback =','callback =',1).replace('@NonNull ','')
 put('GestureDispatchProbe.java','''import android.window.BackEvent;import android.window.OnBackAnimationCallback;
public class GestureDispatchProbe {
 public OnBackAnimationCallback callback;public GestureOpeningProbe actionBarLayout;
 boolean blocked;Runnable onInvokedGate;int locks,unlocks,ordinaryBacks,gateChecks;DrawerLayoutContainer drawerLayoutContainer;
 static class AndroidUtilities {static boolean tablet;static boolean isTablet(){return tablet;}}
 class AnimationNotificationsLocker {void lock(){locks++;}void unlock(){unlocks++;}}
 static class Drawer {int starts,updates,commits,cancels;boolean startPredictiveBack(){starts++;return true;}void updatePredictiveBackProgress(float p){updates++;}void commitPredictiveBack(){commits++;}void cancelPredictiveBack(){cancels++;}}
 static class DrawerLayoutContainer {final Drawer drawer=new Drawer();Drawer getDrawerContainer(){return drawer;}}
 boolean onBackPressed(boolean invoked){gateChecks++;if(invoked&&onInvokedGate!=null){Runnable callback=onInvokedGate;onInvokedGate=null;callback.run();}return !blocked;}void onBackPressed(){ordinaryBacks++;}
 public GestureDispatchProbe(GestureOpeningProbe p){actionBarLayout=p;AndroidUtilities.tablet=false;
'''+callback+''';}
}
''')
