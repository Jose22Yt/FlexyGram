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
  assert (ROOT/p).read_bytes()==subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
 assert 'AP_GlareEffect' not in (J/'app/flexygram/effects/GlareSettingsSection.java').read_text()
def test_one_owner_and_direct_chat_entry():
 policy=(S/'Settings2Policy.java').read_text()
 assert 'own("appearance:glassOutline", "chat_glare")' in policy
 assert 'own("appearance:glassOutline", "effects")' not in policy
 direct=(S/'SignatureDirectSettingsActivity.java').read_text()
 assert direct.count('new app.flexygram.effects.GlareSettingsSection()')==1
 assert direct.index('new app.flexygram.composer.FlexyComposerSettingsActivity')<direct.index('new app.flexygram.effects.GlareSettingsSection()')
 assert 'case "glassOutline":case "glareEffects":return Settings3Registry.open("chat")' in (S/'SignatureSettingsRegistry.java').read_text()
def test_default_static_renderer_is_preserved():
 p='TMessagesProj/src/main/java/org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java'
 old=subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT,text=True)
 new=(ROOT/p).read_text()
 replacement='if (org.telegram.ui.Components.blur3.StaticOutlineStroke.drawOverride(canvas,left,top,right,bottom,radii,isTop,paint,GlassOutlineStyle.current())) return;'
 assert new.count(replacement)==2
 assert new.replace(replacement,'if (GlassOutlineStyle.current() != GlassOutlineStyle.GLARE) return;')==old

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
