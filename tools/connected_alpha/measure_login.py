#!/usr/bin/env python3
"""Account-free performance capture for a prepared TEST device. Never clears data or logs UI.

Run the two packages in the same manually prepared guest state, device, animation/font/
density settings and frame budget. First-install/account state is never fabricated here.
Cold-start timings include the original Telegram process initialization. Manual captures
can measure phone/country/back/keyboard interactions without reading screen content.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import time


def stats(values):
    if not values: return {'samples':0,'median_ms':None,'p95_ms':None}
    ordered=sorted(values)
    return {'samples':len(ordered),'median_ms':statistics.median(ordered),'p95_ms':ordered[math.ceil(.95*len(ordered))-1]}


def frame_times(text):
    values=[];header=None
    for row in csv.reader(text.splitlines()):
        if 'Flags' in row and 'IntendedVsync' in row and 'FrameCompleted' in row: header=row;continue
        if header is None or len(row)<len(header):continue
        try:
            record=dict(zip(header,row));start=int(record['IntendedVsync']);end=int(record['FrameCompleted'])
            if int(record['Flags'])==0 and 0<start<end<9223372036854775807:values.append((end-start)/1e6)
        except (ValueError,KeyError): pass
    return values


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial',required=True);p.add_argument('--package',required=True);p.add_argument('--component',required=True)
    p.add_argument('--label',required=True);p.add_argument('--prepared-state',required=True,choices=['guest-welcome','guest-phone','guest-auth-step'])
    p.add_argument('--confirm-test-device',action='store_true',required=True)
    p.add_argument('--frame-budget-ms',type=float,required=True);p.add_argument('--iterations',type=int,default=20)
    p.add_argument('--manual-seconds',type=float,default=0,help='Capture user-driven guest interaction instead of force-stopping/relaunching')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if not 5<=a.iterations<=100 or a.frame_budget_ms<=0 or not 0<=a.manual_seconds<=120:p.error('Invalid sample count, time window or frame budget')
    def adb(*args):return subprocess.check_output(['adb','-s',a.serial,*args],text=True,stderr=subprocess.DEVNULL)
    environment={k:adb('shell','settings','get','global',k).strip() for k in ('window_animation_scale','transition_animation_scale','animator_duration_scale')}
    environment['font_scale']=adb('shell','settings','get','system','font_scale').strip()
    environment['display_size']=adb('shell','wm','size').strip();environment['density']=adb('shell','wm','density').strip()
    environment['build']=adb('shell','getprop','ro.build.fingerprint').strip()
    environment['model']=adb('shell','getprop','ro.product.model').strip()
    # Serial identifies only the comparison pair, never expose it in output.
    environment['device_pair_id']=hashlib.sha256(a.serial.encode()).hexdigest()
    starts=[];frames=[]
    for _ in range(a.iterations):
        adb('shell','dumpsys','gfxinfo',a.package,'reset')
        if a.manual_seconds:time.sleep(a.manual_seconds)
        else:
            adb('shell','am','force-stop',a.package)
            result=adb('shell','am','start','-W','-n',a.component)
            import re
            found=re.search(r'^TotalTime:\s*(\d+)',result,re.M)
            if not found:raise SystemExit('Startup timing unavailable; no result inferred')
            starts.append(int(found[1]));time.sleep(.5)
        frames+=frame_times(adb('shell','dumpsys','gfxinfo',a.package,'framestats'))
    output={'label':a.label,'package':a.package,'prepared_state':a.prepared_state,'state_verified_by_harness':False,
            'environment':environment,'scenario':'manual-guest-interaction' if a.manual_seconds else 'cold-start',
            'startup':stats(starts),'frames':stats(frames),'frame_budget_ms':a.frame_budget_ms,
            'over_budget_frames':sum(x>a.frame_budget_ms for x in frames),'performance_superiority':'NOT_ESTABLISHED'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(output,indent=2)+'\n')

if __name__=='__main__':main()
