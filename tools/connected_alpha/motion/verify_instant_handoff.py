#!/usr/bin/env python3
"""Fail-closed source scope check for the experimental one-touch handoff."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java"
BASE_GIT_BLOB = "78b0b482add965ca590d9da397bc083dd7a5ab3c"

START = "    private FlexyInstantNavigationCoordinator instantNavigation;"
END = "    @Override\n    public void requestDisallowInterceptTouchEvent"
ORIGINAL = (
    "    @Override\n"
    "    public boolean onInterceptTouchEvent(MotionEvent ev) {\n"
    "        return animationInProgress || checkTransitionAnimation() || onTouchEvent(ev);\n"
    "    }\n\n"
)
NEW_IMPORT = "import org.telegram.ui.DialogsActivity;\n"


def main() -> None:
    content = SOURCE.read_text(encoding="utf-8")
    assert content.count(START) == 1, "Handoff block must have one owner"
    assert content.count(END) == 1, "Native dispatch anchor changed"
    assert content.count(NEW_IMPORT) == 1, "Missing or duplicate DialogsActivity import"
    start = content.index(START)
    end = content.index(END, start)
    delta = content[start:end]

    # Guard the exact change in control flow and forbid synthetic/replayed touch.
    for required in (
        "event.getActionMasked() != MotionEvent.ACTION_DOWN",
        "onCloseAnimationEndRunnable == null",
        "isRightLayout || sheetFragment != null",
        "outgoingDialog != null && outgoingDialog.isShowing()",
        "destinationDialog != null && destinationDialog.isShowing()",
        "activityDialog != null && activityDialog.isShowing()",
        "destination instanceof MainTabsActivity || destination instanceof DialogsActivity",
        "FlexyNavigationHandoffPolicy.canHandoffClosingDown(",
        "onAnimationEndCheck(true);",
        "getLastFragment() == destination;",
        "setInnerTranslationX(0);",
        "swipeProgress = 1f;",
        "if (tryHandoffSettlingChatDown(ev) || tryHandoffClosingChatDown(ev)) {\n            return false;",
        "!instantSwipeSettlingClosing || !animationInProgress || !startedTracking",
        "backAnimator != null || velocityTracker != null",
        "!currentSpringAnimation.canContinue()",
        "settling.finishNow()",
    ):
        assert required in delta, "Missing safety contract: " + required
    for prohibited in ("MotionEvent.obtain(", "dispatchTouchEvent(", "performClick(", "postDelayed("):
        assert prohibited not in delta, "No synthetic event, injected click or wait: " + prohibited

    reconstructed = (content[:start] + ORIGINAL + content[end:]).replace(NEW_IMPORT, "", 1)
    gesture_begin = "        try { // Instant gesture owns pending state only during native admission.\n"
    gesture_finish = "        } finally {\n            clearInstantBackSeed();\n            if (!instantGestureActive) clearInstantGesture();\n        }"
    assert reconstructed.count(gesture_begin) == 1 and reconstructed.count(gesture_finish) == 1
    ga = reconstructed.index(gesture_begin)
    gb = reconstructed.index(gesture_finish, ga)
    gesture_native = reconstructed[ga + len(gesture_begin):gb]
    assert all(not line or line.startswith("    ") for line in gesture_native.splitlines())
    reconstructed = reconstructed[:ga] + "\n".join(line[4:] if line else "" for line in gesture_native.splitlines()) + reconstructed[gb + len(gesture_finish):]
    for gesture_hook in (
        "        if (!prepareInstantGestureBack()) return false;\n",
        "        adoptInstantGesture(currentFragment);\n",
        "        if (applyInstantGestureProgress(t)) return;\n",
        "        clearInstantGesture();\n",
        "        velX = prepareInstantGestureSettleVelocity(velX);\n",
        "            final boolean instantGestureOwned = instantGestureActive;\n",
        "            final long instantGestureTicket = instantGestureGeneration;\n",
        "                if (instantGestureOwned && instantNavigation != null) instantNavigation.complete(instantGestureTicket);\n",
    ):
        assert reconstructed.count(gesture_hook) == 1, "Unexpected opening gesture hook: " + gesture_hook
        reconstructed = reconstructed.replace(gesture_hook, "")
    terminal_guard = "        if (consumeAbandonedInstantGesture()) return;\n"
    assert reconstructed.count(terminal_guard) == 2
    reconstructed = reconstructed.replace(terminal_guard, "")
    for gesture_hook, count in (
        ("                    if (instantGestureOwned && isObsoleteInstantFrame(animation, instantGestureTicket)) return;\n", 3),
        ("                if (instantGestureOwned && isObsoleteInstantFrame(animation, instantGestureTicket)) return;\n", 2),
    ):
        assert reconstructed.count(gesture_hook) == count
        reconstructed = reconstructed.replace(gesture_hook, "")
    renderer_begin = "                if (instantGestureOwned) {\n                    renderInstantGestureValue(value);\n                } else { // Preserve the unowned native gesture renderer.\n"
    assert reconstructed.count(renderer_begin) == 1
    ra = reconstructed.index(renderer_begin)
    rb = reconstructed.index("\n                }\n\n                if (!backAnimation)", ra)
    native_renderer = reconstructed[ra + len(renderer_begin):rb]
    assert all(not line or line.startswith("    ") for line in native_renderer.splitlines())
    reconstructed = reconstructed[:ra] + "\n".join(line[4:] if line else "" for line in native_renderer.splitlines()) + reconstructed[rb + len("\n                }"):]
    gesture_initial = "new FloatValueHolder(instantGestureActive ? instantGestureValue : (x / containerView.getMeasuredWidth()) * SPRING_MULTIPLIER)"
    assert reconstructed.count(gesture_initial) == 1
    reconstructed = reconstructed.replace(gesture_initial, "new FloatValueHolder((x / containerView.getMeasuredWidth()) * SPRING_MULTIPLIER)")
    # Remove only the synchronous seed scope around the unchanged native Back body.
    begin = "        try { // Instant Back owns a seed only within this native call.\n"
    finish = "        } finally {\n            clearInstantBackSeed();\n        }"
    assert reconstructed.count(begin) == 1 and reconstructed.count(finish) == 1
    a = reconstructed.index(begin)
    b = reconstructed.index(finish, a)
    native_back = reconstructed[a + len(begin):b]
    assert all(line.startswith("    ") for line in native_back.splitlines())
    reconstructed = reconstructed[:a] + "\n".join(line[4:] for line in native_back.splitlines()) + reconstructed[b + len(finish):]
    seeded_factory = "            currentSpringAnimation = createInstantLayoutSpring(open, preview);"
    original_factory = """            FloatValueHolder valueHolder = new FloatValueHolder(0);
            currentSpringAnimation = new SpringAnimation(this, valueHolder)
                    .setSpring(new SpringForce(SPRING_MULTIPLIER)
                            .setStiffness(preview ? open ? SPRING_STIFFNESS_PREVIEW : SPRING_STIFFNESS_PREVIEW_OUT : SPRING_STIFFNESS)
                            .setDampingRatio(preview ? 0.6f : 1f));"""
    assert reconstructed.count(seeded_factory) == 1
    reconstructed = reconstructed.replace(seeded_factory, original_factory)
    frame_generation = "            final long springGeneration = instantNavigation == null ? 0 : instantNavigation.generation();\n"
    assert reconstructed.count(frame_generation) == 1
    reconstructed = reconstructed.replace(frame_generation, "")
    frame_entry = "                if (isObsoleteInstantFrame(animation, springGeneration)) return;\n"
    frame_callback = "                    if (isObsoleteInstantFrame(animation, springGeneration)) return;\n"
    assert reconstructed.count(frame_entry) == 4 and reconstructed.count(frame_callback) == 2
    reconstructed = reconstructed.replace(frame_callback, "").replace(frame_entry, "")
    hooks = (
        ("        if (!prepareInstantBack()) return;\n", 1),
        ("        final long instantGeneration = instantNavigation == null ? 0 : instantNavigation.generation();\n", 1),
        ("        final SpringAnimation endingSpring = currentSpringAnimation;\n", 1),
        ("        final Animator endingAnimator = currentAnimation;\n", 1),
        ("        final Runnable endingFrame = animationRunnable;\n", 1),
        ("        if (isObsoleteInstantCompletion(instantGeneration, endingSpring, endingAnimator, endingFrame)) return;\n", 2),
        ("            final long closeGeneration = instantNavigation == null ? 0 : instantNavigation.generation();\n", 1),
        ("                if (instantNavigation != null && !instantNavigation.isCurrent(closeGeneration)) return;\n", 1),
        ("        if (instantNavigation != null) instantNavigation.complete(instantGeneration);\n", 1),
        ("        reportInstantNavigation(FlexyInstantNavigationCoordinator.State.OPENING, fragment,\n                fragment instanceof ChatActivity ? FlexyInstantNavigationCoordinator.Kind.OPEN_CHAT : FlexyInstantNavigationCoordinator.Kind.OPEN_SCREEN);\n", 1),
        ("        reportInstantNavigation(FlexyInstantNavigationCoordinator.State.CLOSING, getLastFragment(), FlexyInstantNavigationCoordinator.Kind.BACK);\n", 1),
    )
    for hook, count in hooks:
        assert reconstructed.count(hook) == count, "Unexpected coordinator hook scope"
        reconstructed = reconstructed.replace(hook, "")
    spring_end = "                final long endingGeneration = instantNavigation == null ? 0 : instantNavigation.generation();\n"
    spring_reset = "                if (instantNavigation == null || instantNavigation.isCurrent(endingGeneration)) setInnerTranslationX(0);"
    assert reconstructed.count(spring_end) == 1 and reconstructed.count(spring_reset) == 1, "Unexpected spring completion scope"
    reconstructed = reconstructed.replace(spring_end, "").replace(spring_reset, "                setInnerTranslationX(0);")
    finishing = """                Animator finishingBackAnimator = backAnimator;
                finishingBackAnimator.end();
                if (backAnimator == finishingBackAnimator) backAnimator = null;"""
    assert reconstructed.count(finishing) == 1
    reconstructed = reconstructed.replace(finishing, "                backAnimator.end();\n                backAnimator = null;")
    for first, last, end_parameter in (
        ("    private void animatePredictiveBackEndAnimation(", "    private void resetPredictiveBackState()", "animation"),
        ("    private void animateBackEndAnimation(", "    @Override\n    public void onBackPressed()", "animator"),
    ):
        a = reconstructed.index(first)
        b = reconstructed.index(last, a)
        renderer = reconstructed[a:b]
        cancel_guard = "                if (backAnimator != animation) return;\n                backAnimator = null;\n"
        end_guard = "                if (cancelled || backAnimator != " + end_parameter + ") return;\n                backAnimator = null;"
        assert renderer.count(cancel_guard) == 1 and renderer.count(end_guard) == 1
        renderer = renderer.replace(cancel_guard, "").replace(end_guard, "                if (cancelled) return;")
        for callback in ("onSlideAnimationEnd(true);", "onSlideAnimationEnd(backAnimation);"):
            line = "                " + callback
            assert renderer.count(line) == 1
            renderer = renderer.replace(line, line + "\n                backAnimator = null;")
        reconstructed = reconstructed[:a] + renderer + reconstructed[b:]
    for swipe_hook in (
        "                instantSwipeSettlingClosing = false;\n",
        "            instantSwipeSettlingClosing = !backAnimation && !predictiveBackInProgress;\n",
        "        instantSwipeSettlingClosing = false;\n",
    ):
        assert reconstructed.count(swipe_hook) == 1, "Unexpected released-swipe scope"
        reconstructed = reconstructed.replace(swipe_hook, "")
    data = reconstructed.encode("utf-8")
    blob_sha = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    assert blob_sha == BASE_GIT_BLOB, (
        f"Unreviewed ActionBarLayout change: {blob_sha} != {BASE_GIT_BLOB}; "
        "rebase and explicitly review new upstream edits"
    )
    print("Instant handoff scope: PASS (entire upstream ActionBarLayout recovered byte-for-byte)")


if __name__ == "__main__":
    main()
