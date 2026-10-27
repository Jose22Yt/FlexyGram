#!/usr/bin/env python3
"""Compile real engine against Android API37; execute API35 widget/clock tests, not a full APK/device."""
from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('motion_pipeline',HERE.parent/'music_visual/run.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
sys.path.insert(0,str(HERE))
from stubs import write
if __name__=='__main__':
 if '--output-dir'not in sys.argv:sys.argv+=['--output-dir',str(HERE.parents[2]/'build/connected-alpha-motion-native')]
 raise SystemExit(pipeline.main(here=HERE,test_class='MotionEngineTest',stubs_writer=write))
