#!/usr/bin/env python3
"""Real Android touch dispatch; navigation methods are extracted unchanged, stack hosts isolated."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('native_touch_harness',ROOT/'tools/connected_alpha/music_visual/run.py')
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
from stubs import write
if __name__=='__main__':
 raise SystemExit(harness.main(here=HERE,test_class='NavigationInterruptAndroidTest',stubs_writer=write))
