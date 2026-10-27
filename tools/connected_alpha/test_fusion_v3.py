"""Native Signature Fusion compact v3 geometry, alpha curve, and stable RTL.
Pure JVM tests; physical GPU and APK verification remain Work 1 acceptance gates.
"""
from pathlib import Path
import subprocess, tempfile, unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "TMessagesProj/src/main/java/app/flexygram/header/fusion"

class FusionV3(unittest.TestCase):
    def test_adaptive_full_card_fade_compact_touch_safety_and_no_allocated_layouts(self):
        java = r'''package app.flexygram.header.fusion;
public final class FusionCompactProbe {
    private static int count;
    private static void check(boolean valid, String detail) {
        count++;
        if (!valid) throw new AssertionError(detail);
    }
    private static void close(float got, float expected, String detail) {
        check(Math.abs(got - expected) <= .03f, detail + ": " + got + " != " + expected);
    }
    public static void main(String[] args) {
        SignatureFusionGeometry.Layout reused = new SignatureFusionGeometry.Layout();
        var back = reused.back; var actions = reused.actions; var center = reused.center;
        var portrait = reused.portrait; var text = reused.text;
        for (int width = 240; width <= 840; width += 13)
            for (float d : new float[] {.75f, 1f, 1.5f, 2f, 3f, 4f})
                for (boolean rtl : new boolean[] {false, true})
                    for (boolean hasCall : new boolean[] {false, true}) {
                        float px = width * d;
                        var g = SignatureFusionGeometry.update(reused, px, d, rtl, hasCall);
                        check(g == reused && g.back == back && g.actions == actions &&
                              g.center == center && g.portrait == portrait && g.text == text,
                              "no new layout objects");
                        close(g.height, 48 * d, "native touch height");
                        close(g.back.width(), 48 * d, "back hit");
                        close(g.actions.width(), (hasCall ? 96 : 48) * d, "menu hit");
                        close(g.backVisual.width(), 42 * d, "back visual");
                        close(g.actionsVisual.width(), (hasCall ? 84 : 40) * d, "menu visual");
                        close(g.actionsVisual.height(), 40 * d, "menu visual height");
                        close(g.center.height(), 46 * d, "central pill visual");
                        close(g.center.centerY(), g.back.centerY(), "center vertically aligned");
                        close(g.actionsVisual.centerY(), g.center.centerY(), "actions centered");
                        check(g.back.left >= 0 && g.back.right <= px && g.actions.left >= 0 &&
                              g.actions.right <= px, "touch bounds on screen");
                        if (g.fits) {
                            check(g.text.width() >= 48 * d, "safe text width");
                            check(g.portrait.width() >= .75f * g.center.width(), "near full card avatar");
                            check(g.portrait.left >= g.center.left && g.portrait.right <= g.center.right, "portrait clipped");
                            check(g.text.left >= g.center.left && g.text.right <= g.center.right, "text within pill");
                            float firstText = rtl ? g.text.right : g.text.left;
                            float totalFade = Math.abs(g.fadeEndX - g.fadeStartX);
                            float t = Math.abs(firstText - g.fadeStartX) / totalFade;
                            check(Math.abs(t - g.fadeSafeStop) <= .0001f, "calculated alpha-safe edge");
                            check(SignatureFusionFade.opacityAt(t, g.fadeSafeStop) <= .041f,
                                    "under four-percent photo at first text pixel");
                            check(SignatureFusionFade.opacityAt(t, g.fadeSafeStop) > 0f,
                                    "fade extends under text instead of hard stop");
                            check(!rtl ? g.back.right + 8*d <= g.center.left &&
                                              g.center.right + 8*d <= g.actions.left
                                       : g.actions.right + 8*d <= g.center.left &&
                                              g.center.right + 8*d <= g.back.left,
                                    "gapped independent native touch zones");
                        }
                    }
        for (int i=0; i<7; i++) for (float safe : new float[] {.20f,.40f,.65f,.84f}) {
            float[] ltr = new float[8], rtl = new float[8];
            SignatureFusionFade.fillStops(safe, false, ltr);
            SignatureFusionFade.fillStops(safe, true, rtl);
            for (int j=1; j<8; j++) {
                check(ltr[j] > ltr[j-1] && rtl[j] > rtl[j-1], "monotonic stops");
            }
            for (int j=0; j<8; j++) close(ltr[j], 1f-rtl[7-j], "RTL mirror");
            float previous = 1f;
            for(int j=0; j<=1000; j++) {
                float alpha=SignatureFusionFade.opacityAt(j/1000f, safe);
                check(alpha <= previous + 0.00001f && alpha >= 0, "monotonic opacity");
                previous=alpha;
            }
        }
        for (float density : new float[] {1,2,3}) for (int width : new int[] {320,360,393,412}) {
            var left = SignatureFusionGeometry.calculate(width*density,density,false,true);
            var right= SignatureFusionGeometry.calculate(width*density,density,true,true);
            check(left.fits && right.fits, "phone widths with both actions");
            close(left.center.left, width*density-right.center.right, "center mirror");
            close(left.text.left, width*density-right.text.right, "text mirror");
            close(left.actionsVisual.left, width*density-right.actionsVisual.right, "visual mirror");
        }
        System.out.println("PASS " + count + " compact/full-card/RTL native geometry assertions");
    }
}'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "FusionCompactProbe.java"
            path.write_text(java)
            args = ["java", "-m", "jdk.compiler/com.sun.tools.javac.Main", "-d", tmp,
                str(SOURCE / "SignatureFusionGeometry.java"),
                str(SOURCE / "SignatureFusionFade.java"), str(path)]
            done = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(0, done.returncode, done.stderr)
            done = subprocess.run(["java", "-cp", tmp,
                "app.flexygram.header.fusion.FusionCompactProbe"], capture_output=True, text=True)
            self.assertEqual(0, done.returncode, done.stderr)
            self.assertIn("PASS", done.stdout)
