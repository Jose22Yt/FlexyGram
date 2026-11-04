"""Isolated native widgets/graphics/preferences for message menus. Never builds the application APK."""
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('menu_harness',ROOT/'tools/connected_alpha/music_visual/run.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
from stubs import write
if __name__=='__main__':raise SystemExit(h.main(here=HERE,test_class='MessageMenuAndroidTest',stubs_writer=write))
