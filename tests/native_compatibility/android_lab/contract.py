"""Fail-closed reviewed-artifact contract. No device access in this module."""
from pathlib import Path
from io import BytesIO
import hashlib,json,re,struct,zipfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def require(value,message):
    if not value:raise ValueError(message)
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()
def regular(path):
    require(not path.is_symlink() and path.is_file(),'Missing or unsafe artifact: '+path.name)
    require(not any(p.is_symlink() for p in path.parents),'Symlink artifact ancestor')
def load_contract():
    c=json.loads((HERE/'contract.json').read_text())
    require(c['reviewed_head']=='867e1178719ff0bda8d9b5381b17ecc3ae8391e5','Unexpected reviewed HEAD')
    for p,h in c['protected_files'].items():require(digest(ROOT/p)==h,'Protected Diagnostic input changed: '+p)
    for key in ['runtime_cases','font','font_license']:
        require(digest(ROOT/c[key+'_path'])==c[key+'_sha256'],'Reviewed test input changed: '+key)
    require(len(c['case_ids'])==12 and len(set(c['case_ids']))==12,'Expected exactly twelve reviewed cases')
    return c

def elf16(data):
    require(data[:6]==b'\x7fELF\x02\x01' and len(data)>=64,'Expected ELF64 little-endian')
    require(struct.unpack_from('<H',data,18)[0]==183,'Expected ARM64, not native bridge/x86')
    start=struct.unpack_from('<Q',data,32)[0];stride,count=struct.unpack_from('<HH',data,54)
    require(stride>=56 and count and start+stride*count<=len(data),'Invalid program header table')
    loads=0
    for i in range(count):
        kind,flags,offset,vaddr,paddr,filesz,memsz,align=struct.unpack_from('<IIQQQQQQ',data,start+i*stride)
        if kind==1:
            loads+=1;require(align>=16384 and not align&(align-1) and (vaddr-offset)%align==0 and filesz<=memsz and offset+filesz<=len(data),'Invalid 16KB PT_LOAD')
    require(loads,'Missing PT_LOAD')

def verify_inputs(apk,wheelhouse,c):
    regular(apk);require(apk.stat().st_size==c['apk_bytes'] and digest(apk)==c['apk_sha256'],'Reviewed APK digest/size mismatch')
    require(not wheelhouse.is_symlink() and wheelhouse.is_dir() and not any(p.is_symlink() for p in wheelhouse.parents),'Missing/unsafe experimental wheelhouse')
    rows=c['wheels'];require(len(rows)==18 and sum(bool(r['rebuilt']) for r in rows)==3,'Invalid reviewed overlay inventory')
    require({p.name for p in wheelhouse.iterdir()}=={r['filename'] for r in rows},'Wheel inventory mismatch')
    wheel_libs={}
    for row in rows:
        p=wheelhouse/row['filename'];regular(p);require(digest(p)==row['sha256'],'Reviewed wheel digest mismatch: '+p.name)
        with zipfile.ZipFile(p) as z:
            require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())),'Invalid/duplicate wheel ZIP')
            if row['rebuilt']:
                for name in c['libraries']:
                    member='chaquopy/lib/'+name
                    if member in z.namelist():
                        data=z.read(member);elf16(data);require(hashlib.sha256(data).hexdigest()==c['libraries'][name],'Wheel ELF hash mismatch');require(name not in wheel_libs,'Duplicate wheel ELF');wheel_libs[name]=hashlib.sha256(data).hexdigest()
    require(wheel_libs==c['libraries'],'Four reviewed wheel ELF required')
    with zipfile.ZipFile(apk) as z:
        require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())),'Invalid/duplicate APK ZIP')
        require(all(n.startswith('lib/arm64-v8a/') for n in z.namelist() if n.startswith('lib/') and n.endswith('.so')),'Wrong installable APK ABI')
        jni=z.read('lib/arm64-v8a/'+c['jni_library']);elf16(jni);require(hashlib.sha256(jni).hexdigest()==c['jni_sha256'],'JNI APK digest mismatch')
        with zipfile.ZipFile(BytesIO(z.read('assets/chaquopy/requirements-common.imy'))) as inner:
            require(inner.testzip() is None,'Requirements IMY CRC')
            for name,h in c['libraries'].items():
                data=inner.read('chaquopy/lib/'+name);elf16(data);require(hashlib.sha256(data).hexdigest()==h,'APK/wheel native mismatch')
    return {'apk_sha256':c['apk_sha256'],'wheels':18,'rebuilt_wheels':3,'elf':4,'status':'VERIFIED_INPUTS_ONLY','android_execution':False}

def validate_environment(e,profile):
    require(profile in ['api24-4k','arm64-16k'],'Unknown environment profile')
    require(e['abi']=='arm64-v8a' and e['arch']=='aarch64' and e['native_bridge'] in ['', '0'],'Native ARM64 required; x86 translation rejected')
    require(e['emulator'] is True and e['clean_lab'] is True,'Authorized clean emulator required')
    require((e['api']==24 and e['page_size']==4096) if profile=='api24-4k' else (e['api']>=35 and e['page_size']==16384),'Wrong actual API/page size')
    if profile=='arm64-16k':require(e['strict_16k'] is True,'16KB backcompat must be disabled and recorded')

def validate_result(r,c,profile,run_id):
    require(r['status']=='PASS' and r['run_id']==run_id and r['profile']==profile,'Incomplete/failed/replayed instrumentation')
    validate_environment(r['environment'],profile)
    require(r['apk_sha256']==c['apk_sha256'] and r['certificate_sha256']==c['certificate_sha256'],'Wrong installed APK/signature')
    require(r['internet_absent'] is True and r['capabilities_closed'] is True and r['jni_loaded'] is True,'Diagnostic/JNI guard failed')
    p=r['python'];require(p['android_api']==r['environment']['api'] and p['python_minor']=='3.11','Wrong Python platform')
    require(p['jni_sha256']==c['jni_sha256'] and p['jni_scope_verified'] is True and p['plugins_not_loaded'] is True,'JNI policy or plugin isolation failed')
    rows=p['cases'];require(len(rows)==12 and {x['id'] for x in rows}==set(c['case_ids']) and all(x['status']=='PASS' for x in rows),'Missing/failed/skipped/duplicated functional cases')
    require(p['tests_run']==12 and all(p[k]==0 for k in ['failures','errors','skipped','expected_failures','unexpected_successes']),'Runtime tests were not all executed')
    libs=p['libraries'];require(len(libs)==4 and {x['name'] for x in libs}==set(c['libraries']),'Missing native load proofs')
    for x in libs:require(x['sha256']==c['libraries'][x['name']] and x['mapped_before'] is True and x['mapped_after'] is True,'Wrong/non-loaded native ELF')
    return True

def instrumentation_result(text):
    lines=[x[len('INSTRUMENTATION_RESULT: lab_result='):] for x in text.splitlines() if x.startswith('INSTRUMENTATION_RESULT: lab_result=')]
    require(len(lines)==1 and 'INSTRUMENTATION_CODE: -1' in text,'Missing/ambiguous instrumentation completion')
    return json.loads(lines[0])
