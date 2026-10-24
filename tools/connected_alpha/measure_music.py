#!/usr/bin/env python3
"""Opt-in gfxinfo collection on a prepared TEST device; never reads UI/account data.
No app launch, data clear, login, install, screenshot or logcat. No speedup claim.
"""
import argparse
import json
import math
from pathlib import Path
import re
import statistics
import subprocess


def frames(text):
    result=[];header=None
    for line in text.splitlines():
        cells=line.strip().split(',')
        if 'IntendedVsync' in cells and 'FrameCompleted' in cells:
            header={name:i for i,name in enumerate(cells)};continue
        if header is None or not cells[0].isdigit():continue
        try:
            if int(cells[header['Flags']]) != 0:continue
            begin=int(cells[header['IntendedVsync']]);end=int(cells[header['FrameCompleted']])
            if 0<begin<end:result.append((end-begin)/1_000_000)
        except (ValueError,IndexError,KeyError):continue
    return result


def stats(values,budget):
    if not values:raise ValueError('No completed non-flagged frames; capture is invalid')
    ordered=sorted(values)
    return {'frame_count':len(values),'median_frame_ms':statistics.median(values),
            'p95_frame_ms':ordered[max(0,math.ceil(len(values)*.95)-1)],
            'over_budget_frames':sum(v>budget for v in values),'budget_ms':budget,
            'metric':'gfxinfo intended-vsync to completed; not SurfaceFlinger jank or tap latency'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial',required=True);p.add_argument('--package',required=True)
    p.add_argument('--label',required=True);p.add_argument('--scenario',required=True)
    p.add_argument('--budget-ms',type=float,required=True);p.add_argument('--samples',type=int,default=20)
    p.add_argument('--prepared-test-device',action='store_true',required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.]+',a.package) or a.samples<5 or a.budget_ms<=0:p.error('Valid package, >=5 samples and positive frame budget required')
    def adb(*args):return subprocess.check_output(['adb','-s',a.serial,'shell',*args],text=True)
    environment={'density':adb('wm','density').strip(),'size':adb('wm','size').strip(),
        'font_scale':adb('settings','get','system','font_scale').strip(),
        'animator':adb('settings','get','global','animator_duration_scale').strip(),
        'transition':adb('settings','get','global','transition_animation_scale').strip(),
        'window':adb('settings','get','global','window_animation_scale').strip(),
        'device':adb('getprop','ro.product.model').strip(),'build':adb('getprop','ro.build.fingerprint').strip()}
    captures=[]
    for i in range(a.samples):
        input(f'Guest/test state ready for {a.scenario}, sample {i+1}/{a.samples}. Enter to reset frame stats: ')
        adb('dumpsys','gfxinfo',a.package,'reset')
        input('Perform the same interaction sequence, then Enter: ')
        captures.append(stats(frames(adb('dumpsys','gfxinfo',a.package,'framestats')),a.budget_ms))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps({'label':a.label,'scenario':a.scenario,'environment':environment,
        'captures':captures,'median_sample_median_ms':statistics.median(x['median_frame_ms'] for x in captures),
        'median_sample_p95_ms':statistics.median(x['p95_frame_ms'] for x in captures),
        'superiority':'NOT_ESTABLISHED','prepared_state':'owner/operator attestation; not inspected'},indent=2))

if __name__=='__main__':main()
