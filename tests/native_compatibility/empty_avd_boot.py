"""Empty-AVD infrastructure launcher. Never installs, signs or starts an application.

Reuses run_lab.preflight/Adb for guest inspection. A new offline network namespace
must be created successfully before Emulator or ADB can be invoked.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
import zipfile

import lab_host_preflight as host

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'android_lab'))
from run_lab import Adb, preflight

AVDS = {'api24-4k': 'flexygram-api24-offline-v2',
        'arm64-16k': 'flexygram-api35-offline-v2'}
IMAGE_DIRS = {'api24-4k': 'system-images/android-24/default/arm64-v8a',
              'arm64-16k': 'system-images/android-35/google_apis_ps16k/arm64-v8a'}


def require(value, message):
    if not value:
        raise ValueError(message)


def network_identity():
    return os.readlink('/proc/self/ns/net')


def clean_environment(sdk, user_home, avd_home):
    # Do not inherit proxies, ADB endpoints, preloads or emulator command overrides.
    allowed = ('PATH', 'LANG', 'LC_ALL', 'TZ', 'SYSTEMROOT')
    env = {k: os.environ[k] for k in allowed if k in os.environ}
    env.update(ANDROID_HOME=str(sdk), ANDROID_SDK_ROOT=str(sdk),
               ANDROID_USER_HOME=str(user_home), ANDROID_AVD_HOME=str(avd_home),
               ADB_SERVER_SOCKET='tcp:127.0.0.1:5037',
               ADB_MDNS_AUTO_CONNECT='0',
               LD_LIBRARY_PATH=str(sdk/'emulator/lib64'))
    return env


def isolation_check(parent, links, routes4, routes6):
    require(parent == os.readlink('/proc/'+str(os.getppid())+'/ns/net'), 'Parent namespace identity mismatch')
    require(network_identity() != parent, 'A newly created network namespace is required')
    require(len(links) == 1 and links[0].get('ifname') == 'lo', 'Only loopback is permitted')
    require('UP' in links[0].get('flags', []), 'Loopback must be up')
    for route in routes4 + routes6:
        require(route.get('dev') == 'lo' and 'gateway' not in route and
                route.get('dst') != 'default', 'External or ambiguous route rejected')


def ini(text):
    rows = {}
    for line in text.splitlines():
        if '=' in line:
            key, value = (part.strip() for part in line.split('=', 1))
            require(key not in rows, 'Duplicate AVD configuration key')
            rows[key] = value
    return rows


def check_fresh_avd(home, profile, sdk):
    name = AVDS[profile]
    directory = home/(name+'.avd')
    for path in (home, directory, directory/'config.ini', home/(name+'.ini')):
        require(path.exists() and not path.is_symlink() and
                not any(p.is_symlink() for p in path.parents), 'Regular fresh AVD required')
    require(not any(directory.glob('userdata-qemu*')) and
            not any((directory/p).exists() for p in ('snapshots', 'cache.img', 'hardware-qemu.ini')),
            'Previously booted AVD rejected; create a new lab profile')
    config = ini((directory/'config.ini').read_text())
    require(config.get('abi.type') == 'arm64-v8a', 'ARM64 AVD required')
    require(ini((home/(name+'.ini')).read_text()).get('path') == str(directory), 'AVD pointer escapes private home')
    image = Path(config.get('image.sysdir.1', ''))
    image = image if image.is_absolute() else sdk/image
    require(image.resolve() == (sdk/IMAGE_DIRS[profile]).resolve(), 'AVD image path mismatch')
    for key in ('disk.dataPartition.path', 'sdcard.path', 'disk.cachePartition.path'):
        require(config.get(key, '') in ('', '<temp>'), 'Explicit data/cache/SD paths require separate review')
    return name


def verify_materialized(sdk, archives, profile):
    destination = sdk/IMAGE_DIRS[profile]
    with zipfile.ZipFile(archives/host.IMAGES[profile]['filename']) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            relative = Path(*Path(member.filename).parts[1:])
            require(relative.parts and '..' not in relative.parts and not relative.is_absolute(), 'Unsafe image member')
            target = destination/relative
            require(target.is_file() and not target.is_symlink() and
                    not any(p.is_symlink() for p in target.parents), 'Materialized image missing or symlinked')
            def sha(stream):
                result = hashlib.sha256()
                for block in iter(lambda: stream.read(1024*1024), b''):result.update(block)
                return result.digest()
            with archive.open(member) as source, target.open('rb') as actual:
                require(sha(source) == sha(actual), 'Materialized image differs from pinned archive')


def check_guest(environment, profile, packages, accounts, bridge_exec):
    require(environment['api'] == (24 if profile == 'api24-4k' else 35), 'Exact laboratory API required')
    require(bridge_exec.lower() in ('', '0', 'false'), 'Native bridge execution must be disabled')
    require(not any(x in packages.lower() for x in
                    ('io.github.jose22yt.flexygram', 'org.telegram', 'com.exteraless.app',
                     'org.thunderdog.challegram')), 'Existing client or runner rejected')
    counts = re.findall(r'^\s*Accounts:\s*(\d+)\s*$', accounts, re.M)
    require(counts and all(int(x) == 0 for x in counts), 'Empty accounts not verifiable')


def inside(args):
    # This path is entered only as a child of unshare. No Android process yet.
    subprocess.run(['ip', 'link', 'set', 'lo', 'up'], check=True, capture_output=True)
    def ip(*parts):
        p = subprocess.run(['ip', '-j', *parts], check=True, capture_output=True, text=True)
        return json.loads(p.stdout)
    links = ip('link', 'show')
    routes4, routes6 = ip('route', 'show', 'table', 'all'), ip('-6', 'route', 'show', 'table', 'all')
    isolation_check(args.parent_netns, links, routes4, routes6)
    require(host.check_storage(args.sdk)['status'] == 'PASS', 'AVD storage below 10 GiB margin')
    name = check_fresh_avd(args.avd_home, args.profile, args.sdk)
    result = {'status': 'BLOCKED', 'profile': args.profile, 'android_boot_attempted': False,
              'application_installed': False, 'application_started': False,
              'runtime_application_validated': False, 'network_namespace': network_identity(),
              'links': links, 'routes4': routes4, 'routes6': routes6}
    emulator = None
    adb = Adb(args.sdk/'platform-tools/adb', 'emulator-5554')
    def interrupted(_signal, _frame):
        raise TimeoutError('Parent deadline or shutdown requested')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        with (args.output/'emulator.log').open('w') as log:
            emulator = subprocess.Popen([str(args.sdk/'emulator/emulator'), '-avd', name,
                '-port', '5554', '-no-window', '-no-audio', '-no-snapshot', '-no-boot-anim',
                '-camera-back', 'none', '-camera-front', 'none',
                '-gpu', 'swiftshader', '-accel', 'off'], stdout=log, stderr=log,
                start_new_session=True, close_fds=True)
            result['android_boot_attempted'] = True
            deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline:
                require(emulator.poll() is None, 'Emulator exited; inspect emulator.log for the exact TCG/frontend error')
                try:
                    if adb.shell('getprop', 'sys.boot_completed', timeout=5, check=False) == '1':
                        break
                except subprocess.TimeoutExpired:
                    pass
                time.sleep(1)
            else:
                raise ValueError('Android boot deadline exceeded')
            environment = preflight(adb, args.profile)  # existing ARM64/page/strict16K checks
            check_guest(environment, args.profile, adb.shell('pm', 'list', 'packages'),
                        adb.shell('dumpsys', 'account'), adb.prop('ro.enable.native.bridge.exec'))
            result.update(status='EMPTY_ANDROID_BOOT_VERIFIED_NO_APP_TEST', environment=environment,
                          image_sha256=host.IMAGES[args.profile]['sha256'])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result.update(error_type=type(error).__name__, reason=str(error))
    finally:
        if emulator is not None:
            try:
                adb.run('emu', 'kill', check=False, timeout=5)
            except (OSError, subprocess.SubprocessError):
                pass
            if emulator.poll() is None:
                os.killpg(emulator.pid, signal.SIGTERM)
            try:
                emulator.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(emulator.pid, signal.SIGKILL)
                emulator.wait(timeout=5)
            try:
                subprocess.run([str(args.sdk/'platform-tools/adb'), 'kill-server'],
                               timeout=10, capture_output=True, check=False)
            except (OSError, subprocess.SubprocessError):
                result['adb_cleanup_failed'] = True
                result['status'] = 'BLOCKED'
        (args.output/'empty-boot.json').write_text(json.dumps(result, indent=2)+'\n')
    return int(result['status'] != 'EMPTY_ANDROID_BOOT_VERIFIED_NO_APP_TEST')


def launch(args):
    require(300 <= args.timeout <= 1800, 'Boot timeout must be 300..1800 seconds')
    for name in ('sdk', 'archives', 'avd_home', 'user_home'):
        setattr(args, name, getattr(args, name).resolve())
    require(args.avd_home.is_dir() and args.user_home.is_dir(), 'Private Android homes required')
    require(not args.output.exists() and HERE.parents[1] not in args.output.resolve().parents and
            not any(p.is_symlink() for p in args.output.absolute().parents), 'New private output outside repository required')
    args.output = args.output.absolute()
    args.output.mkdir(mode=0o700)
    (args.output/'tmp').mkdir(mode=0o700)
    os.environ['ANDROID_AVD_HOME'] = str(args.avd_home)
    report = host.probe(args.sdk, args.archives)
    (args.output/'preflight.json').write_text(json.dumps(report, indent=2)+'\n')
    require(not report['blockers'], 'Host preflight BLOCKED; no Android boot or ADB device operation invoked')
    require(not any(Path('/dev/bus/usb').glob('*/*')), 'Use a lab VM without USB passthrough before starting ADB')
    check_fresh_avd(args.avd_home, args.profile, args.sdk)
    verify_materialized(args.sdk, args.archives, args.profile)
    child = ['unshare', '--user', '--map-root-user', '--net', sys.executable, str(Path(__file__).resolve()),
             '--inside', '--parent-netns', network_identity(), '--profile', args.profile,
             '--sdk', str(args.sdk), '--archives', str(args.archives), '--avd-home', str(args.avd_home),
             '--user-home', str(args.user_home), '--output', str(args.output), '--timeout', str(args.timeout)]
    with (args.output/'namespace.log').open('w') as log:
        env = clean_environment(args.sdk, args.user_home, args.avd_home)
        env['TMPDIR'] = str(args.output/'tmp')
        p = subprocess.Popen(child, env=env,
                             close_fds=True, stdout=log, stderr=log)
        try:
            p.wait(timeout=args.timeout+120)
        except subprocess.TimeoutExpired:
            p.terminate()  # child finally stops only its own Emulator/ADB
            try:
                p.wait(timeout=45)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=10)
            raise ValueError('Empty boot deadline exceeded; review cleanup logs before any retry')
    require(p.returncode == 0, 'Isolated empty boot failed; inspect namespace.log and empty-boot.json')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=AVDS, required=True)
    for name in ('sdk', 'archives', 'avd-home', 'user-home', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--inside', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--parent-netns', help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        return inside(args) if args.inside else launch(args)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'BLOCKED', 'reason': str(error), 'app_installed': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
