"""Explicit Telegram/settings scaffolding; Android widgets/Choreographer and all motion classes are real."""
import re,shutil

def write(source,root):
 def put(name,code):
  target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(code)
 codes=''
 for f in (root/'TMessagesProj/src/main/java/app/flexygram/motion').glob('*.java'):
  put('app/flexygram/motion/'+f.name,f.read_text());codes+=f.read_text()
 f=root/'TMessagesProj/src/main/java/app/flexygram/settings/SignatureNavigationCell.java';put('app/flexygram/settings/'+f.name,f.read_text());codes+=f.read_text()
 strings=sorted(set(re.findall(r'R.string.(\w+)',codes)))
 put('org/telegram/messenger/R.java','package org.telegram.messenger;public class R {public static class string {'+''.join(f'public static final int {n}={i+1};'for i,n in enumerate(strings))+'}public static class drawable {public static final int ic_ab_back=1,round_keyboard_arrow_right_24=2;}}')
 put('org/telegram/messenger/AndroidUtilities.java','package org.telegram.messenger;public class AndroidUtilities {public static int dp(float f){return (int)f;}private static final android.os.Handler handler=new android.os.Handler(android.os.Looper.getMainLooper());public static void runOnUIThread(Runnable r,long delay){handler.postDelayed(r,delay);}public static void cancelRunOnUIThread(Runnable r){handler.removeCallbacks(r);}}')
 put('org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController {public static boolean isRTL;public static String getString(int id){return "motion-"+id;}}')
 put('org/telegram/ui/ActionBar/Theme.java','package org.telegram.ui.ActionBar;public class Theme {public interface ResourcesProvider{}public static int key_windowBackgroundWhiteBlackText=1,key_windowBackgroundWhiteGrayIcon=2,key_glass_tabSelected=3;public static int multAlpha(int c,float a){return c;}public static int getColor(int k,ResourcesProvider p){return 0xff333333;}}')
 put('androidx/recyclerview/widget/RecyclerView.java','''package androidx.recyclerview.widget;public class RecyclerView {public static class LayoutParams extends android.view.ViewGroup.LayoutParams {public LayoutParams(int w,int h){super(w,h);}}public static class ViewHolder {public final android.view.View itemView;public ViewHolder(android.view.View v){itemView=v;}public int getItemViewType(){return 0;}}}''')
 put('org/telegram/ui/Components/RecyclerListView.java','''package org.telegram.ui.Components;public class RecyclerListView {public static class Holder extends androidx.recyclerview.widget.RecyclerView.ViewHolder {public Holder(android.view.View v){super(v);}}public static class Adapter {public void notifyDataSetChanged(){}}public Adapter getAdapter(){return new Adapter();}}''')
 put('org/telegram/ui/Cells/TextSettingsCell.java','''package org.telegram.ui.Cells;public class TextSettingsCell extends android.widget.FrameLayout {protected boolean needDivider;private android.widget.TextView text;public TextSettingsCell(android.content.Context c,org.telegram.ui.ActionBar.Theme.ResourcesProvider p){super(c);text=new android.widget.TextView(c);addView(text);}public android.widget.TextView getTextView(){return text;}public void setText(String s,boolean d){text.setText(s);needDivider=d;}public void setTextAndValue(String s,String v,boolean d){setText(s,d);}}''')
 put('org/telegram/ui/Cells/TextCheckCell.java','''package org.telegram.ui.Cells;public class TextCheckCell extends android.widget.CheckBox {public TextCheckCell(android.content.Context c){super(c);}public void setTextAndCheck(String s,boolean b,boolean d){setText(s);setChecked(b);}}''')
 put('org/telegram/ui/Cells/TextInfoPrivacyCell.java','package org.telegram.ui.Cells;public class TextInfoPrivacyCell extends android.widget.TextView {public TextInfoPrivacyCell(android.content.Context c){super(c);}}')
 put('tw/nekomimi/nekogram/ui/cells/HeaderCell.java','package tw.nekomimi.nekogram.ui.cells;public class HeaderCell extends android.widget.TextView {public HeaderCell(android.content.Context c){super(c);}}')
 put('org/telegram/ui/ActionBar/AlertDialog.java','''package org.telegram.ui.ActionBar;public class AlertDialog {public static class Builder extends android.app.AlertDialog.Builder {public Builder(android.content.Context c,Theme.ResourcesProvider p){super(c);}}}''')
 put('app/flexygram/settings/SignatureMatteSettingsActivity.java','''package app.flexygram.settings;public abstract class SignatureMatteSettingsActivity {
 public static android.app.Activity host;protected org.telegram.ui.ActionBar.Theme.ResourcesProvider resourcesProvider;protected org.telegram.ui.Components.RecyclerListView listView;
 protected int count;protected void updateRows(){count=0;}protected int addRow(){return count++;}protected int addRow(String id){return addRow();}protected android.app.Activity getParentActivity(){return host;}protected org.telegram.ui.ActionBar.Theme.ResourcesProvider getResourceProvider(){return resourcesProvider;}protected void showDialog(android.app.Dialog d){d.show();}
 protected abstract String getActionBarTitle();protected abstract BaseListAdapter createAdapter(android.content.Context c);protected abstract void onItemClick(android.view.View v,int p,float x,float y);
 protected class BaseListAdapter {protected static final int TYPE_HEADER=1,TYPE_SHADOW=2,TYPE_CHECK=3,TYPE_INFO_PRIVACY=4,TYPE_SETTINGS=5;public int getItemViewType(int p){return 0;}public androidx.recyclerview.widget.RecyclerView.ViewHolder onCreateViewHolder(android.view.ViewGroup p,int t){return new org.telegram.ui.Components.RecyclerListView.Holder(new android.view.View(p.getContext()));}public void onBindViewHolder(androidx.recyclerview.widget.RecyclerView.ViewHolder h,int p,boolean b){}public boolean isEnabled(androidx.recyclerview.widget.RecyclerView.ViewHolder h){return false;}}
 protected class MatteListAdapter extends BaseListAdapter {protected MatteListAdapter(android.content.Context c){}}
}''')

 # Compile the exact opt-in popup dismissal body; window manager and native PopupWindow remain real.
 popup=(root/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarPopupWindow.java').read_text()
 fields=popup[popup.index('    private AnimatorSet windowAnimatorSet;'):popup.index('    private boolean animationEnabled')]
 methods=popup[popup.index('    @Override\n    public void dismiss() {'):popup.index('    public void setEmptyOutAnimation')]
 methods=methods.replace('ActionBarPopupWindow.super.dismiss()','PopupMotionProbe.super.dismiss()')
 put('PopupMotionProbe.java','''import android.animation.*;import android.view.*;import android.widget.*;import java.util.*;
public class PopupMotionProbe extends PopupWindow {
 public static class ActionBarPopupWindowLayout extends FrameLayout {public ActionBarPopupWindowLayout(android.content.Context c){super(c);}ArrayList<AnimatorSet> itemAnimators=new ArrayList<>();boolean shownFromBottom;}
 public boolean animationEnabled=true,pauseNotifications=true,scaleOut,isClosingAnimated;public int dismissAnimationDuration=220,unregisters,dims;public long outEmptyTime=-1;
 public static class Locker {public int locks,releases;boolean held;public void lock(){if(held)throw new AssertionError("duplicate lock");held=true;locks++;}public void unlock(){if(held){held=false;releases++;}}}
 public final Locker notificationsLocker=new Locker();public void unregisterListener(){unregisters++;}public void dismissDim(){dims++;}public static int dp(float v){return (int)v;}
 public PopupMotionProbe(View content){super(content,300,150,true);}public app.flexygram.motion.FlexyMotionAnimator current(){return flexyDismissAnimator;}
'''+fields+methods+'}')

 from tabs_probe import write as write_tabs
 write_tabs(put,root)

 put('org/telegram/ui/Components/ButtonBounce.java',(root/'TMessagesProj/src/main/java/org/telegram/ui/Components/ButtonBounce.java').read_text())
 put('org/telegram/messenger/BuildConfig.java','package org.telegram.messenger;public class BuildConfig {public static boolean CONNECTED_ALPHA=true;}')
 put('org/telegram/ui/Components/CubicBezierInterpolator.java',(root/'TMessagesProj/src/main/java/org/telegram/ui/Components/CubicBezierInterpolator.java').read_text())

 from player_probe import write as write_player
 write_player(put,root)

 from bot_probe import write as write_bot
 write_bot(put,root,source)

 from navigation_probe import write as write_navigation
 write_navigation(put,root,source)

 from folder_probe import write as write_folder
 write_folder(put,root)
