#!/usr/bin/env python3
"""Personal beta read-only capture. Default: plan; never launch/install/sign/reset."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools/personal_beta'), str(ROOT/'tests/native_compatibility')]
import import_events
from verify_post_sign_diagnostic import check_signature, strict_json, regular

PACKAGE = import_events.PACKAGE
ENTRY = 'org.telegram.ui.beta.BetaPreviewActivity'
SCOPE = 'personal_beta_read_only_capture_v1'
HEX = re.compile(r'[0-9a-f]{64}')
EXPORT = re.compile(r'b[0-9a-z]+_[0-9a-z]+_[1-9][0-9]*')


def require(value, code):
    if not value:
        raise ValueError(code)


def digest(path):
    regular(path)
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def plan():
    return dict(status='PLAN_ONLY', package=PACKAGE, adb_executed=False,
                operations=['USB target verification', 'pm path/package version',
                            'hash installed base.apk against approved signed APK',
                            'package-scoped exit-info before/after manual actions',
                            'verified live PID Logcat only', 'package gfxinfo framestats',
                            'explicit app-private observer batches only'],
                forbidden=['install', 'uninstall', 'launch', 'input', 'root', 'settings',
                           'logcat clear', 'accounts', 'global Logcat', 'uploads'])


def authorize(args):
    data = strict_json(args.authorization)
    require(isinstance(data, dict) and data.get('schema') == 1 and
            data.get('scope') == SCOPE and data.get('package') == PACKAGE and
            data.get('authorized') is True and data.get('apk_sha256') == args.apk_sha256 and
            data.get('certificate_sha256') == args.certificate_sha256 and
            data.get('device_serial') == args.serial and
            isinstance(data.get('approval_reference'), str) and
            len(data['approval_reference'].strip()) >= 8, 'READ_ONLY_AUTHORIZATION_REQUIRED')


class Adb:
    """Closed command set. No arbitrary shell or inherited remote ADB configuration."""
    def __init__(self, binary, serial):
        require(re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', serial or '') and
                not serial.startswith(('emulator-', '-')), 'USB_SERIAL_REQUIRED')
        self.prefix = [str(binary), '-H', '127.0.0.1', '-P', '5037', '-s', serial]

    def allowed(self, parts):
        fixed = [('get-state',), ('get-devpath',), ('shell','am','get-current-user'),
                 ('shell','pm','path','--user','current',PACKAGE),
                 ('shell','dumpsys','package',PACKAGE), ('shell','pidof',PACKAGE),
                 ('shell','dumpsys','activity','exit-info',PACKAGE),
                 ('shell','dumpsys','activity','activities',PACKAGE),
                 ('shell','dumpsys','gfxinfo',PACKAGE,'framestats'),
                 ('shell','getprop','ro.build.version.sdk'),
                 ('shell','getprop','ro.product.cpu.abi'), ('shell','getconf','PAGE_SIZE'),
                 ('shell','date','+%s.%N')]
        if tuple(parts) in fixed:
            return True
        if len(parts) == 3 and parts[:2] == ['shell','cat']:
            return bool(re.fullmatch(r'/proc/[1-9][0-9]{0,7}/(?:cmdline|stat|status)', parts[2]))
        if len(parts) == 10 and parts[:7] == ['logcat','-b','main','-b','crash','-d','-v']:
            return (parts[7] == 'epoch' and bool(re.fullmatch(r'--pid=[1-9][0-9]{0,7}', parts[8]))
                    and parts[9] == '-t500')
        if len(parts) == 3 and parts[:2] == ['exec-out','cat']:
            return bool(re.fullmatch(r'/data/app/[A-Za-z0-9_./=+~\-]+/base\.apk', parts[2]) and
                        '..' not in parts[2].split('/'))
        if len(parts) == 5 and parts[:4] == ['exec-out','run-as',PACKAGE,'cat']:
            return bool(re.fullmatch(r'files/beta-observer/b[0-9a-z]+_[0-9a-z]+_[1-9][0-9]*/(?:observer\.json|events\.jsonl)', parts[4]))
        return False

    def read(self, parts, *, hash_only=False):
        require(self.allowed(parts), 'COMMAND_NOT_READ_ONLY_ALLOWLISTED')
        require(not hash_only or parts[:2] == ['exec-out','cat'], 'INVALID_HASH_OPERATION')
        limit = 512*1024*1024 if hash_only else 64*1024*1024
        env = {k: os.environ[k] for k in ('PATH','LANG','LC_ALL','SYSTEMROOT') if k in os.environ}
        env.update(ADB_SERVER_SOCKET='tcp:127.0.0.1:5037', ADB_MDNS_AUTO_CONNECT='0')
        # Anonymous private temporary streams, removed on every exit; no raw logs saved.
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            process = subprocess.Popen(self.prefix + parts, stdout=out, stderr=err, env=env)
            try:
                deadline = time.monotonic() + 90
                while process.poll() is None:
                    require(time.monotonic() < deadline, 'ADB_TIMEOUT')
                    require(os.fstat(out.fileno()).st_size <= limit and
                            os.fstat(err.fileno()).st_size <= 1024*1024, 'ADB_OUTPUT_LIMIT')
                    time.sleep(.02)
                require(process.returncode == 0 and os.fstat(out.fileno()).st_size <= limit,
                        'ADB_READ_UNAVAILABLE')
                out.seek(0)
                return hashlib.file_digest(out, 'sha256').hexdigest() if hash_only else out.read().decode('utf-8')
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()


def optional(adb, parts):
    try:
        return adb.read(parts)
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError):
        return None


def parse_version(text, code, name):
    # Exact package heading; do not accept substring identities or multiple packages.
    headings = re.findall(r'(?m)^\s*Package \[([^\]]+)\]', text)
    require(headings == [PACKAGE], 'INSTALLED_PACKAGE_UNRECOGNIZED')
    codes = re.findall(r'(?m)^\s*versionCode=(\d+)\b', text)
    names = re.findall(r'(?m)^\s*versionName=(\S+)\s*$', text)
    require(codes == [code] and names == [name], 'INSTALLED_VERSION_MISMATCH')


def exits(text, user=0):
    """AOSP exit-info subset; reason codes, never descriptions, accounts or traces."""
    if text is None or not text.startswith('ACTIVITY MANAGER PROCESS EXIT INFO'):
        return None
    sections = re.split(r'(?m)^\s*package: (\S+)\s*$', text)
    result = set()
    for index in range(1, len(sections), 2):
        if sections[index] != PACKAGE:
            continue
        for block in re.split(r'(?m)^\s*ApplicationExitInfo #[0-9]+:\s*$', sections[index+1])[1:]:
            stamp = re.search(r'(?m)^\s*timestamp=(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3}) pid=(\d+)\b', block)
            process = re.search(r'(?m)^\s*process=(\S+) reason=(\d+) \([^\n]*\) subreason=', block)
            status = re.search(r'\bstatus=(-?\d+)\s*$', block, re.M)
            owner = re.search(r'(?m)^\s*timestamp=[^\n]+ user=(\d+)\s*$', block)
            if not (stamp and process and status and owner):
                return None
            if process[1] == PACKAGE and int(owner[1]) == user:
                result.add((stamp[1], int(stamp[2]), int(process[2]), int(status[1])))
    if len(sections) > 1:
        return result
    # AOSP's empty history includes a persistence timestamp but no package section.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return set() if all(line == 'ACTIVITY MANAGER PROCESS EXIT INFO (dumpsys activity exit-info)' or
                       re.fullmatch(r'Last Timestamp of Persistence Into Persistent Storage: \d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3}', line)
                       for line in lines) else None


def exit_delta(before, after):
    if before is None or after is None:
        return dict(status='UNKNOWN', confirmed_error_reasons=[], exit_self=0, system_or_other=0)
    rows = after - before
    errors = [r[2] for r in rows if r[2] in (4,5,6,7)]
    return dict(status='CONFIRMED_OS_ERROR_EXIT' if errors else 'NO_NEW_ERROR_EXIT_OBSERVED',
                confirmed_error_reasons=sorted(errors), exit_self=sum(r[2] == 1 for r in rows),
                system_or_other=sum(r[2] not in (1,4,5,6,7) for r in rows),
                limits='Only new OS exit records; self exit is not proof of a correct UI close. Ring buffer/delayed records may be incomplete.')


def process_identity(adb, pid, user=0):
    cmd = optional(adb, ['shell','cat',f'/proc/{pid}/cmdline'])
    stats = optional(adb, ['shell','cat',f'/proc/{pid}/stat'])
    status = optional(adb, ['shell','cat',f'/proc/{pid}/status'])
    uid = re.search(r'(?m)^Uid:\s+(\d+)\s+\d+\s+\d+\s+\d+\s*$', status or '')
    if cmd is None or cmd.split('\0')[0] != PACKAGE or stats is None or not uid or int(uid[1])//100000 != user:
        return None
    parts = stats.rsplit(')', 1)
    fields = parts[-1].split()
    if len(parts) != 2 or not re.fullmatch(str(pid) + r' \(.*', parts[0]) or len(fields) < 20 or not fields[19].isdigit():
        return None
    return fields[19]  # Linux /proc stat starttime, field22; detect PID reuse.


def scoped_logs(adb, analyzer, during=lambda: None, user=0):
    ids = optional(adb, ['shell','pidof',PACKAGE])
    if ids is None or not re.fullmatch(r'[1-9][0-9]{0,7}\s*', ids):
        during()
        return dict(status='UNKNOWN_NO_VERIFIED_LIVE_MAIN_PROCESS')
    pid = int(ids)
    identity = process_identity(adb, pid, user)
    start = optional(adb, ['shell','date','+%s.%N'])
    if identity is None or start is None or not re.fullmatch(r'\d{1,12}\.\d{9}\s*', start):
        during()
        return dict(status='UNKNOWN_PROCESS_OR_CLOCK_UNAVAILABLE')
    during()
    text = optional(adb, ['logcat','-b','main','-b','crash','-d','-v','epoch',f'--pid={pid}','-t500'])
    end = optional(adb, ['shell','date','+%s.%N'])
    if text is None or end is None or not re.fullmatch(r'\d{1,12}\.\d{9}\s*', end) or float(end) <= float(start):
        return dict(status='UNKNOWN_LOG_WINDOW_UNAVAILABLE')
    if process_identity(adb, pid, user) != identity:
        return dict(status='UNKNOWN_PROCESS_ENDED_OR_REUSED_LOGS_DISCARDED')
    # Defence against tool/OEM filter failure: never forward another PID's message.
    lines = []
    trusted_tags = {'AndroidRuntime','libc','DEBUG','linker','linker64','python',
                    'python.stderr','Chaquopy','chaquopy','System.err','Choreographer','art'}
    for line in text.splitlines():
        parsed = analyzer.EPOCH.match(line)
        if parsed and int(parsed[2]) == pid and parsed[5].strip() in trusted_tags:
            lines.append(line)
    return analyzer.logs('\n'.join(lines), PACKAGE, [pid], (float(start), float(end)))


def export_batches(adb, analyzer, names, directory):
    require(len(names) == len(set(names)) and len(names) <= 100, 'INVALID_EXPORT_LIST')
    if not names:
        return None
    # Invalid batches (possibly containing arbitrary text) never persist as diagnostics.
    with tempfile.TemporaryDirectory(dir=directory) as temporary:
        folders = []
        for name in names:
            require(EXPORT.fullmatch(name), 'INVALID_EXPLICIT_EXPORT_NAME')
            folder = Path(temporary)/name
            folder.mkdir(mode=0o700)
            for filename, limit in [('observer.json',4096), ('events.jsonl',64*1024*1024)]:
                data = adb.read(['exec-out','run-as',PACKAGE,'cat',f'files/beta-observer/{name}/{filename}'])
                require(len(data.encode()) <= limit, 'EXPORT_SIZE_LIMIT')
                with os.fdopen(os.open(folder/filename, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600), 'w') as target:
                    target.write(data)
            folders.append(folder)
        result = import_events.assemble(analyzer, folders)
        require(not any((directory/f.name).exists() for f in folders), 'EXPORT_OUTPUT_EXISTS')
        for folder in folders:
            folder.rename(directory/folder.name)
        return result


def collect(args, adb, analyzer, directory, sleeper=time.sleep):
    require(adb.read(['get-state']).strip() == 'device' and
            re.fullmatch(r'usb:[A-Za-z0-9_.:-]+\s*', adb.read(['get-devpath'])), 'AUTHORIZED_USB_DEVICE_REQUIRED')
    require(digest(args.approved_apk) == args.apk_sha256, 'APPROVED_APK_HASH_MISMATCH')
    check_signature(args.approved_apk, args.apksigner, args.certificate_sha256)
    local_hash = digest(args.approved_apk)
    user = adb.read(['shell','am','get-current-user']).strip()
    require(re.fullmatch(r'[0-9]{1,6}',user), 'CURRENT_ANDROID_USER_UNAVAILABLE')
    version = adb.read(['shell','dumpsys','package',PACKAGE])
    parse_version(version, args.version_code, args.version_name)
    paths = adb.read(['shell','pm','path','--user','current',PACKAGE]).splitlines()
    require(len(paths) == 1 and paths[0].startswith('package:'), 'SPLIT_OR_UNAVAILABLE_APK')
    apk_path = paths[0][len('package:'):]
    require(adb.allowed(['exec-out','cat',apk_path]), 'UNSAFE_INSTALLED_APK_PATH')
    require(adb.read(['exec-out','cat',apk_path], hash_only=True) == args.apk_sha256,
            'INSTALLED_APK_HASH_MISMATCH')
    before = exits(optional(adb, ['shell','dumpsys','activity','exit-info',PACKAGE]),int(user))
    # Start the log window BEFORE manual navigation, not after the observation wait.
    def observe():
        print('{"status":"READ_ONLY_WINDOW_READY_MANUAL_ACTIONS_ONLY"}', flush=True)
        sleeper(args.observe_seconds)
    logs = scoped_logs(adb, analyzer, during=observe, user=int(user))
    after = exits(optional(adb, ['shell','dumpsys','activity','exit-info',PACKAGE]),int(user))
    history = exit_delta(before, after)
    activity = optional(adb, ['shell','dumpsys','activity','activities',PACKAGE])
    resumed = bool(activity and re.search(r'(?m)^\s*(?:mResumedActivity|topResumedActivity)[:=]?\s*.*\b' +
                   re.escape(PACKAGE+'/'+ENTRY) + r'(?=[\s}])', activity))
    frames = None
    frame_error = None
    if args.refresh_hz is not None:
        raw_frames = optional(adb, ['shell','dumpsys','gfxinfo',PACKAGE,'framestats'])
        if raw_frames is not None:
            try:
                frames = analyzer.frames(raw_frames, args.refresh_hz, args.stream)
            except (ValueError, TypeError, OverflowError):
                frame_error = 'UNKNOWN_INVALID_OR_TRUNCATED_FRAME_DATA'
    events = None
    export_error = None
    if args.exports:
        try:
            events = export_batches(adb, analyzer, args.exports, directory)
        except (OSError, ValueError, UnicodeError, TypeError, KeyError):
            export_error = 'UNKNOWN_EXPORT_UNAVAILABLE_OR_INVALID'
    profile = {}
    for field, command in [('android_api',['shell','getprop','ro.build.version.sdk']),
                           ('abi',['shell','getprop','ro.product.cpu.abi']),
                           ('page_bytes',['shell','getconf','PAGE_SIZE'])]:
        value = optional(adb, command)
        value = value.strip() if value else ''
        profile[field] = (int(value) if value.isdigit() and len(value) < 6 else None) if field != 'abi' else (value if value in ('arm64-v8a','x86_64','armeabi-v7a') else None)
    # Detect replacement/update during observation without re-reading a 100MB APK.
    require(adb.read(['shell','am','get-current-user']).strip() == user, 'ANDROID_USER_CHANGED_DURING_CAPTURE')
    require(adb.read(['shell','pm','path','--user','current',PACKAGE]).splitlines() == paths, 'PACKAGE_REPLACED_DURING_CAPTURE')
    parse_version(adb.read(['shell','dumpsys','package',PACKAGE]), args.version_code, args.version_name)
    require(digest(args.approved_apk) == local_hash, 'LOCAL_APK_CHANGED_DURING_CAPTURE')
    counts = logs.get('signal_counts') or {}
    return dict(schema=1, capture_environment='personal_device', package=PACKAGE,
                status='OBSERVED_ERROR_EVIDENCE' if history['confirmed_error_reasons'] or any(counts.values()) else 'OBSERVATIONS_ONLY_PENDING_MANUAL_REVIEW',
                installed_identity={'status':'PASS_BYTE_IDENTICAL_TO_APPROVED_SIGNED_APK',
                                    'apk_sha256':args.apk_sha256, 'certificate_sha256':args.certificate_sha256,
                                    'version_code':args.version_code, 'version_name':args.version_name,
                                    'source_commit_declared':args.commit},
                device_profile=profile, logcat=logs, exit_history=history,
                activity={'status':'RESUMED_RECORD_OBSERVED' if resumed else 'UNKNOWN',
                          'oncreate_completed':'UNKNOWN', 'ui_correct':'UNKNOWN',
                          'first_scene_observer':'PRESENTED_EVENT_OBSERVED' if events and events['interactions']['operations']['startup']['presented'] else 'UNKNOWN'},
                jni_initialized='UNKNOWN_REQUIRES_LOCAL_PYTHON_PROBE',
                python_initialized='UNKNOWN_REQUIRES_LOCAL_PYTHON_PROBE',
                lifecycle_correct='UNKNOWN_MANUAL_RECREATION_REQUIRED',
                framestats=frames, frame_error=frame_error, events=events, export_error=export_error,
                adb_reads_executed=True, app_launched_by_tool=False, android_compatibility_certified=False,
                limits='No raw logs/exception text/serial emitted. Live-PID log window is short; early/dead-process logs may be missed. OS exit history may be delayed. No absence-of-crash, FPS, JNI/Python success or physical touch latency inferred.')


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        print('{"status":"BLOCKED_INVALID_ARGUMENTS"}')
        raise SystemExit(2)


def error_code(error):
    # Only our fixed uppercase ValueError codes; never stderr, paths or exception text.
    return str(error) if type(error) is ValueError and re.fullmatch(r'[A-Z][A-Z0-9_]{1,80}',str(error)) else 'READ_OR_FORMAT_UNAVAILABLE'


def main(argv=None):
    parser = SafeParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    for name in ('authorization','approved-apk','apksigner','source-dir','output-dir','adb'):
        parser.add_argument('--'+name, type=Path)
    for name in ('serial','apk-sha256','certificate-sha256','version-code','version-name','commit'):
        parser.add_argument('--'+name)
    parser.add_argument('--observe-seconds', type=float, default=15)
    parser.add_argument('--refresh-hz', type=float)
    parser.add_argument('--stream', type=int)
    parser.add_argument('--exports', nargs='*', default=[])
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps(plan()))
        return 0
    try:
        require(all(getattr(args, n.replace('-','_')) is not None for n in
                    ('authorization','approved-apk','apksigner','source-dir','output-dir','adb','serial',
                     'apk-sha256','certificate-sha256','version-code','version-name','commit')), 'CAPTURE_INPUTS_REQUIRED')
        require(HEX.fullmatch(args.apk_sha256) and HEX.fullmatch(args.certificate_sha256) and
                re.fullmatch('[0-9a-f]{40}',args.commit), 'INVALID_IDENTITY')
        require(math.isfinite(args.observe_seconds) and 0 <= args.observe_seconds <= 60,
                'INVALID_OBSERVATION_WINDOW')
        require(args.refresh_hz is None or math.isfinite(args.refresh_hz) and 1 <= args.refresh_hz <= 360, 'INVALID_REFRESH_RATE')
        authorize(args)
        analyzer, _ = import_events.load_reviewed(args.source_dir)
        # Reuse an already-running local ADB server; no server/key provisioning.
        with socket.create_connection(('127.0.0.1',5037), timeout=2):
            pass
        require(not args.output_dir.is_symlink() and not any(p.is_symlink() for p in args.output_dir.parents), 'UNSAFE_OUTPUT_DIRECTORY')
        require(not args.output_dir.resolve().is_relative_to(ROOT), 'REPORT_MUST_BE_PRIVATE_OUTSIDE_REPO')
        args.output_dir.mkdir(mode=0o700)
        try:
            result = collect(args, Adb(args.adb,args.serial), analyzer, args.output_dir)
        except Exception as error:
            result = dict(status='BLOCKED_CAPTURE_INCOMPLETE',code=error_code(error),error_type=type(error).__name__,android_compatibility_certified=False)
        with os.fdopen(os.open(args.output_dir/'report.json',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'w') as file:
            json.dump(result,file,indent=2,allow_nan=False)
            file.write('\n')
        print(json.dumps({'status':result['status']}))
        return 1 if result['status'].startswith('BLOCKED') else 0
    except Exception as error:
        print(json.dumps({'status':'BLOCKED_INVALID_INPUT_OR_AUTHORIZATION','code':error_code(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
