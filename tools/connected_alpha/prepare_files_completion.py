"""Snapshot the explicit continuation inventory; audit requires regenerating after reviewed edits."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[2];BASE='f11921c651b52b080899f9e86a7a975dab0afeb7'
paths=set(subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines())
paths.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard','tools/connected_alpha','TMessagesProj/src','.github'],cwd=ROOT,text=True).splitlines())
paths.add('tools/connected_alpha/files_completion.json')
existing={}
for path in sorted(paths):
 before=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
 if before.returncode==0:existing[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
(ROOT/'tools/connected_alpha/files_completion.json').write_text(json.dumps({'base':BASE,'existing':existing,'paths':sorted(paths)},indent=2)+'\n')
