#!/usr/bin/env python3
"""Native Android Canvas regression tests of the production message border in both modes."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('native_host',ROOT/'tools/connected_alpha/music_visual/run.py')
host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
from stubs import write
if __name__=='__main__':
    raise SystemExit(host.main(here=HERE,test_class='AdaptiveBorderAndroidTest',stubs_writer=write))
