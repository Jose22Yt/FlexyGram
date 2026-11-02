#!/usr/bin/env python3
"""Production mode mapper/controller/static rendering; Telegram and Kotlin config hosts explicit."""
import importlib.util,sys,os
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('glare_pipeline',ROOT/'tools/connected_alpha/music_visual/run.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
from stubs import write,resources
if __name__=='__main__':
 os.environ['SETTINGS2_SDK_ROOT']=str(Path(sys.argv[sys.argv.index('--sdk-root')+1]).resolve())
 result=h.main(here=HERE,test_class='GlareAndroidTest',stubs_writer=write,resource_writer=resources,extra_aars=[('androidx.recyclerview','recyclerview','1.4.0')])
 print('Glare probe: production mapper/controller/static draw methods, real Android Canvas; Telegram/config host doubles; full app/device NOT_TESTED.')
 raise SystemExit(result)
