#!/usr/bin/env python3
"""Read-only telemetry around operator-driven TEST workloads. No private UI automation.

Cold-start explicitly force-stops only the selected test package, preserving data.
All other scenarios leave launch/navigation/input entirely to the operator.
No settings writes, account inspection, screenshots, logcat, installation or network.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from .metrics import gfxinfo
from .scenarios import SCENARIOS


def parse_health(thermal, battery, max_thermal, min_battery, max_temp):
    def one(pattern, text):
        found = re.search(pattern, text, re.M)
        return int(found.group(1)) if found else None
    status = one(r'^\s*Thermal Status:\s*(\d+)', thermal)
    level = one(r'^\s*level:\s*(\d+)', battery)
    temperature = one(r'^\s*temperature:\s*(\d+)', battery)
    plugged = any(re.search(r'^\s*' + source + r' powered:\s*true', battery, re.M) for source in ('AC', 'USB', 'Wireless'))
    known = status is not None and level is not None and temperature is not None
    return {'thermal_status': status, 'battery_percent': level,
            'battery_temperature_c': temperature / 10 if temperature is not None else None,
            'plugged': plugged, 'eligible': bool(known and status <= max_thermal and level >= min_battery and temperature <= max_temp * 10)}


def memory(text):
    def find(name):
        match = re.search(r'^\s*' + re.escape(name) + r':\s*(\d+)', text, re.M)
        return int(match.group(1)) if match else None
    return {'total_pss_kib': find('TOTAL PSS'), 'total_rss_kib': find('TOTAL RSS'),
            'java_heap_pss_kib': find('Java Heap'), 'native_heap_pss_kib': find('Native Heap'),
            'gc_count': None, 'allocations': None, 'gpu': None}


def startup(text):
    if re.search(r'(^Error:|Warning: Activity not started|Error type)', text, re.M):
        raise ValueError('Activity launch failed/reused; no cold-start result inferred')
    matches = re.findall(r'^TotalTime:\s*(\d+)\s*$', text, re.M)
    if len(matches) != 1:
        raise ValueError('Unique Android am TotalTime unavailable')
    return int(matches[0])


class Device:
    def __init__(self, serial):
        self.serial = serial
    def shell(self, *args):
        return subprocess.check_output(['adb', '-s', self.serial, 'shell', *args], text=True,
                                       stderr=subprocess.DEVNULL, timeout=45)


def collect_environment(device, args):
    result = {key: device.shell('settings', 'get', 'global', key).strip() for key in
              ('window_animation_scale', 'transition_animation_scale', 'animator_duration_scale')}
    result.update(font_scale=device.shell('settings', 'get', 'system', 'font_scale').strip(),
                  density=device.shell('wm', 'density').strip(), display_size=device.shell('wm', 'size').strip(),
                  build=device.shell('getprop', 'ro.build.fingerprint').strip(),
                  device_pair_id=hashlib.sha256(args.serial.encode()).hexdigest())
    for key in ('theme', 'cache_state', 'conversation_fixture', 'workload_id', 'music_state',
                'refresh_profile', 'installation_state', 'test_session_state'):
        result[key] = getattr(args, key)
    result['build_mode'] = getattr(args, 'build_mode', 'unverified')
    result['network_profile'] = getattr(args, 'network_profile', 'unverified')
    result['sync_state'] = getattr(args, 'sync_state', 'unverified')
    result['thermal_policy'] = f'status<={args.max_thermal};temperature<={args.max_temperature_c}'
    result['battery_policy'] = f'level>={args.min_battery};charging={args.charging}'
    return result


def run(args, device, prompt=input):
    if args.scenario == 'cold_start' and not getattr(args, 'allow_test_force_stop', False):
        raise ValueError('Cold start requires explicit TEST-package force-stop authorization')
    environment = collect_environment(device, args)
    report = {'schema': 1, 'evidence': 'test_device', 'label': args.label,
              'prepared_test_device': True, 'source_commit': args.source_commit,
              'scenario': args.scenario, 'package': args.package, 'environment': environment,
              'operator_attested': ['test_account_only', 'same_test_fixture', 'cache_state', 'theme', 'refresh_profile', 'installation_state'],
              'captures': [], 'superiority': 'NOT_ESTABLISHED'}
    def health():
        value = parse_health(device.shell('dumpsys', 'thermalservice'), device.shell('dumpsys', 'battery'),
                             args.max_thermal, args.min_battery, args.max_temperature_c)
        wanted = args.charging == 'plugged'
        value['eligible'] &= value['plugged'] == wanted
        return value
    for i in range(args.iterations):
        prompt(f'{args.scenario}: prepare TEST workload {i+1}/{args.iterations}; Enter when ready: ')
        before = health()
        if not before['eligible']:
            raise ValueError('Device health outside declared conditions or unavailable; capture stopped')
        memory_before = memory(device.shell('dumpsys', 'meminfo', args.package))
        # Existing tools use the same reset. It clears only frame statistics, never app/session data.
        device.shell('dumpsys', 'gfxinfo', args.package, 'reset')
        start_ms = None
        if args.scenario == 'cold_start':
            device.shell('am', 'force-stop', args.package)
            start_ms = startup(device.shell('am', 'start', '-W', '-n', args.component))
        prompt('Perform/finish the declared TEST interaction, then Enter: ')
        frame_report = gfxinfo(device.shell('dumpsys', 'gfxinfo', args.package, 'framestats'), args.verified_hz)
        if not frame_report['duration_ms']['count'] and start_ms is None:
            raise ValueError('Empty frame telemetry; no result inferred')
        after = health()
        if not after['eligible']:
            raise ValueError('Device heated/changed battery condition; capture stopped without qualifying comparison')
        # Exclude meminfo cost from the frame window by collecting it only after framestats.
        report['captures'].append({'frames': frame_report, 'startup_ms': start_ms,
                                   'health': after, 'health_before': before,
                                   'memory_before': memory_before,
                                   'memory_after': memory(device.shell('dumpsys', 'meminfo', args.package))})
        # Preserve a numerical checkpoint after each successful repetition; no raw dumps/serial/private UI.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial', required=True)
    p.add_argument('--package', required=True)
    p.add_argument('--component')
    p.add_argument('--source-commit', required=True)
    p.add_argument('--label', required=True, choices=['exteraless', 'alpha1271', 'alpha1272', 'pr92', 'alpha1275', 'alpha1276', 'candidate'])
    p.add_argument('--scenario', required=True, choices=SCENARIOS)
    p.add_argument('--build-mode', required=True, help='Same release/profileable/debug mode for all compared builds')
    p.add_argument('--iterations', type=int, default=20)
    p.add_argument('--verified-hz', type=float, help='Explicit operator-verified fallback only; FrameInterval wins')
    p.add_argument('--confirm-test-device', action='store_true', required=True)
    p.add_argument('--allow-test-force-stop', action='store_true')
    for key in ('theme', 'cache-state', 'conversation-fixture', 'workload-id', 'music-state',
                'refresh-profile', 'installation-state', 'test-session-state'):
        p.add_argument('--' + key, required=True)
    p.add_argument('--network-profile', default='unverified', help='Operator-declared equivalent network conditions; no network changes are automated')
    p.add_argument('--sync-state', default='unverified', help='Operator-declared equivalent initial synchronization state')
    p.add_argument('--max-thermal', type=int, default=1)
    p.add_argument('--min-battery', type=int, default=30)
    p.add_argument('--max-temperature-c', type=float, default=38)
    p.add_argument('--charging', choices=['plugged', 'unplugged'], required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+', a.package):
        p.error('Invalid package')
    if not re.fullmatch('[0-9a-f]{40}', a.source_commit) or not 5 <= a.iterations <= 100:
        p.error('Full source commit and5–100 repetitions required; acceptance requires20')
    if a.verified_hz is not None and (not math.isfinite(a.verified_hz) or not 1 <= a.verified_hz <= 1000):
        p.error('Invalid refresh fallback')
    if not math.isfinite(a.max_temperature_c) or not 0 <= a.max_temperature_c <= 60 or not 0 <= a.max_thermal <= 6 or not 1 <= a.min_battery <= 100:
        p.error('Invalid device health limits')
    if a.scenario == 'cold_start':
        if not a.allow_test_force_stop or not a.component or not a.component.startswith(a.package + '/') or not re.fullmatch(r'[A-Za-z0-9_./]+', a.component):
            p.error('Cold start needs explicit TEST force-stop permission and a component in that package')
    run(a, Device(a.serial))

if __name__ == '__main__':
    main()
