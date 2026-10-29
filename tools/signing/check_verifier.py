#!/usr/bin/env python3
"""Compile and test fail-closed CLI behavior. Generates no cryptographic keys."""
from pathlib import Path
import subprocess
import tempfile
import json

SOURCE = Path(__file__).resolve().with_name('VerifySigning.java')


def main():
    with tempfile.TemporaryDirectory(prefix='flexygram-signing-check-') as directory:
        work = Path(directory)
        subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', str(work), str(SOURCE)], check=True)
        invalid = work / 'PRIVATE_PATH_DECOY.cer'
        invalid.write_bytes(b'INVALID_CERTIFICATE_PRIVATE_DECOY')
        commands = [[], ['generate', str(invalid)], ['certificate', str(invalid)],
                    ['certificate', str(invalid), 'PRIVATE_PASSWORD_DECOY'], ['keystore', str(invalid)], ['keystore-env', str(invalid)]]
        for arguments in commands:
            result = subprocess.run(['java', '-cp', str(work), 'VerifySigning', *arguments],
                                    stdin=subprocess.DEVNULL, capture_output=True, text=True)
            if result.returncode != 1 or result.stdout or not result.stderr.startswith('FAIL:'):
                raise AssertionError('Verifier must reject invalid/non-interactive inputs without a public PASS report')
            if any(value in result.stdout + result.stderr for value in ['PRIVATE_PATH_DECOY', 'PRIVATE_PASSWORD_DECOY', 'INVALID_CERTIFICATE_PRIVATE_DECOY']):
                raise AssertionError('Verifier echoed sensitive input')
        official = SOURCE.with_name('flexygram-release.cer')
        if not official.exists():
            official = SOURCE.parents[2] / 'config/signing/flexygram-release.cer'
        fingerprint = '5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c'
        valid = subprocess.run(['java', '-cp', str(work), 'VerifySigning', 'certificate', str(official), fingerprint], capture_output=True, text=True, check=True)
        report = json.loads(valid.stdout)
        assert report['status'] == 'PASS' and report['sha256'] == fingerprint and report['private_key'] == 'NOT_CHECKED'
        wrong = subprocess.run(['java', '-cp', str(work), 'VerifySigning', 'certificate', str(official), '0' * 64], capture_output=True, text=True)
        assert wrong.returncode == 1 and not wrong.stdout
        corrupted = work / 'corrupted-public.cer'
        data = bytearray(official.read_bytes()); data[-1] ^= 1; corrupted.write_bytes(data)
        bad = subprocess.run(['java', '-cp', str(work), 'VerifySigning', 'certificate', str(corrupted)], capture_output=True, text=True)
        assert bad.returncode == 1 and not bad.stdout
        if any(work.glob('*.p12')) or any(work.glob('*.keystore')):
            raise AssertionError('Verifier tests must not create signing identities')
    print('PASS: official public certificate verified; 8 rejection/non-disclosure cases passed; no key or Android artifact generated.')


if __name__ == '__main__':
    main()
