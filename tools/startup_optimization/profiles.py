"""Import device-generated ART profiles only when their build still matches this source."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = 'com.flexygram.messenger.nativebaseline'
CODE_PATHS = ['TMessagesProj/src/main', 'TMessagesProj/build.gradle', 'TMessagesProj/proguard-rules.pro',
              'TMessagesProj/performance-shrink.pro', 'gradle/flexygram-performance.gradle', 'gradle.properties']

_spec = importlib.util.spec_from_file_location('startup_capture_legacy', ROOT/'tools/performance_profiles/import_profiles.py')
_capture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_capture)


def read_rules(path):
    if Path(path).stat().st_size > 5_000_000:
        raise ValueError('Profile text exceeds the import limit')
    raw = Path(path).read_text(encoding='utf-8')
    rules = list(dict.fromkeys(line.strip() for line in raw.splitlines() if line.strip() and not line.lstrip().startswith('#')))
    if not rules:
        raise ValueError('Device profile is empty')
    if any(not re.fullmatch(r'[HSP]*L[^;\s*?]+;(?:->[^\s]+)?', line) or '**' in line or '->*' in line for line in rules):
        raise ValueError('Expected captured ART rules, without whole-package wildcards')
    return rules


def descriptor(rule):
    return re.sub(r'^[HSP]+', '', rule)


def import_profiles(baselines, startup, results, report_path, root=ROOT):
    root = Path(root)
    report = json.loads(Path(report_path).read_text())
    if report.get('package') != PACKAGE or not report.get('r8_optimization_enabled'):
        raise ValueError('Profiles must come from the optimized Native Test build')
    if not re.fullmatch(r'[0-9a-f]{64}', report.get('apk_sha256', '')):
        raise ValueError('Missing profiled APK digest')
    commit = report.get('source_commit', '')
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Missing source commit in the APK build report')
    subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=root,check=True,capture_output=True)
    paths = [p for p in CODE_PATHS if p != 'TMessagesProj/src/main']
    # Profiles themselves are excluded; source/resource changes invalidate the captured run.
    result = subprocess.run(['git','diff','--quiet',commit,'--',*paths,
        'TMessagesProj/src/main/java','TMessagesProj/src/main/kotlin','TMessagesProj/src/main/res',
        'TMessagesProj/src/main/AndroidManifest.xml'],cwd=root,capture_output=True)
    if result.returncode:
        raise ValueError('The app code differs from the profiled APK; capture again')
    untracked = subprocess.run(['git','ls-files','--others','--exclude-standard','--',*CODE_PATHS],cwd=root,capture_output=True,text=True,check=True)
    if untracked.stdout.strip():
        raise ValueError('Commit the application inputs before collecting/importing profiles')
    _capture.validate_results(results)
    baseline_rules = list(dict.fromkeys(rule for path in baselines for rule in read_rules(path)))
    startup_rules = read_rules(startup)
    if not {descriptor(r) for r in startup_rules} <= {descriptor(r) for r in baseline_rules}:
        raise ValueError('Startup rules must be covered by the captured baseline profiles')
    destination = root/'TMessagesProj/src/main/generated/baselineProfiles'
    metadata = {'package': PACKAGE, 'profiled_source_commit': commit, 'profiled_apk_sha256': report.get('apk_sha256'),
                'baseline_rules': len(baseline_rules), 'startup_rules': len(startup_rules),
                'inputs': [{'file':Path(p).name,'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in [*baselines,startup]]}
    destination.mkdir(parents=True,exist_ok=True)
    (destination/'baseline-prof.txt').write_text('\n'.join(baseline_rules)+'\n')
    (destination/'startup-prof.txt').write_text('\n'.join(startup_rules)+'\n')
    (destination/'startup-profile-provenance.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,action='append',required=True)
    parser.add_argument('--startup',type=Path,required=True)
    parser.add_argument('--build-report',type=Path,required=True)
    parser.add_argument('--junit-results',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(import_profiles(args.baseline,args.startup,args.junit_results,args.build_report),indent=2))

if __name__ == '__main__':
    main()
