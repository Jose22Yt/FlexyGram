"""Type-check all Camera Pop classes against the real Android SDK when available.
Large Telegram services/settings hosts are explicit doubles, not an integrated APK.
"""
import os
from pathlib import Path
import re
import shutil
import subprocess
import pytest
from test_camera_pop import POP, runtime_hosts


def test_camera_pop_android_api_and_native_host_types(tmp_path):
    candidates=[Path('/workspace/work/ios-icon-check/android35.jar')]
    for name in ['ANDROID_HOME','ANDROID_SDK_ROOT']:
        if os.environ.get(name):candidates+=sorted((Path(os.environ[name])/'platforms').glob('*/android.jar'),reverse=True)
    sdk=next((p for p in candidates if p.is_file()),None)
    if sdk is None:pytest.skip('Android SDK required for capsule/settings type check')
    files={p:s for p,s in runtime_hosts().items() if not p.startswith('android/') and not p.endswith('CameraPopCapsule.java')}
    files['org/telegram/messenger/MessagesController.java']=files['org/telegram/messenger/MessagesController.java'].replace('final SharedPreferences prefs=new SharedPreferences();','final SharedPreferences prefs=null;')
    files['org/telegram/messenger/AndroidUtilities.java']='''package org.telegram.messenger;public class AndroidUtilities{public static int statusBarHeight;public static int dp(float v){return Math.round(v);}public static android.graphics.Typeface bold(){return null;}public static boolean isAccessibilityScreenReaderEnabled(){return false;}public static boolean needShowPasscode(){return false;}public static void runOnUIThread(Runnable r){}public static void runOnUIThread(Runnable r,long d){}public static void cancelRunOnUIThread(Runnable r){}}'''
    files['org/telegram/messenger/SharedConfig.java']='package org.telegram.messenger;public class SharedConfig{public static boolean appLocked,isWaitingForPasscodeEnter;public static boolean animationsEnabled(){return true;}}'
    files['org/telegram/ui/LaunchActivity.java']='package org.telegram.ui;public class LaunchActivity extends android.app.Activity{public static org.telegram.ui.ActionBar.BaseFragment getLastFragmentIncludeMainTabs(){return null;}}'
    files['org/telegram/ui/ActionBar/BaseFragment.java']='''package org.telegram.ui.ActionBar;public class BaseFragment{protected int currentAccount;public int getCurrentAccount(){return currentAccount;}public void setCurrentAccount(int a){currentAccount=a;}public boolean presentFragment(BaseFragment f){return true;}public android.app.Activity getParentActivity(){return null;}public Theme.ResourcesProvider getResourceProvider(){return null;}public void showDialog(android.app.Dialog d){}public void onResume(){}}'''
    ids=sorted(set(re.findall(r'R.string.(\w+)', '\n'.join(p.read_text() for p in POP.glob('*.java')))))
    files['org/telegram/messenger/R.java']='package org.telegram.messenger;public class R{public static class string{'+''.join('public static final int '+n+'='+str(i)+';' for i,n in enumerate(ids))+'}public static class drawable{public static final int fg_ios_original_chat_context_menu_collapse=1;}}'
    files['org/telegram/messenger/LocaleController.java']='package org.telegram.messenger;public class LocaleController{public static String getString(int i){return "";}public static String formatPluralString(String s,int n){return "";}}'
    files['org/telegram/ui/ActionBar/Theme.java']='''package org.telegram.ui.ActionBar;public class Theme{public interface ResourcesProvider{}public static int key_windowBackgroundWhite=1,key_divider=2,key_windowBackgroundWhiteBlackText=3,key_windowBackgroundWhiteGrayText=4;public static int getColor(int c){return 0;}}'''
    files['org/telegram/messenger/ImageLocation.java']='package org.telegram.messenger;public class ImageLocation{public static int TYPE_SMALL;public static ImageLocation getForUser(org.telegram.tgnet.TLRPC.User u,int t){return null;}public static ImageLocation getForChat(org.telegram.tgnet.TLRPC.Chat c,int t){return null;}}'
    files['org/telegram/messenger/NotchInfoUtils.java']='package org.telegram.messenger;public class NotchInfoUtils{public static class NotchInfo{public android.graphics.RectF bounds;}public static NotchInfo getInfo(android.content.Context c){return null;}}'
    files['org/telegram/ui/Components/AvatarDrawable.java']='''package org.telegram.ui.Components;public class AvatarDrawable extends android.graphics.drawable.Drawable{public void draw(android.graphics.Canvas c){}public void setAlpha(int a){}public void setColorFilter(android.graphics.ColorFilter c){}public int getOpacity(){return 0;}public void setInfo(org.telegram.tgnet.TLRPC.User u){}public void setInfo(int a,org.telegram.tgnet.TLRPC.User u){}public void setInfo(org.telegram.tgnet.TLRPC.Chat c){}public void setInfo(int a,org.telegram.tgnet.TLRPC.Chat c){}public void setInfo(long id,String f,String l){}}'''
    files['org/telegram/ui/Components/BackupImageView.java']='''package org.telegram.ui.Components;public class BackupImageView extends android.view.View{public BackupImageView(android.content.Context c){super(c);}public void setRoundRadius(int r){}public void setImage(org.telegram.messenger.ImageLocation i,String f,android.graphics.drawable.Drawable d,Object p){}public void setImageDrawable(android.graphics.drawable.Drawable d){}}'''
    files['androidx/recyclerview/widget/RecyclerView.java']='''package androidx.recyclerview.widget;public class RecyclerView{public static class ViewHolder{public android.view.View itemView;}}'''
    files['app/flexygram/settings/SignatureMatteSettingsActivity.java']='''package app.flexygram.settings;import android.content.Context;import android.view.View;import androidx.recyclerview.widget.RecyclerView;public abstract class SignatureMatteSettingsActivity extends org.telegram.ui.ActionBar.BaseFragment{
 protected static final int TYPE_INFO_PRIVACY=7,TYPE_CHECK=3,TYPE_SETTINGS=2;protected BaseListAdapter listAdapter;
 protected abstract String getActionBarTitle();protected abstract BaseListAdapter createAdapter(Context c);protected abstract void onItemClick(View v,int p,float x,float y);
 protected void updateRows(){}protected int addRow(String s){return 0;}protected int settingsRowPosition(RecyclerView.ViewHolder h){return 0;}
 protected abstract class BaseListAdapter{public void notifyDataSetChanged(){}public int getItemViewType(int p){return 0;}public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){}public boolean isEnabled(RecyclerView.ViewHolder h){return true;}}
 protected abstract class MatteListAdapter extends BaseListAdapter{protected MatteListAdapter(Context c){}}
 }'''
    files['org/telegram/ui/ActionBar/AlertDialog.java']='''package org.telegram.ui.ActionBar;public class AlertDialog extends android.app.Dialog{public AlertDialog(android.content.Context c){super(c);}public static class Builder{public Builder(android.content.Context c,Theme.ResourcesProvider p){}public Builder setTitle(String s){return this;}public Builder setMessage(String s){return this;}public Builder setView(android.view.View v){return this;}public Builder setPositiveButton(String s,android.content.DialogInterface.OnClickListener l){return this;}public Builder setNegativeButton(String s,android.content.DialogInterface.OnClickListener l){return this;}public Builder setItems(CharSequence[]a,android.content.DialogInterface.OnClickListener l){return this;}public AlertDialog create(){return null;}}}'''
    for cls,methods in {
        'TextCheckCell':'public void setTextAndCheck(String s,boolean c,boolean d){}public void setTextAndValueAndCheck(String s,String v,boolean c,boolean m,boolean d){}',
        'TextSettingsCell':'public void setTextAndValue(String s,String v,boolean d){}',
        'TextInfoPrivacyCell':'public void setText(CharSequence s){}',
    }.items():files['org/telegram/ui/Cells/'+cls+'.java']='package org.telegram.ui.Cells;public class '+cls+' extends android.view.View{public '+cls+'(android.content.Context c){super(c);}'+methods+'}'
    files['org/telegram/ui/UsersSelectActivity.java']='''package org.telegram.ui;public class UsersSelectActivity extends org.telegram.ui.ActionBar.BaseFragment{public boolean noChatTypes,allowSelf;public UsersSelectActivity(boolean i,java.util.ArrayList<Long>a,int flags){}public interface Delegate{void selected(java.util.ArrayList<Long>ids,int flags);}public void setDelegate(Delegate d){}}'''
    paths=[]
    for name,content in files.items():
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content);paths.append(p)
    result=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-classpath',str(sdk),'-d',str(tmp_path/'classes'),*map(str,paths),*map(str,POP.glob('*.java'))],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
