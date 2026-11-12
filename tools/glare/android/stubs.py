"""Explicit host doubles; actual new Java and actual existing blur3 static methods are compiled.
AppearanceConfig is a bridge double using the ORIGINAL ConfigItem implementation and stored key.
The real Kotlin object and full BlurredBackgroundDrawable engine are not integration-compiled.
"""
from pathlib import Path
import importlib.util,xml.etree.ElementTree as E,re,subprocess,json,os
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('settings3_glare_hosts',ROOT/'tools/settings3/android/stubs.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def resources(root,out):
 old.resources(root,out)
 values=out.parent/'values/strings.xml';r=E.parse(values).getroot()
 for x in E.parse(root/'TMessagesProj/src/main/res/values-es/flexy_glare.xml').getroot():r.append(x)
 E.ElementTree(r).write(values,encoding='utf-8',xml_declaration=True)
def method(text,anchor):
 a=text.index(anchor);i=text.index('{',a)+1;level=1;j=i
 while level:
  level+=(text[j]=='{')-(text[j]=='}');j+=1
 return text[a:j]
def write(dest,root):
 J=root/'TMessagesProj/src/main/java'
 def emit(path,text):
  p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 for path in ['app/flexygram/effects/GlareMode.java','app/flexygram/effects/GlareSettingsSection.java','org/telegram/ui/Components/blur3/StaticOutlineStroke.java','org/telegram/ui/Components/blur3/GlareStrokeWidth.java','org/telegram/ui/Components/blur3/MicroContourStroke.java','org/telegram/ui/Components/blur3/GlassOutlineStyle.java','org/telegram/ui/Components/blur3/StrokeDrawable.java','tw/nekomimi/nekogram/config/ConfigItem.java']:
  emit(path,(J/path).read_text())
 emit('androidx/recyclerview/widget/RecyclerView.java','''package androidx.recyclerview.widget;
public class RecyclerView extends android.view.ViewGroup {
 public RecyclerView(android.content.Context c){super(c);}public void setAdapter(Adapter a){}
 protected void onLayout(boolean changed,int l,int t,int r,int b){}
 public abstract static class ViewHolder{public final android.view.View itemView;public ViewHolder(android.view.View v){itemView=v;}public int getItemViewType(){return 1;}}
 public abstract static class Adapter<T extends ViewHolder>{public abstract int getItemCount();public abstract T onCreateViewHolder(android.view.ViewGroup p,int t);public abstract void onBindViewHolder(T h,int p);public int getItemViewType(int p){return 0;}public void notifyDataSetChanged(){}public void notifyItemChanged(int p){}}
}''')
 emit('org/telegram/messenger/R.java','package org.telegram.messenger;public class R{public static class string{}public static class drawable{public static final int settings3_sliders=android.R.drawable.ic_menu_preferences;}}')
 emit('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}')
 emit('org/telegram/messenger/FileLog.java','package org.telegram.messenger;public class FileLog{public static void e(Throwable e){}}')
 emit('org/telegram/messenger/AndroidUtilities.java','package org.telegram.messenger;public class AndroidUtilities{public static float dpf2(float v){return v;}public static int dp(float v){return (int)Math.ceil(v);}}')
 emit('tw/nekomimi/nekogram/NekoConfig.java','package tw.nekomimi.nekogram;public class NekoConfig{public static final Object sync=new Object();public static android.content.SharedPreferences getPreferences(){return org.telegram.messenger.ApplicationLoader.applicationContext.getSharedPreferences("glare-test",0);}}')
 emit('org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController{public static String getString(int id){return switch(id){default->"";};}}')
 emit('org/telegram/ui/ActionBar/Theme.java','package org.telegram.ui.ActionBar;public class Theme{public static final int key_windowBackgroundWhite=1;public static int getColor(int key){return 0xffffffff;}public static int multAlpha(int c,float a){return(c&0xffffff)|((int)((c>>>24)*a)<<24);}}')
 emit('org/telegram/ui/ActionBar/BaseFragment.java','package org.telegram.ui.ActionBar;public class BaseFragment{public static android.app.Activity activity;public android.app.Activity getParentActivity(){return activity;}public void showDialog(android.app.Dialog d){}}')
 emit('tw/nekomimi/nekogram/ui/cells/HeaderCell.java','package tw.nekomimi.nekogram.ui.cells;public class HeaderCell extends android.widget.TextView{public HeaderCell(android.content.Context c){super(c);}}')
 emit('org/telegram/ui/Cells/TextSettingsCell.java','package org.telegram.ui.Cells;public class TextSettingsCell extends android.widget.TextView{public TextSettingsCell(android.content.Context c){super(c);}public void setTextAndValue(String s,String v,boolean d){setText(s+" · "+v);}}')
 emit('app/flexygram/settings/SignatureMatteSettingsActivity.java','''package app.flexygram.settings;
import android.content.*;import android.view.*;import androidx.recyclerview.widget.*;
public abstract class SignatureMatteSettingsActivity extends org.telegram.ui.ActionBar.BaseFragment{
 protected static final int TYPE_HEADER=0,TYPE_SETTINGS=1;protected BaseListAdapter listAdapter;protected RecyclerView listView;protected Object resourcesProvider;
 private final java.util.Map<String,Integer> rows=new java.util.LinkedHashMap<>();
 protected abstract String getActionBarTitle();protected abstract String getKey();public abstract int getSearchGuid();public abstract int getSearchIcon();public abstract String getSearchPrefix();
 protected void updateRows(){rows.clear();}protected int addRow(){return addRow("preview");}protected int addRow(String k){int n=rows.size();rows.put(k,n);return n;}
 public java.util.Map<String,Integer> rowKeys(){return rows;}public boolean onFragmentCreate(){updateRows();return true;}
 public View createView(Context c){listView=new RecyclerView(c);listAdapter=createAdapter(c);listView.setAdapter(listAdapter);return listView;}
 public void click(int p){onItemClick(null,p,0,0);}protected abstract void onItemClick(View v,int p,float x,float y);
 protected abstract BaseListAdapter createAdapter(Context c);
 protected abstract class BaseListAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder>{
  final Context context;BaseListAdapter(Context c){context=c;}protected boolean isSectionContent(int t){return true;}public boolean isEnabled(RecyclerView.ViewHolder h){return true;}public int getItemCount(){return rows.size();}
  public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup p,int type){return new RecyclerView.ViewHolder(type==0?new tw.nekomimi.nekogram.ui.cells.HeaderCell(context):new org.telegram.ui.Cells.TextSettingsCell(context)){};}
  public void onBindViewHolder(RecyclerView.ViewHolder h,int p){onBindViewHolder(h,p,false);}
  public abstract void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial);
 }
 protected abstract class MatteListAdapter extends BaseListAdapter{protected MatteListAdapter(Context c){super(c);}}
}''')
 emit('org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundColorProvider.java',(J/'org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundColorProvider.java').read_text())
 # Default provider divider is a native-theme host double.
 p=dest/'org/telegram/ui/ActionBar/Theme.java';p.write_text(p.read_text().replace('public static int getColor(', 'public static int getDividerColor(Object p){return 0xff888888;}public static int getColor('))
 # Link new production string IDs into the same real resource APK.
 dump=subprocess.check_output([str(Path(os.environ['SETTINGS2_SDK_ROOT'])/'build-tools/36.0.0/aapt2'),'dump','resources',str(dest.parents[2]/'resources.ap_')],text=True)
 ids={m[2]:int(m[1],16)for m in re.finditer(r'resource (0x[0-9a-f]+) (?:[^: ]+:)?string/(FlexyGlare\w+)',dump)}
 p=dest/'org/telegram/messenger/R.java';s=p.read_text().replace('public static class string{','public static class string{'+''.join('public static final int '+n+'='+str(v)+';'for n,v in ids.items()));p.write_text(s)
 p=dest/'org/telegram/messenger/LocaleController.java';s=p.read_text();texts={x.get('name'):x.text for x in E.parse(root/'TMessagesProj/src/main/res/values-es/flexy_glare.xml').getroot()};s=s.replace('return switch(id){','return switch(id){'+''.join('case '+str(v)+'->'+json.dumps(texts[n])+';'for n,v in ids.items()));p.write_text(s)
 # Same original key and changed-only dispatch shape, backed by the original Java ConfigItem.
 emit('app/exteraless/appearance/AppearanceConfig.java','''package app.exteraless.appearance;import tw.nekomimi.nekogram.config.ConfigItem;public class AppearanceConfig{public static final ConfigItem glassOutlineStyle=new ConfigItem("OEAppearanceGlassOutlineStyle",ConfigItem.configTypeInt,0){public void setConfigInt(int v){boolean change=Int()!=v;super.setConfigInt(v);if(change)org.telegram.ui.Components.blur3.GlassOutlineStyle.dispatchChange();}};public static int glassOutlineStyle(){return glassOutlineStyle.Int();}}''')
 emit('org/telegram/ui/Components/AlertsCreator.java','''package org.telegram.ui.Components;public class AlertsCreator{public static int selected;public static String[] options;public static android.content.DialogInterface.OnClickListener listener;public static android.app.Dialog createSingleChoiceDialog(android.app.Activity c,String[] values,String title,int checked,android.content.DialogInterface.OnClickListener l){selected=checked;options=values;listener=l;return new android.app.Dialog(c);}}''')
 # Extract all three EXISTING public static draw overloads verbatim from production.
 body=(J/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java').read_text()
 anchors=['public static void drawStroke(Canvas canvas, float left, float top, float right, float bottom, float radii,','public static void drawStroke(Canvas canvas, float left, float top, float right, float bottom, float[] radii,','public static void drawStroke(Canvas canvas, RectF rect,','protected static void drawStrokeRaw(\n','protected static void drawStrokeRaw(Canvas canvas, float left, float top, float right, float bottom,']
 methods='\n'.join(method(body,a)for a in anchors)
 emit('org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java','package org.telegram.ui.Components.blur3.drawable;import android.graphics.*;import androidx.core.math.MathUtils;import org.telegram.ui.Components.blur3.GlassOutlineStyle;public class BlurredBackgroundDrawable{'+methods+'}')

 # Historical static implementation for pixel-identical default-mode regression.
 baseline=subprocess.check_output(['git','show','4679f74ebd312acc4968dd2e044a6c6b7478445a:TMessagesProj/src/main/java/org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java'],cwd=root,text=True)
 emit('org/telegram/ui/Components/blur3/drawable/BaselineStroke.java','package org.telegram.ui.Components.blur3.drawable;import android.graphics.*;import androidx.core.math.MathUtils;import org.telegram.ui.Components.blur3.GlassOutlineStyle;public class BaselineStroke{'+ '\n'.join(method(baseline,a)for a in ['public static void drawStroke(\n','public static void drawStroke(Canvas canvas, RectF rect,','public static void drawStroke(Canvas canvas, float left, float top, float right, float bottom,'])+'}')
