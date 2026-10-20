"""Real synthetic ELF mutations; compile only, never load the shared libraries."""
from pathlib import Path
from io import BytesIO
import copy
import shutil
import subprocess
import tempfile
import unittest
from elftools.elf.elffile import ELFFile
import elf_candidate_review as review


class CandidateElfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('cc') or not shutil.which('strip'):
            raise RuntimeError('Host C compiler and strip required; no skipped ELF tests')
        cls.directory = tempfile.TemporaryDirectory()
        root = Path(cls.directory.name)
        source = root/'probe.c'
        source.write_text('const char text[]="SYNTHETIC_ONLY"; const char *lab(void){return text;}\n')
        full, stripped = root/'full.so', root/'stripped.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-g', '-Wl,-soname,libsynthetic.so',
                        str(source), '-o', str(full)], check=True, capture_output=True)
        subprocess.run(['strip', '--strip-unneeded', '-o', str(stripped), str(full)],
                       check=True, capture_output=True)
        cls.raw = stripped.read_bytes()
        cls.left = review.inspect(full.read_bytes())
        cls.right = review.inspect(cls.raw)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def changed_section(self, name):
        data = bytearray(self.raw)
        section = ELFFile(BytesIO(self.raw)).get_section_by_name(name)
        self.assertIsNotNone(section)
        data[section['sh_offset']] ^= 1
        return review.inspect(bytes(data))

    def test_strip_preserves_loadable_sections(self):
        r = review.compare(self.left, self.right)
        self.assertTrue(r['only_nonallocated_sections_removed'])
        self.assertEqual(r['allocated_section_differences'], [])
        self.assertIn('.debug_info', r['removed_sections'])

    def test_allocated_data_mutation_detected(self):
        r = review.compare(self.right, self.changed_section('.rodata'))
        self.assertIn('.rodata', r['allocated_section_differences'])
        self.assertIn('.rodata', r['allocated_byte_differences'])
        self.assertEqual(r['executable_section_differences'], [])

    def test_executable_mutation_detected(self):
        r = review.compare(self.right, self.changed_section('.text'))
        self.assertIn('.text', r['executable_section_differences'])
        self.assertIn('.text', r['executable_byte_differences'])

    def test_relocation_mutation_detected(self):
        other = copy.deepcopy(self.right)
        self.assertTrue(other['relocations'])
        other['relocations'][0][-1] = 123456
        self.assertFalse(review.compare(self.right, other)['relocations_equal'])

    def test_changed_export_type_changes_abi(self):
        other = copy.deepcopy(self.right)
        other['exports'][0][1] = 'STT_TLS'
        self.assertFalse(review.compare(self.right, other)['export_abi_equal'])

    def test_export_address_changes_layout_not_abi(self):
        other = copy.deepcopy(self.right)
        other['exports'][0][4] += 16
        r = review.compare(self.right, other)
        self.assertFalse(r['exports_equal'])
        self.assertTrue(r['export_abi_equal'])

    def test_dependency_change_detected(self):
        other = copy.deepcopy(self.right)
        other['needed'].append('libunreviewed.so')
        self.assertFalse(review.compare(self.right, other)['needed_equal'])

    def test_soname_change_detected(self):
        other = copy.deepcopy(self.right)
        other['sonames'] = ['unreviewed.so']
        self.assertFalse(review.compare(self.right, other)['sonames_equal'])

    def test_elf_abi_flags_change_detected(self):
        other = copy.deepcopy(self.right)
        other['abi']['flags'] += 1
        self.assertFalse(review.compare(self.right, other)['elf_abi_equal'])

    def test_wrong_machine_rejected(self):
        other = copy.deepcopy(self.right)
        other['machine'] = 'EM_X86_64' if self.right['machine'] == 'EM_AARCH64' else 'EM_AARCH64'
        with self.assertRaises(ValueError):
            review.compare(self.right, other)

    def test_entry_and_program_header_changes_detected(self):
        other = copy.deepcopy(self.right)
        other['entry'] += 1
        other['program_headers'][0]['p_flags'] ^= 1
        r = review.compare(self.right, other)
        self.assertFalse(r['entry_equal'])
        self.assertFalse(r['program_headers_equal'])

    def test_malformed_input_cannot_pass(self):
        for data in (b'', b'NOT_ELF', self.raw[:64]):
            with self.assertRaises(Exception):
                review.inspect(data)
