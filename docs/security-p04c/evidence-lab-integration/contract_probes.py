"""Offline review probes, not another Android runner. Synthetic fixtures only.
Usage: python contract_probes.py --pr17-root ... --pr20-root ... --pr21-root ...
Requires exact reviewed checkouts. Does not install, connect or write to them.
"""
from pathlib import Path
import argparse,contextlib,hashlib,importlib.util,io,json,sys,tempfile,zipfile

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def run(a):
    t20=load('review_preflight_fixture',a.pr20_root/'tests/android_lab_preflight/test_preflight.py')
    t21=load('review_evidence_fixture',a.pr21_root/'tests/android_lab_evidence/test_check.py')
    c=json.loads((a.pr17_root/'tests/native_compatibility/android_lab/contract.json').read_text())
    gate=t21.gate;pre=t20.module
    pins=gate.APK_SHA256==c['apk_sha256'] and gate.CERT_SHA256==c['certificate_sha256'] and gate.LIBRARIES==c['libraries'] and set(gate.CASE_NAMES)==set(c['case_ids'])
    if not pins:raise ValueError('Contract constants diverged')
    rows=[]
    # Advertising ARM64 can come from translation; PR20 currently only checks membership.
    mixed=t20.SimulatedRunner(abis='x86_64,arm64-v8a')
    got=pre.emulator_probe('emulator-5554','api24',mixed)
    rows.append({'probe':'mixed_x86_arm64_advertisement','observed_pr20':'ACCEPTED_ADVERTISED_ABI','actual_android_execution':False,'missing_reads':[x for x in ['uname','ro.product.cpu.abi','ro.dalvik.vm.native.bridge'] if not any(x in cmd for cmd in mixed.calls)],'fix_required_before_authoritative_preflight':True})
    # This is an intentional counterexample to treating preflight exit0 as a runtime gate.
    with tempfile.TemporaryDirectory() as td:
        apk=Path(td)/'synthetic.apk'
        with zipfile.ZipFile(apk,'w') as z:z.writestr('AndroidManifest.xml',b'SYNTHETIC_NOT_ANDROID')
        log=Path(td)/'synthetic.log';log.write_text('FATAL EXCEPTION: synthetic\nModuleNotFoundError: synthetic\n')
        argv=['--serial','emulator-5554','--profile','api24','--apk',str(apk),'--expected-apk-sha256',hashlib.sha256(apk.read_bytes()).hexdigest(),'--expected-cert-sha256',t20.CERT,'--log-file',str(log)]
        output=io.StringIO()
        with contextlib.redirect_stdout(output):rc=pre.main(argv,run=t20.SimulatedRunner())
        report=json.loads(output.getvalue())
        rows.append({'probe':'critical_log_with_valid_mock_preflight','exit_code':rc,'status':report['status'],'counts':report['log_indicators']['category_counts'],'must_not_be_used_as_final_runtime_gate':True})
    # Formats are deliberately different; direct ingestion must fail, not fill defaults.
    sys.path.insert(0,str(a.pr17_root/'tests/native_compatibility/android_lab'))
    from contract import validate_environment
    env={'api':24,'page_size':4096,'abi':'arm64-v8a','arch':'x86_64','native_bridge':'libndk_translation.so','emulator':True,'clean_lab':True,'strict_16k':False}
    rejected=False
    try:validate_environment(env,'api24-4k')
    except ValueError:rejected=True
    if not rejected:raise ValueError('PR17 native guard no longer rejects translated x86')
    direct=gate.validate({'status':'PASS_BOTH_ANDROID_LABS','profiles':['api24-4k','arm64-16k']})
    fixture=gate.validate(t21.fixture())
    if direct['status']!='BLOCKED' or fixture['runtime_certified'] is not False:raise ValueError('Evidence semantics weakened')
    return {'status':'OFFLINE_REVIEW_REPRODUCED','pins_and_12_case_ids_match':pins,'pr17_rejects_translated_x86':rejected,'pr21_rejects_direct_pr17_format':direct['status'],'pr21_synthetic_positive_status':fixture['status'],'runtime_certified':False,'observations':rows,'android_executed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['pr17-root','pr20-root','pr21-root']:p.add_argument('--'+name,type=Path,required=True)
    print(json.dumps(run(p.parse_args()),indent=2))
