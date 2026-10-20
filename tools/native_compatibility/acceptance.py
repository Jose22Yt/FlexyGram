"""Conservative static acceptance gates. A clean gate never certifies Android execution.
No ELF is loaded; no application/provider/session is executed.
"""
import argparse,json
from pathlib import Path
from audit import elf

def candidate_contract(before,after):
    blockers=[]
    if before['machine']!='EM_AARCH64' or after['machine']!='EM_AARCH64':blockers.append('wrong_machine')
    if not before.get('soname') or before['soname']!=after.get('soname'):blockers.append('soname_changed')
    if not after['load_4k'] or not after['load_16k']:blockers.append('pt_load_incompatible')
    api=after.get('android_note_api')
    if not isinstance(api,int) or not 1<=api<=24:blockers.append('api24_provenance_missing_or_newer')
    missing=sorted(set(map(tuple,before['exports']))-set(map(tuple,after['exports'])),key=lambda s:(s[0],s[1] or ''))
    if missing:blockers.append('export_contract_loss')
    new_needed=sorted(set(after['needed'])-set(before['needed']))
    if new_needed:blockers.append('new_needed_requires_review')
    return {'static_contract_pass':not blockers,'blockers':blockers,'missing_export_pairs':missing,
            'new_needed':new_needed,'before_sha256':before.get('sha256'),'after_sha256':after.get('sha256'),
            'runtime_required':True,'replacement_approved':False,
            'limits':'Necessary static conditions only. Export equality does not prove optional features, behavior, symbol resolution or Android loading.'}

def artifact_acceptance(report):
    target=[r for r in report['libraries'] if r['machine']=='EM_AARCH64']
    blockers=[]
    if not target:blockers.append({'code':'no_arm64_elf','path':None})
    for row in target:
        for code,failed in [('pt_load_4k',not row['load_4k']),('pt_load_16k',not row['load_16k']),
                            ('missing_needed_api24',bool(row.get('missing_needed_api24'))),
                            ('strong_unresolved_api24',bool(row.get('strong_unresolved_api24'))),
                            ('version_provider_mismatch',bool(row.get('version_provider_mismatches_api24'))),
                            ('global_symbol_runtime_validation',bool(row.get('strong_outside_needed_closure'))),
                            ('relro_writable_overlap',any(s['writable_sections_in_roundup'] for s in row['relro']))]:
            if failed:blockers.append({'code':code,'path':row['path']})
    return {'status':'STATIC_BLOCKED' if blockers else 'STATIC_CLEAN_PENDING_ANDROID',
            'arm64_elf':len(target),'non_target_payloads':len(report['libraries'])-len(target),
            'blockers':blockers,'runtime_required':True,'distribution_allowed':False,
            'limits':'Static API24/16KB conditions; no ART/linker/device certification. Non-target ELF payloads remain in the full report.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    c=sub.add_parser('candidate');c.add_argument('--before',required=True,type=Path);c.add_argument('--after',required=True,type=Path)
    a=sub.add_parser('artifact');a.add_argument('--report',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    if args.mode=='candidate':
        result=candidate_contract(elf(args.before.read_bytes(),args.before.name),elf(args.after.read_bytes(),args.after.name))
        accepted=result['static_contract_pass']
    else:result=artifact_acceptance(json.loads(args.report.read_text()));accepted=not result['blockers']
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'static_gate_pass':accepted,'runtime_required':True,'distribution_allowed':False}))
    raise SystemExit(0 if accepted else 1)
