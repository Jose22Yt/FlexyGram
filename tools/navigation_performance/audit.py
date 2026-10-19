"""Read-only, source-grounded inventory of FlexyGram's chat-navigation gates.

This tool does NOT measure real latency, suggest removing transition guards,
modify Java, or claim that every deliberate delay is a performance regression.
Run against the exact SHA being reviewed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

SOURCES = {
    "navigation": "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java",
    "fragment": "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/BaseFragment.java",
    "dialogs": "TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java",
}
# Each expression must match close to its specific method. A random occurrence of
# "animationInProgress" elsewhere in a 4,000-line file is NOT sufficient.
CHECKS = (
    ("PRESENT_REJECTS_TRANSITION", "navigation", "public boolean presentFragment(NavigationParams params)",
     r"if\s*\([^;]{0,250}checkTransitionAnimation\(\)[^;]{0,110}animationInProgress[^;]{0,110}startedTracking", 1100,
     "gate", "Present returns false while a transition or tracking state is active."),
    ("CLOSE_REJECTS_TRANSITION", "navigation", "public void closeLastFragment(boolean animated, boolean forceNoAnimation)",
     r"if\s*\([^;]{0,260}checkTransitionAnimation\(\)[^;]{0,110}animationInProgress[^;]{0,110}startedTracking", 1100,
     "gate", "Close returns without action while a transition or tracking state is active."),
    ("BACK_REJECTS_TRANSITION", "navigation", "public void onBackPressed()",
     r"if\s*\([^;]{0,150}checkTransitionAnimation\(\)[^;]{0,100}fragmentsStack\.isEmpty\(\)", 550,
     "gate", "Back is ignored while a transition/tracking state is active."),
    ("TRANSITION_WATCHDOG", "navigation", "public boolean checkTransitionAnimation()",
     r"transitionAnimationInProgress[^;]{0,160}System\.currentTimeMillis\(\)\s*-\s*(\d+)", 600,
     "fallback", "A stale animation can be terminated by an elapsed-time fallback."),
    ("PREVIEW_SPECIAL_CASE", "navigation", "public boolean checkTransitionAnimation()",
     r"if\s*\(\s*transitionAnimationPreviewMode\s*\)\s*\{\s*return false", 600,
     "exception", "Preview-mode handling must be studied separately from normal transitions."),
    ("OPEN_KEYBOARD_WAIT", "navigation", "public boolean presentFragment(NavigationParams params)",
     r"AndroidUtilities\.runOnUIThread\(waitingForKeyboardCloseRunnable,\s*(\d+)\)", 20000,
     "conditional_wait", "A keyboard-dependent branch schedules opening later."),
    ("OPEN_DEFERRED_WAIT", "navigation", "public boolean presentFragment(NavigationParams params)",
     r"AndroidUtilities\.runOnUIThread\(delayedOpenAnimationRunnable,\s*(\d+)\)", 20000,
     "conditional_wait", "A branch using needDelayOpenAnimation schedules opening later."),
    ("CLOSE_KEYBOARD_WAIT", "navigation", "public void closeLastFragment(boolean animated, boolean forceNoAnimation)",
     r"AndroidUtilities\.runOnUIThread\(waitingForKeyboardCloseRunnable,\s*(\d+)\)", 11500,
     "conditional_wait", "A keyboard-dependent closing branch schedules its transition later."),
    ("ANIMATION_END_CLEANUP", "navigation", "private void onAnimationEndCheck(boolean byCheck)",
     r"if\s*\(\s*byCheck\s*\)\s*\{\s*currentAnimation\.cancel\(\)", 1150,
     "cleanup", "Timeout/cancellation already has animation cleanup and lifecycle work."),
    ("BASE_FINISH_DELEGATES", "fragment", "public boolean finishFragment(boolean animated)",
     r"parentLayout\.closeLastFragment\(animated\)\s*;\s*return true", 450,
     "semantics", "The wrapper returns true after invoking a void close method; measure actual acceptance."),
    ("DIALOG_SWIPE_TRANSITION_GATE", "dialogs", "public boolean onTouchEvent(MotionEvent ev)",
     r"!parentLayout\.checkTransitionAnimation\(\)", 1400,
     "gate", "Dialogs swipe navigation is guarded during transitions."),
)


def _method_body(source: str, anchor: str) -> tuple[int, str] | None:
    """Return the span of one Java method; never inspect a neighboring method.

    Mask comments and Java string/character literals before matching braces and evidence.
    The mask preserves offsets so evidence lines refer to the real source.
    """
    masked = re.sub(
        r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
        lambda match: " " * len(match.group(0)),
        source,
    )
    start = masked.find(anchor)
    if start == -1:
        return None
    opening = masked.find("{", start + len(anchor))
    if opening < 0 or ";" in masked[start + len(anchor):opening]:
        return None
    nesting = 0
    for index in range(opening, len(masked)):
        if masked[index] == "{":
            nesting += 1
        elif masked[index] == "}":
            nesting -= 1
            if nesting == 0:
                return opening + 1, masked[opening + 1:index]
    return None


def audit(root: Path) -> dict:
    root = Path(root)
    data: dict[str, str] = {}
    unreadable = []
    for name, rel in SOURCES.items():
        try:
            data[name] = (root / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            unreadable.append({"file": rel, "error": type(exc).__name__})

    findings = []
    missing = []
    for code, name, anchor, pattern, width, category, meaning in CHECKS:
        source = data.get(name)
        if source is None:
            missing.append(code)
            continue
        method = _method_body(source, anchor)
        if method is None:
            missing.append(code)
            continue
        offset, body = method
        match = re.search(pattern, body[:width], flags=re.DOTALL)
        if match is None:
            missing.append(code)
            continue
        pos = offset + match.start()
        line = source.count("\n", 0, pos) + 1
        record = {
            "id": code,
            "file": SOURCES[name],
            "line": line,
            "category": category,
            "source_line": source.splitlines()[line - 1].strip()[:240],
            "interpretation": meaning,
        }
        if match.groups():
            record["literal_delay_ms"] = int(match.group(1))
        findings.append(record)
    return {
        "schema": 1,
        "scope": "static navigation evidence; no device latency measurements",
        "found_count": len(findings),
        "required_count": len(CHECKS),
        "findings": findings,
        "unreadable": unreadable,
        "missing_checks": missing,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--strict", action="store_true",
                        help="fail when expected source anchors change, not for intentional waits")
    args = parser.parse_args(argv)
    report = audit(args.repo)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(bool(args.strict and (report["missing_checks"] or report["unreadable"])))


if __name__ == "__main__":
    sys.exit(main())
