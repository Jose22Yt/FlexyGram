#!/usr/bin/env python3
"""Deterministic source-only toolkit ZIP. Explicit whitelist excludes private inputs."""
from pathlib import Path
import hashlib
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NAMES = ['owner_wizard.py', 'VerifySigning.java', 'README_LOCAL.md', 'check_verifier.py', 'test_owner_wizard.py']


def main():
    entries = {name: (HERE / name).read_bytes() for name in NAMES}
    entries['flexygram-release.cer'] = (ROOT / 'config/signing/flexygram-release.cer').read_bytes()
    entries['identity.properties'] = (ROOT / 'config/signing/identity.properties').read_bytes()
    entries['LICENSE'] = (ROOT / 'LICENSE').read_bytes()
    entries['SHA256SUMS'] = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n'
                                  for name, data in sorted(entries.items())).encode()
    output = HERE / 'FlexyGram_Firma_Local.zip'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo('FlexyGram_Firma_Local/' + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100600 << 16
            archive.writestr(info, data)
    (HERE / 'FlexyGram_Firma_Local.zip.sha256').write_text(hashlib.sha256(output.read_bytes()).hexdigest() + '  ' + output.name + '\n')
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == {'FlexyGram_Firma_Local/' + n for n in entries}
        assert archive.testzip() is None
    print('PASS: source-only toolkit ZIP built from explicit whitelist; no private keys, passwords or backups included.')


if __name__ == '__main__':
    main()
