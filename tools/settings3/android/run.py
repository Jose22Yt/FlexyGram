#!/usr/bin/env python3
"""Real Android graphics and AndroidX adapter tests; Telegram hosts are explicit doubles."""
import importlib.util,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('settings3_harness',ROOT/'tools/connected_alpha/music_visual/run.py')
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
from stubs import write,resources
if __name__=='__main__':
 os.environ['SETTINGS2_SDK_ROOT']=str(Path(sys.argv[sys.argv.index('--sdk-root')+1]).resolve())
 result=harness.main(here=HERE,test_class='Settings3AndroidTest',stubs_writer=write,resource_writer=resources,extra_aars=[('androidx.recyclerview','recyclerview','1.4.0')])
 print('Settings3 isolated probe: native row rendering and AndroidX adapter only; integrated APK/device NOT_TESTED.')
 raise SystemExit(result)
