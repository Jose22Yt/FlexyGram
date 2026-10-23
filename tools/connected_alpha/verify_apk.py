#!/usr/bin/env python3
"""Fail closed on an actual APK. Requires Android build-tools and readelf-free ELF parsing."""
import argparse
import hashlib
import io
import json
import re
import struct
import subprocess
import sys
import zipfile
from pathlib import Path
from ci_inputs import fingerprint

APP = 'io.github.jose22yt.flexygram.alpha'
NATIVE_LIBRARY = 'lib/arm64-v8a/libtmessages.49.so'
ANDROID_ATTR = r'(?:android:|http://schemas\.android\.com/apk/res/android:)'

def require_telegram_payload(names):
    require('classes.dex' in names and NATIVE_LIBRARY in names, 'Missing Java or native Telegram code (libtmessages.49.so required)')

def require(condition, message):
    if not condition:
        raise ValueError(message)

def command(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)

def package_version_code(badging):
    lines = [line for line in badging.splitlines() if line.startswith('package: ')]
    require(len(lines) == 1, 'Expected exactly one packaged application')
    versions = re.findall(r"\bversionCode='([0-9]+)'", lines[0])
    require(len(versions) == 1 and int(versions[0]) > 0, 'Missing or invalid APK version code')
    return int(versions[0])

def parse_xmltree(xmltree):
    root = {'children': [], 'attrs': {}}
    stack = [(-1, root)]
    for line in xmltree.splitlines():
        indent = len(line) - len(line.lstrip())
        element = re.match(r'\s*E: ([\w-]+)\b', line)
        if element:
            while stack[-1][0] >= indent:
                stack.pop()
            node = {'tag': element[1], 'children': [], 'attrs': {}}
            stack[-1][1]['children'].append(node)
            stack.append((indent, node))
            continue
        attr = re.match(r'\s*A: (?:android:|http://schemas\.android\.com/apk/res/android:)([\w]+)(?:\([^)]*\))?=(.*)', line)
        if attr and len(stack) > 1:
            value = attr[2]
            quoted = re.search(r'"([^"]*)"', value)
            stack[-1][1]['attrs'][attr[1]] = quoted[1] if quoted else value.strip()
    return root

def application_nodes(xmltree):
    root = parse_xmltree(xmltree)
    for manifest in root['children']:
        if manifest['tag'] == 'manifest':
            yield from (child for child in manifest['children'] if child['tag'] == 'application')

def has_launcher_alias(xmltree):
    """Inspect the packaged manifest: AAPT2 badging omits launcher aliases."""

    def enabled(node):
        return node['attrs'].get('enabled', 'true') not in ('false', '(type 0x12)0x0', '0x0')

    for application in application_nodes(xmltree):
        if not enabled(application):
            continue
        activities = set()
        for component in application['children']:
            if component['tag'] == 'activity':
                activities.add(component['attrs'].get('name'))
            if component['tag'] != 'activity-alias' or not enabled(component):
                continue
            attrs = component['attrs']
            if attrs.get('targetActivity') not in activities or attrs.get('name') != 'org.telegram.messenger.ExteralessIcon':
                continue
            if attrs.get('exported') not in ('true', '(type 0x12)0xffffffff'):
                continue
            for intent in component['children']:
                if intent['tag'] != 'intent-filter':
                    continue
                actions = {child['attrs'].get('name') for child in intent['children'] if child['tag'] == 'action'}
                categories = {child['attrs'].get('name') for child in intent['children'] if child['tag'] == 'category'}
                if 'android.intent.action.MAIN' in actions and 'android.intent.category.LAUNCHER' in categories:
                    return True
    return False

def launcher_diagnostic(xmltree):
    """Only public component structure; never print arbitrary manifest metadata."""
    lines = xmltree.splitlines()
    structural = [line for line in lines if re.search(r'\bE: (manifest|application|activity-alias)\b', line)]
    named = [line for line in lines if any(value in line for value in (
        'ExteralessIcon', 'LaunchActivity', 'android.intent.action.MAIN',
        'android.intent.category.LAUNCHER'))]
    return {'lines': len(lines), 'structure': structural[:20], 'launcher_references': named[:24]}

def binary_boolean_is_false(xmltree, name):
    values = re.findall(r'^\s*A: ' + ANDROID_ATTR + re.escape(name) +
                        r'\([^)]*\)=(?:\(type 0x12\)0x([0-9a-fA-F]+)\b|(false|true)\b)',
                        xmltree, re.M)
    return len(values) == 1 and (values[0][1] == 'false' or
                                 bool(values[0][0]) and int(values[0][0], 16) == 0)

def provider_authorities(xmltree):
    return [provider['attrs']['authorities']
            for application in application_nodes(xmltree)
            for provider in application['children']
            if provider['tag'] == 'provider' and 'authorities' in provider['attrs']]

def security_attribute_diagnostic(xmltree):
    return [line for line in xmltree.splitlines()
            if re.search(r'^\s*A: ' + ANDROID_ATTR +
                         r'(?:allowBackup|restoreAnyVersion|authorities)\(', line)][:24]

def inspect_elf(data, name):
    require(len(data) >= 64, f'{name}: truncated ELF header')
    require(data[:6] == b'\x7fELF\x02\x01', f'{name}: expected ELF64 little endian')
    require(struct.unpack_from('<H', data, 18)[0] == 183, f'{name}: not AArch64')
    offset = struct.unpack_from('<Q', data, 32)[0]
    size, count = struct.unpack_from('<HH', data, 54)
    require(size >= 56 and offset+size*count <= len(data), f'{name}: truncated program headers')
    loads = 0
    for i in range(count):
        kind, flags, file_offset, address, _, file_size, memory_size, alignment = struct.unpack_from('<IIQQQQQQ', data, offset+i*size)
        if kind == 1:
            loads += 1
            require(alignment >= 16384 and (address-file_offset) % 16384 == 0, f'{name}: PT_LOAD incompatible with 16 KB pages')
            require(file_offset+file_size <= len(data), f'{name}: truncated PT_LOAD')
    require(loads > 0, f'{name}: missing PT_LOAD')
    return {'name': name, 'sha256': hashlib.sha256(data).hexdigest()}

def inspect_archive(z, prefix='', failures=None):
    found = []
    top_level = failures is None
    if failures is None:
        failures = []
    require(z.testzip() is None, f'{prefix}: invalid ZIP CRC')
    for entry in z.infolist():
        if entry.filename.endswith('.so'):
            try:
                found.append(inspect_elf(z.read(entry), prefix+entry.filename))
            except ValueError as exc:
                failures.append(str(exc))
        # Chaquopy bootstrap/runtime libraries can be inside nested ZIP assets.
        elif entry.filename.endswith(('.zip','.imy')) and 'chaquopy' in entry.filename:
            data = z.read(entry)
            if zipfile.is_zipfile(io.BytesIO(data)):
                with zipfile.ZipFile(io.BytesIO(data)) as nested:
                    found += inspect_archive(nested, prefix+entry.filename+'!/', failures)
    if top_level and failures:
        raise ValueError('Incompatible ELF payloads: ' + '; '.join(failures))
    return found

def main():
    p = argparse.ArgumentParser()
    p.add_argument('apk', type=Path)
    p.add_argument('--build-tools', type=Path, required=True)
    p.add_argument('--certificate-sha256', required=True, help='Expected authorized Alpha-only signing certificate fingerprint')
    p.add_argument('--expected-version-code', type=int, help='Required update version, when building a delivery profile')
    args = p.parse_args()
    expected = fingerprint(args.certificate_sha256)
    bt = args.build_tools
    signature = command(str(bt/'apksigner'), 'verify', '--verbose', '--print-certs', str(args.apk))
    require('Verified using v2 scheme (APK Signature Scheme v2): true' in signature, 'Missing APK Signature Scheme v2')
    certs = re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)', signature)
    require([c.lower() for c in certs] == [expected], 'Unexpected signing certificate or multiple signers')
    command(str(bt/'zipalign'), '-c', '-P', '16', '4', str(args.apk))
    badging = command(str(bt/'aapt2'), 'dump', 'badging', str(args.apk))
    require(f"package: name='{APP}'" in badging, 'Wrong application ID')
    version_code = package_version_code(badging)
    if args.expected_version_code is not None:
        require(version_code == args.expected_version_code, 'Unexpected update version code')
    require("application-label:'FlexyGram Alpha'" in badging, 'Wrong label')
    require("uses-permission: name='android.permission.INTERNET'" in badging, 'Missing INTERNET')
    require('application-debuggable' not in badging, 'Unexpected debuggable APK')
    require("native-code: 'arm64-v8a'" in badging and "'x86_64'" not in badging, 'Unexpected native ABI')
    manifest = command(str(bt/'aapt2'), 'dump', 'xmltree', str(args.apk), '--file', 'AndroidManifest.xml')
    if not has_launcher_alias(manifest):
        print('Launcher diagnostic (public component structure only): ' +
              json.dumps(launcher_diagnostic(manifest)), file=sys.stderr)
        raise ValueError('Missing enabled, exported launcher alias in packaged manifest')
    require('sharedUserId' not in manifest and 'backupAgent' not in manifest, 'Shared UID or backup agent present')
    if not (binary_boolean_is_false(manifest, 'allowBackup') and
            binary_boolean_is_false(manifest, 'restoreAnyVersion')):
        print('Packaged backup flags: ' + json.dumps(security_attribute_diagnostic(manifest)),
              file=sys.stderr)
        raise ValueError('Backup and restore must be disabled in merged manifest')
    authorities = provider_authorities(manifest)
    require(authorities and all(a.startswith(APP+'.') for a in authorities), 'Provider identity collision')
    with zipfile.ZipFile(args.apk) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), 'Duplicate ZIP entries')
        require_telegram_payload(names)
        require(not any(n.startswith('lib/') and not n.startswith('lib/arm64-v8a/') for n in names if not n.endswith('/')), 'Non-ARM64 JNI payload')
        elfs = inspect_archive(z)
        require(elfs, 'No ELF payloads inspected')
    print(json.dumps({'apk':args.apk.name,'bytes':args.apk.stat().st_size,
        'application_id':APP,'version_code':version_code,
        'sha256':hashlib.sha256(args.apk.read_bytes()).hexdigest(),
        'certificate_sha256':expected,'elf_count':len(elfs),'elfs':elfs,
        'status':'PASS_ARTIFACT_ONLY','android_runtime':'NOT_TESTED'}, indent=2))

if __name__ == '__main__':
    main()
