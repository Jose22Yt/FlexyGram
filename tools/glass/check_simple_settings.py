"""Type-check the real settings and original material classes against Android API 37.
Project services are minimal doubles: this does not replace a full application build.
No Gradle tasks, packaging, signing or network access.
"""
from pathlib import Path
import argparse,os,re,shutil,subprocess,tempfile
import xml.etree.ElementTree as ET
parser=argparse.ArgumentParser(description="Type-check the simple blur settings against Android; no Gradle or APK.")
parser.add_argument('--android-jar', type=Path)
args=parser.parse_args()
sdk=os.getenv('ANDROID_HOME') or os.getenv('ANDROID_SDK_ROOT')
android_jar=args.android_jar or (Path(sdk)/'platforms/android-37.0/android.jar' if sdk else None)
if android_jar is None or not android_jar.is_file(): parser.error('Pass --android-jar or set ANDROID_HOME with API 37 installed')
javac=str(Path(os.environ['JAVA_HOME'])/'bin/javac') if os.getenv('JAVA_HOME') else shutil.which('javac')
if not javac: parser.error('A JDK is required')
root=Path(__file__).resolve().parents[2]/'TMessagesProj/src/main/java'
files=['app/flexygram/effects/GlassSettings.java','app/flexygram/effects/GlassContour.java','app/flexygram/bubbles/BubbleOutline.java','app/flexygram/bubbles/BubbleFusion.java','app/exteraless/settings/UniversalGlassSettingsActivity.java','app/exteraless/appearance/UniversalGlassConfig.java','app/exteraless/appearance/FlexyGlassConfig.java','app/exteraless/appearance/GlassContrastPolicy.java','app/exteraless/appearance/UniversalGlass.java','app/exteraless/appearance/SimpleGlassProvider.java','org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundColorProvider.java','org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundProvider.java','org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundProviderBuilder.java']
texts='\n'.join((root/f).read_text() for f in files)
rclasses={}
for kind,name in re.findall(r'R\.(\w+)\.(\w+)',texts):rclasses.setdefault(kind,set()).add(name)
resource_root=root.parent/'res'
strings=set()
for path in (resource_root/'values').glob('*.xml'):
 for item in ET.parse(path).getroot():
  if item.tag=='string' or item.attrib.get('type')=='string': strings.add(item.attrib.get('name'))
drawables={p.stem for folder in resource_root.glob('drawable*') for p in folder.iterdir() if p.is_file()}
for kind,available in [('string',strings),('drawable',drawables)]:
 missing=rclasses.get(kind,set())-available
 assert not missing, f'Unknown R.{kind} identifiers: {sorted(missing)}'
keys=sorted(set(re.findall(r'Theme\.(key_\w+)',texts)))
stubs={
'org.telegram.messenger.R':'public class R {'+''.join('public static class '+kind+' {'+''.join('public static final int '+name+'='+str(i+1)+';' for i,name in enumerate(sorted(names)))+'}' for kind,names in rclasses.items())+'}',
'org.telegram.messenger.AndroidUtilities':'public class AndroidUtilities {public static int dp(float f){return (int)f;}public static float dpf2(float f){return f;} public static android.graphics.Typeface bold(){return android.graphics.Typeface.DEFAULT_BOLD;}public static void runOnUIThread(Runnable r){r.run();}}',
'org.telegram.messenger.LocaleController':'public class LocaleController {public static boolean isRTL;public static String getString(int id){return "test";}}',
'org.telegram.messenger.LiteMode':'public class LiteMode {public static void onGlassEffectChanged(){}}',
'tw.nekomimi.nekogram.NekoConfig':'public class NekoConfig {public static android.content.SharedPreferences getPreferences(){return null;}}',
'org.telegram.ui.ActionBar.Theme':'public class Theme { public static final int '+','.join(k+'='+str(i+1) for i,k in enumerate(keys))+'; public interface ResourcesProvider{boolean isDark();}public static int getColor(int key,ResourcesProvider p){return 0;}public static int getColor(int key){return 0;}public static int getDividerColor(ResourcesProvider p){return 0;}public static boolean isCurrentThemeDark(){return false;}public static int multAlpha(int c,float a){return c;}public static android.graphics.drawable.Drawable createSimpleSelectorRoundRectDrawable(int r,int color,int pressed){return null;}}',
'org.telegram.ui.Stories.DarkThemeResourceProvider':'public class DarkThemeResourceProvider implements org.telegram.ui.ActionBar.Theme.ResourcesProvider {public boolean isDark(){return true;}}',
'org.telegram.ui.ActionBar.ActionBar':'public class ActionBar {public void setTitle(String s){}public void setBackButtonImage(int r){}public void setActionBarMenuOnItemClick(ActionBarMenuOnItemClick c){}public Menu createMenu(){return new Menu();}public static class ActionBarMenuOnItemClick{public void onItemClick(int id){}}public static class Menu{public android.view.View addItem(int id,int r){return null;}}}',
'org.telegram.ui.ActionBar.BaseFragment':'''public class BaseFragment {protected ActionBar actionBar;protected Theme.ResourcesProvider resourcesProvider;protected android.view.View fragmentView;public android.content.Context getContext(){return null;}public android.app.Activity getParentActivity(){return null;}public Theme.ResourcesProvider getResourceProvider(){return null;}public int getThemedColor(int key){return 0;}public android.view.View createView(android.content.Context c){return null;}public void finishFragment(){}public void onFragmentDestroy(){}public void onResume(){}public boolean onBackPressed(boolean b){return true;}public java.util.ArrayList<ThemeDescription> getThemeDescriptions(){return null;}public void showDialog(AlertDialog d){}public Parent getParentLayout(){return null;}public static class Parent{public void rebuildFragments(int flags){}}}''',
'org.telegram.ui.ActionBar.AlertDialog':'''public class AlertDialog {public interface Click{void onClick(AlertDialog d,int w);}public static class Builder{public Builder(android.content.Context c,Theme.ResourcesProvider p){} public Builder setTitle(String s){return this;}public Builder setMessage(String s){return this;}public Builder setItems(CharSequence[] items,Click c){return this;}public Builder setView(android.view.View v,int h){return this;}public Builder setPositiveButton(String s,Click c){return this;}public Builder setNegativeButton(String s,Click c){return this;}public Builder setNeutralButton(String s,Click c){return this;}public AlertDialog create(){return null;}}}''',
'org.telegram.ui.ActionBar.ThemeDescription':'public class ThemeDescription {public interface Delegate{void changed();}public ThemeDescription(android.view.View v,int flags,Class[] classes,android.graphics.Paint p,android.graphics.drawable.Drawable[] drawables,Delegate d,int key){}}',
'app.flexygram.settings.FlexySignatureSlider':'public class FlexySignatureSlider extends android.widget.SeekBar {public FlexySignatureSlider(android.content.Context c){super(c);}public void updateColors(){}}',
'org.telegram.ui.Components.LayoutHelper':'public class LayoutHelper {public static final int MATCH_PARENT=-1;public static android.widget.FrameLayout.LayoutParams createFrame(int w,float h){return null;}}',
'org.telegram.ui.Components.blur3.GlassOutlineStyle':'public enum GlassOutlineStyle {HIDDEN,SOLID,GLARE;public static void dispatchChange(){}}',
'org.telegram.ui.Components.blur3.drawable.color.impl.BlurredBackgroundProviderImpl':'public class BlurredBackgroundProviderImpl {public static boolean checkBlurEnabled(org.telegram.ui.ActionBar.Theme.ResourcesProvider p){return true;}}',
'androidx.core.graphics.ColorUtils':'public class ColorUtils {public static double calculateContrast(int c,int d){return 1;}public static int blendARGB(int a,int b,float f){return a;}}',
'androidx.annotation.ColorInt':'public @interface ColorInt {}',
'androidx.annotation.Px':'public @interface Px {}',
}
stubs['org.telegram.ui.ActionBar.ActionBar']=stubs['org.telegram.ui.ActionBar.ActionBar'].replace('public void setTitle', 'public void setAdaptiveBackground(android.view.View v){}public void setTitle')
stubs['app.exteraless.appearance.AppearanceConfig']='public class AppearanceConfig{public static final Item glassOutlineStyle=new Item();public static int glassOutlineStyle(){return 0;}public static class Item{public void setConfigInt(int value){}}}'
stubs['org.telegram.ui.Cells.TextSettingsCell']='public class TextSettingsCell extends android.view.View{public TextSettingsCell(android.content.Context c){super(c);}public void setTextAndValue(String s,String v,boolean divider){}}'
stubs['org.telegram.ui.Components.UItem']='public class UItem{public int id;public static UItem asCheck(int id,String title){return new UItem();}public UItem setChecked(boolean b){return this;}public static UItem asCustom(int id,android.view.View v){return new UItem();}public static UItem asButton(int id,String title){return new UItem();}public static UItem asShadow(String s){return new UItem();}public UItem setValue(String value){return this;}}'
stubs['org.telegram.ui.Components.UniversalAdapter']='public class UniversalAdapter{public void setApplyBackground(boolean b){}public void whiteSectionStart(){}public void whiteSectionEnd(){}public void update(boolean animated){}}'
stubs['org.telegram.ui.Components.UniversalRecyclerView']='public class UniversalRecyclerView extends android.widget.FrameLayout{public UniversalAdapter adapter;public interface Fill{void fill(java.util.ArrayList<UItem> items,UniversalAdapter a);}public interface Click{void click(UItem item,android.view.View view,int position,float x,float y);}public UniversalRecyclerView(org.telegram.ui.ActionBar.BaseFragment f,Fill fill,Click click,Object o){super(f.getContext());}public void setSections(){}}'
stubs['org.telegram.ui.Components.LayoutHelper']=stubs['org.telegram.ui.Components.LayoutHelper'].replace('public static android.widget.FrameLayout.LayoutParams createFrame', 'public static android.widget.LinearLayout.LayoutParams createLinear(int w,int h){return null;}public static android.widget.LinearLayout.LayoutParams createLinear(int w,int h,int l,int t,int r,int b){return null;}public static android.widget.FrameLayout.LayoutParams createFrame')
with tempfile.TemporaryDirectory(prefix='crystal-api-') as d:
 paths=[]
 for name,body in stubs.items():
  p=Path(d)/(name.replace('.','/')+'.java');p.parent.mkdir(parents=True,exist_ok=True);p.write_text('package '+name.rsplit('.',1)[0]+';'+body);paths.append(str(p))
 cmd=[javac,'-cp',str(android_jar),'-d',d,*[str(root/f) for f in files],*paths]
 r=subprocess.run(cmd,capture_output=True,text=True);print(r.stdout,r.stderr);assert r.returncode==0
 print('Actual settings, configuration and providers type-check against Android API 37; project services stubbed, no APK')
