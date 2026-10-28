"""Native restoration and preservation contracts; not physical performance claims."""
from pathlib import Path
import hashlib,json,subprocess,unittest
import native_motion_restore_contract as audit
ROOT=Path(__file__).resolve().parents[2]
REFERENCE='14e586b4ddb7a686f39cda3cb175920c49cecf11'

def git_bytes(ref,path):return subprocess.check_output(['git','show',ref+':'+path],cwd=ROOT)
class NativeMotionRestoration(unittest.TestCase):
 def test_review_scope_and_mutations_fail_closed(self):
  audit.verify_current()
  for path in audit.spec()['reviewed']:
   mutated=audit.read_current(path)+b'\nUNREVIEWED_NATIVE_EDIT'
   self.assertEqual(mutated,audit.restore(path,mutated),path)
 def test_eighteen_complete_native_classes_are_recovered(self):
  paths=json.loads((ROOT/'tools/connected_alpha/native_motion_restore/scope.json').read_text())['modified']
  exact=[p for p in paths if not p.endswith(('/ChatActivity.java','/FilterTabsView.java'))]
  self.assertEqual(18,len(exact))
  for path in exact:self.assertEqual(git_bytes(REFERENCE,path),(ROOT/path).read_bytes(),path)
 def test_only_reviewed_engine_patch_is_removed_from_current_classes(self):
  # Re-apply the original engine-only diff to the restoration. It must reconstruct
  # Alpha1281 exactly, including all post-engine blur and folder fixes.
  import tempfile
  paths=json.loads((ROOT/'tools/connected_alpha/native_motion_restore/scope.json').read_text())['modified']
  patch=subprocess.check_output(['git','diff',REFERENCE,'c3dd04ec43a8ec7ff53a4d9df7dae1a9bd2600ed','--',*paths],cwd=ROOT)
  with tempfile.TemporaryDirectory() as folder:
   folder=Path(folder)
   for path in paths:
    target=folder/path;target.parent.mkdir(parents=True,exist_ok=True)
    data=(ROOT/path).read_bytes()
    if path.endswith('/FilterTabsView.java'):
     # Keep the independently required native callback guard in production;
     # the old engine diff also contains it, so reverse only this exact guard
     # before using that diff as a reconstruction proof.
     guard=b"                if (colorChangeAnimator != animation) return;\n                colorChangeAnimator = null;\n"
     self.assertEqual(1,data.count(guard));data=data.replace(guard,b'',1)
    target.write_bytes(data)
   subprocess.run(['git','apply','--unsafe-paths','-'],cwd=folder,input=patch,check=True,capture_output=True)
   for path in paths:self.assertEqual(git_bytes(audit.PIN,path),(folder/path).read_bytes(),path)
 def test_no_engine_or_instant_consumers_in_new_or_changed_production(self):
  paths=subprocess.check_output(['git','diff','--name-only',REFERENCE,'--','TMessagesProj/src/main'],cwd=ROOT,text=True).splitlines()
  for path in paths:
   if path.endswith(('.java','.kt','.xml')):
    text=audit.read_current(path)
    for token in [b'app.flexygram.motion',b'FlexyMotionActivity',b'FlexyInstantNavigation',b'FlexyFrameMotion']:
     self.assertNotIn(token,text,path)
  self.assertFalse(any((ROOT/'TMessagesProj/src/main/java/app/flexygram/motion').glob('*.java')))
 def test_current_design_services_identity_and_private_delivery_are_unchanged(self):
  protected=['TMessagesProj/build.gradle','.github/workflows/connected-alpha-arm64.yml','tools/connected_alpha/build_private_apk.py','TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java','TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java','TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java','TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java']
  protected += subprocess.check_output(['git','ls-tree','-r','--name-only',audit.PIN,'--','TMessagesProj/src/main/java/app/flexygram/home','TMessagesProj/src/main/java/app/flexygram/studio','TMessagesProj/src/main/java/app/flexygram/files','TMessagesProj/src/main/java/app/flexygram/composer'],cwd=ROOT,text=True).splitlines()
  for path in protected:self.assertEqual(git_bytes(audit.PIN,path),(ROOT/path).read_bytes(),path)
 def test_blur_keeps_cache_workers_prefetch_and_native_cancel(self):
  path='TMessagesProj/src/main/java/app/flexygram/bubbles/SignatureWallpaperBlur.java'
  s=(ROOT/path).read_text();before=git_bytes(audit.PIN,path).decode()
  # The worker/cache portion preceding Owner is entirely unchanged except imports.
  a=s[:s.index('    public static final class Owner')];b=before[:before.index('    public static final class Owner')]
  a=a.replace('import android.animation.ValueAnimator;\nimport android.view.animation.LinearInterpolator;','import app.flexygram.motion.FlexyFrameMotion;')
  self.assertEqual(b,a)
  self.assertIn('ValueAnimator.ofFloat(0, 1)',s);self.assertIn('setDuration(120)',s)
  self.assertIn('revealMotion.removeAllUpdateListeners(); revealMotion.cancel()',s)
  self.assertIn('else reveal = 1; // Warm reuse is final from its very first draw.',s)
 def test_original_input_and_native_navigation_remain_not_rebuilt(self):
  s=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
  self.assertIn('import androidx.dynamicanimation.animation.SpringAnimation;',s)
  self.assertNotIn('FlexyInstant',s);self.assertNotIn('app.flexygram.motion',s)
  self.assertIn('onSlideAnimationEnd',s);self.assertIn('predictiveBackAnimation',s)
 def test_cancelled_settings_resources_and_tests_are_not_shipped(self):
  data=json.loads((ROOT/'tools/connected_alpha/native_motion_restore/scope.json').read_text())
  for path in data['deleted']:self.assertFalse((ROOT/path).exists(),path)
  self.assertFalse((ROOT/'.github/workflows/flexy-motion-arm64.yml').exists())
if __name__=='__main__':unittest.main()
