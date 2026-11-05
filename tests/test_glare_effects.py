"""Source compatibility checks; Android pixel/controller checks live in tools/glare/android."""
import subprocess
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
J=ROOT/'TMessagesProj/src/main/java'
BASE='4679f74ebd312acc4968dd2e044a6c6b7478445a'
S=J/'app/flexygram/settings/signature'
def test_no_preference_migration_or_backend_replacement():
 for p in ['TMessagesProj/src/main/kotlin/app/exteraless/appearance/AppearanceConfig.kt','TMessagesProj/src/main/java/org/telegram/ui/Components/blur3/GlassOutlineStyle.java']:
  current=(ROOT/p).read_text()
  if p.endswith('AppearanceConfig.kt'):
   getter='\n    /** Native metadata only; account/session preferences are not part of this catalog. */\n    fun getStudioItems(): List<ConfigItem> = configs.toList()\n'
   assert current.count(getter)==1
   current=current.replace(getter,'')
  if p.endswith('GlassOutlineStyle.java'):
   current=current.replace('    HIDDEN,\n    DOUBLE,\n    ADAPTIVE;', '    HIDDEN;')
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
 # Existing static glare algorithms remain unchanged; the new modes use separate paths.
 from test_composer_layout import method
 for anchor in ['public static void drawStroke(\n','public static void drawStroke(Canvas canvas, RectF rect,','public static void drawStroke(Canvas canvas, float left, float top, float right, float bottom,']:
  before=method(old,anchor);after=method(new,anchor)
  after=after.replace(replacement,'if (GlassOutlineStyle.current() != GlassOutlineStyle.GLARE) return;')
  assert before==after
 assert 'private void drawSourceContents(' in new
 assert 'drawSourceContents(canvas,source);\n        drawAdditionalOutline(canvas,source);' in new

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
  assert len(items)==7 and all(x.text and x.text.strip() for x in items)
  values.append({x.get('name') for x in items})
 assert values[0]==values[1]==values[2]

def test_extended_modes_preserve_ordinals_and_backup_range():
 for path in ['org/telegram/ui/Components/blur3/GlassOutlineStyle.java', 'com/exteragram/messenger/GlassOutlineStyle.java']:
  text=(J/path).read_text()
  assert text.index('GLARE,') < text.index('SOLID,') < text.index('HIDDEN,') < text.index('DOUBLE,') < text.index('ADAPTIVE;')
 backup=(J/'app/exteraless/backup/EtgBackup.java').read_text()
 assert '"glassOutlineStyle", AppearanceConfig.glassOutlineStyle, 0, 4' in backup

def test_extended_contours_use_existing_surface_routes():
 base=(J/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java').read_text()
 hardware=(J/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text()
 assert 'drawSourceContents(canvas, ((BlurredBackgroundSourceWrapped) source).getSource());' in base
 assert 'canvas.restore();\n        drawAdditionalOutline(canvas, source);' in hardware
 sampler=(J/'org/telegram/ui/Components/blur3/GlassBackdropColor.java').read_text()
 assert 'now-sampledAt<180' in sampler
 for forbidden in ['PixelCopy', 'scheduleSelf', 'postDelayed', 'createBitmap', 'RenderEffect']:
  assert forbidden not in sampler
