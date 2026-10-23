#!/usr/bin/env python3
"""Build only the offline helper; never rebuild, sign or change FlexyGram itself."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'build'
PACKAGE = 'io.github.jose22yt.flexygram.delivery'

def run(*args, env=None, capture=False):
    return subprocess.run([str(a) for a in args], cwd=ROOT, env=env, check=True,
                          text=True, stdout=subprocess.PIPE if capture else None).stdout

def elf_check(path, machine):
    data = path.read_bytes()
    assert data[:6] == b'\x7fELF\x02\x01'
    assert struct.unpack_from('<H', data, 18)[0] == machine
    offset = struct.unpack_from('<Q', data, 32)[0]
    size, count = struct.unpack_from('<HH', data, 54)
    loads = 0
    for i in range(count):
        kind, _, file_offset, address, _, file_size, _, align = struct.unpack_from('<IIQQQQQQ', data, offset+i*size)
        if kind == 1:
            loads += 1
            assert align >= 16384 and (address-file_offset) % 16384 == 0
            assert file_offset + file_size <= len(data)
    assert loads

def main():
    sdk = Path(os.environ['ANDROID_HOME'])
    bt = sdk / 'build-tools/36.0.0'
    jars = list((sdk / 'platforms/android-37.0').rglob('android.jar'))
    assert len(jars) == 1, jars
    jar = jars[0]
    ndk = sdk / 'ndk/27.2.12479018'
    llvm = ndk / 'toolchains/llvm/prebuilt/linux-x86_64/bin'
    java = Path(os.environ['JAVA_HOME'])
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / 'lib').mkdir(parents=True)
    (OUT / 'classes').mkdir()
    (OUT / 'dex').mkdir()
    # x86_64 is only for testing this independent helper in an emulator. It is
    # never used as evidence of FlexyGram ARM64 runtime or Poco compatibility.
    for abi, arch, compiler, machine in [('arm64-v8a', 'arm64', 'aarch64-linux-android30-clang', 183),
                                         ('x86_64', 'amd64', 'x86_64-linux-android30-clang', 62)]:
        lib = OUT / 'lib' / abi
        lib.mkdir()
        env = os.environ.copy()
        env.update(GOOS='android', GOARCH=arch, CGO_ENABLED='1', CC=str(llvm / compiler),
                   CGO_LDFLAGS='-Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384')
        run('go', 'build', '-mod=readonly', '-trimpath', '-buildmode=c-shared',
            '-ldflags=-s -w -buildid=', '-o', lib / 'libdelivery.so', './cmd/native', env=env)
        run(llvm / compiler, '-shared', '-fPIC', '-O2',
            '-Wl,-z,max-page-size=16384', '-Wl,-z,common-page-size=16384',
            '-Wl,-soname,libdeliveryjni.so', '-Wl,--no-undefined',
            '-I'+str(java / 'include'), '-I'+str(java / 'include/linux'), '-I'+str(lib),
            ROOT / 'android/bridge.c', '-L'+str(lib), '-ldelivery', '-o', lib / 'libdeliveryjni.so')
        for so in lib.glob('*.so'): elf_check(so, machine)
    sources = sorted((ROOT / 'android/src').rglob('*.java'))
    run(java / 'bin/javac', '-encoding', 'UTF-8', '-source', '17', '-target', '17',
        '-classpath', jar, '-d', OUT / 'classes', *sources)
    run(java / 'bin/jar', '--create', '--file', OUT / 'classes.jar', '-C', OUT / 'classes', '.')
    run(bt / 'd8', '--lib', jar, '--min-api', '30', '--output', OUT / 'dex', OUT / 'classes.jar')
    unsigned = OUT / 'unsigned.apk'
    run(bt / 'aapt2', 'link', '-I', jar, '--manifest', ROOT / 'android/AndroidManifest.xml', '-o', unsigned)
    modules = json.loads(run('go', 'list', '-m', '-json', 'filippo.io/age', capture=True))
    # Preserve upstream license notices in the distributed binary.
    all_modules = run('go', 'list', '-m', '-f', '{{.Dir}}', 'all', capture=True).splitlines()
    with zipfile.ZipFile(unsigned, 'a', compression=zipfile.ZIP_DEFLATED) as z:
        z.write(OUT / 'dex/classes.dex', 'classes.dex')
        for so in (OUT / 'lib').rglob('*.so'): z.write(so, str(so.relative_to(OUT)))
        for i, directory in enumerate(all_modules):
            for license in ('LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING'):
                file = Path(directory) / license
                if file.is_file(): z.write(file, f'assets/licenses/module-{i}-{license}')
        z.write(ROOT.parent.parent / 'LICENSE', 'assets/licenses/FlexyGram-LICENSE')
        z.write(Path(run('go', 'env', 'GOROOT', capture=True).strip()) / 'LICENSE', 'assets/licenses/Go-LICENSE')
    aligned = OUT / 'aligned.apk'
    run(bt / 'zipalign', '-P', '16', '4', unsigned, aligned)
    # A throwaway, public-password build key for THIS HELPER ONLY. No Alpha
    # signing material or repository secret is read by this workflow.
    key = OUT / 'helper-only.keystore'
    run(java / 'bin/keytool', '-genkeypair', '-keystore', key, '-storepass', 'android',
        '-keypass', 'android', '-alias', 'helper', '-dname', 'CN=FlexyGram Offline Helper',
        '-keyalg', 'RSA', '-keysize', '3072', '-validity', '3650', '-noprompt')
    apk = OUT / 'FlexyGram-Instalador-local.apk'
    try:
        run(bt / 'apksigner', 'sign', '--ks', key, '--ks-key-alias', 'helper',
            '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--out', apk, aligned)
        # The smoke instrumentation is signed with the helper-only key and is
        # used exclusively in CI. It is NOT included in the delivery artifact.
        (OUT / 'testclasses').mkdir()
        (OUT / 'testdex').mkdir()
        run(java / 'bin/javac', '-encoding', 'UTF-8', '-source', '17', '-target', '17',
            '-classpath', str(jar)+os.pathsep+str(OUT / 'classes.jar'), '-d', OUT / 'testclasses',
            *sorted((ROOT / 'android/test').rglob('*.java')))
        run(java / 'bin/jar', '--create', '--file', OUT / 'testclasses.jar', '-C', OUT / 'testclasses', '.')
        run(bt / 'd8', '--lib', jar, '--lib', OUT / 'classes.jar', '--min-api', '30',
            '--output', OUT / 'testdex', OUT / 'testclasses.jar')
        test_apk = OUT / 'smoke-unsigned.apk'
        run(bt / 'aapt2', 'link', '-I', jar, '--manifest', ROOT / 'android/test/AndroidManifest.xml', '-o', test_apk)
        with zipfile.ZipFile(test_apk, 'a', compression=zipfile.ZIP_DEFLATED) as z:
            z.write(OUT / 'testdex/classes.dex', 'classes.dex')
        run(bt / 'apksigner', 'sign', '--ks', key, '--ks-key-alias', 'helper',
            '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--out', OUT / 'smoke.apk', test_apk)
    finally: key.unlink(missing_ok=True)
    signature = run(bt / 'apksigner', 'verify', '--verbose', '--print-certs', apk, capture=True)
    print(signature)
    # With minSdk 30, apksigner may select v3 rather than v2. Both are modern
    # whole-APK schemes. Verification itself must succeed, and v1 alone fails.
    assert any(f'Verified using {v} scheme (APK Signature Scheme {v}): true' in signature
               for v in ('v2', 'v3', 'v3.1'))
    run(bt / 'zipalign', '-c', '-P', '16', '4', apk)
    badging = run(bt / 'aapt2', 'dump', 'badging', apk, capture=True)
    assert f"package: name='{PACKAGE}'" in badging
    permissions = [line for line in badging.splitlines() if line.startswith('uses-permission:')]
    assert permissions == ["uses-permission: name='android.permission.REQUEST_INSTALL_PACKAGES'"]
    assert 'application-debuggable' not in badging
    report = {'helper_sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
              'helper_bytes': apk.stat().st_size, 'helper_package': PACKAGE,
              'source_commit': os.environ.get('GITHUB_SHA', 'local'), 'upstream_age': modules['Version'],
              'permissions': ['android.permission.REQUEST_INSTALL_PACKAGES'],
              'helper_native_16kb': True, 'physical_android_test': 'NOT_TESTED',
              'target_apk_sha256': '579f70e6e90f4445b2fedfe747ad433392bc8a7f9beebebf98752e4b284194fb',
              'target_source_commit': 'c4210911a048d4fde080c03c31aa98741336db2f'}
    (OUT / 'helper-verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__': main()
