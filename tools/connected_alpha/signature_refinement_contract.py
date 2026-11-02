"""Exact presentation checkpoint over Alpha1275; reject unreviewed source mutations."""
from pathlib import Path
import hashlib
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = '8c47e5532a600f9a8b4ccbfdac5090d09a1075a0'
REVIEWED = {'TMessagesProj/src/main/java/app/flexygram/header/HeaderSettingsActivity.java': '042ad19c6c3e8088ffe014ca2790c8cdd81ae9ca458d330559ce70b771f354f8', 'TMessagesProj/src/main/java/app/flexygram/header/HeaderPreviewView.java': 'bd53f21f573e2c232b9f556dcff4e19c923875d1d4deeafc48f459a35bd7cd35', 'tools/connected_alpha/alpha1275_contract.py': '599d5f7aa5eef5ca7c0b6d1d22b603a86031961ea973041c09d60526c91050ef', 'tools/connected_alpha/header_visual/HeaderVisualTest.java.in': '2cb10bfbffd73679c3f414bc6f3c795628f43939dd4e54ebf1b7af6749db1510', 'tools/connected_alpha/bubble_visual/CachedBlurVisualTest.java.in': '7ed0fc0351645908bb84e66a310a6815d76851c827dd19d17431061933bc87d5', 'TMessagesProj/src/main/java/app/flexygram/header/SignatureChatHeader.java': 'fbbba7cac9cb9b5fa13543bb4863433a235ef4222ad0a7b6f7a1fee14900d5cf', 'tools/connected_alpha/refinement1274_contract.py': '706463989d6e06104b57bd676efe664022eea0b2fa90c50d09ee71c862b868db', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleConfig.java': 'fbc6001bae9a262a58111fd3c5033ec09954232a840e810f0c4962eaa0cdeff5', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleOutline.java': '1483f9ba4245b87c77377cd6e4a422ff2bdeada68964c8f205016b75f0ab68f9', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleSettingsActivity.java': '6601701871d3e0fe4334b438f00b1f6b41640513e8dd2bae8bd104027838c4ad', 'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/MessageDrawable.java': '027811ba83faba91fea61397b076749d987529f3dd5d7ba0583b4325e937f921', 'TMessagesProj/src/main/res/values-es/flexygram_bubbles.xml': 'ff97970e4a37bcd4d447721984aef966b73a87557b8bb1c2b93dfa3c02948eb8', 'TMessagesProj/src/main/res/values-ru/flexygram_bubbles.xml': '583809bb5395ecc47bc09d42d287deb74f3d037697f69f29424830d8990f8de7', 'TMessagesProj/src/main/res/values/flexygram_bubbles.xml': '38c19a58df0496335a9e1d0bac70e5100fac4a37a6938a0e887992739d07c625', 'tools/connected_alpha/bubble_visual/BubbleVisualTest.java.in': '110dea27ca7dec1293d866f306f5184a9af56cd6b091c12a9b93cce4d85dad95', 'tools/connected_alpha/bubble_visual/stubs.py': '1d535708a44c1777c42cfb19c33c011bbe0281cbdbff3448542afb4182a8aa4b', 'TMessagesProj/src/main/java/app/flexygram/bubbles/SignatureBorderPath.java': 'f578ab1049a0096e5df9e297a4918af0339dd6aceb7b0e23c8e3e774e63f789a', 'TMessagesProj/src/main/java/app/flexygram/bubbles/SignatureWallpaperBlur.java': '6924e34dfb421342b09dea44252b9ccb1f35bcbe672e317323f1eca9f9430539', 'TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java': 'a914f14ee648cc8072b33b046e05da8b100753021216120809f70f32bfbe8dbe', 'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java': '0d112aee4544889f4ef033073301214c0ccb751e9278baa48587afcc04ce0907', 'TMessagesProj/src/main/java/app/flexygram/bubbles/BubblePreviewView.java': '77c6a295eb1bef71ee480d8d0bdb2b4e80b8163fdc3c167524753ff6f2f2b292', 'TMessagesProj/src/main/java/app/flexygram/composer/FlexyComposerSettingsActivity.java': 'afa9eb8e67bc930e0ca47006b359da3bae6abd36e06fbed008c06e96787a6285', 'TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java': 'f35ba19e8a741e6635d704e8163a82f71a098a6b7510940de34b5e3c3ea8273d', 'TMessagesProj/src/main/java/org/telegram/ui/Components/ChatAvatarContainer.java': '64893d0a3643498c0b6e0829035fa4734f3e923d76878a15a9242659042edfc9', 'TMessagesProj/src/main/res/values-es/flexygram_header.xml': '63c23fb38619dc5f2162c64d3e88d50112c75e662ff542ba778fd4e0a5679798', 'TMessagesProj/src/main/res/values-ru/flexygram_header.xml': '878677ee83fdeaa720807d69082f808b9bfd531d0a82fdb95ab89ab83f6e24e1', 'TMessagesProj/src/main/res/values/flexygram_header.xml': 'f8c37bf6b83f00c35032db9e927dbe98b8db1808867362938e06d6258c05d4f1', 'tools/connected_alpha/bubble_visual/BubblePreviewVisualTest.java.in': 'b552c40b198bf34a1b73a6840ce06b3154faed2a489693fde48adfa2bb874b8d', 'TMessagesProj/src/main/java/app/flexygram/preview/SignatureWallpaperPreview.java': '048ef9d7ff1c98e39e1bcd6148ab37201f94ba308b2962e8c005d51f720ad556', 'tools/connected_alpha/test_flexy_composer.py': 'd533c4c8dc84938442e83dab0ac0ebcfb4bff5e92e15aae580c84f02a427a8ff', 'tools/connected_alpha/test_stabilization1272.py': '04b49491f92aa60b0156491b916403a9935f9723b9e0463023f9e0c32cf99058', 'TMessagesProj/src/main/java/app/flexygram/files/core/SelectedDocument.java': 'd431e26028001f024b2bdec4b56f17617341f3d6aaedc93293d5b8ff9ef7bcc4', 'tools/connected_alpha/test_flexyfiles_core.py': '24651b8a9fb26b59aa8018b049962551ef13da807bd2b1ec65002e077df12800', 'tools/connected_alpha/test_bubbles1270.py': '69fa73956791c78c37e18f40e683571f47f65137ff0cbe408d8bc801d591c2bf'}


def restore(path, data):
    path = str(path)
    from files_completion_contract import restore as restore_files
    data = restore_files(path, data)
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
                     '751c926d91acd536d96b427af5f34f2fe6bedbc4',
                     '43e14d876601d16890b8c6f24c515103e6ece54f',
                     '8619ba40fbd8fd9d9d898ff307fb0c0716661254',
                     '997ac40a65be00c672dc8009b61f55825537d498',
                     '0e359f0e7841a99d61c79f996dd162b7c836a9bf'):
        accepted = subprocess.run(['git', 'show', revision + ':' + path], cwd=ROOT, capture_output=True)
        if accepted.returncode == 0 and data == accepted.stdout:
            return data
    raise ValueError('Unreviewed Signature Refinement delta: ' + path)
