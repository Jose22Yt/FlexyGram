#!/usr/bin/env python3
"""Regenerate an exact motion review only after inspecting the diff; historical review is untouched."""
from pathlib import Path
import json,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[2]
BASE='14e586b4ddb7a686f39cda3cb175920c49cecf11'
paths=set(subprocess.check_output(['git','diff',BASE,'--name-only'],cwd=ROOT,text=True).splitlines())
paths.add('tools/connected_alpha/motion_review.json')
review={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths) if p!='tools/connected_alpha/motion_review.json'}
(ROOT/'tools/connected_alpha/motion_review.json').write_text(json.dumps(dict(base=BASE,paths=sorted(paths),reviewed=review),indent=2)+'\n')
