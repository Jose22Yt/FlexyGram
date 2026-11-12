#!/usr/bin/env python3
"""Run isolated Android graphics/widget tests, without Gradle or an APK."""
import argparse,json,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--maven',required=True);parser.add_argument('--android-jar',required=True);parser.add_argument('--runtime-aar',type=Path,required=True);opt=parser.parse_args()
 out=opt.output;source=out/'src/test/java';source.mkdir(parents=True,exist_ok=True)
 def write(name,text):
  p=source/(name.replace('.','/')+'.java');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 files=['DuotoneSettingsIcon','SettingsTheme','SettingsCategoryIcon','SettingsCardStyle','Settings2Cell']
 for name in files:write('app.flexygram.settings.signature.'+name,(ROOT/f'TMessagesProj/src/main/java/app/flexygram/settings/signature/{name}.java').read_text())
 write('app.exteraless.settings.utils.SettingsIcons',(ROOT/'TMessagesProj/src/main/java/app/exteraless/settings/utils/SettingsIcons.java').read_text())
 text='\n'.join(p.read_text() for p in source.rglob('*.java'))
 keys=sorted(set(re.findall(r'Theme\.(key_\w+)',text)))
 write('org.telegram.ui.ActionBar.Theme','''package org.telegram.ui.ActionBar;
import android.graphics.*;import android.graphics.drawable.*;
public class Theme {
 public static boolean dark=true;public static int accent=0xff93bb6d;
 public interface ResourcesProvider {int getColor(int k);default boolean isDark(){return dark;}default int getCurrentColor(int k){return getColor(k);}default void setAnimatedColor(int k,int c){}default Drawable getDrawable(String k){return null;}default Paint getPaint(String k){return null;}default boolean hasGradientService(){return false;}default void applyServiceShaderMatrix(int w,int h,float x,float y){}default ColorFilter getAnimatedEmojiColorFilter(){return null;}}
 KEYS
 public static boolean isCurrentThemeDark(){return dark;}
 public static ColorFilter chat_animatedEmojiTextColorFilter;
 public static int getColor(int k,ResourcesProvider p){if(p!=null)return p.getColor(k);if(k==key_windowBackgroundWhiteBlueHeader)return accent;if(k==key_windowBackgroundWhiteBlackText)return dark?0xffffffff:0xff000000;if(k==key_windowBackgroundGray)return dark?0xff151515:0xffeeeeee;if(k==key_windowBackgroundWhite)return dark?0xff000000:0xffffffff;return 0xff777777;}
 public static Paint getThemePaint(String k){return new Paint();} public static void applyServiceShaderMatrix(int w,int h,float x,float y){}
}'''.replace('KEYS',''.join('public static final int '+k+'='+str(i+1)+';' for i,k in enumerate(keys))))
 assets=json.loads((ROOT/'tools/settings_monet/approved_assets.json').read_text());entries={kind:sorted(set(re.findall(r'R\.'+kind+r'\.(\w+)',text))) for kind in ['drawable','raw']}
 write('org.telegram.messenger.R','package org.telegram.messenger;public class R{'+''.join('public static class '+kind+'{'+''.join('public static int '+name+'='+str((i+1)+(1000 if kind=='raw' else 100))+';' for i,name in enumerate(names))+'}' for kind,names in entries.items())+'}')
 write('org.telegram.messenger.AndroidUtilities','package org.telegram.messenger;public class AndroidUtilities{public static int dp(float v){return Math.round(v);}public static android.graphics.Typeface regular(){return android.graphics.Typeface.DEFAULT;}public static android.graphics.Typeface bold(){return android.graphics.Typeface.DEFAULT_BOLD;}}')
 write('org.telegram.messenger.LocaleController','package org.telegram.messenger;public class LocaleController{public static boolean isRTL=false;}')
 write('app.flexygram.icons.IconPressFeedback','package app.flexygram.icons;public class IconPressFeedback{public interface Target{void setIconPressScale(float scale);}}')
 write('org.telegram.ui.ActionBar.ActionBar','package org.telegram.ui.ActionBar;public class ActionBar extends android.view.View{public ActionBar(android.content.Context c){super(c);}public void setItemsColor(int c,boolean b){}public void setTitleColor(int c){}}')
 marker=re.search(r'public static final int TAG_NOT_SECTION\s*=\s*-?\d+;', (ROOT/'TMessagesProj/src/main/java/org/telegram/ui/Components/RecyclerListView.java').read_text()).group(0)
 write('org.telegram.ui.Components.RecyclerListView','package org.telegram.ui.Components;public class RecyclerListView extends android.widget.FrameLayout{MARKERpublic RecyclerListView(android.content.Context c){super(c);}public void invalidateViews(){invalidate();}}'.replace('MARKER',marker))
 write('org.telegram.ui.ActionBar.ThemeDescription','package org.telegram.ui.ActionBar;public class ThemeDescription{public interface ThemeDescriptionDelegate{void didSetColor();}public ThemeDescription(Object a,int b,Object c,Object d,Object e,ThemeDescriptionDelegate f,int key){}}')
 write('org.telegram.ui.ActionBar.BaseFragment','package org.telegram.ui.ActionBar;public class BaseFragment{public android.view.View getFragmentView(){return null;}public ActionBar getActionBar(){return null;}public Theme.ResourcesProvider getResourceProvider(){return null;}}')
 test=(ROOT/'tools/settings_monet/NativeMonetTest.java.in').read_text().replace('RAW_PATH',str(ROOT/'TMessagesProj/src/main/res/raw'))
 mappings=''.join('if(id==org.telegram.messenger.R.raw.'+x['coverage']+')return "'+x['coverage']+'.png";' for x in assets)
 names=''.join('if(id==org.telegram.messenger.R.drawable.'+name+')return "'+name+'";' for name in entries['drawable'])
 write('app.flexygram.settings.signature.NativeMonetTest',test.replace('RAW_MAPPING',mappings).replace('DRAWABLE_MAPPING',names).replace('ALL_DRAWABLES',','.join('org.telegram.messenger.R.drawable.'+x['drawable'] for x in assets)))
 pom=(ROOT/'tools/connected_alpha/bubble_visual/pom.xml').read_text().replace('<version>4.17</version>','<version>4.16</version>');(out/'pom.xml').write_text(pom)
 (out/'target/aar').mkdir(parents=True,exist_ok=True)
 for name in ['monitor.jar','espresso-idling-resource.jar']:shutil.copyfile(opt.runtime_aar/name,out/'target/aar'/name)
 subprocess.run([opt.maven,'-o','-B','-f',str(out/'pom.xml'),'-Dandroid.sdk.jar='+opt.android_jar,'test'],check=True)
if __name__=='__main__':main()
