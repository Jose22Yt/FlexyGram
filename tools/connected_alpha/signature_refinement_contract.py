"""Exact presentation checkpoint over Alpha1275; reject unreviewed source mutations."""
from pathlib import Path
import hashlib
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = '8c47e5532a600f9a8b4ccbfdac5090d09a1075a0'
REVIEWED = {'TMessagesProj/src/main/java/app/flexygram/header/HeaderSettingsActivity.java': '042ad19c6c3e8088ffe014ca2790c8cdd81ae9ca458d330559ce70b771f354f8', 'TMessagesProj/src/main/java/app/flexygram/header/HeaderPreviewView.java': 'd5182bd6ff9d3a92728487a5594f6854d4bd6bdc75b24ba3f03fc79dd2cc81d7', 'tools/connected_alpha/alpha1275_contract.py': '599d5f7aa5eef5ca7c0b6d1d22b603a86031961ea973041c09d60526c91050ef', 'tools/connected_alpha/header_visual/HeaderVisualTest.java.in': '2cb10bfbffd73679c3f414bc6f3c795628f43939dd4e54ebf1b7af6749db1510', 'tools/connected_alpha/bubble_visual/CachedBlurVisualTest.java.in': 'd6077d567cc2b99b646101dec9bdc0a16abe9fcf0d60a99049893da0b56af330', 'TMessagesProj/src/main/java/app/flexygram/header/SignatureChatHeader.java': '6649005e8ef0e337502d2e0fbce82cbbd0c6d29bbf24bfc12f4e3e0dee15e172', 'tools/connected_alpha/refinement1274_contract.py': '1445ea148db386e79aaaca45d16ceb1dbbc8bdb73d926aefb2a4b57227ca4bc5', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleConfig.java': 'fbc6001bae9a262a58111fd3c5033ec09954232a840e810f0c4962eaa0cdeff5', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleOutline.java': '1483f9ba4245b87c77377cd6e4a422ff2bdeada68964c8f205016b75f0ab68f9', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleSettingsActivity.java': '4b1fd7d195d9f826880e431dbdfec653c957ce5fe0e9c3c6a7e450a29c340de3', 'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/MessageDrawable.java': '027811ba83faba91fea61397b076749d987529f3dd5d7ba0583b4325e937f921', 'TMessagesProj/src/main/res/values-es/flexygram_bubbles.xml': 'ff97970e4a37bcd4d447721984aef966b73a87557b8bb1c2b93dfa3c02948eb8', 'TMessagesProj/src/main/res/values-ru/flexygram_bubbles.xml': '583809bb5395ecc47bc09d42d287deb74f3d037697f69f29424830d8990f8de7', 'TMessagesProj/src/main/res/values/flexygram_bubbles.xml': '38c19a58df0496335a9e1d0bac70e5100fac4a37a6938a0e887992739d07c625', 'tools/connected_alpha/bubble_visual/BubbleVisualTest.java.in': '110dea27ca7dec1293d866f306f5184a9af56cd6b091c12a9b93cce4d85dad95', 'tools/connected_alpha/bubble_visual/stubs.py': '4940fc3e82a259cdc5c1232e222183d912bcb60f8488bb1ade889d49703a0b85', 'TMessagesProj/src/main/java/app/flexygram/bubbles/SignatureBorderPath.java': 'f578ab1049a0096e5df9e297a4918af0339dd6aceb7b0e23c8e3e774e63f789a'}


def restore(path, data):
    path = str(path)
    if path not in REVIEWED:
        return data
    before = subprocess.run(['git', 'show', BASE + ':' + path], cwd=ROOT, capture_output=True)
    original = before.stdout if before.returncode == 0 else b''
    if before.returncode != 0 and data == b'':
        return data
    if hashlib.sha256(data).hexdigest() == REVIEWED[path]:
        return original
    # Historical audits may enter again after an earlier layer has restored its base.
    for revision in (BASE, '8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881',
                     '534b30c4edea3dffa0fc726eaec254ed8ebadbc1',
                     '751c926d91acd536d96b427af5f34f2fe6bedbc4'):
        accepted = subprocess.run(['git', 'show', revision + ':' + path], cwd=ROOT, capture_output=True)
        if accepted.returncode == 0 and data == accepted.stdout:
            return data
    raise ValueError('Unreviewed Signature Refinement delta: ' + path)
