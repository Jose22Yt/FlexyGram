"""Reviewable presentation-only patch; reverse to exact native authentication source."""
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]
BASE='a261ccc3cf2fe1c4af46cb858bb3318b2310aeb8'
PATCH_PATHS=frozenset([
 'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java',
 'TMessagesProj/src/main/java/org/telegram/ui/IntroActivity.java',
 'TMessagesProj/src/main/java/org/telegram/ui/Components/OutlineTextContainerView.java',
 'TMessagesProj/src/main/java/app/exteraless/updater/GitHubUpdater.java',
 'TMessagesProj/src/main/java/app/exteraless/updater/UpdaterSheet.java'])
def restore_login_presentation(path, data):
    if path not in PATCH_PATHS: raise ValueError('Unreviewed login presentation path')
    patch=(ROOT/'tools/connected_alpha/login_native_presentation.patch').read_bytes()
    with tempfile.TemporaryDirectory(prefix='login-parity-') as directory:
        target=Path(directory)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
        result=subprocess.run(['git','apply','--reverse','--include='+path,'-'],cwd=directory,input=patch,capture_output=True)
        if result.returncode: raise ValueError('Login presentation differs from reviewed patch')
        return target.read_bytes()
