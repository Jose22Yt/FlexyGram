"""Production menu/settings/config/physics, with explicit Telegram navigation/theme hosts only."""
import json,re
from pathlib import Path
from xml.etree import ElementTree as E

def write(dest,root):
 def put(name,source):
  path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source)
 java=root/'TMessagesProj/src/main/java'
 names=['BubbleActionPanelView','BubbleMenuConfig','BubbleMenuIcon','BubbleMenuGallery','BubbleInteractionSettings','BubbleInteractionSettingsActivity','BubbleTapMotion','SelectedBubbleMotion','DampedSpringCurve','ContextPreviewPlacement']
 sources=[]
 for name in names:
  source=(java/'app/flexygram/bubbles/interaction'/(name+'.java')).read_text();sources.append(source);put('app/flexygram/bubbles/interaction/'+name+'.java',source)
 for path in ['app/flexygram/animation/FastMotionTiming.java','app/exteraless/player/Spring.java']:
  source=(java/path).read_text();sources.append(source);put(path,source)
 keys=sorted(set(re.findall(r'R.string.(\w+)', '\n'.join(sources))))
 values={}
 for path in (root/'TMessagesProj/src/main/res/values').glob('*.xml'):
  for item in E.parse(path).getroot():
   if item.tag=='string':values[item.attrib['name']]=''.join(item.itertext())
 missing=set(keys)-values.keys()
 if missing:raise AssertionError('Missing production string resources: '+str(missing))
 put('org/telegram/messenger/R.java','package org.telegram.messenger;public class R{public static class string{'+''.join('public static final int '+k+'='+str(i+1)+';'for i,k in enumerate(keys))+'}}')
 put('org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController{public static boolean isRTL;public static String getString(int id){switch(id){'+''.join('case '+str(i+1)+':return '+json.dumps(values[k],ensure_ascii=True)+';'for i,k in enumerate(keys))+'default:throw new IllegalArgumentException();}}}')
 theme_keys=sorted(set(re.findall(r'Theme.(key_\w+)','\n'.join(sources))))
 put('org/telegram/ui/ActionBar/Theme.java','''package org.telegram.ui.ActionBar;public class Theme{public interface ResourcesProvider{}public static boolean dark;
 KEYS public static int getColor(int key){return getColor(key,null);}public static int getColor(int key,ResourcesProvider provider){
 if(key==key_text_RedRegular)return 0xffdc2626;if(key==key_windowBackgroundWhiteBlueText)return 0xff258ce6;
 if(key==key_actionBarDefaultSubmenuBackground)return dark?0xff263240:0xffffffff;
 if(key==key_windowBackgroundGray)return dark?0xff15202c:0xffeff0f4;
 if(key==key_divider)return dark?0xff465260:0xffd8dce2;
 return dark?0xfff1f4f7:0xff182220;}}
 '''.replace('KEYS',''.join('public static final int '+k+'='+str(i+1)+';'for i,k in enumerate(theme_keys))))
 put('org/telegram/messenger/SharedConfig.java','package org.telegram.messenger;public class SharedConfig{public static boolean animationsEnabled(){return true;}}')
 put('org/telegram/messenger/AndroidUtilities.java','package org.telegram.messenger;public class AndroidUtilities{public static boolean isAccessibilityScreenReaderEnabled(){return false;}public static android.graphics.Typeface bold(){return android.graphics.Typeface.create("sans-serif-medium",0);}}')
 put('androidx/recyclerview/widget/RecyclerView.java','package androidx.recyclerview.widget;public class RecyclerView{public static class ViewHolder{public android.view.View itemView;public int position;public ViewHolder(android.view.View view){itemView=view;}}}')
 put('org/telegram/ui/Components/RecyclerListView.java','package org.telegram.ui.Components;public class RecyclerListView{public static class Holder extends androidx.recyclerview.widget.RecyclerView.ViewHolder{public Holder(android.view.View v){super(v);}}}')
 put('org/telegram/ui/Cells/TextSettingsCell.java','package org.telegram.ui.Cells;public class TextSettingsCell extends android.widget.TextView{public TextSettingsCell(android.content.Context c){super(c);}public void setTextAndValue(String text,String value,boolean divider){setText(text+" "+value);}}')
 put('org/telegram/ui/Cells/TextInfoPrivacyCell.java','package org.telegram.ui.Cells;public class TextInfoPrivacyCell extends android.widget.TextView{public TextInfoPrivacyCell(android.content.Context c){super(c);}}')
 put('org/telegram/ui/ActionBar/AlertDialog.java','''package org.telegram.ui.ActionBar;import android.content.*;public class AlertDialog{public static class Builder{
 private final android.app.AlertDialog.Builder builder;public Builder(Context c,Theme.ResourcesProvider p){builder=new android.app.AlertDialog.Builder(c);}
 public Builder setTitle(String text){builder.setTitle(text);return this;}public Builder setView(android.view.View v){builder.setView(v);return this;}
 public Builder setItems(String[] items,DialogInterface.OnClickListener listener){builder.setItems(items,listener);return this;}
 public Builder setPositiveButton(String text,DialogInterface.OnClickListener listener){builder.setPositiveButton(text,listener);return this;}
 public Builder setNegativeButton(String text,DialogInterface.OnClickListener listener){builder.setNegativeButton(text,listener);return this;}
 public Builder setNeutralButton(String text,DialogInterface.OnClickListener listener){builder.setNeutralButton(text,listener);return this;}
 public android.app.AlertDialog create(){return builder.create();}}}''')
 put('app/flexygram/settings/SignatureMatteSettingsActivity.java','''package app.flexygram.settings;import android.view.*;import android.content.*;import android.widget.*;import androidx.recyclerview.widget.RecyclerView;import org.telegram.ui.ActionBar.Theme;
 public abstract class SignatureMatteSettingsActivity{public static android.app.Activity activity;public android.app.AlertDialog dialog;protected Theme.ResourcesProvider resourcesProvider;
 protected static final int TYPE_SETTINGS=1,TYPE_INFO_PRIVACY=2;protected int rows;protected BaseListAdapter listAdapter;protected LinearLayout listView;
 protected void updateRows(){rows=0;}protected int addRow(){return rows++;}protected int addRow(String key){return addRow();}
 protected abstract String getActionBarTitle();protected abstract BaseListAdapter createAdapter(Context c);protected abstract void onItemClick(View v,int p,float x,float y);
 public View createView(Context c){updateRows();listView=new LinearLayout(c);listView.setOrientation(1);listAdapter=createAdapter(c);render();return listView;}
 private void render(){listView.removeAllViews();for(int i=0;i<rows;i++){RecyclerView.ViewHolder h=listAdapter.onCreateViewHolder(listView,listAdapter.getItemViewType(i));h.position=i;listAdapter.onBindViewHolder(h,i,false);listView.addView(h.itemView,new LinearLayout.LayoutParams(-1,-2));}}
 public void click(int p){onItemClick(null,p,0,0);}public android.app.Activity getParentActivity(){return activity;}public Theme.ResourcesProvider getResourceProvider(){return resourcesProvider;}
 protected int getThemedColor(int key){return Theme.getColor(key);}protected int settingsRowPosition(RecyclerView.ViewHolder h){return h.position;}public void onResume(){}
 protected void showDialog(android.app.AlertDialog value){dialog=value;dialog.show();}
 protected class BaseListAdapter{public void notifyDataSetChanged(){render();}public void notifyItemChanged(int p){render();}public int getItemViewType(int p){return TYPE_SETTINGS;}
 public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){return new org.telegram.ui.Components.RecyclerListView.Holder(type==TYPE_INFO_PRIVACY?new org.telegram.ui.Cells.TextInfoPrivacyCell(parent.getContext()):new org.telegram.ui.Cells.TextSettingsCell(parent.getContext()));}
 public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){}public boolean isEnabled(RecyclerView.ViewHolder h){return true;}}
 protected class MatteListAdapter extends BaseListAdapter{public MatteListAdapter(Context c){}}}
 ''')
