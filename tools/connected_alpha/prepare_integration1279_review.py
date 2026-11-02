"""Regenerate only after reviewing the integration; never edit prior review manifests."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='14e586b4ddb7a686f39cda3cb175920c49cecf11'
TARGET='tools/connected_alpha/integration1279_review.json'
paths=set(subprocess.check_output(['git','diff',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())|{TARGET}
review={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths) if p!=TARGET}
(ROOT/TARGET).write_text(json.dumps({'base':BASE,'paths':sorted(paths),'reviewed':review},indent=2)+'\n')
