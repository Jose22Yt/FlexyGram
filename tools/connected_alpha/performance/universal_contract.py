"""Small exact Performance3 delta on approved Alpha1275; fail closed on source mutations."""
from pathlib import Path
import re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[3]
BASE='8c47e5532a600f9a8b4ccbfdac5090d09a1075a0'
PRODUCTION=frozenset(['TMessagesProj/src/main/java/org/telegram/ui/Components/voip/CellFlickerDrawable.java','TMessagesProj/src/main/java/org/telegram/ui/Components/ClipRoundedDrawable.java'])
PATCHES={next(p for p in PRODUCTION if 'CellFlicker' in p):'flicker3.patch',next(p for p in PRODUCTION if 'ClipRounded' in p):'clip3.patch','tools/connected_alpha/test_performance2.py':'guards3.patch','tools/connected_alpha/test_alpha1275.py':'alpha_guard3.patch'}

def clean_context(lines):
 result=[];i=0
 while i<len(lines):
  header=lines[i]
  if not header.startswith('@@ '):result.append(header);i+=1;continue
  m=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)\n',header);assert m,header
  j=i+1
  while j<len(lines)and not lines[j].startswith('@@ '):j+=1
  body=lines[i+1:j];removed=0
  while body and body[-1]==' \n':body.pop();removed+=1
  result.append(f'@@ -{m[1]},{int(m[2]or 1)-removed} +{m[3]},{int(m[4]or 1)-removed} @@{m[5]}\n');result.extend('\n' if line==' \n' else line for line in body);i=j
 return result

def restore(path,data):
 path=str(path)
 if path not in PATCHES:return data
 before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
 if data==before:return data
 with tempfile.TemporaryDirectory()as temp:
  target=Path(temp)/path;target.parent.mkdir(parents=True);target.write_bytes(data)
  patch=ROOT/'tools/connected_alpha/performance'/PATCHES[path]
  result=subprocess.run(['git','apply','--reverse',str(patch)],cwd=temp,capture_output=True)
  if result.returncode or target.read_bytes()!=before:raise ValueError('Unreviewed universal3 delta: '+path)
 return before
PATHS=frozenset(['.github/workflows/performance3.yml', 'TMessagesProj/src/main/java/org/telegram/ui/Components/ClipRoundedDrawable.java', 'TMessagesProj/src/main/java/org/telegram/ui/Components/voip/CellFlickerDrawable.java', 'tools/connected_alpha/next_alpha_contract.py', 'tools/connected_alpha/performance/UNIVERSAL3.md', 'tools/connected_alpha/performance/capture.py', 'tools/connected_alpha/performance/clip3.patch', 'tools/connected_alpha/performance/compare.py', 'tools/connected_alpha/performance/flicker3.patch', 'tools/connected_alpha/performance/motion3.patch', 'tools/connected_alpha/performance/native3/ClipNativeTest.java.in', 'tools/connected_alpha/performance/native3/FlickerNativeTest.java.in', 'tools/connected_alpha/performance/native3/MotionNativeTest.java.in', 'tools/connected_alpha/performance/native3/run.py', 'tools/connected_alpha/performance/native3/stubs.py', 'tools/connected_alpha/performance/prepare3.py', 'tools/connected_alpha/performance/scenarios.py', 'tools/connected_alpha/performance/universal3.py', 'tools/connected_alpha/performance/universal_contract.py', 'tools/connected_alpha/performance/work1_boundary3.json', 'tools/connected_alpha/test_performance2.py', 'tools/connected_alpha/performance/alpha_guard3.patch', 'tools/connected_alpha/performance/guards3.patch', 'tools/connected_alpha/test_alpha1275.py', 'tools/connected_alpha/test_universal3.py'])
