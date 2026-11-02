#!/usr/bin/env python3
"""Reuse Music's real AAPT2/Maven/Android pipeline; compile production lyric drawing code.
Not a complete app module, ART allocation profiler, device frame-time benchmark or P0 fix.
"""
import importlib.util
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1]
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('music_probe_reused', TOOLS/'music_visual/run.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from stubs import write_stubs
if __name__ == '__main__':
    if '--output-dir' not in sys.argv:
        sys.argv += ['--output-dir', str(TOOLS.parents[1]/'build/connected-alpha-performance-native')]
    raise SystemExit(module.main(here=HERE, test_class='PerformanceNativeTest', stubs_writer=write_stubs))
