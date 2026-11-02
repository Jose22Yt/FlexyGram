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
 old.write(dest,root);J=root/'TMessagesProj/src/main/java'
 def emit(path,text):
  p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 for path in ['app/flexygram/effects/GlareMode.java','app/flexygram/effects/GlareSettingsSection.java','org/telegram/ui/Components/blur3/StaticOutlineStroke.java','org/telegram/ui/Components/blur3/GlassOutlineStyle.java']:
  emit(path,(J/path).read_text())
 # Link new production string IDs into the same real resource APK.
 dump=subprocess.check_output([str(Path(os.environ['SETTINGS2_SDK_ROOT'])/'build-tools/36.0.0/aapt2'),'dump','resources',str(dest.parents[2]/'resources.ap_')],text=True)
 ids={m[2]:int(m[1],16)for m in re.finditer(r'resource (0x[0-9a-f]+) (?:[^: ]+:)?string/(FlexyGlare\w+)',dump)}
 p=dest/'org/telegram/messenger/R.java';s=p.read_text().replace('public static class string{','public static class string{'+''.join('public static final int '+n+'='+str(v)+';'for n,v in ids.items()));p.write_text(s)
 p=dest/'org/telegram/messenger/LocaleController.java';s=p.read_text();texts={x.get('name'):x.text for x in E.parse(root/'TMessagesProj/src/main/res/values-es/flexy_glare.xml').getroot()};s=s.replace('return switch(id){','return switch(id){'+''.join('case '+str(v)+'->'+json.dumps(texts[n])+';'for n,v in ids.items()));p.write_text(s)
 p=dest/'org/telegram/messenger/AndroidUtilities.java';s=p.read_text().replace('public static int dp(float v)','public static float dpf2(float v){return v;}public static int dp(float v)');p.write_text(s)
 p=dest/'org/telegram/ui/Cells/TextSettingsCell.java';s=p.read_text().replace('public void setText(String s,boolean d)','public void setTextAndValue(String s,String value,boolean d){setText(s+" · "+value);}public void setText(String s,boolean d)');p.write_text(s)
 p=dest/'tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java';s=p.read_text().replace('public int getSearchGuid()', 'public int getSearchIcon(){return 0;}public int getSearchGuid()');p.write_text(s)
 # Same original key and changed-only dispatch shape, backed by the original Java ConfigItem.
 emit('app/exteraless/appearance/AppearanceConfig.java','''package app.exteraless.appearance;import tw.nekomimi.nekogram.config.ConfigItem;public class AppearanceConfig{public static final ConfigItem glassOutlineStyle=new ConfigItem("OEAppearanceGlassOutlineStyle",ConfigItem.configTypeInt,0){public void setConfigInt(int v){boolean change=Int()!=v;super.setConfigInt(v);if(change)org.telegram.ui.Components.blur3.GlassOutlineStyle.dispatchChange();}};public static int glassOutlineStyle(){return glassOutlineStyle.Int();}}''')
 emit('org/telegram/ui/Components/AlertsCreator.java','''package org.telegram.ui.Components;public class AlertsCreator{public static int selected;public static String[] options;public static android.content.DialogInterface.OnClickListener listener;public static android.app.Dialog createSingleChoiceDialog(android.app.Activity c,String[] values,String title,int checked,android.content.DialogInterface.OnClickListener l){selected=checked;options=values;listener=l;return new android.app.Dialog(c);}}''')
 p=dest/'org/telegram/ui/ActionBar/BaseFragment.java';s=p.read_text().replace('public android.content.Context getParentActivity()','public android.app.Activity getParentActivity()').replace('public void showDialog(AlertDialog d){}','public void showDialog(AlertDialog d){}public void showDialog(android.app.Dialog d){}');p.write_text(s)
 # Extract all three EXISTING public static draw overloads verbatim from production.
 body=(J/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java').read_text()
 anchors=['public static void drawStroke(\n','public static void drawStroke(Canvas canvas, RectF rect,','public static void drawStroke(Canvas canvas, float left, float top, float right, float bottom,']
 methods='\n'.join(method(body,a)for a in anchors)
 emit('org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java','package org.telegram.ui.Components.blur3.drawable;import android.graphics.*;import androidx.core.math.MathUtils;import org.telegram.ui.Components.blur3.GlassOutlineStyle;public class BlurredBackgroundDrawable{'+methods+'}')

 # Historical static implementation for pixel-identical default-mode regression.
 baseline=subprocess.check_output(['git','show','4679f74ebd312acc4968dd2e044a6c6b7478445a:TMessagesProj/src/main/java/org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java'],cwd=root,text=True)
 emit('org/telegram/ui/Components/blur3/drawable/BaselineStroke.java','package org.telegram.ui.Components.blur3.drawable;import android.graphics.*;import androidx.core.math.MathUtils;import org.telegram.ui.Components.blur3.GlassOutlineStyle;public class BaselineStroke{'+ '\n'.join(method(baseline,a)for a in anchors)+'}')
