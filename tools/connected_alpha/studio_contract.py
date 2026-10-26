"""Reviewed additive FlexyStudio hooks; reverse exactly or fail closed."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
BASE='751c926d91acd536d96b427af5f34f2fe6bedbc4'
PATHS=frozenset(['tools/connected_alpha/test_performance2.py', 'tools/connected_alpha/performance/navigation_contract.py', 'tools/connected_alpha/test_integrated_approved_composer.py', 'tools/connected_alpha/studio_native/StudioCodecBenchmark.java', '.github/workflows/flexystudio.yml', '.github/workflows/pr.yml', 'TMessagesProj/src/main/AndroidManifest.xml', 'TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraSettingsActivity.java', 'TMessagesProj/src/main/java/app/flexygram/studio/FlexyStudioActivity.java', 'TMessagesProj/src/main/java/app/flexygram/studio/FlexyStudioCleanup.java', 'TMessagesProj/src/main/java/app/flexygram/studio/FlexyStudioFiles.java', 'TMessagesProj/src/main/java/app/flexygram/studio/FlexyStudioIO.java', 'TMessagesProj/src/main/java/app/flexygram/studio/FlexyStudioProvider.java', 'TMessagesProj/src/main/java/app/flexygram/studio/FlexyStudioSheet.java', 'TMessagesProj/src/main/java/app/flexygram/studio/FlexyStudioStore.java', 'TMessagesProj/src/main/java/app/flexygram/studio/FlexyStudioText.java', 'TMessagesProj/src/main/java/app/flexygram/studio/FlexyStyleInstallHelper.java', 'TMessagesProj/src/main/java/app/flexygram/studio/core/StudioCodec.java', 'TMessagesProj/src/main/java/app/flexygram/studio/core/StudioSchema.java', 'TMessagesProj/src/main/java/app/flexygram/studio/core/StudioTransaction.java', 'TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java', 'TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java', 'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java', 'TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java', 'TMessagesProj/src/main/java/org/telegram/ui/Components/SharedMediaLayout.java', 'TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java', 'TMessagesProj/src/main/res/drawable/flexy_studio_document.xml', 'TMessagesProj/src/main/res/drawable/flexy_studio_export.xml', 'TMessagesProj/src/main/res/drawable/flexy_studio_import.xml', 'TMessagesProj/src/main/res/drawable/flexy_studio_layers.xml', 'TMessagesProj/src/main/res/drawable/flexy_studio_share.xml', 'TMessagesProj/src/main/res/values-es/flexystudio.xml', 'TMessagesProj/src/main/res/values-ru/flexystudio.xml', 'TMessagesProj/src/main/res/values/flexystudio.xml', 'TMessagesProj/src/main/res/xml/flexystudio_paths.xml', 'tools/connected_alpha/FLEXYSTUDIO.md', 'tools/connected_alpha/flexystudio_native.patch', 'tools/connected_alpha/next_alpha_contract.py', 'tools/connected_alpha/studio_contract.py', 'tools/connected_alpha/studio_native/StudioCoreTest.java', 'tools/connected_alpha/studio_native/StudioNativeTest.java.in', 'tools/connected_alpha/studio_native/run.py', 'tools/connected_alpha/studio_native/stubs.py', 'tools/connected_alpha/test_flexystudio.py'])
HOOKS=frozenset(['.github/workflows/pr.yml', 'TMessagesProj/src/main/AndroidManifest.xml', 'TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraSettingsActivity.java', 'TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java', 'TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java', 'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java', 'TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java', 'TMessagesProj/src/main/java/org/telegram/ui/Components/SharedMediaLayout.java', 'TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java'])
def restore(path,data):
 from refinement1274_contract import restore as restore_refinement
 data=restore_refinement(path,data)
 path=str(path)
 if path not in HOOKS:return data
 original=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
 if data==original:return data
 patch=(ROOT/'tools/connected_alpha/flexystudio_native.patch').read_bytes()
 sections={x.split(b'\n',1)[0]:b'diff --git '+x for x in patch.split(b'diff --git ')[1:]}
 section=sections[('a/'+path+' b/'+path).encode()]
 with tempfile.TemporaryDirectory()as tmp:
  target=Path(tmp)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
  result=subprocess.run(['git','apply','--reverse','-'],input=section,cwd=tmp,capture_output=True)
  if result.returncode or target.read_bytes()!=original:raise ValueError('Unreviewed FlexyStudio hook: '+path)
 return original

# Audit-only documentation/tools; no additional production file is authorized.
from prebeta.contract import PATHS as PREBETA_PATHS
PATHS = PATHS | PREBETA_PATHS
