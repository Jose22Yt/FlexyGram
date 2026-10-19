"""Synthetic fail-closed regressions; no native build, network, emulator or signing."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / 'tools/native_compatibility/reproduce_locked_16k.py'
spec = importlib.util.spec_from_file_location('native_p04c_repro', SCRIPT)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class ReproductionGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.folder = self.path / 'run-a'
        self.folder.mkdir()
        self.libs = {}
        for i, name in enumerate(r.NAMES):
            data = (name + str(i)).encode()
            target = self.folder / ('freetype-build' if name == 'libfreetype.so' else 'prefix/lib') / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            self.libs[name] = r.sha(target)
        self.approved = []
        self.rebuilt = {}
        self.rows = []
        wheel_dir = self.folder / 'wheels'
        wheel_dir.mkdir()
        for i in range(18):
            original = f'package{i}-1-py3-none-android_21_arm64_v8a.whl'
            if i < 3:
                current = f'package{i}-2flexygram16k-py3-none-android_24_arm64_v8a.whl'
                rebuilt = True
            else:
                current = original
                rebuilt = False
            path = wheel_dir / current
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('payload.txt', str(i).encode())
            digest = r.sha(path)
            self.approved.append({'filename': original, 'sha256': digest})
            if rebuilt:
                self.rebuilt[current] = digest
            self.rows.append({'filename': current, 'original_filename': original,
                              'sha256': digest, 'rebuilt': rebuilt})
        self.manifest = {'wheels': self.rows, 'android_runtime_validated': False}
        self.save()

    def save(self):
        (self.folder / 'wheels-manifest.json').write_text(json.dumps(self.manifest))

    def validate(self):
        return r.check_outputs(self.folder, self.approved, self.libs, self.rebuilt)

    def test_exact_rebuilt_and_original_inputs_are_accepted(self):
        result = self.validate()
        self.assertEqual(len(result['elf_sha256']), 4)
        self.assertEqual(len(result['wheel_sha256']), 18)

    def test_changed_native_elf_is_rejected(self):
        (self.folder / 'prefix/lib/libxml2.so').write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError, 'ELF SHA-256 mismatch'):
            self.validate()

    def test_missing_native_elf_is_rejected(self):
        (self.folder / 'prefix/lib/libxslt.so').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing source-rebuilt ELF'):
            self.validate()

    def test_changed_rebuilt_wheel_is_rejected(self):
        name = self.rows[0]['filename']
        (self.folder / 'wheels' / name).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'Wheel manifest checksum mismatch'):
            self.validate()

    def test_rebuilt_wheel_with_wrong_approved_pin_is_rejected(self):
        self.rebuilt[self.rows[0]['filename']] = 'a' * 64
        with self.assertRaisesRegex(ValueError, 'Reviewed rebuilt wheel SHA-256 mismatch'):
            self.validate()

    def test_original_wheel_sha_mismatch_is_rejected(self):
        self.approved[4]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Original wheel was modified'):
            self.validate()

    def test_missing_wheel_is_rejected(self):
        (self.folder / 'wheels' / self.rows[3]['filename']).unlink()
        with self.assertRaisesRegex(ValueError, 'Missing wheel file'):
            self.validate()

    def test_extra_unpinned_wheel_is_rejected(self):
        (self.folder / 'wheels' / 'unapproved.whl').write_bytes(b'fake')
        with self.assertRaisesRegex(ValueError, 'Extra files'):
            self.validate()

    def test_duplicate_wheel_manifest_is_rejected(self):
        self.manifest['wheels'][1] = dict(self.manifest['wheels'][0])
        self.save()
        with self.assertRaisesRegex(ValueError, 'exactly 18 unique wheels'):
            self.validate()

    def test_runtime_certification_in_manifest_is_rejected(self):
        self.manifest['android_runtime_validated'] = True
        self.save()
        with self.assertRaisesRegex(ValueError, 'Unsupported Android runtime assertion'):
            self.validate()

    def test_symlinked_native_library_is_rejected(self):
        lib = self.folder / 'prefix/lib/libxml2.so'
        real = self.folder / 'original-library'
        lib.replace(real)
        lib.symlink_to(real)
        with self.assertRaisesRegex(ValueError, 'Missing source-rebuilt ELF'):
            self.validate()

    def test_reviewed_evidence_must_contain_all_libraries_and_three_wheels(self):
        fake_evidence = self.path / 'evidence'
        fake_evidence.mkdir()
        abi = [{'library': k, 'contract': {'after_sha256': v},
                'static_abi_pass': True, 'independent_build_identical': True}
               for k, v in self.libs.items()]
        (fake_evidence / 'abi-report-final.json').write_text(json.dumps(abi))
        wheels = [{'filename': k, 'sha256': v, 'rebuilt': True} for k, v in self.rebuilt.items()]
        (fake_evidence / 'wheel-reproducibility.json').write_text(json.dumps({'rebuilt': wheels}))
        with patch.object(r, 'EVIDENCE', fake_evidence):
            self.assertEqual(r.expected(), (self.libs, self.rebuilt))
            abi[0]['independent_build_identical'] = False
            (fake_evidence / 'abi-report-final.json').write_text(json.dumps(abi))
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                r.expected()

    def test_existing_output_directory_is_not_overwritten(self):
        output = self.path / 'exists'
        output.mkdir()
        args = type('Args', (), {'sources': str(self.path / 'source'),
                                 'wheelhouse': str(self.path / 'wheels'),
                                 'ndk': str(self.path / 'ndk'),
                                 'cmake': str(self.path / 'cmake'),
                                 'output': str(output)})()
        with self.assertRaisesRegex(ValueError, 'previously nonexistent'):
            r.execute(args)

    def test_missing_input_preflight_exits_blocked_without_output(self):
        out = self.path / 'result-do-not-create'
        flags = ['--sources', str(self.path / 'not-here'), '--wheelhouse', str(self.path),
                 '--ndk', str(self.path), '--cmake', str(self.path / 'cmake'),
                 '--output', str(out), '--verify-inputs-only']
        with patch.object(r, 'check_inputs', side_effect=ValueError('Missing inputs')):
            self.assertEqual(r.main(flags), 1)
        self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
