#!/usr/bin/env python3
"""Compatibility entry point: the approved Settings3 root supersedes the Settings2 visual fixture.
Settings2 source ownership checks and its resource host helpers are retained and reused.
"""
from pathlib import Path
import runpy,sys
if __name__=='__main__':
 path=Path(__file__).resolve().parents[2]/'settings3/android/run.py'
 sys.path.insert(0,str(path.parent))
 runpy.run_path(str(path),run_name='__main__')
