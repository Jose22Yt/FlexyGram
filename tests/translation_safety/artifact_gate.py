"""Read-only candidate scanner for future APK checks. Never prints matched values.

Fingerprints detect retirement; they DO NOT remove, encrypt or authorize keys.
ZIP/IMY/JAR recursion and UTF-16LE are covered. Obfuscation/runtime assembly,
other secret formats and actual Android execution require separate verification.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

CLIENT = re.compile(rb'AIza[A-Za-z0-9_-]{35}')
CLIENT16 = re.compile(rb'A\x00I\x00z\x00a\x00(?:[A-Za-z0-9_-]\x00){35}')
HEX40 = re.compile(rb'(?<![a-fA-F0-9])[a-fA-F0-9]{40}(?![a-fA-F0-9])')
HEX40_16 = re.compile(rb'(?:[a-fA-F0-9]\x00){40}')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def scan(payload, registry, *, max_depth=5, max_entries=50000,
         max_expanded_bytes=512 * 1024 * 1024, require_apk=False):
    result = dict(complete=True, apk_shaped=False, entries=0, nested_archives=0,
                  client_key_candidates=0, known_key_occurrences=0,
                  foreign_package_occurrences=0, foreign_certificate_occurrences=0,
                  embedded_service_configurations=0, errors=[])
    known = set(registry.get('retired_key_sha256', []))
    certificates = set(registry.get('foreign_certificate_sha256', []))
    markers = registry.get('foreign_package_markers', [])
    expanded = 0

    def fail(code):
        result['complete'] = False
        if code not in result['errors']:
            result['errors'].append(code)

    def inspect(data, depth):
        nonlocal expanded
        for pattern in (CLIENT, CLIENT16):
            for match in pattern.finditer(data):
                token = match[0].replace(b'\x00', b'')
                result['client_key_candidates'] += 1
                result['known_key_occurrences'] += digest(token) in known
        for marker in markers:
            for encoding in ('utf-8', 'utf-16le'):
                result['foreign_package_occurrences'] += data.count(marker.encode(encoding))
        for pattern in (HEX40, HEX40_16):
            for match in pattern.finditer(data):
                candidate = match[0].replace(b'\x00', b'').lower()
                result['foreign_certificate_occurrences'] += digest(candidate) in certificates
        # Do not allow malformed/nested ZIP-looking data to disappear as a clean scan.
        archive = zipfile.is_zipfile(io.BytesIO(data))
        if data.startswith(b'PK\x03\x04') and not archive:
            fail('malformed_archive')
        if not archive:
            return
        if depth >= max_depth:
            fail('depth_limit')
            return
        if depth:
            result['nested_archives'] += 1
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                names = z.namelist()
                if depth == 0:
                    result['apk_shaped'] = ('AndroidManifest.xml' in names
                        and any(re.fullmatch(r'classes(?:\d+)?\.dex', n) for n in names))
                for entry in z.infolist():
                    if entry.is_dir():
                        continue
                    result['entries'] += 1
                    expanded += entry.file_size
                    if result['entries'] > max_entries or expanded > max_expanded_bytes:
                        fail('expansion_limit')
                        return
                    if Path(entry.filename).name == 'google-services.json':
                        result['embedded_service_configurations'] += 1
                    inspect(z.read(entry), depth + 1)  # CRC validated by zipfile.
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError):
            fail('unreadable_archive')

    inspect(payload, 0)
    if require_apk and not result['apk_shaped']:
        fail('apk_structure_missing')
    result['sha256'] = digest(payload)
    result['passed'] = result['complete'] and not any(result[k] for k in (
        'client_key_candidates', 'foreign_package_occurrences',
        'foreign_certificate_occurrences', 'embedded_service_configurations'))
    result['limits'] = 'Static candidates only; no proof of execution or universal absence of secrets.'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path)
    parser.add_argument('--registry', type=Path,
                        default=Path(__file__).with_name('retired_fingerprints.json'))
    parser.add_argument('--apk', action='store_true', help='Require APK-shaped root ZIP')
    args = parser.parse_args()
    output = scan(args.artifact.read_bytes(), json.loads(args.registry.read_text()),
                  require_apk=args.apk)
    print(json.dumps(output, indent=2))
    raise SystemExit(0 if output['passed'] else 1)
