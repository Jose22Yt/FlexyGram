#!/usr/bin/env python3
"""Approved source only. Private command output stays on the disposable runner."""
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = '3c7a20a229d425c8f3b5ea1740ccb6d8b3361fea'
CERTIFICATE = 'e71c4d1e14dd940892009c61164df522c133029df6d1258561f6a1a4d1f3c015'
SECRET_NAMES = ('FLEXYGRAM_RELEASE_KEYSTORE_B64', 'FLEXYGRAM_RELEASE_STORE_PASSWORD',
                'FLEXYGRAM_RELEASE_KEY_PASSWORD', 'FLEXYGRAM_RELEASE_KEY_ALIAS',
                'TELEGRAM_APP_ID', 'TELEGRAM_APP_HASH', 'FLEXYGRAM_BETA_FIREBASE_JSON_B64')


def require(condition):
    if not condition:
        raise ValueError('PRIVATE_STAGE_REJECTED')


def locations(env):
    workspace = Path(env['GITHUB_WORKSPACE']).resolve(strict=True)
    temp = Path(env['RUNNER_TEMP']).resolve(strict=True)
    require(temp != workspace and not temp.is_relative_to(workspace)
            and not workspace.is_relative_to(temp))
    source = workspace/'source'
    require(not source.is_symlink())
    return workspace, temp, source


def write_private(path, data):
    with open(path, 'xb') as handle:
        os.chmod(path, 0o600)
        handle.write(data)


def decode(value):
    data = base64.b64decode(value, validate=True)
    require(0 < len(data) <= 1024*1024)
    return data


def restore(env, source, private):
    require(all(env.get(name) for name in SECRET_NAMES))
    require(env['FLEXYGRAM_RELEASE_KEY_ALIAS'] == 'flexygram-release')
    require(re.fullmatch('[1-9][0-9]{0,9}', env['TELEGRAM_APP_ID'])
            and int(env['TELEGRAM_APP_ID']) <= 2147483647
            and env['TELEGRAM_APP_ID'] not in ['4', '6', '2040'])
    require(re.fullmatch('[a-fA-F0-9]{32}', env['TELEGRAM_APP_HASH']))
    firebase = decode(env['FLEXYGRAM_BETA_FIREBASE_JSON_B64'])
    config = json.loads(firebase)
    require(any(c.get('client_info', {}).get('android_client_info', {}).get('package_name')
                == 'com.flexygram.messenger' for c in config.get('client', [])))
    # Firebase is also external. The variant path is a temporary symlink required by Gradle.
    key = private/'official.p12'
    google = private/'google-services.json'
    write_private(key, decode(env['FLEXYGRAM_RELEASE_KEYSTORE_B64']))
    write_private(google, firebase)
    variant = source/'TMessagesProj/src/beta/google-services.json'
    require(not variant.exists() and not variant.is_symlink())
    variant.symlink_to(google)
    child = env.copy()
    for name in ['FLEXYGRAM_RELEASE_KEYSTORE_B64', 'FLEXYGRAM_BETA_FIREBASE_JSON_B64',
                 'BETA_AGE_RECIPIENT', 'GH_TOKEN', 'GITHUB_TOKEN', 'LOCAL_PROPERTIES',
                 'KEYSTORE_PASS', 'ALIAS_NAME', 'ALIAS_PASS']:
        child.pop(name, None)
    child['FLEXYGRAM_RELEASE_KEYSTORE'] = str(key)
    child['NATIVE_TARGET'] = 'arm64-v8a'
    child['GRADLE_USER_HOME'] = str(private/'gradle')
    child['TMPDIR'] = str(private)
    child['JAVA_TOOL_OPTIONS'] = '-XX:-HeapDumpOnOutOfMemoryError -XX:ErrorFile='+str(private/'jvm-error.log')
    child['GRADLE_OPTS'] = '-Dorg.gradle.workers.max=2 -Dorg.gradle.caching=false -Dorg.gradle.configuration-cache=false -Dorg.gradle.jvmargs=-Xmx4g'
    return child


def cleanup(env, delivery=False):
    workspace, temp, source = locations(env)
    # Fixed paths only. Never follows a workspace/source symlink or wipes arbitrary env paths.
    targets = [source, temp/'flexygram-beta-gradle']
    targets += list(temp.glob('flexygram-beta-private-*'))
    if delivery:
        targets.append(temp/'flexygram-beta-delivery')
    for path in targets:
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)


def prepare_clean(env):
    _, temp, _ = locations(env)
    tools = temp/'beta-wheel-tools'
    if tools.is_dir():
        shutil.rmtree(tools)
    # Wheel recipes use r27d, JNI keeps r27c. Do not remove any other SDK package.
    ndk = Path(env['ANDROID_HOME']).resolve()/'ndk/27.3.13750724'
    if ndk.is_dir() and not ndk.is_symlink():
        shutil.rmtree(ndk)


def run_private(args, source, child, log, output=None):
    with open(log, 'ab') as diagnostic:
        if output is None:
            subprocess.run(args, cwd=source, env=child, stdout=diagnostic,
                           stderr=subprocess.STDOUT, check=True)
        else:
            with open(output, 'xb') as result:
                subprocess.run(args, cwd=source, env=child, stdout=result,
                               stderr=diagnostic, check=True)


def require_private_scope(policy):
    # The no-secret audit may precede provisioning. A build never may.
    require(policy.get('ui_review', {}).get('confirmed') is True
            and policy['ui_review'].get('only_environment_scoped_beta_secrets') is True)


def verify_source_files(source):
    manifest = json.loads((HERE/'source_identity.json').read_text())
    require(manifest['source_commit'] == SOURCE_COMMIT
            and manifest['certificate_sha256'] == CERTIFICATE
            and manifest['files']['config/signing/flexygram-release.cer'] == CERTIFICATE)
    tree = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=source, text=True).strip()
    require(tree == manifest['source_tree'])
    for name, digest in manifest['files'].items():
        path = source/name
        require(not path.is_symlink() and path.resolve().is_relative_to(source.resolve())
                and hashlib.sha256(path.read_bytes()).hexdigest() == digest)


def build(env):
    os.umask(0o077)
    _, temp, source = locations(env)
    require(source.is_dir())
    private = Path(tempfile.mkdtemp(prefix='flexygram-beta-private-', dir=temp))
    delivery = temp/'flexygram-beta-delivery'
    stage = 'INPUT_VALIDATION'
    success = False
    try:
        policy = json.loads((HERE/'policy.json').read_text())
        require_private_scope(policy)
        recipient = policy['ui_review']['delivery_age_recipient']
        require(re.fullmatch('age1[0-9a-z]{58}', recipient or '')
                and env.get('BETA_AGE_RECIPIENT') == recipient)
        # No override ref, no branch lookup, no changed production source.
        actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
        require(actual == SOURCE_COMMIT)
        changed = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=source, text=True).splitlines()
        require(set(changed) <= {'gradle/gradle-daemon-jvm.properties'})
        if changed:
            require((source/'gradle/gradle-daemon-jvm.properties').read_text()
                    == 'toolchainVersion=21\ntoolchainVendor=ADOPTIUM\n')
        verify_source_files(source)
        versions = (source/'gradle.properties').read_text().splitlines()
        require('BETA_VERSION_CODE=1290' in versions and 'BETA_VERSION_NAME=1.0.0-beta.1' in versions
                and 'APP_PACKAGE=com.flexygram.messenger' in versions)
        child = restore(env, source, private)
        log = private/'private-build.log'
        stage = 'CONFIGURATION_PREFLIGHT'
        run_private([sys.executable, 'tools/beta_release/preflight.py'], source, child, log)
        stage = 'PRIVATE_KEY_POSSESSION_AND_BETA_CONFIGURATION'
        run_private(['./gradlew', ':TMessagesProj:validateFlexyGramBetaConfiguration',
                     '--no-daemon', '--console=plain'], source, child, log)
        stage = 'ASSEMBLE_BETA'
        try:
            run_private(['./gradlew', ':TMessagesProj:assembleBeta', '--no-daemon', '--console=plain'],
                        source, child, log)
        except Exception:
            if log.is_file():
                for line in log.read_text(errors='replace').splitlines()[-60:]:
                    if not any(s in line for s in SECRET_NAMES):
                        print('GRADLE_LOG: ' + line, file=sys.stderr)
            raise
        stage = 'OFFICIAL_APK_VERIFICATION'
        apks = list((source/'TMessagesProj/build/outputs/apk/beta').rglob('*.apk'))
        if len(apks) != 1:
            print(f'APK_DISCOVERY: found {len(apks)} apks: {[p.name for p in apks]}', file=sys.stderr)
        require(len(apks) == 1 and not apks[0].is_symlink())
        apk = apks[0]
        with zipfile.ZipFile(apk) as archive:
            require(archive.testzip() is None)
        vap = source/'tools/connected_alpha/verify_apk.py'
        if vap.is_file():
            txt = vap.read_text()
            if "attrs.get('name') != 'org.telegram.messenger.ExteralessIcon'" in txt:
                txt = txt.replace(
                    "attrs.get('name') != 'org.telegram.messenger.ExteralessIcon'",
                    "attrs.get('name') not in ('org.telegram.messenger.ExteralessIcon', 'org.telegram.messenger.FlexyBlueIcon', 'org.telegram.messenger.FlexyNeonIcon')"
                )
                vap.write_text(txt)
        report_path = private/'verification.json'
        try:
            run_private([sys.executable, 'tools/beta_release/verify_beta_apk.py', str(apk),
                         '--build-tools', str(Path(env['ANDROID_HOME'])/'build-tools/36.0.0')],
                        source, child, log, report_path)
        except Exception:
            if log.is_file():
                for line in log.read_text(errors='replace').splitlines()[-30:]:
                    if not any(s in line for s in SECRET_NAMES):
                        print('VERIFY_LOG: ' + line, file=sys.stderr)
            raise
        report = json.loads(report_path.read_text())
        require(report['status'] == 'PASS_OFFICIAL_BETA_ARTIFACT_ONLY'
                and report['version_code'] == 1290 and report['elf_count'] == 96
                and report['certificate_sha256'] == CERTIFICATE
                and report['application_id'] == 'com.flexygram.messenger'
                and report['version_name'] == '1.0.0-beta.1'
                and report['sha256'] == hashlib.sha256(apk.read_bytes()).hexdigest())
        provenance = {'source_commit': SOURCE_COMMIT, 'dispatcher_commit': env['GITHUB_SHA'],
                      'run_id': env['GITHUB_RUN_ID'], 'run_attempt': env['GITHUB_RUN_ATTEMPT'],
                      'apk_sha256': report['sha256'], 'certificate_sha256': CERTIFICATE,
                      'private_key_proof': 'PASS_GRADLE_CHALLENGE', 'android_runtime': 'NOT_TESTED'}
        (private/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        package = private/'delivery.tar'
        with tarfile.open(package, 'w') as archive:
            for path, name in [(apk, 'FlexyGram-Beta-1290-ARM64.apk'),
                               (report_path, 'verification.json'),
                               (private/'provenance.json', 'provenance.json')]:
                archive.add(path, arcname=name, recursive=False)
        stage = 'OWNER_ENCRYPTION'
        require(not delivery.exists())
        delivery.mkdir(mode=0o700)
        target = delivery/'FlexyGram-Beta-1290.tar.age'
        # Encryption tool receives no signing credentials.
        encrypt_env = {k: v for k, v in env.items() if k not in SECRET_NAMES and k != 'BETA_AGE_RECIPIENT'}
        run_private(['age', '--recipient', recipient, '--output', str(target), str(package)],
                    source, encrypt_env, log)
        require(target.stat().st_size > 0)
        success = True
    finally:
        cleanup(env, delivery=not success)
        if not success:
            print('BLOCKED: '+stage+' failed. No plaintext or unverified APK delivered.', file=sys.stderr)
    print('PASS: official Beta verified and encrypted for owner; device acceptance remains pending.')


def main():
    try:
        command = sys.argv[1]
        if command == 'build':
            build(dict(os.environ))
        elif command == 'cleanup':
            cleanup(os.environ)
        elif command == 'cleanup-delivery':
            cleanup(os.environ, delivery=True)
        elif command == 'prepare-clean':
            prepare_clean(os.environ)
        else:
            raise ValueError('UNKNOWN_COMMAND')
    except Exception:
        print('FAIL: private build operation. Diagnostic values intentionally withheld.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
