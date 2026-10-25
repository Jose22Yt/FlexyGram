#!/usr/bin/env python3
"""Real API37 resource linking and isolated API35 Studio views/storage. Not full app compilation."""
import importlib.util,sys,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
TOOLS=HERE.parent
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('studio_android_pipeline',TOOLS/'music_visual/run.py');pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
from stubs import write_stubs

def resources(root,res):
 for file in (root/'TMessagesProj/src/main/res/drawable').glob('flexy_studio_*.xml'):shutil.copyfile(file,res/file.name)
 for folder in ('values','values-es','values-ru','xml'):
  target=res.parent/folder;target.mkdir(parents=True,exist_ok=True)
  name='flexystudio_paths.xml' if folder=='xml' else 'flexystudio.xml'
  shutil.copyfile(root/'TMessagesProj/src/main/res'/folder/name,target/name)
if __name__=='__main__':
 if '--output-dir'not in sys.argv:sys.argv+=['--output-dir',str(TOOLS.parents[1]/'build/connected-alpha-studio-native')]
 result=pipeline.main(here=HERE,test_class='StudioNativeTest',stubs_writer=write_stubs,resource_writer=resources)
 print('Studio result: isolated API35 widgets/storage; Telegram/theme/navigation and resource IDs are doubles. Full app/API37 runtime/device NOT_TESTED.')
 raise SystemExit(result)
