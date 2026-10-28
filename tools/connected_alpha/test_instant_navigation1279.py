"""Post-Alpha1279 Instant Navigation P1 exact-byte and safety regression."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
NAV = "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java"
POLICY = "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/FlexyNavigationHandoffPolicy.java"


class InstantNavigation1279Regression(unittest.TestCase):
    def test_reviewed_scope_and_frozen_projection(self):
        import integration1279_contract as integration
        import instant_navigation1279_contract as handoff
        handoff.verify_current()
        integration.verify_current()
        source = (ROOT / NAV).read_bytes()
        self.assertEqual(handoff.original(NAV), handoff.restore(NAV, source))
        self.assertEqual(source + b"// unknown", handoff.restore(NAV, source + b"// unknown"))
        for scope in ("base", "motion", "smart"):
            self.assertEqual(integration.project(scope, NAV, handoff.original(NAV)),
                             integration.project(scope, NAV, source))

    def test_new_policy_rejects_unknown_bytes(self):
        import instant_navigation1279_contract as handoff
        source = (ROOT / POLICY).read_bytes()
        self.assertEqual(b"", handoff.restore(POLICY, source))
        self.assertEqual(source + b"// unknown", handoff.restore(POLICY, source + b"// unknown"))
        self.assertIn(b"boolean canHandoffClosingDown", source)
        self.assertNotIn(b"MotionEvent.obtain(", source)

    def test_original_actionbar_guards_still_exist(self):
        source = (ROOT / NAV).read_text(encoding="utf-8")
        self.assertIn("return animationInProgress || checkTransitionAnimation() || onTouchEvent(ev);", source)
        self.assertIn("onCloseAnimationEndRunnable == null", source)
        self.assertIn("getLastFragment() == destination", source)
        self.assertIn("setInnerTranslationX(0);", source)
        self.assertIn("swipeProgress = 1f;", source)
        self.assertNotIn("MotionEvent.obtain(", source[source.index("private boolean tryHandoffClosingChatDown"):source.index("public void requestDisallowInterceptTouchEvent")])


if __name__ == "__main__":
    unittest.main()
