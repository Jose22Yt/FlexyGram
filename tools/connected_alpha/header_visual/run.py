#!/usr/bin/env python3
"""Real Android controller, views and geometry; native navigation/theme dependencies are explicit doubles."""
import importlib.util,sys,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
TOOLS=HERE.parent
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('header_music_pipeline',TOOLS/'music_visual/run.py');pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
from stubs import write_stubs
from motion_probe import write_probe
from adaptive_probe import write_probe as write_adaptive_probe

def write_all_stubs(source,root):
 write_stubs(source,root)
 write_probe(source,root)
 write_adaptive_probe(source,root)

def resources(root,res):
 for name in ['ic_ab_back.webp','ic_ab_other.webp','msg_callback.webp']:shutil.copyfile(root/'TMessagesProj/src/main/res/drawable-mdpi'/name,res/name)
if __name__=='__main__':
 if '--output-dir'not in sys.argv:sys.argv+=['--output-dir',str(TOOLS.parents[1]/'build/connected-alpha-header-visual')]
 raise SystemExit(pipeline.main(here=HERE,test_class='HeaderVisualTest',stubs_writer=write_all_stubs,resource_writer=resources))
