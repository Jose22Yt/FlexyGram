#!/usr/bin/env python3
"""Reuse Performance1/2 capture/compare. Group by test instrument, never vendor/device production rules."""
import argparse,json,math,re
from pathlib import Path
from .metrics import summary
from .compare import compare
from .scenarios import SCENARIOS

def distribution(values):
 if any(isinstance(v,bool)or not isinstance(v,(int,float))or not math.isfinite(v)or v<0 for v in values):raise ValueError('Invalid numeric metric')
 out=summary(values);ordered=sorted(values)
 out['p99']=ordered[math.ceil(.99*len(ordered))-1]if len(ordered)>=1000 else None
 out['p99_minimum_samples']=1000
 return out

def grouped(reports):
 groups={}
 for report in reports:
  device=report.get('environment',{}).get('device_pair_id');scenario=report.get('scenario')
  if not isinstance(device,str)or not re.fullmatch('[0-9a-f]{64}',device)or scenario not in SCENARIOS:raise ValueError('Hashed test instrument and known scenario required')
  if report.get('label')not in {'exteraless','alpha1275','candidate'}:raise ValueError('Known cohort label required')
  groups.setdefault((device,scenario),[]).append(report)
 result=[]
 for (device,scenario),items in sorted(groups.items()):
  compared=compare(items,'universal3')
  if compared['comparable']:
   for row,report in zip(compared['rows'],items):
    try:
     raw=[];expected=0
     for capture in report['captures']:
      count=capture['frames']['duration_ms']['count']
      if type(count)is not int or count<0:raise ValueError('Invalid frame count')
      expected+=count;raw.extend(f['duration_ms']for f in capture['frames'].get('frames',[]))
     if len(raw)!=expected:raise ValueError('Missing raw frames')
     row['pooled_frame_duration_ms']=distribution(raw)
    except (ValueError,KeyError,TypeError):
     compared={'comparable':False,'reasons':['Invalid raw frame samples'],'rows':[],'superiority':'NOT_ESTABLISHED'};break
  result.append({'test_instrument_id':device,'scenario':scenario,**compared})
 return {'schema':1,'cohort':'universal3','groups':result,'comparable':bool(result)and all(x['comparable']for x in result),
         'cross_device_fps_comparison':'NOT_PERFORMED','universal_device_acceptance':'NOT_ESTABLISHED',
         'first_useful_frame_ms':None,'first_interaction_available_ms':None,
         'limits':'Existing capture/per-frame refresh and Perfetto input-present analysis remain distinct. No physical data inferred from tests or drawable counts.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('reports',nargs='+',type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
 result=grouped([json.loads(path.read_text())for path in a.reports]);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');return 0 if result['comparable']else 2
if __name__=='__main__':raise SystemExit(main())
