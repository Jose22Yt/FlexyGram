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

    def test_motion_guard_projects_only_the_exact_navigation_overlay(self):
        import instant_navigation1279_contract as handoff
        source=(ROOT/NAV).read_bytes()
        original=handoff.original(NAV)
        self.assertEqual(original,handoff.restore(NAV,source))
        for marker in (b"// unknown",b"\n"):
            changed=source+marker
            self.assertEqual(changed,handoff.restore(NAV,changed))
            self.assertNotEqual(original,handoff.restore(NAV,changed))
        guard=(ROOT/'tools/connected_alpha/test_flexy_motion.py').read_text()
        self.assertIn('new=restore_handoff(path,(ROOT/path).read_bytes()).decode()',guard)

    def test_historical_launcher_guard_projects_only_exact_reviewed_cleanup(self):
        import instant_navigation1279_contract as handoff
        from motion_contract import restore_navigation
        path="TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java"
        source=(ROOT/path).read_bytes()
        self.assertEqual(handoff.original(path),restore_navigation(path,source))
        mutations=[source+b"// unknown",source+b"\n",
            source.replace(b"cancelledLayout.onBackCancelled();",b"cancelledLayout.onBackInvoked();",1),
            source.replace(b"passcodeDialog != null",b"passcodeDialog == null",1)]
        for mutant in mutations:
            self.assertNotEqual(source,mutant)
            self.assertEqual(mutant,restore_navigation(path,mutant))
            self.assertNotEqual(handoff.original(path),restore_navigation(path,mutant))
        for path in ("TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java",
                     "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/Theme.java",
                     "TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java"):
            self.assertEqual(b"unknown",restore_navigation(path,b"unknown"))

    def test_timed_scope_rejects_modified_hunks_and_preserves_unknown_bytes(self):
        import importlib.util
        path=ROOT/'tools/connected_alpha/motion/timed_gesture_scope.py'
        spec=importlib.util.spec_from_file_location('timed_scope_probe',path)
        scope=importlib.util.module_from_spec(spec);spec.loader.exec_module(scope)
        spec=importlib.util.spec_from_file_location('reveal_scope_probe',ROOT/'tools/connected_alpha/motion/reveal_scope.py')
        reveal=importlib.util.module_from_spec(spec);spec.loader.exec_module(reveal)
        for name in (scope.ACTION,scope.HELPER,scope.BRIDGE):
            source=(ROOT/name).read_text()
            if name==scope.ACTION:
                a=source.index('    private FlexyInstantNavigationCoordinator instantNavigation;')
                b=source.index('    @Override\n    public void requestDisallowInterceptTouchEvent',a)
                source=source[:a]+source[b:]
            restored=scope.restore(name,reveal.restore(name,source))
            self.assertNotEqual(source,restored)
            self.assertEqual(restored+'// unknown',scope.restore(name,reveal.restore(name,source+'// unknown')))
        helper=(ROOT/scope.HELPER).read_text()
        with self.assertRaises(AssertionError):
            scope.restore(scope.HELPER,helper.replace('commitStartAlpha = closingAlpha;', 'commitStartAlpha = 0;',1))

    def test_reveal_scope_and_original_touch_wrapper_are_fail_closed(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('reveal_scope_test',ROOT/'tools/connected_alpha/motion/reveal_scope.py')
        scope=importlib.util.module_from_spec(spec);spec.loader.exec_module(scope)
        source=(ROOT/NAV).read_text()
        self.assertEqual(1,source.count('public boolean dispatchTouchEvent(MotionEvent event)'))
        self.assertIn('return dispatchNativeRevealTouch(event);',source)
        self.assertIn('handled = dispatchNativeRevealTouch(event);',source)
        self.assertIn('instantRevealDrawX - instantRevealHitX',source)
        self.assertIn('findInstantRevealRow(surface, windowX, windowY, 0) != 1',source)
        a=source.index('    private FlexyInstantNavigationCoordinator instantNavigation;')
        b=source.index('    @Override\n    public void requestDisallowInterceptTouchEvent',a)
        source=source[:a]+source[b:]
        restored=scope.restore(NAV,source)
        self.assertNotEqual(source,restored)
        self.assertEqual(restored+'// unknown',scope.restore(NAV,source+'// unknown'))
        for old,new in [('&& !revealOpen','&& revealOpen'),
                        ('setInstantRevealTranslationX(containerView,','containerView.setTranslationX('),
                        ('!instantNavigation.isCurrent(fallbackGeneration)','instantNavigation.isCurrent(fallbackGeneration)')]:
            mutant=source.replace(old,new,1)
            self.assertNotEqual(source,mutant)
            with self.assertRaises(AssertionError):scope.restore(NAV,mutant)

    def test_actual_coordinator_protocol(self):
        import subprocess,tempfile
        with tempfile.TemporaryDirectory() as folder:
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',folder,
                str(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/FlexyInstantNavigationCoordinator.java'),
                str(ROOT/'tools/connected_alpha/motion/InstantNavigationCoordinatorTest.java')],check=True)
            subprocess.run(['java','-cp',folder,'InstantNavigationCoordinatorTest'],check=True)

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
        self.assertIn("outgoingDialog != null && outgoingDialog.isShowing()", source)
        self.assertIn("destinationDialog != null && destinationDialog.isShowing()", source)
        self.assertIn("activityDialog != null && activityDialog.isShowing()", source)
        self.assertNotIn("MotionEvent.obtain(", source[source.index("private boolean tryHandoffClosingChatDown"):source.index("public void requestDisallowInterceptTouchEvent")])


if __name__ == "__main__":
    unittest.main()
