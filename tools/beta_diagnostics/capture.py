"""Plan by default. Explicit execution only in an already-authorized offline emulator.
No boot, input injection, launch, installation, reset, signing, root, or settings changes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from analyze import report, metadata, strict_json, read, require, PACKAGE, SafeParser, InputError

ROOT = Path(__file__).resolve().parents[2]
ATTESTATIONS = ('disposable_emulator', 'offline_isolation_verified', 'no_accounts',
                'no_personal_data', 'authorized_read_only_capture')


def serial_valid(serial):
    match = re.fullmatch(r'emulator-([0-9]{1,5})', serial)
    return bool(match and 1 <= int(match[1]) <= 65534)


def command_plan(adb, serial, package):
    require(serial_valid(serial) and PACKAGE.fullmatch(package), 'INVALID_CAPTURE_TARGET')
    prefix = [str(adb), '-s', serial]
    return [prefix + args for args in [
        ['get-state'], ['shell', 'getprop', 'ro.kernel.qemu'],
        ['shell', 'dumpsys', 'account'], ['shell', 'pidof', package],
        ['logcat', '-b', 'main', '-b', 'system', '-b', 'crash', '-d', '-v', 'epoch', '-t', '5000'],
        ['shell', 'dumpsys', 'gfxinfo', package, 'framestats'],
        ['shell', 'pm', 'path', package]]]


def run(command, runner, missing_ok=False):
    env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL') if key in os.environ}
    env.update(ADB_SERVER_SOCKET='tcp:127.0.0.1:5037', ADB_MDNS_AUTO_CONNECT='0')
    value = runner(command, capture_output=True, text=True, timeout=30, env=env)
    if missing_ok and value.returncode == 1 and not value.stdout.strip():
        return None
    require(value.returncode == 0 and len(value.stdout.encode()) <= 32 * 1024 * 1024, 'CAPTURE_COMMAND_FAILED_OR_TOO_LARGE')
    return value.stdout


def namespace_check(receipt, runner):
    require(receipt.get('network_namespace') == os.readlink('/proc/self/ns/net'), 'NAMESPACE_RECEIPT_MISMATCH')
    require(not any(Path('/dev/bus/usb').glob('*/*')), 'USB_EXPOSURE_REJECTED')
    links = strict_json(run(['ip', '-j', 'link', 'show'], runner))
    require(type(links) is list and len(links) == 1 and type(links[0]) is dict and links[0].get('ifname') == 'lo' and 'UP' in links[0].get('flags', []), 'OFFLINE_LOOPBACK_REQUIRED')
    for command in [['ip', '-j', 'route', 'show', 'table', 'all'], ['ip', '-j', '-6', 'route', 'show', 'table', 'all']]:
        routes = strict_json(run(command, runner))
        require(type(routes) is list and all(type(row) is dict and row.get('dev') == 'lo' and 'gateway' not in row and row.get('dst') != 'default' for row in routes), 'EXTERNAL_ROUTE_REJECTED')


def collect(adb, serial, package, meta, receipt, output, runner=subprocess.run):
    commands = command_plan(adb, serial, package)
    metadata(meta)
    require(meta['source'] == 'android_lab', 'LAB_SOURCE_REQUIRED')
    require(type(receipt) is dict and receipt.get('schema') == 1 and all(receipt.get(k) is True for k in ATTESTATIONS), 'CAPTURE_AUTHORIZATION_REQUIRED')
    require(receipt.get('serial') == serial and receipt.get('package') == package, 'CAPTURE_SCOPE_MISMATCH')
    digest = hashlib.sha256(json.dumps(meta, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    require(receipt.get('metadata_sha256') == digest, 'METADATA_RECEIPT_MISMATCH')
    known = receipt.get('known_pids', [])
    require(type(known) is list and all(type(x) is int and x > 0 for x in known), 'INVALID_KNOWN_PIDS')
    output = Path(output).absolute()
    require(not output.exists() and output != ROOT and ROOT not in output.resolve().parents
            and not any(p.is_symlink() for p in output.parents), 'NEW_PRIVATE_OUTPUT_OUTSIDE_REPOSITORY_REQUIRED')
    require(Path(adb).is_absolute() and Path(adb).is_file(), 'EXPLICIT_ADB_BINARY_REQUIRED')
    namespace_check(receipt, runner)  # No ADB invocation until this passes.
    require(run(commands[0], runner).strip() == 'device', 'EMULATOR_NOT_CONNECTED')
    require(run(commands[1], runner).strip() == '1', 'EMULATOR_REQUIRED')
    observed = {}
    for key, command in [('android_api', ['getprop', 'ro.build.version.sdk']),
                         ('page_bytes', ['getconf', 'PAGE_SIZE'])]:
        text = run([str(adb), '-s', serial, 'shell', *command], runner).strip()
        require(re.fullmatch(r'[0-9]+', text), 'INVALID_DEVICE_PROPERTIES')
        observed[key] = int(text)
        require(meta.get('conditions', {}).get(key) == observed[key], 'DEVICE_CONDITION_MISMATCH')
    observed['abi'] = run([str(adb), '-s', serial, 'shell', 'getprop', 'ro.product.cpu.abi'], runner).strip()
    require(observed['android_api'] >= 24 and observed['page_bytes'] in (4096, 16384)
            and observed['abi'] == 'arm64-v8a', 'UNSUPPORTED_LAB_PROFILE')
    paths = run(commands[6], runner).strip().splitlines()
    require(len(paths) == 1 and paths[0].startswith('package:'), 'SINGLE_APK_REQUIRED')
    apk_path = paths[0][len('package:'):]
    require(re.fullmatch(r'/data/app/[A-Za-z0-9_./=+~\-]+/base\.apk', apk_path)
            and '..' not in Path(apk_path).parts, 'INVALID_INSTALLED_APK_PATH')
    checksum = run([str(adb), '-s', serial, 'shell', 'sha256sum', apk_path], runner).strip().split()
    require(checksum == [meta['apk_sha256'], apk_path], 'INSTALLED_APK_DIGEST_MISMATCH')
    accounts = run(commands[2], runner)
    counts = re.findall(r'^\s*Accounts:\s*(\d+)\s*$', accounts, re.M)
    require(counts and all(int(x) == 0 for x in counts), 'EMPTY_ACCOUNTS_NOT_VERIFIED')
    del accounts
    pid_text = run(commands[3], runner, missing_ok=True)
    running = pid_text is not None
    if running:
        pid_text = pid_text.strip()
        require(re.fullmatch(r'[0-9]+(?:\s+[0-9]+)*', pid_text) and all(int(x) > 0 for x in pid_text.split()), 'INVALID_TARGET_PID_OUTPUT')
        pids = list(set(known + [int(x) for x in pid_text.split()]))
    else:
        pids = known
    log_text = run(commands[4], runner)
    frame_text = run(commands[5], runner) if running else None
    result = report(meta, package, pids, log_text, frame_text,
                    stream=receipt.get('frame_stream'), log_window=receipt.get('log_epoch_window'),
                    frame_window=receipt.get('frame_window_ns'))
    result['capture'] = {'read_only': True, 'target_running_at_snapshot': running,
                         'offline_namespace_checked': True, 'accountmanager_zero_observed': True,
                         'raw_logs_retained': False, 'apk_digest_verified_on_device': True,
                         'observed_device': observed,
                         'limits': 'Installed single APK digest checked; no signature/condition certification. AccountManager zero does not prove absence of app-private sessions. Snapshot may miss earlier crashed PIDs or truncated logs.'}
    output.mkdir(parents=True, mode=0o700)
    target = output / 'report.json'
    with open(target, 'x', encoding='utf-8', opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    return result


def main():
    parser = SafeParser(description=__doc__)
    parser.add_argument('--adb', type=Path, required=True)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--package', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--metadata', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if not args.execute:
            result = {'status': 'PLAN_ONLY', 'device_contacted': False,
                      'commands_after_namespace_validation': command_plan(args.adb, args.serial, args.package),
                      'additional_read_only_device_probes': [[str(args.adb), '-s', args.serial, 'shell', *tail] for tail in
                          [['getprop', 'ro.build.version.sdk'], ['getconf', 'PAGE_SIZE'], ['getprop', 'ro.product.cpu.abi']]]}
        else:
            require(args.metadata and args.receipt and args.output, 'CAPTURE_ARGUMENTS_REQUIRED')
            result = collect(args.adb, args.serial, args.package, strict_json(read(args.metadata)), strict_json(read(args.receipt)), args.output)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'CAPTURE_BLOCKED', 'code': error.args[0] if isinstance(error, InputError) else 'CAPTURE_IO_FORMAT_OR_TIMEOUT', 'raw_error_suppressed': True}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
