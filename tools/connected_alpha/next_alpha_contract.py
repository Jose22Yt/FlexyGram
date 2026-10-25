"""Exact reviewed delta on Alpha1272; reject changes outside the recorded patch."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
BASE='8619ba40fbd8fd9d9d898ff307fb0c0716661254'
PATHS=frozenset(['TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java','tools/connected_alpha/preview_input1273.patch','tools/connected_alpha/next_alpha_contract.py','tools/connected_alpha/test_preview_input1273.py','tools/connected_alpha/check_source.py','tools/connected_alpha/stabilization_contract.py','tools/connected_alpha/test_stabilization1272.py','tools/connected_alpha/NEXT_ALPHA.md'])
def restore1272(path,data):
 path=str(path)
 patch=(ROOT/'tools/connected_alpha/preview_input1273.patch').read_bytes()
 sections={x.split(b'\n',1)[0]:b'diff --git '+x for x in patch.split(b'diff --git ')[1:]}
 section=sections.get(('a/'+path+' b/'+path).encode())
 if section is None:return data
 original=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
 if data==original:return data
 with tempfile.TemporaryDirectory()as tmp:
  target=Path(tmp)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
  result=subprocess.run(['git','apply','--reverse','-'],input=section,cwd=tmp,capture_output=True)
  if result.returncode or target.read_bytes()!=original:raise ValueError('Unreviewed next-alpha delta: '+path)
 return original
