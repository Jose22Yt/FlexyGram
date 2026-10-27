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

    def test_no_protected_navigation_or_reaction_owner_is_modified(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
        from motion_contract import BASE
        for name in ['org/telegram/ui/ActionBar/ActionBarLayout.java','org/telegram/ui/ChatActivity.java','org/telegram/ui/DialogsActivity.java','org/telegram/ui/Components/ReactionsContainerLayout.java','app/exteraless/player/PlayerSheet.java']:
            path='TMessagesProj/src/main/java/'+name
            self.assertEqual(subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),(ROOT/path).read_bytes(),name)

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
