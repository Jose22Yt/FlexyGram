"""Offline export of existing PR17 results to the pinned PR21 schema.
No ADB, signing, Android execution or default PASS observations. Not certification.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,re
from contract import HERE,ROOT,digest,load_contract,regular,require,validate_environment
from run_lab import matrix,counters
PINS={
 'pr20':{'head':'3aaae0fc3065b631968476195da5adfd13ba95d8','sha256':'f840911ae0adc5cb5fcfb3351e986d1024151838eca3af7434e86fecd65bf146'},
 'pr21':{'head':'88f988ee844248a4513281cfe7818777fbda660e','sha256':'5e0a1be9fbe1fbcb4e1ac1f283c3faf23b29a328a03138dd93448606583f45ca'}}
PROFILES={'api24-4k':'api24','arm64-16k':'16k'}

def unique(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,'Duplicate JSON key');result[key]=value
    return result

def strict(text):
    def nonfinite(value):raise ValueError('Nonfinite JSON')
    return json.loads(text,object_pairs_hook=unique,parse_constant=nonfinite)

def text_file(path,limit=16*1024*1024):
    regular(path);require(path.stat().st_size<=limit,'Evidence file too large');return path.read_text(encoding='utf-8')

def pinned_module(name,path):
    regular(path);require(digest(path)==PINS[name]['sha256'],'Auxiliary code digest mismatch')
    spec=importlib.util.spec_from_file_location('flexygram_pinned_'+name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def prepare(paths,preflight,validator):
    c=load_contract();require(len(paths)==2,'Both Android results required')
    pre=pinned_module('pr20',preflight);secondary=pinned_module('pr21',validator)
    require(secondary.APK_SHA256==c['apk_sha256'] and secondary.CERT_SHA256==c['certificate_sha256'] and secondary.LIBRARIES==c['libraries'] and secondary.CASE_NAMES==set(c['case_ids']) and secondary.PACKAGE==c['target_package'],'Secondary schema is not the approved artifact contract')
    rows=[strict(text_file(p,2*1024*1024)) for p in paths]
    require(all(type(r) is dict for r in rows),'Result object required')
    snapshots={};counts={}
    # Bound and strictly parse data before the historical matrix's normal JSON reader.
    for path,r in zip(paths,rows):
        require(type(r.get('evidence_sha256')) is dict,'Evidence index missing')
        snapshots[str(path)]=digest(path)
        for name,h in r['evidence_sha256'].items():
            require(type(name) is str and Path(name).name==name and re.fullmatch(r'[0-9a-f]{64}',h),'Invalid evidence member')
            f=path.parent/name;text_file(f);require(digest(f)==h,'Evidence digest mismatch');snapshots[str(f)]=h
        log=text_file(path.parent/'instrumentation.log')
        payload=[x.removeprefix('INSTRUMENTATION_RESULT: lab_result=') for x in log.splitlines() if x.startswith('INSTRUMENTATION_RESULT: lab_result=')]
        require(len(payload)==1 and strict(payload[0])==r['instrumentation'],'Strict instrumentation proof mismatch')
    primary=matrix(paths,c)  # Existing runner remains authoritative; no duplicate executor.
    output={'schema':1,'apk_sha256':c['apk_sha256'],'cert_sha256':c['certificate_sha256'],'profiles':{}}
    provenance=[]
    for path,r in zip(paths,rows):
        profile=r['profile'];p=r['instrumentation'];py=p['python'];env=r['environment'];validate_environment(env,profile)
        require(r['reviewed_head']==c['reviewed_head'],'Wrong reviewed source head')
        for key in ['api','page_size','abi','arch','native_bridge','emulator','clean_lab','strict_16k']:
            require(env[key]==p['environment'][key],'Host/device observations disagree')
        inputs=r['inputs'];require(inputs['status']=='VERIFIED_INPUTS_ONLY' and inputs['apk_sha256']==c['apk_sha256'],'Missing pinned input verification')
        for key,value in [('wheels',18),('rebuilt_wheels',3),('elf',4)]:require(type(inputs[key]) is int and inputs[key]==value,'Incomplete wheel/ELF verification')
        runner=r['runner'];require(runner['signed_with_reviewed_lab_key'] is True and runner['status']=='BUILT_SIGNED_NOT_RUN' and runner['reviewed_target_sha256']==c['apk_sha256'] and re.fullmatch(r'[0-9a-f]{64}',runner['apk_sha256']),'Runner signature/build receipt missing')
        sources=[HERE/'java/io/github/jose22yt/flexygram/lab/LabInstrumentation.java',HERE/'AndroidManifest.xml',HERE/'assets/probe.py',HERE/'contract.json',ROOT/c['runtime_cases_path']]
        require(runner['source_hashes']=={str(f.relative_to(ROOT)):digest(f) for f in sources},'Runner compiled from other sources')
        require(re.fullmatch(r'[0-9a-f]{64}',r['image']['image_sha256']) and r['image']['image_origin'] and r['image']['image_revision'],'Image provenance missing')
        needed={'install-target.log','install-runner.log','package-before.log','package-after.log'}
        require(needed.issubset(r['evidence_sha256']),'Missing installation/package evidence')
        for name in ['install-target.log','install-runner.log']:
            require(re.search(r'(?m)^Success\s*$',text_file(path.parent/name)),'Installation not successful')
        for name in ['package-before.log','package-after.log']:
            log=text_file(path.parent/name);require(c['target_package'] in log and 'android.permission.INTERNET' not in log,'Package evidence contradicts isolation')
        require(re.search(r'(?m)^Status:\s*ok\s*$',text_file(path.parent/'cold-launch.log')),'Cold start not successful')
        category_counts={}
        for name in ['logcat.log','crash.log']:
            report=pre.read_log_counts(path.parent/name);require(type(report['category_counts']) is dict,'Log categories absent')
            require(set(report['category_counts'])==set(pre.LOG_PATTERNS),'Incomplete log categories')
            require(all(type(v) is int and v==0 for v in report['category_counts'].values()),'Critical log indicator')
            require(not re.search(r'NoClassDefFoundError|VerifyError',text_file(path.parent/name)),'Critical Java verification error')
            category_counts[name]=report['category_counts']
        for family in ['iptables','ip6tables']:
            for when in ['before','after']:
                actual=counters(text_file(path.parent/(family+'-'+when+'.log')));claimed=r['network'][when][family]
                require(set(claimed)=={'packets','bytes'} and all(type(v) is int for v in claimed.values()) and actual==claimed=={'packets':0,'bytes':0},'Traffic counters disagree with logs')
        counts[PROFILES[profile]]=category_counts
        # These statuses are derived only after all corresponding mandatory proofs pass.
        output['profiles'][PROFILES[profile]]={'api':env['api'],'abi':env['abi'],'page_size_bytes':env['page_size'],'package':c['target_package'],'permission_internet':not p['internet_absent'],'startup':'pass','jni':'pass','chaquopy':'pass','python':'pass','native_loader_errors':0,'fatal_exceptions':0,'anrs':0,'network_attempts':0,'libraries':{x['name']:x['sha256'] for x in py['libraries']},'cases':{x['id']:x['status'].lower() for x in py['cases']}}
        provenance.append({'profile':profile,'run_id':r['run_id'],'result_sha256':digest(path),'image_sha256':r['image']['image_sha256'],'runner_apk_sha256':runner['apk_sha256'],'evidence_sha256':r['evidence_sha256']})
    checked=secondary.validate(output)
    require(checked['status']=='CONSISTENT_SELF_REPORTED_EVIDENCE_REQUIRES_HUMAN_REVIEW' and checked['runtime_certified'] is False,'Secondary validation failed')
    for path,h in snapshots.items():require(digest(Path(path))==h,'Evidence changed during export')
    sidecar={'schema':1,'status':'DERIVED_EVIDENCE_REQUIRES_HUMAN_REVIEW','runtime_certified':False,'contract_sha256':digest(HERE/'contract.json'),'reviewed_artifact_head':c['reviewed_head'],'auxiliary_code':PINS,'primary_matrix':primary,'runs':provenance,'log_category_counts':counts,'secondary_validation':checked,'derived_evidence_sha256':hashlib.sha256((json.dumps(output,indent=2)+'\n').encode()).hexdigest(),'distribution_allowed':False,'merge_authorized':False}
    return output,sidecar

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('results',nargs=2,type=Path);p.add_argument('--pr20-preflight',required=True,type=Path);p.add_argument('--pr21-validator',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args(argv)
    try:
        require(not a.output.exists() and not a.output.is_symlink() and not any(x.is_symlink() for x in a.output.parents),'New private output directory required')
        result,sidecar=prepare(a.results,a.pr20_preflight,a.pr21_validator)
        a.output.mkdir(parents=True,mode=0o700)
        for name,data in [('evidence-pr21.json',result),('provenance.json',sidecar)]:
            with (a.output/name).open('x',encoding='utf-8') as f:
                import os
                os.fchmod(f.fileno(),0o600);f.write(json.dumps(data,indent=2)+'\n')
        print(json.dumps({'status':sidecar['status'],'runtime_certified':False,'distribution_allowed':False}));return 0
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        print(json.dumps({'status':'BLOCKED','runtime_certified':False,'reason':'Evidence or pinned auxiliary contract rejected'}));return 1
if __name__=='__main__':raise SystemExit(main())
