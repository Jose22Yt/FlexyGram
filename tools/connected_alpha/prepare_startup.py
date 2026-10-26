"""Refresh only the explicit reviewed startup inventory; never hide arbitrary changes."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
PATHS=[
'TMessagesProj/src/main/java/app/flexygram/performance/StartupAccounts.java',
'TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java',
'TMessagesProj/src/main/java/org/telegram/messenger/MessagesStorage.java',
'TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java',
'TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java',
 'tools/connected_alpha/startup_contract.py','tools/connected_alpha/files_completion_contract.py',
 'tools/connected_alpha/test_startup.py','tools/connected_alpha/prepare_startup.py',
 'tools/connected_alpha/performance/STARTUP.md',
'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleConfig.java',
'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleOutline.java',
'TMessagesProj/src/main/java/app/flexygram/bubbles/BubblePreviewView.java',
'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleSettingsActivity.java',
'TMessagesProj/src/main/java/app/flexygram/bubbles/SignatureBorderPath.java',
'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/MessageDrawable.java',
'TMessagesProj/src/main/res/values/flexygram_bubbles.xml',
'TMessagesProj/src/main/res/values-es/flexygram_bubbles.xml',
'TMessagesProj/src/main/res/values-ru/flexygram_bubbles.xml',
 'tools/connected_alpha/bubble_visual/BubblePreviewVisualTest.java.in',
 'tools/connected_alpha/bubble_visual/BubbleVisualTest.java.in',
 'tools/connected_alpha/bubble_visual/stubs.py',
'TMessagesProj/src/main/java/app/flexygram/files/FlexyFilesSheet.java',
'TMessagesProj/src/main/java/app/flexygram/files/FlexyFileEditorActivity.java',
'TMessagesProj/src/main/java/app/flexygram/files/FlexyFiles.java',
'TMessagesProj/src/main/java/app/flexygram/files/FlexyEditorToolsSheet.java',
'TMessagesProj/src/main/java/app/flexygram/files/FlexyEditorFileTypes.java',
'TMessagesProj/src/main/java/app/flexygram/files/FlexyFilesDirectSend.java',
'TMessagesProj/src/main/res/values/flexyfiles_signature.xml',
'TMessagesProj/src/main/res/values-es/flexyfiles_signature.xml',
'TMessagesProj/src/main/res/values-ru/flexyfiles_signature.xml',
'TMessagesProj/src/main/res/values/flexyfiles_editor_signature.xml',
'TMessagesProj/src/main/res/values-es/flexyfiles_editor_signature.xml',
'TMessagesProj/src/main/res/values-ru/flexyfiles_editor_signature.xml',
 'tools/connected_alpha/files_native/stubs.py',
 'tools/connected_alpha/files_native/FilesNativeTest.java.in',
'TMessagesProj/build.gradle',
'.github/workflows/connected-alpha-arm64.yml',
'TMessagesProj/src/main/java/app/flexygram/studio/core/StudioSchema.java',
 'tools/connected_alpha/studio_native/StudioCoreTest.java',
 'tools/connected_alpha/test_files_completion.py',
 'tools/connected_alpha/test_universal3.py',
 'tools/connected_alpha/test_alpha1275.py',
 'tools/connected_alpha/test_refinement1274.py',
 'tools/connected_alpha/test_private_release1276.py',
'.github/workflows/pr.yml',



]
spec={'base':'175b299e0d4faeb246eca8e1be16a362a3a62213','reviewed':{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest()for path in PATHS},'paths':sorted(PATHS+['tools/connected_alpha/startup_review.json'])}
(ROOT/'tools/connected_alpha/startup_review.json').write_text(json.dumps(spec,indent=2)+'\n')
