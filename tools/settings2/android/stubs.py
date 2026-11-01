"""Explicit navigation/list/legacy-service doubles. Android text/layout/canvas/prefs are real.
The NEW Settings2 Java sources are copied unchanged, including root and category controllers.
"""
import re,json,shutil,subprocess,os
import xml.etree.ElementTree as ET
from pathlib import Path

def write(dest,root):
 J=root/'TMessagesProj/src/main/java';folder=J/'app/flexygram/settings/signature'
 def emit(path,s):
  p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 for p in folder.glob('*.java'):emit('app/flexygram/settings/signature/'+p.name,p.read_text())
 source='\n'.join(p.read_text()for p in folder.glob('*.java'))+'\n'+(J/'app/flexygram/studio/FlexyStudioActivity.java').read_text()
 symbols={}
 dump=subprocess.check_output([str(Path(os.environ['SETTINGS2_SDK_ROOT'])/'build-tools/36.0.0/aapt2'),'dump','resources',str(dest.parents[2]/'resources.ap_')],text=True)
 for m in re.finditer(r'resource (0x[0-9a-f]+) (?:[^: ]+:)?(string|drawable)/(\w+)',dump):symbols[(m[2],m[3])]=int(m[1],16)
 strings=sorted(set(re.findall(r'R.string.(\w+)',source)))
 ids={name:symbols[('string',name)] for name in strings}
 titles={}
 for directory in ['values','values-es']:
  for p in (root/'TMessagesProj/src/main/res'/directory).glob('*.xml'):
   try:
    import xml.etree.ElementTree as E
    for x in E.parse(p).getroot().findall('string'):
     if x.get('name')in ids:titles[x.get('name')]=''.join(x.itertext()).replace("\\'","'")
   except E.ParseError:pass
 def q(s):return json.dumps(s,ensure_ascii=True)
 emit('org/telegram/messenger/R.java','package org.telegram.messenger;public class R{public static class string{'+''.join('public static final int '+n+'='+str(i)+';'for n,i in ids.items())+'}public static class drawable{'+''.join('public static final int '+n+'='+str(symbols[('drawable',n)])+';'for n in sorted(set(re.findall(r'R.drawable.(\w+)',source))))+'}}')
 emit('org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController{public static boolean isRTL;public static String getString(int id){return switch(id){'+''.join('case '+str(i)+'->'+q(titles.get(n,n))+';'for n,i in ids.items())+'default->"";};}}')
 emit('org/telegram/messenger/AndroidUtilities.java','package org.telegram.messenger;public class AndroidUtilities{public static int dp(float v){return Math.round(v);}public static android.graphics.Typeface bold(){return android.graphics.Typeface.DEFAULT_BOLD;}}')
 emit('org/telegram/messenger/browser/Browser.java','package org.telegram.messenger.browser;public class Browser{public static void openUrl(android.content.Context c,String s){}}')
 emit('org/telegram/ui/ActionBar/Theme.java', '''package org.telegram.ui.ActionBar;import android.graphics.*;public class Theme{public interface ResourcesProvider{}public static boolean dark;public static Paint dividerPaint=new Paint();public static final int key_windowBackgroundWhiteBlackText=1,key_windowBackgroundWhiteGrayText2=2,key_windowBackgroundWhiteGrayIcon=3,key_windowBackgroundGray=4,key_windowBackgroundWhite=5,key_divider=6;public static int getColor(int k,ResourcesProvider p){return getColor(k);}public static int getColor(int k){dividerPaint.setColor(dark?0xff303a4a:0xffdbe0e8);return switch(k){case 1->dark?0xffeff2f8:0xff111827;case 4->dark?0xff080c14:0xfff6f7fa;case 5->dark?0xff151e2b:0xffffffff;default->dark?0xffb2bece:0xff566172;};}}''')
 emit('org/telegram/ui/ActionBar/ActionBar.java','''package org.telegram.ui.ActionBar;public class ActionBar {public android.widget.TextView title;public ActionBar(android.content.Context c){title=new android.widget.TextView(c);title.setTextSize(20);title.setGravity(17);}public void centerTitle(){}public void setTitle(String s){title.setText(s);}public Menu createMenu(){return new Menu();}public static class Menu{public ActionBarMenuItem addItem(int id,int image){return new ActionBarMenuItem();}}}''')
 emit('org/telegram/ui/ActionBar/ActionBarMenuItem.java','''package org.telegram.ui.ActionBar;public class ActionBarMenuItem{public static class ActionBarMenuItemSearchListener{public void onTextChanged(android.widget.EditText e){}public void onSearchCollapse(){}}public ActionBarMenuItem setIsSearchField(boolean v){return this;}public ActionBarMenuItem setActionBarMenuItemSearchListener(ActionBarMenuItemSearchListener l){return this;}public void setSearchFieldHint(String s){}}''')
 emit('org/telegram/ui/ActionBar/AlertDialog.java','''package org.telegram.ui.ActionBar;import android.content.*;public class AlertDialog {public static class Builder{public Builder(Context c,Theme.ResourcesProvider p){}public Builder setTitle(String s){return this;}public Builder setMessage(String s){return this;}public Builder setPositiveButton(String s,DialogInterface.OnClickListener l){return this;}public Builder setNeutralButton(String s,DialogInterface.OnClickListener l){return this;}public Builder setNegativeButton(String s,DialogInterface.OnClickListener l){return this;}public AlertDialog create(){return new AlertDialog();}}}''')
 emit('org/telegram/ui/ActionBar/BaseFragment.java','''package org.telegram.ui.ActionBar;public class BaseFragment{public static android.app.Activity activity;public BaseFragment opened;public int currentAccount;public ActionBar actionBar;public boolean onFragmentCreate(){return true;}public android.content.Context getParentActivity(){return activity;}public Theme.ResourcesProvider getResourceProvider(){return null;}public void presentFragment(BaseFragment f){opened=f;}public void showDialog(AlertDialog d){}public void saveSelfArgs(android.os.Bundle b){}public void restoreSelfArgs(android.os.Bundle b){}}''')
 emit('androidx/recyclerview/widget/RecyclerView.java','''package androidx.recyclerview.widget;import android.view.*;public class RecyclerView{public static class LayoutParams extends ViewGroup.LayoutParams{public LayoutParams(int w,int h){super(w,h);}}public static class ViewHolder{public final View itemView;public int position,type;public ViewHolder(View v){itemView=v;}public int getItemViewType(){return type;}public int getAdapterPosition(){return position;}}}''')
 emit('androidx/core/graphics/ColorUtils.java','package androidx.core.graphics;public class ColorUtils{public static int blendARGB(int a,int b,float t){return android.graphics.Color.argb(255,Math.round(android.graphics.Color.red(a)*(1-t)+android.graphics.Color.red(b)*t),Math.round(android.graphics.Color.green(a)*(1-t)+android.graphics.Color.green(b)*t),Math.round(android.graphics.Color.blue(a)*(1-t)+android.graphics.Color.blue(b)*t));}}')
 emit('org/telegram/ui/Components/RecyclerListView.java','''package org.telegram.ui.Components;import android.content.*;import android.view.*;import android.widget.*;import androidx.recyclerview.widget.RecyclerView;public class RecyclerListView extends LinearLayout {public static final int TAG_NOT_SECTION=12;public static class Holder extends RecyclerView.ViewHolder{public Holder(View v){super(v);}}public RecyclerListView(Context c){super(c);setOrientation(VERTICAL);setPadding(16,0,16,16);}public void setItemAnimator(Object a){}public void setSections(int a,int b,boolean c){}public void invalidateViews(){invalidate();}}''')
 # A minimal host copies the EXACT production row allocation methods, rather than a parallel model.
 base=(J/'tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java').read_text()
 def method(start):
  a=base.index(start);b=base.index('{',a);depth=1;i=b+1
  while depth:
   if base[i]=='{':depth+=1
   if base[i]=='}':depth-=1
   i+=1
  return base[a:i]
 rowmethods='\n'.join(method(x)for x in ['protected int addRow()','protected int addRow(String... keys)','protected void updateRows()'])
 emit('tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java','''package tw.nekomimi.nekogram.settings;
import android.content.*;import android.view.*;import android.widget.*;import androidx.recyclerview.widget.RecyclerView;import org.telegram.ui.ActionBar.*;import org.telegram.ui.Components.*;import org.telegram.messenger.*;import java.util.*;
public abstract class BaseNekoSettingsActivity extends BaseFragment{
 protected int rowCount;protected HashMap<String,Integer>rowMap=new HashMap<>();protected HashMap<Integer,String>rowMapReverse=new HashMap<>();protected RecyclerListView listView;protected BaseListAdapter listAdapter;protected Theme.ResourcesProvider resourcesProvider;
 private app.flexygram.settings.signature.Settings2Policy.Rows signatureRows;private int signatureTitle;
 public final void useSignatureSettingsPage(String source,String route,int title){signatureRows=new app.flexygram.settings.signature.Settings2Policy.Rows(source,route);signatureTitle=title;}
 protected String getActionBarTitle(){return "";}protected String getKey(){return null;}public int getSearchGuid(){return 0;}public String getSearchPrefix(){return null;}
 protected abstract BaseListAdapter createAdapter(Context c);protected abstract void onItemClick(View v,int p,float x,float y);
 public final void click(int p){onItemClick(null,p,0,0);}public final int count(){return rowCount;}public Map<String,Integer> rowKeys(){return rowMap;}
 @Override public boolean onFragmentCreate(){updateRows();return true;}
 public View createView(Context c){actionBar=new ActionBar(c);actionBar.setTitle(signatureTitle!=0?LocaleController.getString(signatureTitle):getActionBarTitle());listView=new RecyclerListView(c);listAdapter=createAdapter(c);render();return listView;}
 public void render(){listView.removeAllViews();for(int i=0;i<rowCount;i++){int type=listAdapter.getItemViewType(i);RecyclerView.ViewHolder h=listAdapter.onCreateViewHolder(listView,type);h.position=i;h.type=type;listAdapter.onBindViewHolder(h,i,false);if(h.itemView instanceof app.flexygram.settings.signature.Settings2Cell){android.graphics.drawable.GradientDrawable d=new android.graphics.drawable.GradientDrawable();d.setColor(getThemedColor(Theme.key_windowBackgroundWhite));boolean top=i==0||listAdapter.getItemViewType(i-1)!=type,bottom=i+1==rowCount||listAdapter.getItemViewType(i+1)!=type;d.setCornerRadii(new float[]{top?16:0,top?16:0,top?16:0,top?16:0,bottom?16:0,bottom?16:0,bottom?16:0,bottom?16:0});h.itemView.setBackground(d);}listView.addView(h.itemView,new LinearLayout.LayoutParams(-1,-2));}}
 protected int getThemedColor(int key){return Theme.getColor(key);}protected static final int TYPE_HEADER=4,TYPE_CHECK=3,TYPE_SHADOW=1,TYPE_SETTINGS=2;
 protected abstract class BaseListAdapter{protected final Context mContext;protected BaseListAdapter(Context c){mContext=c;}public int getItemViewType(int p){return 2;}public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup p,int type){return new RecyclerListView.Holder(type==4?new tw.nekomimi.nekogram.ui.cells.HeaderCell(mContext):type==3?new org.telegram.ui.Cells.TextCheckCell(mContext):new TextView(mContext));}public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){}protected boolean isSectionContent(int t){return true;}public boolean isEnabled(RecyclerView.ViewHolder h){return true;}public void notifyDataSetChanged(){if(listView!=null)render();}public void notifyItemChanged(int p){notifyDataSetChanged();}}
'''+rowmethods+'}')
 emit('app/flexygram/settings/SignatureMatteSettingsActivity.java','''package app.flexygram.settings;public abstract class SignatureMatteSettingsActivity extends tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity{protected abstract class MatteListAdapter extends BaseListAdapter{protected MatteListAdapter(android.content.Context c){super(c);}}}''')
 emit('org/telegram/ui/Cells/TextCheckCell.java','''package org.telegram.ui.Cells;public class TextCheckCell extends android.widget.TextView{public TextCheckCell(android.content.Context c){super(c);setTextSize(16);setPadding(20,16,20,16);}public void setTextAndValueAndCheck(String t,String s,boolean b,boolean m,boolean d,boolean n){setText(t+"  "+(b?"ON":"OFF")+"\\n"+s);}}''')
 emit('tw/nekomimi/nekogram/ui/cells/HeaderCell.java','''package tw.nekomimi.nekogram.ui.cells;public class HeaderCell extends android.widget.TextView{public HeaderCell(android.content.Context c){super(c);setPadding(20,24,20,12);setTextSize(13);}}''')
 emit('app/exteraless/settings/OpenExteraGeneralActivity.java','''package app.exteraless.settings;import android.content.*;import android.view.*;import android.widget.*;import androidx.recyclerview.widget.RecyclerView;import org.telegram.ui.Components.RecyclerListView;public class OpenExteraGeneralActivity extends app.flexygram.settings.SignatureMatteSettingsActivity{
 protected void updateRows(){super.updateRows();addRow("storageHeader");addRow("savePath");addRow("saveToChatSubfolder");addRow();}
 protected BaseListAdapter createAdapter(Context c){return new MatteListAdapter(c){public int getItemViewType(int p){return p==0?TYPE_HEADER:TYPE_SETTINGS;}public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){((TextView)h.itemView).setText(p==0?"Almacenamiento":p==1?"Ruta personalizada de guardado":"Guardar en subcarpetas por chat");}};}protected void onItemClick(View v,int p,float x,float y){}
}''')
 for cls in ['OpenExteraAppearanceActivity','OpenExteraOtherActivity','OpenExteraAyuMomentsActivity']:
  emit('app/exteraless/settings/'+cls+'.java','package app.exteraless.settings;public class '+cls+' extends OpenExteraGeneralActivity{}')
 emit('app/exteraless/settings/OpenExteraChatsActivity.java','package app.exteraless.settings;public class OpenExteraChatsActivity extends OpenExteraGeneralActivity{public static final int SCREEN_CHATS=0,SCREEN_MENUS=1,SCREEN_MEDIA=2,SCREEN_HIDING=3,SCREEN_SIGNATURE_MESSAGES=4,SCREEN_SIGNATURE_STICKERS=5;public OpenExteraChatsActivity(int s){}}')
 targets={'app/exteraless/settings/OpenExteraAppNavigationActivity':'','app/exteraless/settings/OpenExteraCloudActivity':'','org/telegram/ui/PrivacySettingsActivity':'','app/flexygram/bubbles/BubbleSettingsActivity':'','app/flexygram/header/HeaderSettingsActivity':'','app/flexygram/composer/FlexyComposerSettingsActivity':'','app/flexygram/navigation/BottomTabsSettingsActivity':'','app/flexygram/bubbles/interaction/BubbleInteractionSettingsActivity':'','app/exteraless/plugins/ui/PluginsActivity':'','app/exteraless/ai/ui/AiSettingsActivity':'','app/exteraless/pillstack/PillStackSettingsActivity':'','tw/nekomimi/nekogram/settings/NekoEmojiSettingsActivity':'','app/exteraless/icons/IconPacksActivity':'','app/flexygram/settings/SignatureChatThemeActivity':'','app/flexygram/bubbles/deletion/MessageAnimationsActivity':'public MessageAnimationsActivity(boolean b){}','tw/nekomimi/nekogram/settings/NekoPasscodeSettingsActivity':''}
 for path,body in targets.items():
  pkg,name=path.rsplit('/',1);emit(path+'.java','package '+pkg.replace('/','.')+';public class '+name+' extends org.telegram.ui.ActionBar.BaseFragment{'+body+'}')
 studio=(J/'app/flexygram/studio/FlexyStudioActivity.java').read_text()
 def extract(text,anchor):
  start=text.index(anchor);i=text.index('{',start);level=1;j=i+1
  while level:
   if text[j]=='{':level+=1
   elif text[j]=='}':level-=1
   j+=1
  return text[start:j]
 studio_ui='\n'.join(extract(studio,a)for a in ['protected String getActionBarTitle()','protected void updateRows()','public View createView(Context context)','protected BaseListAdapter createAdapter(Context context)','private final class Adapter'])
 emit('app/flexygram/studio/FlexyStudioActivity.java','package app.flexygram.studio;import static org.telegram.messenger.LocaleController.getString;import android.content.*;import android.view.*;import androidx.recyclerview.widget.RecyclerView;import app.flexygram.settings.*;import org.telegram.messenger.*;import org.telegram.ui.Components.RecyclerListView;public final class FlexyStudioActivity extends SignatureMatteSettingsActivity{private static final int NAV=110;private int header,export,importRow,share,shadow,tools,files,help,toolsShadow;protected void onItemClick(View v,int p,float x,float y){}'+studio_ui+'}')
 emit('app/flexygram/settings/SignatureNavigationCell.java','package app.flexygram.settings;public class SignatureNavigationCell extends android.widget.TextView{public SignatureNavigationCell(android.content.Context c){super(c);}public void bind(String s,int r,boolean d){setText(s);}}')
 emit('tw/nekomimi/nekogram/settings/BaseNekoXSettingsActivity.java','package tw.nekomimi.nekogram.settings;public class BaseNekoXSettingsActivity extends org.telegram.ui.ActionBar.BaseFragment{public String source,route;public void useSignatureSettingsPage(String s,String r,int t){source=s;route=r;}}')
 for cls in ['NekoGeneralSettingsActivity','NekoChatSettingsActivity','NekoExperimentalSettingsActivity','NekoTranslatorSettingsActivity']:emit('tw/nekomimi/nekogram/settings/'+cls+'.java','package tw.nekomimi.nekogram.settings;public class '+cls+' extends BaseNekoXSettingsActivity{}')
 emit('tw/nekomimi/nekogram/helpers/PasscodeHelper.java','package tw.nekomimi.nekogram.helpers;public class PasscodeHelper{public static boolean hidden;public static boolean isSettingsHidden(){return hidden;}}')
 emit('org/telegram/ui/Cells/AppIconsSelectorCell.java','package org.telegram.ui.Cells;public class AppIconsSelectorCell extends android.widget.TextView{public AppIconsSelectorCell(android.content.Context c,org.telegram.ui.ActionBar.BaseFragment f,int a){super(c);setText("Native launcher icon selector (host double)");}}')
 file_source=(J/'app/flexygram/files/FlexyFiles.java').read_text()
 enabled_methods='\n'.join(re.findall(r'public static (?:boolean enabled\(\)|void enabled\(boolean value\)) \{[^\n]+',file_source))
 emit('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}')
 emit('app/flexygram/files/FlexyFiles.java','package app.flexygram.files;import android.content.Context;import org.telegram.messenger.ApplicationLoader;public class FlexyFiles{'+enabled_methods+'}')
 for cls,body in [('AbstractConfigCell',''),('ConfigCellHeader',''),('ConfigCellDivider','')]:emit('tw/nekomimi/nekogram/config/cell/'+cls+'.java','package tw.nekomimi.nekogram.config.cell;public '+('abstract 'if cls=='AbstractConfigCell'else'')+'class '+cls+(''if cls=='AbstractConfigCell'else' extends AbstractConfigCell')+'{'+body+'}')
 emit('tw/nekomimi/nekogram/config/cell/WithKey.java',(J/'tw/nekomimi/nekogram/config/cell/WithKey.java').read_text())
 emit('tw/nekomimi/nekogram/config/ConfigItem.java',(J/'tw/nekomimi/nekogram/config/ConfigItem.java').read_text())
 emit('tw/nekomimi/nekogram/NekoConfig.java','package tw.nekomimi.nekogram;public class NekoConfig{public static Object sync=new Object();public static android.content.SharedPreferences getPreferences(){return org.telegram.ui.ActionBar.BaseFragment.activity.getSharedPreferences("isolated_settings2",0);}}')
 emit('org/telegram/messenger/FileLog.java','package org.telegram.messenger;public class FileLog{public static void e(Exception e){throw new AssertionError(e);}}')


def resources(root,out):
    folder=root/'TMessagesProj/src/main/java/app/flexygram/settings/signature'
    source='\n'.join(p.read_text()for p in folder.glob('*.java'))+'\n'+(root/'TMessagesProj/src/main/java/app/flexygram/studio/FlexyStudioActivity.java').read_text()
    names=set(re.findall(r'R.string.(\w+)',source));icons=set(re.findall(r'R.drawable.(\w+)',source))
    values=ET.Element('resources')
    found={}
    for directory in ['values','values-es']:
      for p in (root/'TMessagesProj/src/main/res'/directory).glob('*.xml'):
        try:
          for x in ET.parse(p).getroot().findall('string'):
            if x.get('name')in names:found[x.get('name')]=x
        except ET.ParseError:pass
    for n in sorted(names):
      if n not in found:raise ValueError('Unknown production string '+n)
      values.append(found[n])
    (out.parent/'values').mkdir(exist_ok=True)
    ET.ElementTree(values).write(out.parent/'values/strings.xml',encoding='utf-8',xml_declaration=True)
    for n in sorted(icons):
      candidates=[p for d in ['drawable','drawable-mdpi'] for p in (root/'TMessagesProj/src/main/res'/d).glob(n+'.*')]
      if not candidates:raise ValueError('Unknown production icon '+n)
      shutil.copyfile(candidates[0],out/candidates[0].name)
