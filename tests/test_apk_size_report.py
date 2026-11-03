import zipfile
from tools.apk_size_report import report


def test_apk_size_accounting_preserves_archive(tmp_path):
    apk = tmp_path / 'sample.apk'
    with zipfile.ZipFile(apk, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ['classes.dex', 'lib/arm64-v8a/libtest.so', 'res/drawable/icon.png',
                     'assets/chaquopy/requirements-arm64-v8a.imy', 'AndroidManifest.xml']:
            archive.writestr(name, b'payload' * 100)
    before = apk.read_bytes()
    result = report(apk)
    assert result['bytes'] == len(before)
    assert set(result['groups']) == {'dex', 'native', 'resources', 'python', 'other'}
    assert sum(v['uncompressed'] for v in result['groups'].values()) == 5 * 700
    assert sum(v['compressed'] for v in result['groups'].values()) < result['bytes']
    assert apk.read_bytes() == before
