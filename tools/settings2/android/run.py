#!/usr/bin/env python3
"""Isolated production Settings2 views/policy, with explicit Telegram host/transport doubles.
Not a full APK, emulator, device test, or native legacy-screen acceptance.
"""
import argparse,sys,shutil,re,subprocess,xml.etree.ElementTree as E,zipfile
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.append(str(ROOT/'tools/connected_alpha/music_visual'))
import importlib.util
spec=importlib.util.spec_from_file_location("settings2_native_harness",ROOT/"tools/connected_alpha/music_visual/run.py")
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
from stubs import write,resources
if __name__=='__main__':
 os.environ['SETTINGS2_SDK_ROOT']=str(Path(sys.argv[sys.argv.index('--sdk-root')+1]).resolve())
 raise SystemExit(harness.main(here=HERE,test_class='Settings2AndroidTest',stubs_writer=write,resource_writer=resources))
