"""Fully synthetic, no-network tests for the read-only lab preflight."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[2] / 'tools/android_lab_preflight/preflight.py'
spec = importlib.util.spec_from_file_location('flexygram_lab_preflight', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

CERT = '27ef63ae50546c0af28c0ac54ef66a0c00614934cda86c6bea42d9d2759e7b83'


class SimulatedRunner:
    def __init__(self, sdk='24', page='4096', abis='arm64-v8a,armeabi-v7a',
                 qemu='1', devices='List of devices attached\nemulator-5554 device product:test model:test\n',
                 installed='', package=module.PACKAGE, internet=False, cert=CERT, v2=True):
        self.sdk, self.page, self.abis = sdk, page, abis
        self.qemu, self.devices, self.installed = qemu, devices, installed
        self.package, self.internet, self.cert, self.v2 = package, internet, cert, v2
        self.calls = []

    def __call__(self, argv):
        self.calls.append(tuple(argv))
        if argv == ['adb', 'devices', '-l']:
            return self.devices
        if argv[:4] == ['adb', '-s', 'emulator-5554', 'shell']:
            if argv[4:6] == ['getprop', 'ro.kernel.qemu']:
                return self.qemu
            if argv[4:6] == ['getprop', 'ro.boot.qemu']:
                return self.qemu
            if argv[4:6] == ['getprop', 'ro.build.version.sdk']:
                return self.sdk
            if argv[4:6] == ['getprop', 'ro.product.cpu.abilist']:
                return self.abis
            if argv[4:] == ['getconf', 'PAGE_SIZE']:
                return self.page
            if argv[4:] == ['pm', 'path', module.PACKAGE]:
                return self.installed
        if argv[:3] == ['aapt2', 'dump', 'badging']:
            return "package: name='" + self.package + "' versionCode='1261'\n" + (
                "uses-permission: name='android.permission.INTERNET'\n" if self.internet else '')
        if argv[:3] == ['aapt2', 'dump', 'permissions']:
            return "uses-permission: name='android.permission.INTERNET'" if self.internet else ''
        if argv[:4] == ['apksigner', 'verify', '--verbose', '--print-certs']:
            return (f'Verified using v2 scheme (APK Signature Scheme v2): '
                    f'{str(self.v2).lower()}\nSigner #1 certificate SHA-256 digest: {self.cert}\n')
        raise AssertionError('Unexpected tool invocation: ' + repr(argv))


class AndroidPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.apk = self.root / 'experimental-diagnostic.apk'
        with zipfile.ZipFile(self.apk, 'w') as f:
            f.writestr('AndroidManifest.xml', b'synthetic binary placeholder')
            f.writestr('classes.dex', b'fake dex')
        self.digest = module.sha256_file(self.apk)
        self.runner = SimulatedRunner()

    def flags(self, profile='api24'):
        return ['--serial', 'emulator-5554', '--profile', profile,
                '--apk', str(self.apk), '--expected-apk-sha256', self.digest,
                '--expected-cert-sha256', CERT]

    def run_cli(self, argv=None):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            status = module.main(argv if argv is not None else self.flags(), run=self.runner)
        return status, json.loads(stream.getvalue())

    def test_api24_clean_preflight_is_review_only(self):
        status, report = self.run_cli()
        self.assertEqual(status, 0)
        self.assertEqual(report['status'], 'READY_FOR_HUMAN_REVIEW_NOT_RUNTIME_VALIDATED')
        self.assertEqual(report['target']['page_size_bytes'], 4096)
        self.assertTrue(report['apk']['internet_permission_absent_in_dump'])
        self.assertNotIn('emulator-5554', json.dumps(report))
        self.assertIn('Android startup', report['not_certified'])

    def test_16kb_profile_checks_real_page_size_and_sdk(self):
        self.runner.sdk, self.runner.page = '35', '16384'
        status, report = self.run_cli(self.flags('16k'))
        self.assertEqual(status, 0)
        self.assertEqual(report['target']['page_size_bytes'], 16384)

    def test_android_16k_profile_rejects_only_4k_pages(self):
        self.runner.sdk = '35'
        status, report = self.run_cli(self.flags('16k'))
        self.assertEqual((status, report['status']), (1, 'BLOCKED'))

    def test_api24_rejects_wrong_sdk_even_if_arm64(self):
        self.runner.sdk = '27'
        self.assertEqual(self.run_cli()[0], 1)

    def test_16k_requires_modern_android_api(self):
        self.runner.sdk, self.runner.page = '34', '16384'
        self.assertEqual(self.run_cli(self.flags('16k'))[0], 1)

    def test_unsupported_abi_is_rejected(self):
        self.runner.abis = 'x86_64,x86'
        self.assertEqual(self.run_cli()[0], 1)

    def test_emulator_identity_must_be_proven(self):
        self.runner.qemu = ''
        self.assertEqual(self.run_cli()[0], 1)

    def test_non_emulator_hardware_serial_rejected_before_adb(self):
        self.assertRaises(module.Blocked, module.emulator_probe, 'RF8N12345', 'api24', self.runner)
        self.assertFalse(self.runner.calls)

    def test_emulator_must_be_online_authorized(self):
        self.runner.devices = 'List of devices attached\nemulator-5554 unauthorized\n'
        self.assertEqual(self.run_cli()[0], 1)

    def test_refuses_to_continue_if_diagnostic_is_preinstalled(self):
        self.runner.installed = 'package:/data/app/a/base.apk'
        self.assertEqual(self.run_cli()[0], 1)

    def test_bad_digest_does_not_run_aapt2_or_apksigner(self):
        args = self.flags()
        args[args.index('--expected-apk-sha256') + 1] = '0' * 64
        status, _ = self.run_cli(args)
        self.assertEqual(status, 1)
        self.assertFalse(any(x[0] in ('aapt2', 'apksigner') for x in self.runner.calls))

    def test_bad_package_is_rejected(self):
        self.runner.package = 'io.github.jose22yt.flexygram.app'
        self.assertEqual(self.run_cli()[0], 1)

    def test_internet_permission_blocks_preflight(self):
        self.runner.internet = True
        self.assertEqual(self.run_cli()[0], 1)

    def test_wrong_certificate_pin_blocks_preflight(self):
        self.runner.cert = 'c' * 64
        self.assertEqual(self.run_cli()[0], 1)

    def test_unsigned_v2_blocks_preflight(self):
        self.runner.v2 = False
        self.assertEqual(self.run_cli()[0], 1)

    def test_symlinked_apk_not_accepted(self):
        alias = self.root / 'alias.apk'
        alias.symlink_to(self.apk)
        args = self.flags()
        args[args.index('--apk') + 1] = str(alias)
        self.assertEqual(self.run_cli(args)[0], 1)

    def test_no_apk_does_not_claim_full_readiness(self):
        status, report = self.run_cli(['--serial', 'emulator-5554', '--profile', 'api24'])
        self.assertEqual(status, 0)
        self.assertEqual(report['status'], 'EMULATOR_CHECKS_ONLY_APK_NOT_VERIFIED')

    def test_partial_apk_arguments_rejected(self):
        self.assertEqual(self.run_cli(['--serial', 'emulator-5554', '--profile', 'api24',
                                       '--apk', str(self.apk)])[0], 1)

    def test_no_dangerous_commands_can_be_issued(self):
        self.run_cli()
        self.assertTrue(self.runner.calls)
        for argv in self.runner.calls:
            command = ' '.join(argv)
            self.assertNotIn(' install ', command)
            self.assertNotIn(' logcat ', command)
            self.assertNotIn(' am start ', command)
            self.assertNotIn(' push ', command)
            self.assertNotIn(' pull ', command)
            self.assertNotIn('settings put', command)

    def test_log_summarizes_without_including_personal_contents(self):
        path = self.root / 'private.log'
        path.write_text('MySecretToken\nFATAL EXCEPTION: main user=private\n'
                        'UnsatisfiedLinkError on private path\n', encoding='utf-8')
        result = module.read_log_counts(path)
        self.assertEqual(result['category_counts']['native_loader_error'], 1)
        self.assertEqual(result['category_counts']['crash_or_anr'], 1)
        self.assertNotIn('MySecretToken', json.dumps(result))
        self.assertNotIn('private', json.dumps(result))

    def test_log_symlink_is_rejected(self):
        path = self.root / 'private.log'
        path.write_text('secret', encoding='utf-8')
        alias = self.root / 'alias.log'
        alias.symlink_to(path)
        with self.assertRaises(module.Blocked):
            module.read_log_counts(alias)

    def test_corrupt_zip_is_rejected_before_external_tools(self):
        self.apk.write_bytes(b'not a zip')
        args = self.flags()
        args[args.index('--expected-apk-sha256') + 1] = module.sha256_file(self.apk)
        self.assertEqual(self.run_cli(args)[0], 1)
        self.assertFalse(any(x[0] == 'aapt2' for x in self.runner.calls))


if __name__ == '__main__':
    unittest.main()
