"""Exact reviewed P10 hunks, reversed before whole-class native-byte verification.

Unknown changes within or outside the listed hunks are never projected away.
The P1-P9 checks still reconstruct their original complete native classes.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ACTION = "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java"
HELPER = "TMessagesProj/src/main/java/app/exteraless/utils/PredictiveBackAnimationHelper.java"
BRIDGE = "TMessagesProj/src/main/java/app/flexygram/motion/SpringAnimation.java"

def restore(path, content):
    for patch in json.loads((Path(__file__).with_name("timed_gesture_review.json")).read_text())[path]:
        assert content.count(patch["after"]) == 1, "Unreviewed timed gesture hunk: " + path
        content = content.replace(patch["after"], patch["before"], 1)
    return content
