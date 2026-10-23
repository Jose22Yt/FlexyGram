#!/usr/bin/env python3
"""Additional parity evidence. No runtime/performance claim."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UPSTREAM = '1ad6a60a6834ffca722b1a22f4fba27ecb29a061'
COMPONENTS = ['NativeLoader', 'FileLoader', 'DispatchQueue', 'DispatchQueuePoolBackground',
              'MusicPlayerService', 'NotificationsService', 'PushListenerController',
              'GooglePushListenerServiceProvider', 'UserConfig', 'SharedConfig', 'AndroidUtilities']


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    evidence = {}
    for name in COMPONENTS:
        path = f'TMessagesProj/src/main/java/org/telegram/messenger/{name}.java'
        data = (ROOT / path).read_bytes()
        if data != git('show', UPSTREAM + ':' + path):
            raise SystemExit('FAIL: upstream component changed: ' + path)
        evidence[path] = hashlib.sha256(data).hexdigest()
    native_tree = git('rev-parse', UPSTREAM + ':TMessagesProj/jni').decode().strip()
    if git('rev-parse', 'HEAD:TMessagesProj/jni').decode().strip() != native_tree:
        raise SystemExit('FAIL: committed JNI tree differs from original Exteraless')
    if git('diff', '--name-only', 'HEAD', '--', 'TMessagesProj/jni').strip():
        raise SystemExit('FAIL: tracked native worktree changes')
    print(json.dumps({'status': 'PASS_SOURCE_PARITY_ONLY', 'upstream': UPSTREAM,
                      'additional_components_identical': len(evidence), 'sha256': evidence,
                      'committed_jni_tree': native_tree, 'android_runtime': 'NOT_TESTED'}, indent=2))


if __name__ == '__main__':
    main()
