#!/usr/bin/env python3
"""Compare two qualified Alpha captures; never interpret operation fixtures as phone evidence."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.connected_alpha.performance.compare import validate, ENVIRONMENT_KEYS
from tools.connected_alpha.performance.metrics import summary

BASE='0030904ae2e41d7720f43b7906c6a302ed339839'
BASELINES={BASE,'258dd3590f40ca0083a4b7bad6b413433c4e2c14'}
ALPHA='io.github.jose22yt.flexygram.alpha'


def compare(before,after):
    errors=[]
    for label,report in [('before',before),('after',after)]:
        errors.extend(label+': '+e for e in validate(report))
        if report.get('package')!=ALPHA:errors.append('Only the existing Alpha identity is eligible')
    if before.get('source_commit') not in BASELINES:errors.append('Baseline must identify exact PR131 or delivered Alpha1286 source')
    if after.get('source_commit') in BASELINES:errors.append('Candidate must identify a different source')
    if before.get('scenario')!=after.get('scenario'):errors.append('Different scenarios')
    for key in (*ENVIRONMENT_KEYS,'network_profile','sync_state','build_mode'):
        a,b=before.get('environment',{}).get(key),after.get('environment',{}).get(key)
        if a in (None,'','unknown','unverified') or a!=b:errors.append('Unmatched/unverified condition: '+key)
    def profile(report):
        counts={}
        for c in report.get('captures',[]):
            for interval,n in c.get('frames',{}).get('interval_ms_histogram',{}).items():
                counts[interval]=counts.get(interval,0)+n
        total=sum(counts.values())
        return {k:n/total for k,n in counts.items()} if total else {}
    p,q=profile(before),profile(after)
    if set(p)!=set(q) or any(abs(p[k]-q[k])>.05 for k in p if k in q):errors.append('Different observed refresh distributions')
    if errors:return {'comparable':False,'reasons':sorted(set(errors)),'device_improvement':'NOT_ESTABLISHED'}
    def row(report):
        captures=report['captures']
        return {'source_commit':report['source_commit'], 'startup_am_ms':summary([c['startup_ms'] for c in captures if c.get('startup_ms') is not None]),
                'per_run_frame_p95_ms':summary([c['frames']['duration_ms']['p95'] for c in captures if c['frames']['duration_ms']['p95'] is not None]),
                'deadline_missed_frames':sum(c['frames'].get('deadline_missed_frames',0) for c in captures),
                'deadline_observed_count':sum(c['frames'].get('deadline_observed_count',0) for c in captures)}
    return {'comparable':True,'before':row(before),'after':row(after), 'device_improvement':'REQUIRES_REVIEW',
            'ttfd_ms':None,'touch_to_visible_ms':None,'note':'am startup is not useful-list latency; per-run p95 quantiles are not pooled frame quantiles.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=compare(json.loads(a.before.read_text()),json.loads(a.after.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return 0 if result['comparable'] else 2


if __name__=='__main__':raise SystemExit(main())
