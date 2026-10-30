#!/usr/bin/env python3
"""Verify an actual official Beta APK; never accepts Alpha/debug or an override certificate."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/connected_alpha'))
from verify_apk import (command, require, inspect_archive, require_telegram_payload,
                        package_version_code, has_launcher_alias, binary_boolean_is_false,
                        provider_authorities)

APP = 'com.flexygram.messenger'
OFFICIAL = '5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c'
LABEL = 'FlexyGram Beta'
EXPECTED_ELFS = 96  # The inherited native payload; review explicitly when dependencies change.


def expected_version():
    properties = dict(re.findall(r'^(\w+)=(.*)$', (ROOT/'gradle.properties').read_text(), re.M))
    require(properties.get('APP_PACKAGE') == APP, 'Wrong source Beta package')
    require(properties.get('BETA_VERSION_NAME') == '1.0.0-beta.1', 'Unexpected source Beta version')
    code = int(properties['BETA_VERSION_CODE'])
    require(code >= 1290, 'Beta version must not roll back')
    return code, properties['BETA_VERSION_NAME']


def verify(apk, build_tools):
    # Trust only the registered public certificate; no private key is opened here.
    identity = dict(re.findall(r'^(\w+)=(.*)$', (ROOT/'config/signing/identity.properties').read_text(), re.M))
    require(identity.get('applicationId') == APP and identity.get('alias') == 'flexygram-release'
            and identity.get('storeType') == 'PKCS12', 'Wrong registered Beta identity')
    require(identity.get('certificateSha256') == OFFICIAL, 'Wrong official source pin')
    require(hashlib.sha256((ROOT/identity['certificateFile']).read_bytes()).hexdigest() == OFFICIAL,
            'Official public certificate changed')
    code, name = expected_version()
    signature = command(str(build_tools/'apksigner'), 'verify', '--verbose', '--print-certs', str(apk))
    for scheme in (2, 3):
        require(f'Verified using v{scheme} scheme (APK Signature Scheme v{scheme}): true' in signature,
                f'Missing APK Signature Scheme v{scheme}')
    certificates = re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)', signature)
    require([c.lower() for c in certificates] == [OFFICIAL], 'Not the single official Beta signer')
    command(str(build_tools/'zipalign'), '-c', '-P', '16', '4', str(apk))
    badging = command(str(build_tools/'aapt2'), 'dump', 'badging', str(apk))
    packages = re.findall(r"^package: name='([^']+)'", badging, re.M)
    require(packages == [APP], 'Wrong APK package')
    require(package_version_code(badging) == code, 'Wrong Beta versionCode')
    versions = re.findall(r"^package: .*\bversionName='([^']+)'", badging, re.M)
    require(versions == [name], 'Wrong Beta versionName')
    labels = re.findall(r"^application-label(?:-[^:]+)?:'([^']*)'", badging, re.M)
    require(labels and all(label == LABEL for label in labels), 'Wrong Beta application label')
    require("uses-permission: name='android.permission.INTERNET'" in badging, 'Missing INTERNET')
    require('application-debuggable' not in badging, 'Debuggable Beta APK')
    abi = re.findall(r'^native-code: (.+)$', badging, re.M)
    require(len(abi) == 1 and re.findall(r"'([^']+)'", abi[0]) == ['arm64-v8a'], 'Wrong native ABI')
    manifest = command(str(build_tools/'aapt2'), 'dump', 'xmltree', str(apk), '--file', 'AndroidManifest.xml')
    require(has_launcher_alias(manifest), 'Invalid packaged launcher alias')
    require('sharedUserId' not in manifest and 'backupAgent' not in manifest, 'Shared UID/backup agent present')
    require(binary_boolean_is_false(manifest, 'allowBackup')
            and binary_boolean_is_false(manifest, 'restoreAnyVersion'), 'Backup/restore must be disabled')
    authorities = provider_authorities(manifest)
    require(authorities and all(a.startswith(APP+'.') for a in authorities), 'Provider identity collision')
    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'Duplicate APK ZIP entries')
        require_telegram_payload(names)
        require(not any(n.startswith('lib/') and not n.startswith('lib/arm64-v8a/')
                        for n in names if not n.endswith('/')), 'Non-ARM64 native payload')
        elfs = inspect_archive(archive)
        require(len(elfs) == EXPECTED_ELFS, 'Incomplete or unexpected native payload count')
    return {'status':'PASS_OFFICIAL_BETA_ARTIFACT_ONLY','application_id':APP,
            'version_code':code,'version_name':name,'certificate_sha256':OFFICIAL,
            'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'bytes':apk.stat().st_size,
            'elf_count':len(elfs),'elfs':elfs,'android_runtime':'NOT_TESTED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('--build-tools', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(args.apk, args.build_tools)
    except (ValueError, OSError, zipfile.BadZipFile, subprocess.SubprocessError):
        raise SystemExit('FAIL: official Beta APK verification; no valid delivery established')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
