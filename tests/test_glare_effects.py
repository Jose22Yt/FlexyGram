"""Source compatibility checks; Android pixel/controller checks live in tools/glare/android."""
import subprocess
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
J=ROOT/'TMessagesProj/src/main/java'
BASE='4679f74ebd312acc4968dd2e044a6c6b7478445a'
S=J/'app/flexygram/settings/signature'
def without_width_extension(text):
 for key in ['FlexyFolderThemeAccent','OEAppearanceSenderMiniAvatars','OEAppearanceSquareFab','OEAppearanceGooeyAvatarAnimation','OEAppearanceSeparateHeaders','OEAppearanceGlassMessageMenu','OEAppearanceNewLoadingStyle','OEAppearanceMd3Player','OEAppearanceMd3MiniPlayer','OEAppearanceProfileMusicCard']:
  text=text.replace('"'+key+'", ConfigItem.configTypeBool, false','"'+key+'", ConfigItem.configTypeBool, true')
 return text  # Normalize only the approved fresh-install defaults; the glare backend is unchanged.

def test_no_preference_migration_or_backend_replacement():
 for p in ['TMessagesProj/src/main/kotlin/app/exteraless/appearance/AppearanceConfig.kt','TMessagesProj/src/main/java/org/telegram/ui/Components/blur3/GlassOutlineStyle.java']:
  current=(ROOT/p).read_text()
  if p.endswith('AppearanceConfig.kt'):
   getter='\n    /** Native metadata only; account/session preferences are not part of this catalog. */\n    fun getStudioItems(): List<ConfigItem> = configs.toList()\n'
   assert current.count(getter)==1
   current=without_width_extension(current.replace(getter,''))
  assert current==subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT,text=True)
 assert 'AP_GlareEffect' not in (J/'app/flexygram/effects/GlareSettingsSection.java').read_text()
def test_one_owner_and_direct_chat_entry():
 policy=(S/'Settings2Policy.java').read_text()
 assert 'own("appearance:glassOutline", "chat_glare")' in policy
 assert 'own("appearance:glassOutline", "effects")' not in policy
 direct=(S/'SignatureDirectSettingsActivity.java').read_text()
 assert direct.count('new app.flexygram.effects.GlareSettingsSection()')==1
 assert direct.index('"composer_style"')<direct.index('new app.flexygram.effects.GlareSettingsSection()')
 assert 'case "glassOutline":case "glareEffects":return Settings3Registry.open("chat")' in (S/'SignatureSettingsRegistry.java').read_text()
def test_default_static_renderer_is_preserved():
 p='TMessagesProj/src/main/java/org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java'
 old=subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT,text=True)
 new=(ROOT/p).read_text()
 replacement='if (org.telegram.ui.Components.blur3.StaticOutlineStroke.drawOverride(canvas,left,top,right,bottom,radii,isTop,paint,GlassOutlineStyle.current())) return;'
 assert new.count(replacement)==2
 from test_composer_layout import method
 for anchor, historical in [('protected static void drawStrokeRaw(\n','public static void drawStroke(\n'),('protected static void drawStrokeRaw(Canvas canvas, float left, float top, float right, float bottom,','public static void drawStroke(Canvas canvas, float left, float top, float right, float bottom,')]:
  actual=method(new,anchor).replace('protected static void drawStrokeRaw','public static void drawStroke')
  actual=actual.replace(replacement,'if (GlassOutlineStyle.current() != GlassOutlineStyle.GLARE) return;')
  assert actual==method(old,historical)
 assert 'finally { paint.setStrokeWidth(previousWidth); }' in new
 assert 'applyOutlineWidth();' in new

def test_no_frame_allocations_or_background_engine():
 source=(J/'org/telegram/ui/Components/blur3/StaticOutlineStroke.java').read_text()
 methods=source[source.index('public static boolean drawOverride'):]
 assert 'new ' not in methods
 assert 'finally' in methods and 'p.setShader(shader)' in methods
 assert 'ThreadLocal.withInitial' in source
 for forbidden in ['Bitmap','new Thread','Handler','Executor','setShadowLayer','RenderEffect']:
  assert forbidden not in methods

def test_native_dialog_and_changed_row_only():
 source=(J/'app/flexygram/effects/GlareSettingsSection.java').read_text()
 assert 'AlertsCreator.createSingleChoiceDialog' in source
 assert 'notifyItemChanged(typeRow)' in source
 for forbidden in ['notifyDataSetChanged','recreate(','restart','SharedPreferences','setConfigBool']:
  assert forbidden not in source
 assert 'GlareMode.toStored(which)' in source

def test_three_locales_have_exact_same_keys():
 values=[]
 for folder in ['values','values-es','values-ru']:
  items=list(E.parse(ROOT/'TMessagesProj/src/main/res'/folder/'flexy_glare.xml').getroot())
  assert len(items)==5 and all(x.text and x.text.strip() for x in items)
  values.append({x.get('name') for x in items})
 assert values[0]==values[1]==values[2]


def test_no_custom_width_ui_or_storage_and_native_helpers_scale_once():
 section=(J/'app/flexygram/effects/GlareSettingsSection.java').read_text()
 config=(ROOT/'TMessagesProj/src/main/kotlin/app/exteraless/appearance/AppearanceConfig.kt').read_text()
 assert 'widthRow' not in section and 'SeekBar' not in section
 assert 'glassOutlineWidth' not in config
 assert 'glassOutlineWidth' not in (J/'app/exteraless/backup/EtgBackup.java').read_text()
 render=(J/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text()
 assert 'drawStrokeRaw(c,' in render and 'drawStroke(c,' not in render


def test_fixed_emphasis_does_not_compound_or_rebuild_unchanged_geometry(tmp_path):
 from test_composer_layout import method
 from test_render_work_reuse import probe
 source=(J/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java').read_text()
 methods=method(source,'public void setStrokeWidth(')+method(source,'private void applyOutlineWidth(')
 probe(tmp_path,{
 'Probe.java':'''public class Probe{
 static class Props{float strokeWidthTop=3,strokeWidthBottom=2,strokeWidthFull=1;int builds;void build(){builds++;}}
 Props boundProps=new Props();float baseStrokeWidthTop,baseStrokeWidthBottom;int notifications;
 void onBoundPropsChanged(){notifications++;}
 METHODS
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){var p=new Probe();float factor=org.telegram.ui.Components.blur3.GlareStrokeWidth.factor();check(factor>1&&factor<=1.15f);
 for(int i=0;i<1000;i++)p.setStrokeWidth(3,2);
 check(p.boundProps.strokeWidthTop==3*factor&&p.boundProps.strokeWidthBottom==2*factor&&p.boundProps.builds==1&&p.notifications==1);
 p.setStrokeWidth(6,4);check(p.boundProps.strokeWidthTop==6*factor&&p.boundProps.strokeWidthBottom==4*factor&&p.notifications==2);
 }
}'''.replace('METHODS',methods)
 },[J/'org/telegram/ui/Components/blur3/GlareStrokeWidth.java'])
