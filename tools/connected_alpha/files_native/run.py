#!/usr/bin/env python3
"""Extend the existing Performance 1/2 Android pipeline; no full app, device or GPU timing claim."""
from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent
TOOLS=HERE.parent
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('native3_shared_pipeline',TOOLS/'music_visual/run.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
from stubs import write_stubs
if __name__=='__main__':
 if '--output-dir'not in sys.argv:sys.argv+=['--output-dir',str(TOOLS.parents[1]/'build/connected-alpha-files-native')]
 result=pipeline.main(here=HERE,test_class='FilesNativeTest',stubs_writer=write_stubs)
 print('FlexyFiles: real Android editor/files code with explicit Telegram UI doubles. Full app and physical device NOT_TESTED.')
 raise SystemExit(result)
