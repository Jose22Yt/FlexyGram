"""Verify the real merged optimizer policy and record profile packaging, not device AOT status."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile


def verify(apk, config, package, commit, profiles_dir):
    if package != 'com.flexygram.messenger.nativebaseline' or not re.fullmatch(r'[0-9a-f]{40}',commit):
        raise ValueError('Expected Native Test identity and full source commit')
    options = {line.split('#',1)[0].strip() for line in Path(config).read_text().splitlines()}
    if '-dontoptimize' in options or '-dontobfuscate' not in options:
        raise ValueError('Merged R8 policy must optimize code while preserving runtime names')
    with zipfile.ZipFile(apk) as archive:
        baseline = 'assets/dexopt/baseline.prof'
        size = archive.getinfo(baseline).file_size if baseline in archive.namelist() else 0
        if size > 1_500_000:
            raise ValueError('Embedded baseline profile is too large for ART')
    root=Path(profiles_dir)
    own_baseline=(root/'baseline-prof.txt').is_file()
    own_startup=(root/'startup-prof.txt').is_file()
    if own_baseline != own_startup:
        raise ValueError('Incomplete own baseline/startup profile pair')
    if own_baseline and size == 0:
        raise ValueError('Own baseline rules exist but no binary profile was packaged')
    with Path(apk).open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'package':package,'source_commit':commit,'apk_sha256':digest,
            'r8_optimization_enabled':True,'runtime_names_preserved':True,
            'own_device_profiles_present':own_baseline,'embedded_baseline_bytes':size,
            'device_aot_verified':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['apk','r8-config','package','commit','profiles-dir','output']: p.add_argument('--'+key,required=True)
    a=p.parse_args()
    report=verify(a.apk,a.r8_config,a.package,a.commit,a.profiles_dir)
    Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__ == '__main__': main()
