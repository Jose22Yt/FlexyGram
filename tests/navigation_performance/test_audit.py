"""Offline regressions for the read-only chat navigation inventory."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from audit import SOURCES, audit, main


NAV = """
public boolean presentFragment(NavigationParams params) {
    if (fragment == null || checkTransitionAnimation() || animationInProgress || startedTracking) {
        return false;
    }
    AndroidUtilities.runOnUIThread(waitingForKeyboardCloseRunnable, 250);
    AndroidUtilities.runOnUIThread(delayedOpenAnimationRunnable, 200);
}
public void closeLastFragment(boolean animated, boolean forceNoAnimation) {
    if (delegate != null || checkTransitionAnimation() || animationInProgress || startedTracking || fragmentsStack.isEmpty()) {
        return;
    }
    AndroidUtilities.runOnUIThread(waitingForKeyboardCloseRunnable, 200);
}
public void onBackPressed() {
    if (transitionAnimationPreviewMode || startedTracking || checkTransitionAnimation() || fragmentsStack.isEmpty()) {
        return;
    }
}
public boolean checkTransitionAnimation() {
    if (transitionAnimationPreviewMode) { return false; }
    if (transitionAnimationInProgress && (transitionAnimationStartTime < System.currentTimeMillis() - 1500 || inPreviewMode)) {
        onAnimationEndCheck(true);
    }
    return transitionAnimationInProgress;
}
private void onAnimationEndCheck(boolean byCheck) {
    if (currentAnimation != null) {
        if (byCheck) { currentAnimation.cancel(); }
        currentAnimation = null;
    }
}
"""
BASE = """
public boolean finishFragment(boolean animated) {
    if (isFinished || parentLayout == null) return false;
    finishing = true;
    parentLayout.closeLastFragment(animated);
    return true;
}
"""
DIALOGS = """
public boolean onTouchEvent(MotionEvent ev) {
    if (!parentLayout.checkTransitionAnimation() && !parentLayout.isInPreviewMode()) {
        return true;
    }
    return false;
}
"""


class NavigationAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("navigation", NAV)
        self.write("fragment", BASE)
        self.write("dialogs", DIALOGS)

    def write(self, name, data):
        path = self.root / SOURCES[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")

    def result(self):
        return audit(self.root)

    def test_expected_navigation_evidence_is_identified(self):
        r = self.result()
        self.assertEqual(r["required_count"], 11)
        self.assertEqual(r["found_count"], 11)
        self.assertEqual(r["missing_checks"], [])
        self.assertEqual(r["unreadable"], [])

    def test_conditional_waits_and_watchdog_are_not_confused(self):
        by_id = {x["id"]: x for x in self.result()["findings"]}
        self.assertEqual(by_id["TRANSITION_WATCHDOG"]["literal_delay_ms"], 1500)
        self.assertEqual(by_id["OPEN_KEYBOARD_WAIT"]["literal_delay_ms"], 250)
        self.assertEqual(by_id["OPEN_DEFERRED_WAIT"]["literal_delay_ms"], 200)
        self.assertEqual(by_id["CLOSE_KEYBOARD_WAIT"]["literal_delay_ms"], 200)
        self.assertEqual(by_id["TRANSITION_WATCHDOG"]["category"], "fallback")

    def test_open_gate_mutation_is_detected(self):
        self.write("navigation", NAV.replace(
            "fragment == null || checkTransitionAnimation() || animationInProgress",
            "fragment == null || animationInProgress"))
        self.assertIn("PRESENT_REJECTS_TRANSITION", self.result()["missing_checks"])

    def test_close_gate_mutation_is_detected(self):
        self.write("navigation", NAV.replace(
            "delegate != null || checkTransitionAnimation() || animationInProgress",
            "delegate != null || animationInProgress"))
        self.assertIn("CLOSE_REJECTS_TRANSITION", self.result()["missing_checks"])

    def test_back_gate_mutation_is_detected(self):
        self.write("navigation", NAV.replace(
            "startedTracking || checkTransitionAnimation() || fragmentsStack.isEmpty()",
            "startedTracking || fragmentsStack.isEmpty()"))
        self.assertIn("BACK_REJECTS_TRANSITION", self.result()["missing_checks"])

    def test_preview_special_case_mutation_is_detected(self):
        self.write("navigation", NAV.replace(
            "if (transitionAnimationPreviewMode) { return false; }",
            "if (transitionAnimationPreviewMode) { return true; }"))
        self.assertIn("PREVIEW_SPECIAL_CASE", self.result()["missing_checks"])

    def test_timeout_change_is_reported_without_claiming_improvement(self):
        self.write("navigation", NAV.replace("System.currentTimeMillis() - 1500",
                                             "System.currentTimeMillis() - 1700"))
        by_id = {x["id"]: x for x in self.result()["findings"]}
        self.assertEqual(by_id["TRANSITION_WATCHDOG"]["literal_delay_ms"], 1700)

    def test_unrelated_wait_outside_present_does_not_replace_missing_branch(self):
        edited = NAV.replace(
            "AndroidUtilities.runOnUIThread(delayedOpenAnimationRunnable, 200);", "")
        self.write("navigation", "// AndroidUtilities.runOnUIThread(delayedOpenAnimationRunnable, 200);\n"
                   + edited)
        self.assertIn("OPEN_DEFERRED_WAIT", self.result()["missing_checks"])

    def test_base_finish_delegate_change_is_detected(self):
        self.write("fragment", BASE.replace("return true;", "return false;"))
        self.assertIn("BASE_FINISH_DELEGATES", self.result()["missing_checks"])

    def test_dialog_swipe_gate_mutation_is_detected(self):
        self.write("dialogs", DIALOGS.replace(
            "!parentLayout.checkTransitionAnimation()", "true"))
        self.assertIn("DIALOG_SWIPE_TRANSITION_GATE", self.result()["missing_checks"])

    def test_missing_file_is_exposed_not_silently_skipped(self):
        (self.root / SOURCES["dialogs"]).unlink()
        self.assertTrue(self.result()["unreadable"])
        self.assertIn("DIALOG_SWIPE_TRANSITION_GATE", self.result()["missing_checks"])

    def test_strict_checks_source_integrity_not_timing_preferences(self):
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            self.assertEqual(main(["--repo", str(self.root), "--strict"]), 0)
        self.assertEqual(json.loads(capture.getvalue())["found_count"], 11)
        self.write("navigation", NAV.replace("System.currentTimeMillis() - 1500",
                                            "System.currentTimeMillis() - 900"))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--repo", str(self.root), "--strict"]), 0)
        self.write("navigation", NAV.replace(
            "AndroidUtilities.runOnUIThread(waitingForKeyboardCloseRunnable, 250);", ""))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--repo", str(self.root), "--strict"]), 1)

    def test_source_is_not_modified_by_audit(self):
        before = [(self.root / p).read_bytes() for p in SOURCES.values()]
        first = json.dumps(self.result(), sort_keys=True)
        second = json.dumps(self.result(), sort_keys=True)
        self.assertEqual(first, second)
        self.assertEqual(before, [(self.root / p).read_bytes() for p in SOURCES.values()])


if __name__ == "__main__":
    unittest.main()
