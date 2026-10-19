"""Offline, fail-closed contract for FlexyGram's proposed Android lab evidence.

Validates self-reported data only. It cannot authenticate measurements, install
APKs, execute JNI/Python, inspect devices or certify 16 KB compatibility.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

PACKAGE = 'io.github.jose22yt.flexygram.diagnostic'
APK_SHA256 = '17c32ab39e3ac88213241a6bd643637469a4a4d47311a920b357a2e7b3128230'
CERT_SHA256 = '27ef63ae50546c0af28c0ac54ef66a0c00614934cda86c6bea42d9d2759e7b83'
LIBRARIES = {
    'libexslt.so': 'f8e9e0fc0fa7507f3391bacb5c08a16dc9fdab73ca23de48f8adb2dfcca7a194',
    'libfreetype.so': 'd086a897a1c1cfa517b9e46c28d762f817af41bde96b2eda3bf6e6b12220eb01',
    'libxml2.so': 'e282a655ebbe07443cd743bb9dd00a152bfed7edb091d862f0a4e74afc1eff04',
    'libxslt.so': '827d113f3045205b205b52d0e4fe2e59998bd3b471368314415a2c3e91571660',
}
CASE_NAMES = frozenset({
    'test_xml_unicode_and_entities_native', 'test_xml_malformed_is_rejected_native',
    'test_xml_zlib_and_lzma_features_native', 'test_xml_gzip_file_native',
    'test_xml_xz_file_native', 'test_xslt_native_transform', 'test_exslt_native_math',
    'test_freetype_native_font_load_and_render', 'test_pillow_png_rgba_roundtrip',
    'test_pillow_jpeg_roundtrip', 'test_pillow_font_unicode',
    'test_lxml_xpath_xslt_and_html',
})
PROFILES = {'api24': {'api': 24, 'page_size_bytes': 4096},
            '16k': {'minimum_api': 35, 'page_size_bytes': 16384}}
TOP_FIELDS = frozenset({'schema', 'apk_sha256', 'cert_sha256', 'profiles'})
RUN_FIELDS = frozenset({'api', 'abi', 'page_size_bytes', 'package', 'permission_internet',
                        'startup', 'jni', 'chaquopy', 'python', 'native_loader_errors',
                        'fatal_exceptions', 'anrs', 'network_attempts', 'libraries', 'cases'})
HEX64 = re.compile(r'^[0-9a-f]{64}$')
MAX_BYTES = 256 * 1024


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_json_key')
        result[key] = value
    return result


def load(path: Path) -> object:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError('unapproved_evidence_file')
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_unique_pairs,
                      parse_constant=lambda _x: (_ for _ in ()).throw(ValueError('nonfinite_json')))


def validate(evidence: object) -> dict:
    problems = []

    def require(condition: bool, code: str):
        if not condition:
            problems.append(code)

    if type(evidence) is not dict or set(evidence) != TOP_FIELDS:
        return {'status': 'BLOCKED', 'reasons': ['invalid_schema_or_fields'],
                'profiles_checked': [], 'runtime_certified': False}
    require(evidence['schema'] == 1 and type(evidence['schema']) is int, 'invalid_schema')
    require(evidence['apk_sha256'] == APK_SHA256, 'apk_digest_mismatch')
    require(evidence['cert_sha256'] == CERT_SHA256, 'lab_signer_mismatch')
    profiles = evidence['profiles']
    if type(profiles) is not dict or set(profiles) != set(PROFILES):
        return {'status': 'BLOCKED', 'reasons': sorted(set(problems + ['missing_or_extra_lab_profile'])),
                'profiles_checked': [], 'runtime_certified': False}
    checked = []
    for name in ('api24', '16k'):
        run = profiles[name]
        if type(run) is not dict or set(run) != RUN_FIELDS:
            problems.append(f'{name}:invalid_run_fields')
            continue
        checked.append(name)
        api = run['api']
        page = run['page_size_bytes']
        require(type(api) is int and
                (api == 24 if name == 'api24' else api >= 35), f'{name}:wrong_android_api')
        require(type(page) is int and page == PROFILES[name]['page_size_bytes'],
                f'{name}:wrong_page_size')
        require(run['abi'] == 'arm64-v8a' and type(run['abi']) is str,
                f'{name}:wrong_abi')
        require(run['package'] == PACKAGE, f'{name}:wrong_package')
        require(run['permission_internet'] is False, f'{name}:internet_not_denied')
        for field in ('startup', 'jni', 'chaquopy', 'python'):
            require(run[field] == 'pass', f'{name}:{field}_not_pass')
        for field in ('native_loader_errors', 'fatal_exceptions', 'anrs', 'network_attempts'):
            require(type(run[field]) is int and run[field] == 0,
                    f'{name}:{field}_not_zero')
        libs = run['libraries']
        if type(libs) is not dict or set(libs) != set(LIBRARIES):
            problems.append(f'{name}:library_inventory_incomplete')
        else:
            for lib, digest in LIBRARIES.items():
                require(libs[lib] == digest and type(libs[lib]) is str,
                        f'{name}:library_digest_mismatch:{lib}')
        cases = run['cases']
        if type(cases) is not dict or set(cases) != CASE_NAMES:
            problems.append(f'{name}:runtime_cases_incomplete')
        else:
            for case in sorted(CASE_NAMES):
                require(cases[case] == 'pass', f'{name}:case_not_pass:{case}')
    return {'status': ('BLOCKED' if problems else 'CONSISTENT_SELF_REPORTED_EVIDENCE_REQUIRES_HUMAN_REVIEW'),
            'reasons': sorted(set(problems)), 'profiles_checked': checked,
            'case_count_per_profile': len(CASE_NAMES), 'library_count_per_profile': len(LIBRARIES),
            'runtime_certified': False,
            'warning': 'JSON values alone cannot prove device execution, library loading or correct provenance'}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = validate(load(args.evidence))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        result = {'status': 'BLOCKED', 'reasons': ['evidence_read_or_parse_failed'],
                  'profiles_checked': [], 'runtime_certified': False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['status'].startswith('CONSISTENT_') else 1


if __name__ == '__main__':
    raise SystemExit(main())
