"""Compile all production Studio classes. Android widgets/storage are real; Telegram/theme/navigation are explicit doubles."""
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

def write_stubs(source,root):
 def put(path,text):
  p=source/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 studio=root/'TMessagesProj/src/main/java/app/flexygram/studio'
 for p in studio.rglob('*.java'):put('app/flexygram/studio/'+str(p.relative_to(studio)),p.read_text())
 files_entry=(root/'TMessagesProj/src/main/java/app/flexygram/files/FlexyFiles.java').read_text()
 put('app/flexygram/files/FlexyFiles.java',files_entry)
 put('app/flexygram/files/core/SelectedDocument.java',(root/'TMessagesProj/src/main/java/app/flexygram/files/core/SelectedDocument.java').read_text())
 code='\n'.join(p.read_text() for p in studio.rglob('*.java'))+'\n'+files_entry
 strings=sorted(set(re.findall(r'R.string.(\w+)',code)))
 drawables=sorted(set(re.findall(r'R.drawable.(\w+)',code)))
 labels={e.get('name'):e.text or '' for e in ET.parse(root/'TMessagesProj/src/main/res/values/flexystudio.xml').getroot()}
 labels.update({e.get('name'):e.text or '' for e in ET.parse(root/'TMessagesProj/src/main/res/values/flexyfiles.xml').getroot()})
 from json import dumps
 put('org/telegram/messenger/R.java','package org.telegram.messenger;public class R {public static class string {'+''.join(f'public static final int {n}={i+1};'for i,n in enumerate(strings))+'}public static class drawable {'+''.join(f'public static final int {n}=android.R.drawable.ic_menu_agenda;'for n in drawables)+'}}')
 put('org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController {public static boolean isRTL;public static String getString(int id){'+''.join('if(id==R.string.'+n+')return '+dumps(labels.get(n,n))+';' for n in strings)+'return "";}public static String formatString(String key,int id,Object...args){return String.format(getString(id),args);}}')
 theme_keys=sorted(set(re.findall(r'Theme.(key_\w+)',code))|{'key_windowBackgroundWhiteGrayIcon'})
 put('org/telegram/ui/ActionBar/Theme.java','''package org.telegram.ui.ActionBar;
import android.graphics.drawable.*;public class Theme {public static boolean dark;public interface ResourcesProvider {}
'''+''.join(f'public static final int {n}={i+1};'for i,n in enumerate(theme_keys))+'''
public static int getColor(int key,ResourcesProvider p){
if(key==key_windowBackgroundWhiteBlackText)return dark?0xffedf2f8:0xff202630;
if(key==key_windowBackgroundWhiteGrayText2||key==key_windowBackgroundWhiteGrayIcon)return dark?0xffaab8ca:0xff687588;
if(key==key_windowBackgroundWhiteBlueText||key==key_featuredStickers_addButton)return dark?0xff61acff:0xff227ce0;
if(key==key_featuredStickers_buttonText)return 0xffffffff;
if(key==key_divider)return dark?0xff354256:0xffd9e0ea;
return dark?(key==key_windowBackgroundGray?0xff11151c:0xff1b2533):(key==key_windowBackgroundGray?0xfff7f8fa:0xffffffff);}
public static Drawable createSimpleSelectorRoundRectDrawable(int radius,int fill,int pressed){GradientDrawable d=new GradientDrawable();d.setColor(fill);d.setCornerRadius(radius);return new RippleDrawable(android.content.res.ColorStateList.valueOf(pressed),d,null);}}
''')
 put('org/telegram/messenger/BuildConfig.java','package org.telegram.messenger;public class BuildConfig {public static final boolean CONNECTED_ALPHA=true;public static final int VERSION_CODE=1274;}')
 put('org/telegram/messenger/ApplicationLoader.java','''package org.telegram.messenger;public class ApplicationLoader {
public static android.content.Context applicationContext;public static android.os.Handler applicationHandler=new android.os.Handler(android.os.Looper.getMainLooper());public static String getApplicationId(){return applicationContext.getPackageName();}}''')
 put('org/telegram/messenger/AndroidUtilities.java','''package org.telegram.messenger;public class AndroidUtilities {
public static android.graphics.Point displaySize=new android.graphics.Point(400,840);public static float density=1;public static int dp(float x){return (int)Math.ceil(x*density);}public static android.graphics.Typeface bold(){return android.graphics.Typeface.create("sans-serif",1);}public static String formatFileSize(long size){return size+" B";}
public static void runOnUIThread(Runnable r){if(android.os.Looper.myLooper()==android.os.Looper.getMainLooper())r.run();else ApplicationLoader.applicationHandler.post(r);}public static boolean isInternalUri(android.net.Uri uri){return false;}}
''')
 put('org/telegram/messenger/Utilities.java','''package org.telegram.messenger;public class Utilities {public static final Queue globalQueue=new Queue();public static class Queue {public void postRunnable(Runnable r){new Thread(r,"test-queue-double").start();}}}''')
 put('org/telegram/messenger/SharedConfig.java','package org.telegram.messenger;public class SharedConfig {public static boolean animationsEnabled(){return true;}}')
 put('org/telegram/messenger/UserConfig.java','package org.telegram.messenger;public class UserConfig {public static int selectedAccount;public static UserConfig getInstance(int account){return new UserConfig();}public boolean isClientActivated(){return true;}}')
 put('org/telegram/messenger/MessageObject.java','''package org.telegram.messenger;public class MessageObject {public int currentAccount=2;public Owner messageOwner=new Owner();public static class Owner {public String attachPath;public boolean noforwards;}public boolean putInDownloadsStore,isMediaSpoilersRevealed,sensitive;public boolean isSensitive(){return sensitive;}public boolean hasMediaSpoilers(){return sensitive;}public boolean needDrawBluredPreview(){return false;}public String name="Synthetic.flexyGram";public Document document=new Document();public int id=1;public String getDocumentName(){return name;}public Document getDocument(){return document;}public boolean isSecret(){return false;}public boolean isSecretMedia(){return false;}public boolean isSending(){return false;}public boolean isSendError(){return false;}public int getId(){return id;}public long getDialogId(){return 44;}public static class Document {public long size=100;}}''')
 put('org/telegram/messenger/DownloadController.java','''package org.telegram.messenger;public class DownloadController {
public interface FileDownloadProgressListener {void onFailedDownload(String n,boolean c);void onSuccessDownload(String n);void onProgressDownload(String n,long d,long t);void onProgressUpload(String n,long d,long t,boolean e);int getObserverTag();}
private static final DownloadController I=new DownloadController();public static int observedAccount=-1,adds,removes;public static FileDownloadProgressListener listener;
public static DownloadController getInstance(int account){observedAccount=account;return I;}public int generateObserverTag(){return 91;}public void addLoadingFileObserver(String n,MessageObject m,FileDownloadProgressListener l){adds++;listener=l;}public void removeLoadingFileObserver(FileDownloadProgressListener l){if(listener==l){removes++;listener=null;}}
}''')
 put('org/telegram/messenger/FileLoader.java','''package org.telegram.messenger;public class FileLoader {public static int loads,cancels,account;public static java.io.File file;private static final FileLoader I=new FileLoader();public static final int PRIORITY_LOW=1,PRIORITY_NORMAL=2;public static FileLoader getInstance(int a){account=a;return I;}public java.io.File getPathToMessage(Object message){return file;}public static String getAttachFileName(MessageObject.Document d){return "fixture-document";}public void loadFile(MessageObject.Document d,Object parent,int p,int c){loads++;}public void cancelLoadFile(MessageObject.Document d){cancels++;}}''')
 put('org/telegram/ui/ActionBar/BaseFragment.java','''package org.telegram.ui.ActionBar;
public class BaseFragment {public android.app.Activity activity;public android.view.View view;public android.app.Dialog dialog;public boolean paused;public BaseFragment(){}public BaseFragment(android.app.Activity a,android.view.View v){activity=a;view=v;}
public android.app.Activity getParentActivity(){return activity;}public android.view.View getFragmentView(){return view;}public boolean isPaused(){return paused;}public Theme.ResourcesProvider getResourceProvider(){return null;}
public android.app.Dialog showDialog(android.app.Dialog d){return showDialog(d,false,null);}public android.app.Dialog showDialog(android.app.Dialog d,boolean transition,android.content.DialogInterface.OnDismissListener listener){dialog=d;if(listener!=null)d.setOnDismissListener(listener);d.show();return d;}
public void startActivityForResult(android.content.Intent i,int code){}public void onActivityResultFragment(int c,int r,android.content.Intent d){}public void onResume(){paused=false;}public void onTransitionAnimationEnd(boolean o,boolean b){}public void onFragmentDestroy(){}public void saveSelfArgs(android.os.Bundle b){}public void restoreSelfArgs(android.os.Bundle b){}
}''')
 put('org/telegram/ui/ActionBar/BottomSheet.java','''package org.telegram.ui.ActionBar;
public class BottomSheet extends android.app.Dialog {public android.widget.FrameLayout content;public BottomSheet(android.content.Context c,boolean focus,Theme.ResourcesProvider p){super(c);content=new android.widget.FrameLayout(c);setContentView(content);}public void setBackgroundColor(int c){content.setBackgroundColor(c);}public void setApplyTopPadding(boolean b){}public void setCustomView(android.view.View v){content.addView(v,new android.widget.FrameLayout.LayoutParams(-1,-2));}protected boolean canDismissWithSwipe(){return true;}}
''')
 put('org/telegram/ui/ActionBar/AlertDialog.java','''package org.telegram.ui.ActionBar;
public class AlertDialog extends android.app.AlertDialog {protected AlertDialog(android.content.Context c){super(c);}public static class Builder extends android.app.AlertDialog.Builder {public Builder(android.content.Context c,Theme.ResourcesProvider p){super(c);}}}''')
 put('org/telegram/ui/LaunchActivity.java','package org.telegram.ui;public class LaunchActivity {public static org.telegram.ui.ActionBar.BaseFragment current;public static org.telegram.ui.ActionBar.BaseFragment getSafeLastFragment(){return current;}}')
 put('org/telegram/ui/ChatActivity.java','package org.telegram.ui;public class ChatActivity extends org.telegram.ui.ActionBar.BaseFragment {public java.util.Set<String> refreshed;public void onFlexyStudioApplied(java.util.Set<String> s){refreshed=s;}}')
 icons=['EXTERALESS','FLEX_GREEN','FLEX_CORAL','FLEX_MONO','FLEX_BLUEPRINT','FLEX_NYA','FLEX_QUACK','FLEX_GO','LEGACY_EXTERALESS','BLUEPRINT','RED','NYA','AYU','QUACK','GO','HAND','MONO','NOTHING','PLUS','TELEGRAM','VINTAGE','AQUA','PREMIUM','TURBO','NOX']
 put('org/telegram/ui/LauncherIconController.java','''package org.telegram.ui;public class LauncherIconController {public enum LauncherIcon {'''+','.join(icons)+'''}public static LauncherIcon selected=LauncherIcon.EXTERALESS;public static int writes;public static boolean isEnabled(LauncherIcon i){return selected==i;}public static void setIcon(LauncherIcon i){selected=i;writes++;org.telegram.messenger.ApplicationLoader.applicationContext.getSharedPreferences("flexy_launcher",0).edit().putString("selected",i.name()).commit();}}''')
 for name,pkg in [('ChatMessageCell','org/telegram/ui/Cells'),('SharedDocumentCell','org/telegram/ui/Cells')]:
  method='public void updateButtonState(boolean a,boolean b,boolean c){}' if name=='ChatMessageCell' else 'public void updateFileExistIcon(boolean b){}'
  put(pkg+'/'+name+'.java','package '+pkg.replace('/','.')+';public class '+name+' extends android.view.View {public '+name+'(android.content.Context c){super(c);}'+method+'}')
 put('org/telegram/ui/Components/BulletinFactory.java','''package org.telegram.ui.Components;public class BulletinFactory {public static BulletinFactory of(org.telegram.ui.ActionBar.BaseFragment f){return new BulletinFactory();}public BulletinFactory createSimpleBulletin(int i,CharSequence text,CharSequence button,Runnable r){return this;}public void show(){}}''')
 for name,pkg in [('BubbleConfig','app/flexygram/bubbles'),('HeaderConfig','app/flexygram/header')]:put(pkg+'/'+name+'.java','package '+pkg.replace('/','.')+';public class '+name+' {public static int loads;public static void load(){loads++;}}')
 put('app/flexygram/composer/FlexyComposerConfig.java','package app.flexygram.composer;public class FlexyComposerConfig {}')
 put('app/exteraless/appearance/AppearanceConfig.java','package app.exteraless.appearance;public class AppearanceConfig {public static android.content.SharedPreferences getPreferences(){return org.telegram.messenger.ApplicationLoader.applicationContext.getSharedPreferences("appearance-fixture",0);}}')
 put('androidx/recyclerview/widget/RecyclerView.java','''package androidx.recyclerview.widget;public class RecyclerView {public abstract static class ViewHolder {public final android.view.View itemView;public ViewHolder(android.view.View v){itemView=v;}public int getItemViewType(){return 110;}}}''')
 put('org/telegram/ui/Components/RecyclerListView.java','package org.telegram.ui.Components;public class RecyclerListView {public static class Holder extends androidx.recyclerview.widget.RecyclerView.ViewHolder {public Holder(android.view.View v){super(v);}}}')
 put('app/flexygram/settings/SignatureMatteSettingsActivity.java','''package app.flexygram.settings;
public abstract class SignatureMatteSettingsActivity extends org.telegram.ui.ActionBar.BaseFragment {
protected org.telegram.ui.ActionBar.Theme.ResourcesProvider resourcesProvider;protected int count;protected void updateRows(){count=0;}protected int addRow(){return count++;}protected int addRow(String id){return addRow();}protected abstract String getActionBarTitle();protected abstract BaseListAdapter createAdapter(android.content.Context c);protected abstract void onItemClick(android.view.View v,int p,float x,float y);
protected class BaseListAdapter {protected static final int TYPE_HEADER=1,TYPE_SHADOW=2,TYPE_CHECK=3;public int getItemViewType(int p){return 0;}public androidx.recyclerview.widget.RecyclerView.ViewHolder onCreateViewHolder(android.view.ViewGroup p,int t){return new org.telegram.ui.Components.RecyclerListView.Holder(new android.view.View(p.getContext()));}public void onBindViewHolder(androidx.recyclerview.widget.RecyclerView.ViewHolder h,int p,boolean b){}public boolean isEnabled(androidx.recyclerview.widget.RecyclerView.ViewHolder h){return false;}}
protected class MatteListAdapter extends BaseListAdapter {protected MatteListAdapter(android.content.Context c){}}
}''')
 put('app/flexygram/settings/SignatureNavigationCell.java','''package app.flexygram.settings;public class SignatureNavigationCell extends android.widget.TextView {public SignatureNavigationCell(android.content.Context c,org.telegram.ui.ActionBar.Theme.ResourcesProvider p){super(c);}public void bind(String t,int icon,boolean divider){setText(t);}}''')
 put('org/telegram/ui/Cells/CheckBoxCell.java','''package org.telegram.ui.Cells;public class CheckBoxCell extends android.widget.CheckBox {public CheckBoxCell(android.content.Context c,int type,org.telegram.ui.ActionBar.Theme.ResourcesProvider p){super(c);}public void setText(CharSequence t,String v,boolean b,boolean d){setText(t);setChecked(b);}public void setMultiline(boolean b){}public void setChecked(boolean b,boolean a){setChecked(b);}}''')
 put('tw/nekomimi/nekogram/ui/cells/HeaderCell.java','package tw.nekomimi.nekogram.ui.cells;public class HeaderCell extends android.widget.TextView {public HeaderCell(android.content.Context c){super(c);}}')

 put('org/telegram/ui/Cells/TextCheckCell.java','package org.telegram.ui.Cells;public class TextCheckCell extends android.widget.CheckBox {public TextCheckCell(android.content.Context c){super(c);}public void setTextAndValueAndCheck(String t,String v,boolean b,boolean m,boolean d,boolean n){setText(t+"\\n"+v);setChecked(b);}}')
 put('app/flexygram/files/FlexyFilesSheet.java','package app.flexygram.files;public class FlexyFilesSheet extends android.app.Dialog {public FlexyFilesSheet(org.telegram.ui.ActionBar.BaseFragment owner,java.io.File f,String n,long d,int a){super(owner.getParentActivity());}}')
