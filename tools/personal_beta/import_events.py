#!/usr/bin/env python3
"""Offline import of PR23 app-private batches through pinned PR24 parsers. No ADB."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/beta_handoff'))
from diagnostics import load_reviewed, PACKAGE
from gate import require

ENDPOINT = 'beta_idle_predraw_frame_v1'
SID = re.compile(r'b[0-9a-z]+_[0-9a-z]+')
FIELDS = {'session_id', 'export_id', 'observer_lost_events', 'observer_abandoned_operations',
          'records', 'event_endpoint', 'clock', 'source'}


def read_file(path, limit):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= limit,
            'MISSING_UNSAFE_OR_OVERSIZE_EXPORT')
    data = path.read_bytes()
    require(len(data) <= limit, 'EXPORT_LIMIT')
    return data.decode('utf-8')


def assemble(analyzer, folders):
    require(bool(folders) and len(folders) <= 1000, 'INVALID_EXPORT_COUNT')
    batches = []
    for folder in folders:
        require(folder.is_dir() and not folder.is_symlink() and not folder.name.endswith('.partial'),
                'INCOMPLETE_OR_UNSAFE_EXPORT')
        header = analyzer.strict_json(read_file(folder / 'observer.json', 4096))
        require(type(header) is dict and set(header) == FIELDS, 'INVALID_OBSERVER_FIELDS')
        require(type(header['session_id']) is str and SID.fullmatch(header['session_id']), 'INVALID_SESSION')
        for name in ('export_id', 'records', 'observer_lost_events', 'observer_abandoned_operations'):
            require(type(header[name]) is int and header[name] >= (1 if name == 'export_id' else 0),
                    'INVALID_OBSERVER_COUNTER')
        require(folder.name == header['session_id'] + '_' + str(header['export_id']), 'EXPORT_DIRECTORY_MISMATCH')
        require(header['event_endpoint'] == ENDPOINT and header['clock'] == 'android_monotonic_ns'
                and header['source'] == 'beta_local_synthetic_fixture', 'UNSUPPORTED_OBSERVER_CONTRACT')
        content = read_file(folder / 'events.jsonl', 64 * 1024 * 1024)
        lines = content.splitlines()
        require(len(lines) == header['records'] and all(lines), 'EXPORT_RECORD_COUNT_MISMATCH')
        for line in lines:
            event = analyzer.strict_json(line)
            require(type(event) is dict and type(event.get('id')) is str and
                    re.fullmatch(re.escape(header['session_id']) + r'_[0-9a-z]+', event['id']),
                    'EVENT_SESSION_MISMATCH')
        batches.append((header, content))
    require(len({h['session_id'] for h, _ in batches}) == 1, 'MIXED_ACTIVITY_SESSIONS')
    batches.sort(key=lambda item: item[0]['export_id'])
    require([h['export_id'] for h, _ in batches] == list(range(1, len(batches) + 1)),
            'MISSING_OR_DUPLICATE_EXPORT_BATCH')
    for field in ('observer_lost_events', 'observer_abandoned_operations'):
        counts = [h[field] for h, _ in batches]
        require(counts == sorted(counts), 'REGRESSING_OBSERVER_COUNTER')
    combined = '\n'.join(line for _, content in batches for line in content.splitlines())
    require(len(combined.encode()) <= 64 * 1024 * 1024, 'COMBINED_EXPORT_LIMIT')
    # Cross-batch requests may end in a later batch. Never parse fragments separately.
    metrics = analyzer.interactions(combined)
    final = batches[-1][0]
    incomplete = sum(row['incomplete'] for row in metrics['operations'].values())
    usable = (metrics['status'] == 'EVENT_SAMPLE' and final['observer_lost_events'] == 0
              and final['observer_abandoned_operations'] == 0 and incomplete == 0)
    return dict(events_sha256=hashlib.sha256(combined.encode()).hexdigest(), batches=len(batches),
                records=sum(h['records'] for h, _ in batches), endpoint=ENDPOINT,
                observer_lost_events=final['observer_lost_events'],
                observer_abandoned_operations=final['observer_abandoned_operations'],
                quality='COMPLETE_EVENT_SAMPLE_ONLY' if usable else 'INSUFFICIENT_FOR_PERFORMANCE_CLAIMS',
                interactions=metrics)


def device_profile(value):
    require(type(value) is dict and set(value) == {'android_api', 'abi', 'page_bytes', 'compat_mode_disabled'},
            'INVALID_PROFILE_FIELDS')
    require(type(value['android_api']) is int and value['android_api'] >= 24 and value['abi'] == 'arm64-v8a',
            'UNSUPPORTED_DEVICE_PROFILE')
    require(type(value['page_bytes']) is int and value['page_bytes'] in (4096, 16384), 'UNSUPPORTED_PAGE_SIZE')
    require(value['compat_mode_disabled'] is None or type(value['compat_mode_disabled']) is bool,
            'INVALID_COMPAT_OBSERVATION')
    return dict(**value, observed_by_tool=False,
                strict_16k_runtime_proven=False,
                limits='Operator-supplied facts only. A 4KB run does not test 16KB; a 16KB run needs separate compatibility-mode and native-loading evidence.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True, help='Pinned PR24 tools/beta_diagnostics')
    parser.add_argument('--exports', type=Path, nargs='+', default=[])
    parser.add_argument('--logcat', type=Path)
    parser.add_argument('--pids', type=int, nargs='*', default=[])
    parser.add_argument('--log-window', type=float, nargs=2)
    parser.add_argument('--gfxinfo', type=Path)
    parser.add_argument('--refresh-hz', type=float)
    parser.add_argument('--stream', type=int)
    parser.add_argument('--frame-window', type=int, nargs=2)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--environment', choices=['synthetic', 'personal_device'], required=True)
    parser.add_argument('--apk-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        require(re.fullmatch('[0-9a-f]{64}', args.apk_sha256), 'INVALID_DECLARED_APK_DIGEST')
        require(args.exports or args.logcat or args.gfxinfo, 'OBSERVATION_INPUT_REQUIRED')
        analyzer, _ = load_reviewed(args.source_dir)
        profile = device_profile(analyzer.strict_json(read_file(args.profile, 4096)))
        result = dict(schema=1, capture_environment=args.environment, package=PACKAGE,
                      declared_apk_sha256=args.apk_sha256, apk_bytes_verified_by_importer=False,
                      android_execution_verified_by_importer=False, comparable_with_isolated_lab=False,
                      profile=profile, events=assemble(analyzer, args.exports) if args.exports else None,
                      logcat=analyzer.logs(read_file(args.logcat, 64 * 1024 * 1024), PACKAGE, args.pids, args.log_window) if args.logcat else None,
                      frames=analyzer.frames(read_file(args.gfxinfo, 64 * 1024 * 1024), args.refresh_hz, args.stream, args.frame_window) if args.gfxinfo else None,
                      limits='Reads supplied files only; no capture/sign/install/launch, no authorization receipt, no physical touch-to-photon or authenticated chat measurements.')
    except Exception:
        print(json.dumps({'status': 'BLOCKED_INVALID_OR_INCOMPLETE_INPUT'}))
        return 1
    # Refuse overwrite: failed/partial imports cannot replace an approved report.
    with os.fdopen(os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as file:
        json.dump(result, file, indent=2, allow_nan=False)
        file.write('\n')
    print(json.dumps({'status': 'IMPORTED_SUPPLIED_FILES_ONLY', 'quality': result['events']['quality'] if result['events'] else 'NO_EVENT_MEASUREMENTS',
                      'android_execution_verified': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
