"""Synthetic preflight regressions; no Android, ADB devices or network services."""
from pathlib import Path
from types import SimpleNamespace
import gzip
import hashlib
import subprocess
import tempfile
import unittest
import zipfile
from unittest.mock import patch
import lab_host_preflight as lab


class HostPreflightTests(unittest.TestCase):
    def test_arm64_api24_properties(self):
        r = lab.properties('SystemImage.Abi=arm64-v8a\nAndroidVersion.ApiLevel=24\n', 'api24-4k')
        self.assertEqual(r['SystemImage.Abi'], 'arm64-v8a')

    def test_x86_cannot_validate_arm64(self):
        with self.assertRaises(ValueError):
            lab.properties('SystemImage.Abi=x86_64\nAndroidVersion.ApiLevel=24\n', 'api24-4k')

    def test_exact_api35_required(self):
        with self.assertRaises(ValueError):
            lab.properties('SystemImage.Abi=arm64-v8a\nAndroidVersion.ApiLevel=37\nSystemImage.TagId=page_size_16kb\n', 'arm64-16k')

    def test_16k_tag_required_but_not_runtime_proof(self):
        with self.assertRaises(ValueError):
            lab.properties('SystemImage.Abi=arm64-v8a\nAndroidVersion.ApiLevel=35\n', 'arm64-16k')
        lab.properties('SystemImage.Abi=arm64-v8a\nAndroidVersion.ApiLevel=35\nSystemImage.TagId=google_apis,page_size_16kb\n', 'arm64-16k')

    def test_duplicate_properties_rejected(self):
        with self.assertRaises(ValueError):
            lab.properties('SystemImage.Abi=arm64-v8a\nSystemImage.Abi=x86_64\n', 'api24-4k')

    def test_unknown_archive_hash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'untrusted.zip';p.write_bytes(b'SYNTHETIC_WRONG_IMAGE')
            with self.assertRaises(ValueError): lab.verify_image(p, 'api24-4k')

    def kernel_fixture(self, header):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'synthetic.zip'
            with zipfile.ZipFile(p, 'w') as z:
                z.writestr('arm64-v8a/source.properties', 'SystemImage.Abi=arm64-v8a\nAndroidVersion.ApiLevel=35\nSystemImage.TagId=google_apis,page_size_16kb\n')
                z.writestr('arm64-v8a/kernel-ranchu', gzip.compress(header))
            # Only a fixture-scoped expected digest, never a CLI override of production pins.
            with patch.dict(lab.IMAGES['arm64-16k'], {'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}):
                return lab.verify_image(p, 'arm64-16k')

    def test_gzip_kernel_architecture_checked_after_decompression(self):
        header = bytearray(64);header[56:60] = b'ARMd'
        result = self.kernel_fixture(bytes(header))
        self.assertTrue(result['kernel_gzip'])
        self.assertTrue(result['arm64_kernel_header_verified'])
        self.assertIsNone(result['actual_guest_page_size'])
        self.assertFalse(result['strict_16k_runtime_verified'])

    def test_wrong_kernel_cannot_pass_valid_archive(self):
        with self.assertRaises(ValueError): self.kernel_fixture(b'NOT_AN_ARM64_KERNEL'*4)

    def test_timeout_blocks(self):
        with patch.object(lab.subprocess, 'run', side_effect=subprocess.TimeoutExpired('fixture', 20)):
            self.assertIsNone(lab.command(['fixture'])['exit_code'])

    def test_namespace_denial_blocks_before_boot(self):
        def command(args, env=None):
            return {'exit_code': 1 if args[0] == 'unshare' else 0, 'output': 'SYNTHETIC'}
        with patch.object(lab, 'verify_image', return_value={'fixture': True}), \
             patch.object(lab, 'command', side_effect=command), patch.object(lab.shutil, 'which', return_value='/sbin/ip'), \
             patch.object(lab, 'check_storage', return_value={'status': 'PASS', 'free_bytes': 12*1024**3}):
            r = lab.probe(Path('/synthetic/sdk'), Path('/synthetic/images'))
        self.assertEqual(r['status'], 'HOST_BLOCKED_BEFORE_ANDROID_BOOT')
        self.assertIn('isolated network namespace unavailable', r['blockers'])
        self.assertFalse(r['android_executed'])

    def test_ready_preflight_never_authorizes_or_executes_android(self):
        calls = []
        def command(args, env=None):
            calls.append(args);return {'exit_code': 0, 'output': 'SYNTHETIC_VERSION'}
        with patch.object(lab, 'verify_image', return_value={'fixture': True}), \
             patch.object(lab, 'command', side_effect=command), patch.object(lab.shutil, 'which', return_value='/sbin/ip'), \
             patch.object(lab, 'check_storage', return_value={'status': 'PASS', 'free_bytes': 12*1024**3}):
            r = lab.probe(Path('/synthetic/sdk'), Path('/synthetic/images'))
        self.assertEqual(r['status'], 'HOST_READY_FOR_MANUAL_OFFLINE_BOOT_CHECK_ONLY')
        self.assertFalse(r['installation_authorized'])
        self.assertFalse(r['runtime_validated'])
        self.assertFalse(r['android_executed'])
        self.assertEqual(len(calls), 4)
        self.assertFalse(any(token in ('install', 'shell', '-avd', 'start-server') for args in calls for token in args))


    def test_avd_storage_above_margin_allows_preflight(self):
        with tempfile.TemporaryDirectory() as d, \
             patch.dict(lab.os.environ, {'ANDROID_AVD_HOME': d}), \
             patch.object(lab.shutil, 'disk_usage',
                          return_value=SimpleNamespace(free=11*1024**3)):
            status = lab.check_storage(Path('/synthetic/sdk'))
        self.assertEqual(status['status'], 'PASS')
        self.assertEqual(status['target'], 'ANDROID_AVD_HOME')
        self.assertEqual(status['required_free_bytes'], 10*1024**3)

    def test_avd_storage_below_margin_blocks_before_android(self):
        with tempfile.TemporaryDirectory() as d, \
             patch.dict(lab.os.environ, {'ANDROID_AVD_HOME': d}), \
             patch.object(lab.shutil, 'disk_usage',
                          return_value=SimpleNamespace(free=256*1024**2)):
            status = lab.check_storage(Path('/synthetic/sdk'))
        self.assertEqual(status['status'], 'BLOCKED')
        self.assertEqual(status['free_bytes'], 256*1024**2)

    def test_unavailable_avd_storage_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            missing = str(Path(d)/'not-created')
            with patch.dict(lab.os.environ, {'ANDROID_AVD_HOME': missing}):
                status = lab.check_storage(Path(d))
        self.assertEqual(status['status'], 'BLOCKED')
        self.assertIsNone(status['free_bytes'])

    def test_probe_blocks_even_when_tools_and_images_ready_if_disk_full(self):
        def command(args, env=None):
            return {'exit_code': 0, 'output': 'SYNTHETIC'}
        with patch.object(lab, 'verify_image', return_value={'fixture': True}), \
             patch.object(lab, 'command', side_effect=command), \
             patch.object(lab.shutil, 'which', return_value='/sbin/ip'), \
             patch.object(lab, 'check_storage',
                          return_value={'status': 'BLOCKED', 'free_bytes': 265818112}):
            result = lab.probe(Path('/synthetic/sdk'), Path('/synthetic/images'))
        self.assertEqual(result['status'], 'HOST_BLOCKED_BEFORE_ANDROID_BOOT')
        self.assertTrue(any('filesystem space' in item for item in result['blockers']))
        self.assertEqual(result['storage']['free_bytes'], 265818112)
        self.assertFalse(result['android_executed'])
