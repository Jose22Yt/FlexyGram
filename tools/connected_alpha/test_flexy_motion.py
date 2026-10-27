"""Compile and exercise the exact production motion maths on a host JVM.

This is NOT a substitute for Choreographer/device tests or APK evidence.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
JAVA = ROOT / "TMessagesProj/src/main/java/app/flexygram/motion"


class FlexyMotionCore(unittest.TestCase):
    def test_java_spring_profiles_velocity_and_frame_independence(self):
        probe = r"""
import app.flexygram.motion.FlexyMotionProfile;
import app.flexygram.motion.FlexyMotionSpring;

public class FlexyMotionProbe {
    static void ok(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    static float settle(FlexyMotionSpring spring, float dt, int frames) {
        for (int i = 0; i < frames; i++) spring.advance(dt);
        return spring.value();
    }
    public static void main(String[] args) {
        ok(FlexyMotionProfile.parse("FLASH") == FlexyMotionProfile.FLASH, "flash");
        ok(FlexyMotionProfile.parse("signature") == FlexyMotionProfile.SIGNATURE, "signature");
        ok(FlexyMotionProfile.parse("unknown") == FlexyMotionProfile.FLOW, "fallback");
        for (FlexyMotionProfile p : new FlexyMotionProfile[] {
                FlexyMotionProfile.FLOW, FlexyMotionProfile.SIGNATURE }) {
            FlexyMotionSpring s = new FlexyMotionSpring(1f);
            s.configure(p);
            s.target(p.pressedScale);
            for (int i = 0; i < 8; i++) s.advance(1f / 120f);
            float current = s.value(), velocity = s.velocity();
            ok(current < 1f && current > 0.8f, "press motion");
            ok(velocity < 0, "press velocity");
            s.target(1f);
            ok(s.value() == current && s.velocity() == velocity, "interrupt continuity");
            float end = settle(s, 1f / 120f, 240);
            ok(Math.abs(end - 1f) < 0.0008f && s.settled(), "120 Hz release settles");
            s.snapTo(1f);
            s.target(p.pressedScale);
            settle(s, 1f / 60f, 120);
            ok(Math.abs(s.value() - p.pressedScale) < 0.0008f, "60 Hz target settles");
            s.snapTo(1f);
            s.target(p.pressedScale);
            settle(s, 5f, 240); // bounded delayed frames, no NaN/overshoot explosion
            ok(Float.isFinite(s.value()) && s.settled(), "late frame bounded");
        }
        for(float damping : new float[]{.55f,.92f,1f,1.2f}) {
            FlexyMotionSpring a=new FlexyMotionSpring(0), b=new FlexyMotionSpring(0);
            a.configure(560,damping);b.configure(560,damping);a.target(1);b.target(1);
            for(int i=0;i<6;i++)a.advance(1f/60);
            for(int i=0;i<24;i++)b.advance(1f/240);
            ok(Math.abs(a.value()-b.value())<.00001f,"analytical refresh independence");
            ok(Math.abs(a.velocity()-b.velocity())<.0001f,"velocity refresh independence");
        }
        FlexyMotionSpring s = new FlexyMotionSpring(1f);
        s.target(0.9f);
        float old = s.advance(0f);
        ok(old == 1f, "zero dt");
        ok(s.advance(Float.NaN) == 1f, "invalid dt");
        boolean rejected = false;
        try { s.target(Float.NaN); } catch (IllegalArgumentException expected) { rejected = true; }
        ok(rejected, "invalid target rejected");
        System.out.println("PASS: profiles, retarget velocity, 60/120Hz, frame cap and settle");
    }
}
"""
        with tempfile.TemporaryDirectory() as folder:
            probe_file = Path(folder) / "FlexyMotionProbe.java"
            probe_file.write_text(probe)
            result = subprocess.run(
                ["java", "-m", "jdk.compiler/com.sun.tools.javac.Main", "-d", folder, str(JAVA / "FlexyMotionProfile.java"),
                 str(JAVA / "FlexyMotionSpring.java"), str(probe_file)],
                capture_output=True, text=True
            )
            self.assertEqual(0, result.returncode, result.stderr)
            result = subprocess.run(
                ["java", "-cp", folder, "FlexyMotionProbe"],
                capture_output=True, text=True
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("PASS:", result.stdout)

    def test_independent_review_is_exact_and_preserves_work1(self):
        import json, hashlib, sys
        sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
        import motion_contract as review
        spec=json.loads(review.MANIFEST.read_text())
        for name,sha in spec['reviewed'].items():
            current=(ROOT/name).read_bytes()
            self.assertEqual(sha,hashlib.sha256(current).hexdigest(),name)
            original=subprocess.run(['git','show',review.BASE+':'+name],cwd=ROOT,capture_output=True)
            self.assertEqual(original.stdout if original.returncode==0 else b'',review.restore(name,current),name)
            self.assertEqual(current+b'\\nMUTATION',review.restore(name,current+b'\\nMUTATION'),name)
        historical='tools/connected_alpha/signature1278_review.json'
        self.assertEqual(subprocess.check_output(['git','show',review.BASE+':'+historical],cwd=ROOT),(ROOT/historical).read_bytes())

    def test_critical_navigation_is_untouched_and_reaction_binding_is_narrow(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
        from motion_contract import BASE
        for name in ['org/telegram/ui/ActionBar/ActionBarLayout.java','org/telegram/ui/DialogsActivity.java']:
            path='TMessagesProj/src/main/java/'+name
            self.assertEqual(subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),(ROOT/path).read_bytes(),name)

    def test_native_reaction_protocol_is_kept_with_one_standalone_owner(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
        from motion_contract import BASE
        path='TMessagesProj/src/main/java/org/telegram/ui/Components/ReactionsContainerLayout.java'
        old=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
        new=(ROOT/path).read_text().replace('app.flexygram.motion.FlexyMotionAnimator','ObjectAnimator')
        new=new.replace('new ObjectAnimator(this,from,target,this::setTransitionProgress)','ObjectAnimator.ofFloat(this,TRANSITION_PROGRESS_VALUE,from,target)')
        self.assertEqual(old,new)
        path='TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java'
        old=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
        new=(ROOT/path).read_text()
        line='            scrimPopupWindow.setFlexyMotionEnabled(org.telegram.messenger.BuildConfig.CONNECTED_ALPHA && finalReactionsLayout1 != null);\n'
        self.assertEqual(1,new.count(line));self.assertEqual(old,new.replace(line,''))

    def test_real_build_validation_is_scoped_and_preserves_original_gates(self):
        import yaml,sys
        sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
        from motion_contract import BASE
        workflow=yaml.safe_load((ROOT/'.github/workflows/flexy-motion-arm64.yml').read_text())
        triggers=workflow.get('on',workflow.get(True))
        self.assertEqual(['validation/flexy-motion-arm64'],triggers['push']['branches'])
        self.assertNotIn('pull_request',triggers);self.assertEqual({'contents':'read'},workflow['permissions'])
        job=workflow['jobs']['compile']
        self.assertEqual('./.github/workflows/connected-alpha-arm64.yml',job['uses'])
        self.assertEqual(8,len(job['secrets']))
        for p in ['.github/workflows/connected-alpha-arm64.yml','TMessagesProj/build.gradle','TMessagesProj/src/main/AndroidManifest.xml']:
            self.assertEqual(subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT),(ROOT/p).read_bytes())

    def test_tabs_keep_native_selection_and_direct_finger_protocol(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
        from motion_contract import BASE
        path='TMessagesProj/src/main/java/org/telegram/ui/MainTabsLayout.java'
        old=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
        new=(ROOT/path).read_text()
        for start,end in [('    public void setTabSelected(', '    private final Runnable restoreDrawSelector'),('    private void checkLongMove(', '    private final Set<View>'),('    private void checkPivot(', '    private static float clampXToChildrenCenters')]:
            self.assertEqual(old[old.index(start):old.index(end)],new[new.index(start):new.index(end)])
        self.assertNotIn('SpringAnimation',new)
        self.assertIn('if (motionDetaching) return;',new)
        self.assertIn('onWindowVisibilityChanged',new)
        click='TMessagesProj/src/main/java/me/vkryl/android/util/ClickHelper.java'
        self.assertEqual(subprocess.check_output(['git','show',BASE+':'+click],cwd=ROOT),(ROOT/click).read_bytes())

    def test_native_bounce_fallback_and_tab_geometry_remain_reviewable(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
        from motion_contract import BASE
        path='TMessagesProj/src/main/java/org/telegram/ui/Components/ButtonBounce.java'
        old=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
        new=(ROOT/path).read_text()
        # Original ValueAnimator blocks remain verbatim behind the explicit connected/owner bridge.
        for start,end in [('            ValueAnimator pastAnimator', '    public void bounce()'),('        if (bounceAnimator != null)', '    public float isPressedProgress()')]:
            a=old[old.index(start):old.index(end)]
            self.assertIn(a,new)
        self.assertIn('!org.telegram.messenger.BuildConfig.CONNECTED_ALPHA || view == null',new)
        path='TMessagesProj/src/main/java/app/exteraless/appearance/MainTabsUiHelper.java'
        old=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
        self.assertEqual(old,(ROOT/path).read_text().replace('import app.flexygram.motion.FlexyBooleanMotion;','import me.vkryl.android.animator.BoolAnimator;').replace('FlexyBooleanMotion','BoolAnimator'))
        source=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/Components/ScaleStateListAnimator.java').read_text()
        self.assertIn('instanceof app.flexygram.motion.FlexyPressOwner',source)
        self.assertIn('view.setStateListAnimator(scaleStateListAnimator);',source)

    def test_player_transition_delta_preserves_all_playback_and_layout_code(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
        from motion_contract import BASE
        path='TMessagesProj/src/main/java/app/exteraless/player/PlayerSheet.java'
        old=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
        new=(ROOT/path).read_text()
        for name in ['backAnimator','morphAnimator','lyricsAnimator']:
            new=new.replace('private app.flexygram.motion.FlexyMotionAnimator '+name+';','private ValueAnimator '+name+';')
        new=new.replace('    private app.flexygram.motion.FlexyMotionAnimator elevationAnimator;\n','')
        new=new.replace('backAnimator = new app.flexygram.motion.FlexyMotionAnimator(root, backProgress, 0f, value -> {\n            backProgress = value;', 'backAnimator = ValueAnimator.ofFloat(backProgress, 0f);\n        backAnimator.addUpdateListener(a -> {\n            backProgress = (float) a.getAnimatedValue();')
        new=new.replace('morphAnimator = new app.flexygram.motion.FlexyMotionAnimator(root, from, to, value -> {\n            morphProgress = value;', 'morphAnimator = ValueAnimator.ofFloat(from, to);\n        morphAnimator.addUpdateListener(a -> {\n            morphProgress = (float) a.getAnimatedValue();')
        new=new.replace('lyricsAnimator = new app.flexygram.motion.FlexyMotionAnimator(root, lyricsFraction, target, this::setLyricsFraction);','lyricsAnimator = ValueAnimator.ofFloat(lyricsFraction, target);\n        lyricsAnimator.addUpdateListener(a -> setLyricsFraction((float) a.getAnimatedValue()));')
        start=new.index('            if (elevationAnimator != null)')
        end=new.index('            elevationAnimator.start();',start)+len('            elevationAnimator.start();')
        new=new[:start]+'            cover.animate().translationZ(0).setDuration(250).start();'+new[end:]
        new=new.replace('        if (elevationAnimator != null) { elevationAnimator.removeAllListeners(); elevationAnimator.cancel(); elevationAnimator = null; }\n','')
        self.assertEqual(old,new)

    def test_music_geometry_and_actions_preserved_without_draw_time_integration(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
        from motion_contract import BASE
        path='TMessagesProj/src/main/java/app/exteraless/player/MorphButton.java'
        old=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
        new=(ROOT/path).read_text()
        for signature,end in [('    public boolean performClick()', '    @Override\n    protected void onDraw'),('    private void drawIcon(',None)]:
            self.assertEqual(old[old.index(signature):old.index(end) if end else len(old)],new[new.index(signature):new.index(end) if end else len(new)])
        a=old[old.index('        float w = getWidth();',old.index('protected void onDraw')):old.index('        if (animating)')].strip()
        b=new[new.index('        float w = getWidth();',new.index('protected void onDraw')):new.index('    private void drawIcon')].rsplit('    }',1)[0].strip()
        for name in ['radiusLeft','radiusRight','alt','active','badge']:b=b.replace(name+'.value()',name+'.value')
        self.assertEqual(a,b)
        self.assertNotIn('SystemClock',new);self.assertNotIn('postInvalidateOnAnimation',new)
        for name in ['ControlsRow.java','WavySeekBar.java']:
            path='TMessagesProj/src/main/java/app/exteraless/player/'+name
            self.assertEqual(subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),(ROOT/path).read_bytes())

    def test_runtime_uses_frame_clock_not_system_duration_scale(self):
        frame = (JAVA / "FlexyFrameMotion.java").read_text()
        settings = (JAVA / "FlexyMotionSettings.java").read_text()
        self.assertIn("Choreographer.FrameCallback", frame)
        self.assertIn("frameTimeNanos", frame)
        self.assertIn("removeFrameCallback", frame)
        for code in (frame, settings):
            self.assertNotIn("ValueAnimator.", code.replace("ValueAnimator/ObjectAnimator", ""))
            self.assertNotIn("Settings.Global.put", code)
        self.assertIn("onViewDetachedFromWindow", frame)
        self.assertIn("REDUCE_MOTION", settings)


if __name__ == "__main__":
    unittest.main()
