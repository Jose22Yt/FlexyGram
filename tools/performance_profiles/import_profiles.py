#!/usr/bin/env python3
"""Import real device-generated ART profiles. Never builds, installs, captures or invents rules."""
import argparse
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
PACKAGE='io.github.jose22yt.flexygram.alpha'


def rules(paths):
    result=[];seen=set()
    for path in paths:
        data=Path(path).read_bytes()
        if len(data)>8*1024*1024:raise ValueError('Profile exceeds 8 MiB')
        for line in data.decode('utf-8').splitlines():
            line=line.strip()
            if not line or line.startswith('#'):continue
            if not re.fullmatch(r'[HSP]{0,3}L[^;\s]+;(?:->[^\s]+)?',line):raise ValueError('Invalid ART profile rule')
            if line not in seen:seen.add(line);result.append(line)
    if not result:raise ValueError('Empty profile; device generation is required')
    return '\n'.join(result)+'\n'


def validate_results(path):
    cases=ET.parse(path).getroot().iter('testcase')
    passed=set()
    for case in cases:
        if case.get('classname','').endswith('ProfileGeneration') and not any(case.find(tag) is not None for tag in ['skipped','failure','error']):
            passed.add(case.get('name','').split('[')[0])
    if not {'startup','chat','settings'}<=passed:raise ValueError('Successful startup/chat/settings profile journeys are required')


def import_profiles(baseline,startup,results,commit,version,api):
    if not re.fullmatch('[0-9a-f]{40}',commit) or version<=0 or api<28:raise ValueError('Invalid device capture provenance')
    validate_results(results)
    baseline_text=rules(baseline);startup_text=rules([startup])
    # Validate everything before touching the repository. Preserve capture order, especially for DEX layout.
    folder=ROOT/'TMessagesProj/src/main/generated/baselineProfiles'
    folder.mkdir(parents=True,exist_ok=True)
    for name,text in [('baseline-prof.txt',baseline_text),('startup-prof.txt',startup_text)]:
        target=folder/name;temporary=folder/(name+'.tmp');temporary.write_text(text,encoding='utf-8');temporary.replace(target)
    (folder/'capture.json').write_text(json.dumps({'source_commit':commit,'package':PACKAGE,'app_version_code':version,'api_level':api,'journeys':['startup','chat','settings'],'measured_speedup':None},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,nargs='+',required=True)
    parser.add_argument('--startup',type=Path,required=True)
    parser.add_argument('--junit-results',type=Path,required=True)
    parser.add_argument('--source-commit',required=True)
    parser.add_argument('--version-code',type=int,required=True)
    parser.add_argument('--api-level',type=int,required=True)
    args=parser.parse_args()
    import_profiles(args.baseline,args.startup,args.junit_results,args.source_commit,args.version_code,args.api_level)
