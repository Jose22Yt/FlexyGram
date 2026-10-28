#!/usr/bin/env python3
"""Fail-closed source scope check for the experimental one-touch handoff."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java"
BASE_GIT_BLOB = "78b0b482add965ca590d9da397bc083dd7a5ab3c"

START = "    /**\n     * One-touch handoff for an exposed chat-list surface"
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
        "destination instanceof MainTabsActivity || destination instanceof DialogsActivity",
        "FlexyNavigationHandoffPolicy.canHandoffClosingDown(",
        "onAnimationEndCheck(true);",
        "getLastFragment() == destination;",
        "if (tryHandoffClosingChatDown(ev)) {\n            return false;",
    ):
        assert required in delta, "Missing safety contract: " + required
    for prohibited in ("MotionEvent.obtain(", "dispatchTouchEvent(", "performClick(", "postDelayed("):
        assert prohibited not in delta, "No synthetic event, injected click or wait: " + prohibited

    reconstructed = (content[:start] + ORIGINAL + content[end:]).replace(NEW_IMPORT, "", 1)
    data = reconstructed.encode("utf-8")
    blob_sha = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    assert blob_sha == BASE_GIT_BLOB, (
        f"Unreviewed ActionBarLayout change: {blob_sha} != {BASE_GIT_BLOB}; "
        "rebase and explicitly review new upstream edits"
    )
    print("Instant handoff scope: PASS (entire upstream ActionBarLayout recovered byte-for-byte)")


if __name__ == "__main__":
    main()
