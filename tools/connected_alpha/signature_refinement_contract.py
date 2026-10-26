"""Exact presentation checkpoint over Alpha1275; reject unreviewed source mutations."""
from pathlib import Path
import hashlib
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = '8c47e5532a600f9a8b4ccbfdac5090d09a1075a0'
REVIEWED = {'TMessagesProj/src/main/java/app/flexygram/header/HeaderSettingsActivity.java': '042ad19c6c3e8088ffe014ca2790c8cdd81ae9ca458d330559ce70b771f354f8', 'TMessagesProj/src/main/java/app/flexygram/header/HeaderPreviewView.java': 'd5182bd6ff9d3a92728487a5594f6854d4bd6bdc75b24ba3f03fc79dd2cc81d7', 'tools/connected_alpha/alpha1275_contract.py': '599d5f7aa5eef5ca7c0b6d1d22b603a86031961ea973041c09d60526c91050ef', 'tools/connected_alpha/header_visual/HeaderVisualTest.java.in': '2cb10bfbffd73679c3f414bc6f3c795628f43939dd4e54ebf1b7af6749db1510', 'tools/connected_alpha/bubble_visual/CachedBlurVisualTest.java.in': 'd6077d567cc2b99b646101dec9bdc0a16abe9fcf0d60a99049893da0b56af330', 'TMessagesProj/src/main/java/app/flexygram/header/SignatureChatHeader.java': '6649005e8ef0e337502d2e0fbce82cbbd0c6d29bbf24bfc12f4e3e0dee15e172', 'tools/connected_alpha/refinement1274_contract.py': '1985e6e0cb88afbd0002ab00b3401e40da6ae7955ca079bdbda0046397bfabbb'}


def restore(path, data):
    path = str(path)
    if path not in REVIEWED:
        return data
    original = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
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
