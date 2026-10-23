import base64
import csv
import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from rebuild_python_wheels import HOST_HELPERS, android_debugpy, checked_bytes


class PythonWheelRegression(unittest.TestCase):
    def test_source_checksum_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            checked_bytes(b'changed archive', hashlib.sha256(b'authorized archive').hexdigest())

    def test_desktop_attach_helpers_removed_but_network_debugger_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, result = Path(tmp)/'source.whl', Path(tmp)/'result.whl'
            with zipfile.ZipFile(source, 'w') as z:
                for name in HOST_HELPERS:
                    z.writestr(name, b'unsupported desktop helper')
                z.writestr('debugpy/server/api.py', b'network debugger fixture')
                z.writestr('debugpy-1.8.22.dist-info/WHEEL', b'Wheel-Version: 1.0\nTag: py3-none-any\n')
                z.writestr('debugpy-1.8.22.dist-info/RECORD', b'old record')
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            with patch('rebuild_python_wheels.DEBUGPY_SHA256', digest):
                android_debugpy(source, result)
            with zipfile.ZipFile(result) as z:
                self.assertFalse(HOST_HELPERS.intersection(z.namelist()))
                self.assertEqual(z.read('debugpy/server/api.py'), b'network debugger fixture')
                record = csv.reader(io.StringIO(z.read('debugpy-1.8.22.dist-info/RECORD').decode()))
                for name, actual_hash, size in record:
                    if name.endswith('/RECORD'):
                        self.assertEqual((actual_hash, size), ('', ''))
                    else:
                        data = z.read(name)
                        expected_hash = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
                        self.assertEqual(actual_hash, 'sha256='+expected_hash)
                        self.assertEqual(int(size), len(data))


if __name__ == '__main__':
    unittest.main()
