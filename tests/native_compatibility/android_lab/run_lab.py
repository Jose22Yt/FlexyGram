"""Local emulator-only Android executor. Default inventory never installs anything.
Run mode requires the reviewed private artifacts and explicit offline lab receipt.
"""
from pathlib import Path
import argparse,hashlib,json,os,platform,re,secrets,shutil,subprocess,sys,time,zipfile
from contract import HERE,ROOT,digest,load_contract,require,regular,verify_inputs,validate_environment,validate_result,instrumentation_result

def inventory():
    caps=Path('/proc/self/status').read_text() if Path('/proc/self/status').exists() else ''
    cap=re.search(r'^CapEff:\s*([0-9a-f]+)',caps,re.M);bits=int(cap[1],16) if cap else 0
    return {'host_arch':platform.machine(),'host_pages':os.sysconf('SC_PAGE_SIZE'),'kvm':Path('/dev/kvm').exists(),'tun':Path('/dev/net/tun').exists(),'cap_net_admin':bool(bits&(1<<12)),'cap_sys_admin':bool(bits&(1<<21)),'adb':bool(shutil.which('adb')),'emulator':bool(shutil.which('emulator')),'qemu_arm64':bool(shutil.which('qemu-system-aarch64')),'launch_cvd':bool(shutil.which('launch_cvd')),'android_executed':False,'status':'INVENTORY_ONLY'}
def serial_ok(serial):return bool(re.fullmatch(r'emulator-[0-9]+|127\.0\.0\.1:[0-9]+|localhost:[0-9]+',serial))
def counters(text):
    rows=[line.split() for line in text.splitlines() if re.match(r'^\s*\d+\s+\d+\s+DROP\b',line)]
    require(len(rows)==1,'Missing/ambiguous firewall DROP counter')
    return {'packets':int(rows[0][0]),'bytes':int(rows[0][1])}
def offline_receipt(path):
    regular(path);r=json.loads(path.read_text())
    for key in ['disposable_emulator','no_accounts','no_personal_data','host_egress_and_lan_blocked','local_adb_only']:
        require(r.get(key) is True,'Missing operator offline attestation: '+key)
    require(re.fullmatch(r'[0-9a-f]{64}',r.get('image_sha256','')) and r.get('image_origin') and r.get('image_revision'),'Image provenance missing')
    return r

class Adb:
    def __init__(self,binary,serial):require(serial_ok(serial),'Only explicit local emulator serials allowed');self.binary=str(binary);self.serial=serial
    def run(self,*args,timeout=45,check=True):
        p=subprocess.run([self.binary,'-s',self.serial,*map(str,args)],capture_output=True,text=True,timeout=timeout)
        if check:require(p.returncode==0,'ADB command failed: '+str(args[0])+'\n'+p.stderr[:500])
        return p.stdout+p.stderr
    def shell(self,*args,**kw):return self.run('shell',*args,**kw).replace('\r','').strip()
    def prop(self,name):return self.shell('getprop',name)

def preflight(adb,profile):
    require(adb.run('get-state').strip()=='device','ADB device unavailable')
    hardware=adb.prop('ro.hardware')
    e={'api':int(adb.prop('ro.build.version.sdk')),'page_size':int(adb.shell('getconf','PAGE_SIZE')),'abi':adb.prop('ro.product.cpu.abi'),'arch':adb.shell('uname','-m'),'native_bridge':adb.prop('ro.dalvik.vm.native.bridge'),'emulator':adb.prop('ro.kernel.qemu')=='1' or adb.prop('ro.boot.qemu')=='1' or hardware.startswith('cutf_'),'clean_lab':True,'strict_16k':adb.prop('bionic.linker.16kb.app_compat.enabled') in ['false','fatal'] and adb.prop('pm.16kb.app_compat.disabled')=='true','build_fingerprint':adb.prop('ro.build.fingerprint')}
    validate_environment(e,profile)
    return e

def verify_runner(apk,receipt,tools,c):
    regular(apk);regular(receipt);r=json.loads(receipt.read_text())
    require(r['signed_with_reviewed_lab_key'] is True and digest(apk)==r['apk_sha256'],'Runner unsigned or receipt/hash mismatch')
    expected_sources=[HERE/'java/io/github/jose22yt/flexygram/lab/LabInstrumentation.java',HERE/'AndroidManifest.xml',HERE/'assets/probe.py',HERE/'contract.json',ROOT/c['runtime_cases_path']]
    require(r['source_hashes']=={str(p.relative_to(ROOT)):digest(p) for p in expected_sources},'Runner compiled from different source')
    out=subprocess.run([str(tools/'apksigner'),'verify','--verbose','--print-certs',str(apk)],capture_output=True,text=True)
    require(out.returncode==0 and 'certificate SHA-256 digest: '+c['certificate_sha256'] in out.stdout,'Runner signature mismatch')
    with zipfile.ZipFile(apk) as z:
        expected={'contract.json':(HERE/'contract.json').read_bytes(),'probe.py':(HERE/'assets/probe.py').read_bytes(),'runtime_cases.py':(ROOT/c['runtime_cases_path']).read_bytes(),'font.ttf':(ROOT/c['font_path']).read_bytes(),'font-LICENSE.txt':(ROOT/c['font_license_path']).read_bytes()}
        require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())),'Runner ZIP invalid')
        require(not any(x.startswith('lib/') for x in z.namelist()),'No test replacement native libraries allowed')
        for name,data in expected.items():require(z.read('assets/'+name)==data,'Runner assets differ from reviewed harness')
    manifest=subprocess.run([str(tools/'aapt2'),'dump','xmltree','--file','AndroidManifest.xml',str(apk)],capture_output=True,text=True)
    require(manifest.returncode==0 and 'uses-permission' not in manifest.stdout and c['runner_class'] in manifest.stdout and c['target_package'] in manifest.stdout,'Runner manifest mismatch')
    return r

def execute(a):
    require(not a.output.exists() and not any(p.is_symlink() for p in a.output.parents),'New private output directory required')
    a.output.mkdir(parents=True,mode=0o700);report={'status':'BLOCKED','android_executed':False,'stage':'inputs'};adb=None;installed=False
    c=load_contract();nonce=secrets.token_hex(16);report.update(run_id=nonce,profile=a.profile,reviewed_head=c['reviewed_head'])
    try:
        report['inputs']=verify_inputs(a.apk,a.wheelhouse,c);operator=offline_receipt(a.offline_receipt)
        report['runner']=verify_runner(a.runner_apk,a.runner_receipt,a.build_tools,c)
        require(a.adb.is_file(),'ADB unavailable');adb=Adb(a.adb,a.serial);report['stage']='environment';report['environment']=preflight(adb,a.profile)
        for pkg in [c['target_package'],c['runner_package']]:require(not adb.shell('pm','path',pkg),'Existing lab package rejected; use fresh emulator')
        packages=adb.shell('pm','list','packages').lower()
        require(not any(x in packages for x in ['org.telegram','com.exteraless.app','org.thunderdog.challegram']),'Other Telegram client present')
        # Read only counts; never retain or print AccountManager's account dump.
        accounts=adb.shell('dumpsys','account');counts=re.findall(r'^\s*Accounts:\s*(\d+)\s*$',accounts,re.M)
        require(counts and all(int(x)==0 for x in counts),'Empty accounts not verifiable');del accounts
        adb.run('root');adb.run('wait-for-device');require('uid=0' in adb.shell('id'),'Root AOSP emulator required for UID packet counters')
        adb.shell('svc','wifi','disable');adb.shell('svc','data','disable')
        adb.run('logcat','-c');report['stage']='installation'
        (a.output/'install-target.log').write_text(adb.run('install','--no-streaming',a.apk,timeout=180));installed=True
        (a.output/'install-runner.log').write_text(adb.run('install','--no-streaming',a.runner_apk,timeout=180))
        package=adb.shell('dumpsys','package',c['target_package']);(a.output/'package-before.log').write_text(package)
        require('android.permission.INTERNET' not in package,'Installed INTERNET permission found')
        matches=re.findall(r'^\s*userId=(\d+)\s*$',package,re.M);require(len(set(matches))==1,'Ambiguous package UID');uid=matches[0]
        chain='FGLAB_'+nonce[:12];report['app_uid']=int(uid);report['firewall_chain']=chain
        before={}
        for tool in ['iptables','ip6tables']:
            adb.shell(tool,'-w','-N',chain);adb.shell(tool,'-w','-A',chain,'-j','DROP');adb.shell(tool,'-w','-I','OUTPUT','1','-m','owner','--uid-owner',uid,'-j',chain)
            text=adb.shell(tool,'-w','-nvxL',chain);before[tool]=counters(text);(a.output/(tool+'-before.log')).write_text(text)
        report['stage']='launch';report['android_run_attempted']=True
        text=adb.shell('am','start','-W','-n',c['target_package']+'/org.telegram.messenger.ExteralessIcon',timeout=a.timeout)
        (a.output/'cold-launch.log').write_text(text);require('Status: ok' in text,'Cold launch did not complete')
        require(30<=a.observe_seconds<=300,'Observation must be 30..300 seconds');time.sleep(a.observe_seconds)
        require(adb.shell('pidof',c['target_package']),'Target exited before instrumentation');report['android_executed']=True
        # Fresh instrumentation process rechecks on-device APK/signature, API/page and policy.
        report['stage']='instrumentation'
        text=adb.run('shell','am','instrument','-w','-r','-e','run_id',nonce,'-e','profile',a.profile,'-e','clean_lab','true',c['runner_package']+'/'+c['runner_class'],timeout=a.timeout)
        (a.output/'instrumentation.log').write_text(text);r=instrumentation_result(text);report['instrumentation']=r;report['android_executed']=True
        validate_result(r,c,a.profile,nonce)
        after={}
        for tool in ['iptables','ip6tables']:
            text=adb.shell(tool,'-w','-nvxL',chain);after[tool]=counters(text);(a.output/(tool+'-after.log')).write_text(text)
        report['network']={'before':before,'after':after,'host_isolation':'operator_attested','limits':'UID IPv4/IPv6 packet counters during this interval; not all IPC or delegated traffic'}
        require(all(after[k]['packets']==before[k]['packets']==0 and after[k]['bytes']==before[k]['bytes']==0 for k in after),'Network packet attempts detected')
        report['stage']='logs';log=adb.run('logcat','-d','-v','threadtime');(a.output/'logcat.log').write_text(log)
        crashes=adb.run('logcat','-b','crash','-d');(a.output/'crash.log').write_text(crashes)
        require(not re.search(r'FATAL EXCEPTION|Fatal signal|ANR in|dlopen failed|cannot locate symbol|UnsatisfiedLinkError|NoClassDefFoundError|VerifyError',log+'\n'+crashes),'Critical lab log observed; investigate attribution')
        (a.output/'package-after.log').write_text(adb.shell('dumpsys','package',c['target_package']))
        report['image']={k:operator[k] for k in ['image_origin','image_revision','image_sha256']};report['status']='PASS';report['stage']='complete'
    except Exception as error:
        report['error_class']=type(error).__name__;report['error']=str(error)[:2000]
        if adb and installed:
            for label,args in [('logcat.log',['logcat','-d','-v','threadtime']),('crash.log',['logcat','-b','crash','-d'])]:
                try:(a.output/label).write_text(adb.run(*args))
                except Exception:pass
    finally:
        if adb and installed:
            try:adb.shell('am','force-stop',c['target_package'])
            except Exception:pass
        report['evidence_sha256']={p.name:digest(p) for p in sorted(a.output.iterdir()) if p.is_file()}
        (a.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

def matrix(paths,c):
    require(len(paths)==2,'Two separate lab results required');rows=[json.loads(p.read_text()) for p in paths]
    require({r['profile'] for r in rows}=={'api24-4k','arm64-16k'} and len({r['run_id'] for r in rows})==2,'Missing/repeated environment run')
    for path,r in zip(paths,rows):
        evidence=r.get('evidence_sha256',{})
        needed={'instrumentation.log','cold-launch.log','logcat.log','crash.log','iptables-before.log','iptables-after.log','ip6tables-before.log','ip6tables-after.log'}
        require(needed.issubset(evidence),'Missing Android evidence files')
        for name,h in evidence.items():
            require(Path(name).name==name,'Evidence path traversal')
            file=path.parent/name;regular(file);require(digest(file)==h,'Evidence digest mismatch')
        require(instrumentation_result((path.parent/'instrumentation.log').read_text())==r['instrumentation'],'Instrumentation proof differs from report')
        require(r['status']=='PASS' and r['android_executed'] is True,'Unexecuted/blocked environment')
        validate_result(r['instrumentation'],c,r['profile'],r['run_id'])
        require(set(r['network']['after'])=={'iptables','ip6tables'},'Missing traffic family')
        for family in ['iptables','ip6tables']:
            require(r['network']['after'][family]==r['network']['before'][family]=={'packets':0,'bytes':0},'Traffic attempt or incomplete counters')
    return {'status':'PASS_BOTH_ANDROID_LABS','apk_sha256':c['apk_sha256'],'profiles':sorted(r['profile'] for r in rows),'distribution_allowed':False,'merge_authorized':False}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='mode',required=True);s.add_parser('inventory')
    m=s.add_parser('matrix');m.add_argument('results',nargs=2,type=Path)
    v=s.add_parser('verify-inputs');v.add_argument('--apk',required=True,type=Path);v.add_argument('--wheelhouse',required=True,type=Path)
    a=s.add_parser('run')
    for flag in ['apk','wheelhouse','runner-apk','runner-receipt','build-tools','offline-receipt','adb','output']:a.add_argument('--'+flag,required=True,type=Path)
    a.add_argument('--serial',required=True);a.add_argument('--profile',required=True,choices=['api24-4k','arm64-16k']);a.add_argument('--timeout',type=int,default=900);a.add_argument('--observe-seconds',type=int,default=60)
    args=p.parse_args()
    try:
        r=inventory() if args.mode=='inventory' else matrix(args.results,load_contract()) if args.mode=='matrix' else verify_inputs(args.apk,args.wheelhouse,load_contract()) if args.mode=='verify-inputs' else execute(args)
        print(json.dumps(r,indent=2));sys.exit(1 if r['status']=='BLOCKED' else 0)
    except Exception as error:print(json.dumps({'status':'BLOCKED','error_class':type(error).__name__,'error':str(error)[:1000],'android_executed':False}));sys.exit(1)
