"""Execute the production touch routing and external popup anchor regression paths."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_native_menu_cannot_steal_custom_header_taps(tmp_path):
    source = (JAVA / 'org/telegram/ui/ActionBar/ActionBarMenu.java').read_text()
    assert source.count('public boolean dispatchTouchEvent(MotionEvent ') == 1, 'Duplicate native touch override'
    dispatch = method(source, 'public boolean dispatchTouchEvent(MotionEvent event)')
    probe(tmp_path, {'Probe.java': '''
class MotionEvent {}
class NativeMenu {int touches;public boolean dispatchTouchEvent(MotionEvent e){touches++;return true;}}
class HeaderMenu extends NativeMenu {
 static class Bar {boolean custom;boolean hasSignatureActionControls(){return custom;}}
 Bar parentActionBar=new Bar();DISPATCH
}
public class Probe {public static void main(String[]args){HeaderMenu menu=new HeaderMenu();MotionEvent e=new MotionEvent();
 if(!menu.dispatchTouchEvent(e)||menu.touches!=1)throw new AssertionError("native header lost");
 menu.parentActionBar.custom=true;
 for(int i=0;i<10000;i++)if(menu.dispatchTouchEvent(e))throw new AssertionError("custom tap stolen");
 if(menu.touches!=1)throw new AssertionError("hidden native controls received taps");
 menu.parentActionBar.custom=false;if(!menu.dispatchTouchEvent(e)||menu.touches!=2)throw new AssertionError("search/action mode not restored");
 menu.parentActionBar=null;if(!menu.dispatchTouchEvent(e))throw new AssertionError();
}}'''.replace('DISPATCH', dispatch)})


def test_popup_from_external_header_uses_its_actual_anchor(tmp_path):
    source = (JAVA / 'org/telegram/ui/ActionBar/ActionBarMenuItem.java').read_text()
    # Execute the production early branch; unrelated native popup paths stay native.
    external = method(source, 'private void updateOrShowPopup(boolean show, boolean update)')
    external = external[:external.index('        int offsetY;')] + '}'
    probe(tmp_path, {'Probe.java': '''
class View {Object parent;int width;Object getParent(){return parent;}int getWidth(){return width;}int getMeasuredWidth(){return width;}}
class LocaleController {static boolean isRTL;}
public class Probe {
 View anchor,showSubMenuFrom,parentMenu=new View();int additionalXOffset=3,xOffset=2,additionalYOffset=4,yOffset=5;
 static class Window {int shows,updates,x,y;View target,content=new View();View getContentView(){return content;}
 void showAsDropDown(View v,int x,int y){target=v;this.x=x;this.y=y;shows++;}
 void update(View v,int x,int y,int w,int h){target=v;this.x=x;this.y=y;updates++;}}
 static class Layout{int scrolls;void scrollToTop(){scrolls++;}}
 Window popupWindow=new Window();Layout popupLayout=new Layout();METHOD
 public static void main(String[]args){Probe p=new Probe();p.showSubMenuFrom=new View();p.showSubMenuFrom.parent=new Object();p.showSubMenuFrom.width=48;p.popupWindow.content.width=220;
 p.updateOrShowPopup(true,false);if(p.popupWindow.target!=p.showSubMenuFrom||p.popupWindow.x!=-167||p.popupWindow.y!=9||p.popupLayout.scrolls!=1)throw new AssertionError("wrong external coordinates");
 LocaleController.isRTL=true;p.updateOrShowPopup(false,true);if(p.popupWindow.x!=5||p.popupWindow.updates!=1||p.popupLayout.scrolls!=1)throw new AssertionError("RTL/update");
 p.showSubMenuFrom.parent=p.parentMenu;p.updateOrShowPopup(true,true);if(p.popupWindow.shows!=1||p.popupWindow.updates!=1)throw new AssertionError("native path changed");
 }}'''.replace('METHOD', external)})


def test_preview_background_dismisses_without_stealing_menu_gestures(tmp_path):
    probe(tmp_path, {
        'android/content/Context.java': 'package android.content;public class Context{}',
        'android/view/MotionEvent.java': '''package android.view;public class MotionEvent{
 public static final int ACTION_DOWN=0,ACTION_UP=1,ACTION_MOVE=2,ACTION_CANCEL=3,ACTION_OUTSIDE=4;
 final int action;public MotionEvent(int a){action=a;}public int getActionMasked(){return action;}}''',
        'android/widget/FrameLayout.java': '''package android.widget;import android.view.MotionEvent;public class FrameLayout{
 public static final int FOCUS_BEFORE_DESCENDANTS=1;public boolean handled;public int dispatches;
 public FrameLayout(android.content.Context c){}public void setDescendantFocusability(int n){}public void setFocusableInTouchMode(boolean b){}
 public boolean dispatchTouchEvent(MotionEvent e){dispatches++;return handled;}
 public void requestLayout(){}public void scrollTo(int x,int y){}protected void onMeasure(int w,int h){}
 public static class MeasureSpec{public static final int UNSPECIFIED=0,AT_MOST=1;public static int getMode(int n){return n;}public static int getSize(int n){return n;}public static int makeMeasureSpec(int s,int m){return s;}}}''',
        'Probe.java': '''import android.view.MotionEvent;import app.flexygram.bubbles.interaction.MessageMenuViewport;
public class Probe{static int closes;static MotionEvent e(int a){return new MotionEvent(a);}
 public static void main(String[]args){MessageMenuViewport p=new MessageMenuViewport(new android.content.Context());p.setDismissRequest(()->closes++);
 p.handled=true;for(int a:new int[]{0,2,1})if(!p.dispatchTouchEvent(e(a)))throw new AssertionError();
 if(closes!=0||p.dispatches!=3)throw new AssertionError("menu action intercepted");
 p.handled=false;if(!p.dispatchTouchEvent(e(0))||closes!=1)throw new AssertionError("empty preview didn't close");
 int calls=p.dispatches;for(int a:new int[]{2,1})if(!p.dispatchTouchEvent(e(a)))throw new AssertionError();
 if(p.dispatches!=calls||closes!=1)throw new AssertionError("dismiss gesture leaked");
 if(!p.dispatchTouchEvent(e(4))||closes!=2)throw new AssertionError("outside ignored");
 p.handled=true;p.dispatchTouchEvent(e(0));p.dispatchTouchEvent(e(3));if(closes!=2)throw new AssertionError();
 p.setDismissRequest(null);p.handled=false;if(p.dispatchTouchEvent(e(0)))throw new AssertionError("listener cleared");
 }}''',
    }, [JAVA / 'app/flexygram/bubbles/interaction/MessageMenuViewport.java'])


def test_header_actions_and_preview_gap_have_distinct_native_callbacks():
    chat = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    menu = method(chat, 'protected void onSignatureOptionsClick()')
    call = method(chat, 'protected void onSignatureCallClick()')
    assert 'toggleSubMenu(null, avatarContainer.getSignatureMenuAnchor())' in menu
    assert 'onItemClick(call)' in call and 'toggleSubMenu' not in call
    assert 'onItemClick(call)' not in menu
    assert 'signatureMessageGap.setOnClickListener(preview -> closeMenu());' in chat
    assert 'signaturePreviewViewport.setDismissRequest(() -> closeMenu());' in chat
    icons = (JAVA / 'app/flexygram/composer/ComposerIcons.java').read_text()
    assert 'case "STICKER": return reference ? R.drawable.flexy_composer_folded' in icons
