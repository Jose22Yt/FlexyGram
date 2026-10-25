"""Pinned integration boundaries; preserve both Work2 patches and the approved Work1 code."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
WORK1='0e359f0e7841a99d61c79f996dd162b7c836a9bf'
LOGIN='4c7a9328b4c4ee7b93dcf0cf5c1347eb934f6409'
MUSIC='dc159cee26cb694ea4029e8950915bff15534e0c'
INTEGRATION_PATHS=frozenset(['TMessagesProj/src/connectedAlpha/res/values/alpha_name.xml', '.github/workflows/connected-alpha-arm64.yml', 'TMessagesProj/src/main/java/app/exteraless/updater/UpdaterSheet.java', 'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java', 'TMessagesProj/src/main/res/values-es/flexygram_login.xml', 'TMessagesProj/src/main/res/values-ru/flexygram_login.xml', 'TMessagesProj/src/main/res/values/flexygram_login.xml', 'tools/connected_alpha/build_private_apk.py', 'tools/connected_alpha/direct_delivery.patch', 'tools/connected_alpha/integration_contract.py', 'tools/connected_alpha/preview_navigation.patch', 'tools/connected_alpha/release_1270_contract.py', 'tools/connected_alpha/release_1271_contract.py', 'tools/connected_alpha/test_cloud_build.py', 'tools/connected_alpha/test_integrated_release.py', 'tools/connected_alpha/test_preview_navigation.py', 'tools/connected_alpha/test_signature1271.py'])
def combined_paths():
 from release_1271_contract import PATHS as UI
 from login_contract import PATHS as L
 from music_contract import PATHS as M
 from stabilization_contract import PATHS as C
 return UI|L|M|INTEGRATION_PATHS|C

def reverse_patch(path,data,filename):
 patch=(ROOT/'tools/connected_alpha'/filename).read_bytes()
 header=('diff --git a/'+str(path)+' b/'+str(path)+'\n').encode()
 sections=[b'diff --git '+p for p in patch.split(b'diff --git ')[1:]]
 matches=[s for s in sections if s.startswith(header)]
 if not matches:return data
 if len(matches)!=1:raise ValueError('Ambiguous integrated delta')
 with tempfile.TemporaryDirectory() as d:
  target=Path(d)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
  result=subprocess.run(['git','apply','--reverse','-'],cwd=d,input=matches[0],capture_output=True)
  if result.returncode:raise ValueError('Integrated delta differs from reviewed patch: '+str(path))
  return target.read_bytes()
def restore_preview(path,data):return reverse_patch(path,data,'preview_navigation.patch')
def restore_delivery(path,data):
 from stabilization_contract import restore1271
 return reverse_patch(path,restore1271(path,data),'direct_delivery.patch')
def reviewed_work1(path):
 data=restore_preview(path,restore_delivery(path,(ROOT/path).read_bytes()))
 from login_parity import PATCH_PATHS,restore_login_presentation
 if path in PATCH_PATHS:data=restore_login_presentation(path,data)
 return data
