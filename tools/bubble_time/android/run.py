#!/usr/bin/env python3
"""Render the production time-label drawing method in an isolated real Android host."""
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('android_probe', ROOT/'tools/connected_alpha/music_visual/run.py')
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)
from stubs import write
if __name__ == '__main__':
    raise SystemExit(harness.main(here=HERE, test_class='BubbleTimeAndroidTest', stubs_writer=write))
