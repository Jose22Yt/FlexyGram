"""Pinned review of the NEW unsigned candidate; emits only a non-runnable v2 draft.

Never replaces historical v1 pins, authorizes signing, loads code or installs APKs.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import create_lab_v2_draft as draft
import review_unsigned_contract as historical
import review_rebuilt_candidate as candidate

ROOT = Path(__file__).resolve().parents[2]
APK_SHA256 = '291881863ea81418fa6cb12104b6eaea4aee2403822894da2143a51f3030bdd5'
APK_BYTES = 113080183
JNI_SHA256 = '756e53d23f29ecca32d7c9706375494cdf2217d0db8d314a4195d0174400912b'
SOURCE_HEAD = '1177ceb8f4351b1626dd65e3dbd657f3b0ff159f'
INDEX_SHA256 = 'fff31dd27ffc69b1aed2da19428bf0e5d0eabdf51c06d2ca4828db95b74a05b7'
V1_SHA256 = '1a3ecb0160e2babf91c9ef7c1712c3577fadb73c5f647d17d84275af146dbb28'
WHEELS_SHA256 = 'c6495ee9895da29a2c4bdc9c45647721c33070190eeb8c9b8054096cb2bf2f97'
EVIDENCE = ROOT/'docs/security-p04c/evidence-unsigned-rebuild-20261020'
WHEELS = ROOT/'docs/security-p04c/evidence-work-20261019/experimental-wheels-manifest.json'
require = historical.require


def regular(path):
    require(path.is_file() and not path.is_symlink() and
            not any(p.is_symlink() for p in path.parents), 'Regular nonsymlink file required')


def check_physical_result(result):
    require(result['status'] == 'CANDIDATE_BYTES_STATICALLY_VERIFIED_PENDING_ANDROID' and
            result['apk_sha256'] == APK_SHA256 and result['apk_bytes'] == APK_BYTES and
            result['elf_total'] == 97 and result['arm64'] == 96 and
            all(result[k] is False for k in ('signed', 'installed', 'android_runtime_validated',
                                             'distribution_allowed', 'historical_contract_modified')),
            'Physical candidate review required; metadata-only results cannot seed v2')


def prepare(apk, evidence=EVIDENCE):
    # Reuse the concurrent, authoritative 44-file dual-pin + physical ZIP/ELF
    # verifier. Do not maintain a second, weaker candidate-byte implementation.
    physical = candidate.review(evidence, apk)
    check_physical_result(physical)
    require(candidate.SOURCE_HEAD == SOURCE_HEAD and candidate.JNI_SHA256 == JNI_SHA256,
            'Candidate implementation pins changed; separate review required')
    regular(historical.LAB_V1)
    regular(WHEELS)
    require(historical.sha256(historical.LAB_V1) == V1_SHA256 and
            historical.sha256(WHEELS) == WHEELS_SHA256, 'Historical inputs changed')
    receipt = historical.read_json(evidence/'unsigned-apk-receipt.json')
    audit = historical.read_json(evidence/'apk-native-audit.json')
    report = {'status': 'UNSIGNED_EVIDENCE_REVIEWED_SIGNING_BLOCKED',
              'signing_authorized': False, 'android_runtime_validated': False,
              'distribution_allowed': False, 'unsigned_apk_sha256': APK_SHA256,
              'unsigned_apk_bytes': APK_BYTES, 'source_head': SOURCE_HEAD,
              'native_elf_sha256': receipt['packaged_rebuilt_elf']}
    result = draft.make_draft(report, historical.read_json(historical.LAB_V1), audit,
                              historical.read_json(WHEELS),
                              {'apk_sha256': APK_SHA256, 'apk_bytes': APK_BYTES, 'signature': 'absent'})
    result['candidate_technical_review_is_not_owner_approval'] = True
    result['historical_v1_sha256_unchanged'] = V1_SHA256
    result['exact_profile_api_requirements'] = {'api24-4k': 24, 'arm64-16k': 35}
    result['missing_review_gates'][:0] = [
        'Owner acceptance of the NEW unsigned candidate and bounded historical comparison',
        'Separate reviewed v2 post-sign verifier, runner and PR20/21 adaptation; v1 stays frozen']
    return result


def write_private(path, value):
    path = path.absolute()
    require(path.parent.is_dir() and ROOT.resolve() not in path.resolve().parents and
            not path.exists() and not path.is_symlink() and
            not any(p.is_symlink() for p in path.parents), 'New private output outside repository required')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.apk, args.evidence)
    write_private(args.output, result)
    print(json.dumps({'status': result['status'], 'source_sha256': APK_SHA256,
                      'certificate': None, 'runtime_contract_activated': False}))


if __name__ == '__main__':
    main()
