"""Synthetic files and subprocess doubles; no SDK tool or device is executed."""
from pathlib import Path
import sys
import tempfile
import unittest
import subprocess
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/lab_readiness'))
import preflight as p


class Readiness(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sdk, self.avd, self.java = [self.root / n for n in ['sdk', 'avds', 'jdk']]
        for folder in [self.sdk, self.avd, self.java]: folder.mkdir()
        self.commands = []
        for relative in ['platform-tools/adb', 'emulator/emulator']:
            file = self.sdk / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.touch()
        for relative, revision in [('cmdline-tools/19.0', '19.0'), ('build-tools/36.0.0', '36.0.0')]:
            folder = self.sdk / relative
            folder.mkdir(parents=True)
            (folder / 'source.properties').write_text('Pkg.Revision=' + revision + '\n')
        (self.java / 'bin').mkdir()
        (self.java / 'bin/java').touch()
        for profile, (api, tag, name) in p.PROFILES.items():
            directory = self.avd / (name + '.avd')
            directory.mkdir()
            (self.avd / (name + '.ini')).write_text(f'path={directory}\ntarget=android-{api}\n')
            relative = f'system-images/android-{api}/{tag}/arm64-v8a'
            image = self.sdk / relative
            image.mkdir(parents=True)
            (image / 'source.properties').write_text(f'AndroidVersion.ApiLevel={api}\nSystemImage.Abi=arm64-v8a\nPkg.Revision={9 if api == 24 else 5}\nSystemImage.TagId={"default" if api == 24 else "google_apis,page_size_16kb"}\n')
            for file in ['kernel-ranchu', 'system.img', 'userdata.img']: (image / file).write_bytes(b'SYNTHETIC')
            (directory / 'config.ini').write_text(f'abi.type=arm64-v8a\nhw.cpu.arch=arm64\nimage.sysdir.1={relative}\nPlayStore.enabled=false\n')

    def runner(self, command, **kwargs):
        self.commands.append((command, kwargs))
        output = {'adb': 'Android Debug Bridge version 1.0.41\nVersion 37.0.1-16428233',
                  'emulator': 'Android emulator version 37.2.12.0 (build_id 16428233)',
                  'java': 'openjdk version "21.0.8"'}[Path(command[0]).name]
        return SimpleNamespace(returncode=0, stdout=output, stderr='')

    def run_check(self, **kwargs):
        return p.inspect(self.sdk, self.avd, self.java, env={}, runner=self.runner,
                         usage=lambda _: SimpleNamespace(free=100 * p.GIB), **kwargs)

    def config(self, profile='api24-4k'):
        return self.avd / (p.PROFILES[profile][2] + '.avd/config.ini')

    def mutate(self, path, old, new):
        path.write_text(path.read_text().replace(old, new))

    def test_complete_synthetic_fixture_is_preboot_only(self):
        report = self.run_check()
        self.assertEqual(report['blocking_checks'], [])
        for key in ['android_executed', 'apk_installed', 'apk_signed', 'image_bytes_verified', 'network_isolation_verified']:
            self.assertIs(report[key], False)

    def test_only_version_commands_and_explicit_roots(self):
        self.run_check()
        self.assertEqual([c[0][1:] for c in self.commands], [['version'], ['-no-window', '-version'], ['-version']])
        for _, kwargs in self.commands:
            self.assertEqual(kwargs['timeout'], 20)
            self.assertEqual(kwargs['env']['ANDROID_AVD_HOME'], str(self.avd))
            self.assertEqual(kwargs['env']['ANDROID_USER_HOME'], str(self.avd))
            self.assertEqual(kwargs['env']['ANDROID_HOME'], str(self.sdk))
            self.assertNotIn('shell', kwargs)

    def test_inspection_does_not_write_fixture(self):
        def snapshot():
            return {str(f.relative_to(self.root)): f.read_bytes() for f in self.root.rglob('*') if f.is_file()}
        before = snapshot()
        self.run_check()
        self.assertEqual(snapshot(), before)

    def test_mismatched_build_tools_metadata(self):
        (self.sdk / 'build-tools/36.0.0/source.properties').write_text('Pkg.Revision=35.0.0\n')
        self.assertIn('build_tools_metadata', self.run_check()['blocking_checks'])

    def test_missing_cli_metadata(self):
        (self.sdk / 'cmdline-tools/19.0/source.properties').unlink()
        self.assertIn('sdk_cli_metadata', self.run_check()['blocking_checks'])

    def test_noop_tool_is_not_version_proof(self):
        result = p.inspect(self.sdk, self.avd, self.java, env={}, runner=lambda *a, **k: SimpleNamespace(returncode=0, stdout='', stderr=''))
        self.assertTrue({'adb_version', 'emulator_version', 'java_version'} <= set(result['blocking_checks']))

    def test_tool_timeout_is_aggregated(self):
        def fail(*a, **k): raise subprocess.TimeoutExpired('synthetic', 20)
        result = p.inspect(self.sdk, self.avd, self.java, env={}, runner=fail)
        self.assertIn('java_version', result['blocking_checks'])
        self.assertEqual(result['status'], 'PREBOOT_BLOCKED')

    def test_wrong_versions_are_rejected(self):
        def wrong(*a, **k): return SimpleNamespace(returncode=0, stdout='Version 36.0.0 Android emulator version 36.0.0 openjdk version "17.0.1"', stderr='')
        report = p.inspect(self.sdk, self.avd, self.java, env={}, runner=wrong)
        self.assertTrue({'adb_version', 'emulator_version', 'java_version'} <= set(report['blocking_checks']))

    def test_nonzero_version_is_rejected(self):
        def failed(*a, **k): return SimpleNamespace(returncode=1, stdout='Version 37.0.1-', stderr='')
        report = p.inspect(self.sdk, self.avd, self.java, env={}, runner=failed)
        self.assertIn('adb_version', report['blocking_checks'])

    def test_environment_values_never_leak(self):
        secret = 'SYNTHETIC_PRIVATE_PROXY'
        report = p.inspect(self.sdk, self.avd, self.java, env={key: secret for key in p.HOST_OVERRIDES + ['HTTP_PROXY']}, runner=self.runner)
        self.assertIn('environment_HTTP_PROXY', report['blocking_checks'])
        for key in p.HOST_OVERRIDES:
            self.assertIn('environment_' + key, report['blocking_checks'])
        self.assertNotIn(secret, str(report))
        for _, kwargs in self.commands: self.assertNotIn(secret, str(kwargs['env']))

    def test_shared_volume_budget_is_aggregated(self):
        report = p.inspect(self.sdk, self.avd, self.java, env={}, runner=self.runner, usage=lambda _: SimpleNamespace(free=11 * p.GIB))
        self.assertIn('free_space_volume_0', report['blocking_checks'])

    def test_missing_roots_report_all_failures(self):
        report = p.inspect(self.root / 'missing', self.root / 'missing2', self.root / 'missing3', env={}, runner=self.runner)
        self.assertTrue({'storage_sdk', 'storage_avd', 'adb_version', 'avd_api24-4k', 'avd_arm64-16k'} <= set(report['blocking_checks']))

    def test_wrong_abi(self):
        self.mutate(self.config(), 'abi.type=arm64-v8a', 'abi.type=x86_64')
        self.assertIn('avd_api24-4k', self.run_check()['blocking_checks'])

    def test_wrong_image_path(self):
        self.mutate(self.config(), 'android-24/default', 'android-35/google_apis_ps16k')
        self.assertIn('avd_api24-4k', self.run_check()['blocking_checks'])

    def test_image_path_escape(self):
        self.mutate(self.config(), 'image.sysdir.1=system-images/android-24/default/arm64-v8a', 'image.sysdir.1=../outside')
        self.assertIn('avd_api24-4k', self.run_check()['blocking_checks'])

    def test_avd_directory_escape(self):
        name = p.PROFILES['api24-4k'][2]
        locator = self.avd / (name + '.ini')
        self.mutate(locator, str(self.avd / (name + '.avd')), str(self.sdk))
        self.assertIn('avd_api24-4k', self.run_check()['blocking_checks'])

    def test_external_data_partition_rejected(self):
        with self.config().open('a') as out: out.write(f'disk.dataPartition.path={self.sdk}/userdata.img\n')
        self.assertIn('avd_api24-4k', self.run_check()['blocking_checks'])

    def test_duplicate_properties_with_whitespace_rejected(self):
        with self.config().open('a') as out: out.write(' abi.type = arm64-v8a\n')
        self.assertIn('avd_api24-4k', self.run_check()['blocking_checks'])

    def test_missing_kernel(self):
        next(self.sdk.glob('system-images/android-24/*/*/kernel-ranchu')).unlink()
        self.assertIn('avd_api24-4k', self.run_check()['blocking_checks'])

    def test_empty_system_image(self):
        next(self.sdk.glob('system-images/android-24/*/*/system.img')).write_bytes(b'')
        self.assertIn('avd_api24-4k', self.run_check()['blocking_checks'])

    def test_16k_tag_is_required(self):
        source = next(self.sdk.glob('system-images/android-35/*/*/source.properties'))
        self.mutate(source, 'google_apis,page_size_16kb', 'google_apis')
        self.assertIn('avd_arm64-16k', self.run_check()['blocking_checks'])

    def test_unreviewed_revision_rejected(self):
        source = next(self.sdk.glob('system-images/android-35/*/*/source.properties'))
        self.mutate(source, 'Pkg.Revision=5', 'Pkg.Revision=6')
        self.assertIn('avd_arm64-16k', self.run_check()['blocking_checks'])

    def test_wrong_target_rejected(self):
        locator = self.avd / (p.PROFILES['api24-4k'][2] + '.ini')
        self.mutate(locator, 'target=android-24', 'target=android-35')
        self.assertIn('avd_api24-4k', self.run_check()['blocking_checks'])

    def test_symlink_config_escape(self):
        config = self.config()
        outside = self.root / 'outside.ini'
        outside.write_bytes(config.read_bytes())
        config.unlink()
        config.symlink_to(outside)
        self.assertIn('avd_api24-4k', self.run_check()['blocking_checks'])

    def test_play_store_rejected(self):
        self.mutate(self.config(), 'PlayStore.enabled=false', 'PlayStore.enabled=true')
        self.assertIn('avd_api24-4k', self.run_check()['blocking_checks'])

    def test_whitespace_properties_supported(self):
        self.mutate(self.config(), 'abi.type=arm64-v8a', ' abi.type = arm64-v8a ')
        self.assertEqual(self.run_check()['blocking_checks'], [])


if __name__ == '__main__': unittest.main()
