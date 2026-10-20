#!/usr/bin/env python3
"""Check pinned PR24 analyzers against the beta identity, using synthetic input only."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
from gate import require, sha256

PACKAGE = 'io.github.jose22yt.flexygram.beta.development'
COMMIT = 'db5b9a113d54f552a925ea233c5b199ab95bfcdb'
PINS = {
    'analyze.py': '13887e9701a8ce97fa25280d9249c5e8d569f5ac2b1f9349f9d738b44f0b2881',
    'capture.py': '186432313dd9ddecc59227bd223f2ad2783740574aba667018c4648c04b1033e',
}


def load_reviewed(folder):
    # Reject changed files before executing either module. No copy/vendor of PR24.
    for name, digest in PINS.items():
        path = folder / name
        require(path.is_file() and not path.is_symlink() and sha256(path) == digest,
                'PR24_SOURCE_PIN_MISMATCH')
    old = sys.modules.get('analyze')
    try:
        modules = []
        for name in ('analyze', 'capture'):
            spec = importlib.util.spec_from_file_location(name, folder / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            if name == 'analyze':
                sys.modules['analyze'] = module
            spec.loader.exec_module(module)
            modules.append(module)
        return tuple(modules)
    finally:
        if old is None:
            sys.modules.pop('analyze', None)
        else:
            sys.modules['analyze'] = old


def check(folder):
    analyze, capture = load_reviewed(folder)
    meta = dict(schema=1, client='FlexyGram', apk_sha256='0' * 64,
                source='synthetic', run_id='beta_handoff_fixture', repetition=0,
                conditions={'build_type': 'betaDevelopmentDebug', 'protocol': 'pr24_v1'})
    # Use a non-target PID for system-owned ANR attribution to the exact package.
    log = '\n'.join([
        '123.000 10 10 E AndroidRuntime: FATAL EXCEPTION: main',
        '123.001 11 11 E ActivityManager: ANR in ' + PACKAGE,
        '123.002 10 10 E linker: dlopen failed: synthetic.so',
        '123.003 10 10 E python: com.chaquo.python.PyException: synthetic',
        '123.004 12 12 E ActivityManager: ANR in ' + PACKAGE + '.unrelated',
    ])
    result = analyze.report(meta, PACKAGE, [10], log_text=log, event_text='')
    counts = result['logcat']['signal_counts']
    require(all(counts[name] == 1 for name in ('java_fatal', 'anr', 'native_load', 'python')),
            'BETA_DIAGNOSTICS_ATTRIBUTION_MISMATCH')
    require(result['interactions']['status'] == 'NO_EVENT_DATA' and result['frames'] is None,
            'MISSING_OBSERVATIONS_BECAME_METRICS')
    plan = capture.command_plan(Path('/not-executed/adb'), 'emulator-5554', PACKAGE)
    require(any(PACKAGE in command and 'framestats' in command for command in plan),
            'BETA_CAPTURE_PACKAGE_MISMATCH')
    require(not any(token in command for command in plan for token in ('install', 'start', 'input', 'reset')),
            'UNEXPECTED_MUTATING_CAPTURE_COMMAND')
    return dict(status='SYNTHETIC_BETA_COMPATIBILITY_PASS', pr24_commit=COMMIT,
                package=PACKAGE, report=result, capture_plan=plan,
                adb_executed=False, android_executed=False, real_apk_accessed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True,
                        help='tools/beta_diagnostics from a separate PR24 checkout at the pinned commit')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = check(args.source_dir)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
