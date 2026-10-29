#!/usr/bin/env python3
"""Compile and test fail-closed CLI behavior. Generates no cryptographic keys."""
from pathlib import Path
import subprocess
import tempfile

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
        if any(work.glob('*.p12')) or any(work.glob('*.keystore')):
            raise AssertionError('Verifier tests must not create signing identities')
    print('PASS: verifier compiled; 6 rejection/non-disclosure cases passed; no key or Android artifact generated.')


if __name__ == '__main__':
    main()
