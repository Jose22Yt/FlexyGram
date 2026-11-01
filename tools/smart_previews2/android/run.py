#!/usr/bin/env python3
"""Production spans/palette/preferences/demo/settings adapter; explicit Telegram/controller doubles."""
from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
s=importlib.util.spec_from_file_location('smart2_harness',ROOT/'tools/connected_alpha/music_visual/run.py')
h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
from stubs import write
if __name__=='__main__':
 raise SystemExit(h.main(here=HERE,test_class='SmartPreviews2AndroidTest',stubs_writer=write,extra_aars=[('androidx.recyclerview','recyclerview','1.4.0')]))
