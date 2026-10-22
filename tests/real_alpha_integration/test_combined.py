"""Synthetic-host regression gate; requires Python only, no Android SDK."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[2] / 'tools/real_alpha_integration/check_combined.py'
spec = importlib.util.spec_from_file_location('combined_gate', MODULE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def digest(data): return hashlib.sha256(data).hexdigest()

class CombinedGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.offline = {}
        self.alpha = {}
        self.generated = {}
        def put(p, contents):
            target = self.root / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(contents)
            return digest(contents)
        for p in gate.EXPECTED_OFFLINE:
            original, overlay = ('original:' + p).encode(), ('offline:' + p).encode()
            self.offline[p] = {'original_sha256': put(gate.MAIN_ROOT / p, original),
                               'overlay_sha256': put(gate.OFFLINE_ROOT / p, overlay)}
        for p in gate.EXPECTED_ALPHA:
            self.alpha[p] = put(gate.ALPHA_ROOT / p, ('realalpha:' + p).encode())
            self.generated[p] = put(gate.LOCAL_ROOT / 'realAlpha' / p, ('generated:' + p).encode())
        self.login_source = gate.MAIN_ROOT / 'org/telegram/ui/LoginActivity.java'
        self.login_output = gate.LOCAL_ROOT / 'java/org/telegram/ui/LoginActivity.java'
        self.login_orig = put(self.login_source, b'original login')
        self.login_generated = put(self.login_output, b'generated login')
        self.patch = gate.OFFLINE_PATCH
        patch_sha = put(self.patch, b'fake pinned patch')
        self.local_patch = Path('patches/native-login-pages/prereq.patch')
        prereq = put(self.local_patch, b'fake pinned login patch')
        self.offline_inv = Path('tools/real_alpha_offline_ui/sources.json')
        self.login_inv = Path('patches/native-login-pages/inventory.json')
        self.save(self.offline_inv, {'sources': self.offline, 'patch_sha256': patch_sha})
        self.save(Path('tools/real_alpha_local_login/originals.json'), self.alpha)
        self.save(Path('tools/real_alpha_local_login/generated.json'), self.generated)
        self.save(self.login_inv, {'target_sha256': self.login_orig,
            'overlay_sha256': self.login_generated, 'prerequisites': {self.local_patch.as_posix(): prereq}})
        main_gradle = """sourceSets.main.java.exclude('org/telegram/ui/LoginActivity.java')
rootProject.file('build/generated/flexygram-local-login/realAlpha')
file('src/realAlphaLocalLogin/java')
sourceSets.realAlpha.java.setSrcDirs(
if (localLoginPagesEnabled && startupDiagnosticsEnabled)
if (localLoginPagesEnabled && !(flavor == 'realAlpha' && builder.buildType == 'debug'))
apply from: rootProject.file("gradle/real-alpha-offline-ui.gradle")
if (localLoginPagesEnabled && providers.gradleProperty('flexygramOfflineDialogsUi').orNull == 'true')
tasks.register('verifyCombinedRealAlphaSources', Exec)
tasks.named('preBuild').configure { dependsOn verifyCombinedRealAlphaSources }"""
        overlay_gradle = """providers.gradleProperty('flexygramOfflineDialogsUi').orNull == 'true'
providers.gradleProperty('flexygramRealAlpha').orNull != 'true'
providers.gradleProperty('flexygramRealAlphaStartupDiagnostics').orNull == 'true'
android.sourceSets.main.java.exclude(path)
android.sourceSets.realAlpha.java.srcDir(overlayRoot)
android.sourceSets.realAlpha.res.srcDir(
if (flavor != 'realAlpha' || builder.buildType != 'debug')"""
        put(Path('gradle/real-alpha.json'), json.dumps({
            'applicationId': 'io.github.jose22yt.flexygram.realalpha', 'isolated': True,
            'capabilities': {c: False for c in ('authentication','telegramTransport','push',
                'translation','plugins','sessionRestore')}
        }).encode())
        put(Path('TMessagesProj/src/realAlpha/AndroidManifest.xml'), b'''<manifest
            xmlns:android="http://schemas.android.com/apk/res/android"
            xmlns:tools="http://schemas.android.com/tools">
            <uses-permission android:name="android.permission.INTERNET" tools:node="remove" />
            <application android:usesCleartextTraffic="false">
                <activity android:name="org.telegram.ui.realalpha.RealAlphaActivity" android:exported="true" />
            </application>
        </manifest>''')
        put(Path('TMessagesProj/build.gradle'), main_gradle.encode())
        put(Path('gradle/real-alpha-offline-ui.gradle'), overlay_gradle.encode())

    def tearDown(self): self.tmp.cleanup()
    def save(self, p, value):
        (self.root / p).parent.mkdir(parents=True, exist_ok=True)
        (self.root / p).write_text(json.dumps(value))

    def test_full_handoff_passes_with_explicit_non_android_receipt(self):
        receipt = gate.inspect(self.root)
        self.assertEqual(receipt['result'], 'PASS')
        self.assertEqual(receipt['checked_generated_java'], 7)
        self.assertFalse(receipt['android_compiled'])
        self.assertFalse(receipt['signed'])

    def test_static_mode_does_not_require_materialized_outputs(self):
        (self.root / self.login_output).unlink()
        self.assertEqual(gate.inspect(self.root, generated=False)['checked_generated_java'], 0)
        with self.assertRaisesRegex(gate.PreflightError, 'MISSING_FILE'):
            gate.inspect(self.root)

    def test_rejects_stale_original_even_when_outputs_are_valid(self):
        (self.root / self.login_source).write_text('changed')
        with self.assertRaisesRegex(gate.PreflightError, 'SHA256_MISMATCH'):
            gate.inspect(self.root)

    def test_rejects_stale_generated_overlay(self):
        (self.root / self.login_output).write_text('changed')
        with self.assertRaisesRegex(gate.PreflightError, 'SHA256_MISMATCH'):
            gate.inspect(self.root)

    def test_rejects_unexpected_generated_java(self):
        p = self.root / gate.OFFLINE_ROOT / 'Unexpected.java'
        p.write_text('extra')
        with self.assertRaisesRegex(gate.PreflightError, 'GENERATED_SOURCE_INVENTORY_CHANGED'):
            gate.inspect(self.root)

    def test_rejects_symlink_generated_source(self):
        path = self.root / self.login_output
        target = self.root / 'another-file'
        target.write_bytes(path.read_bytes())
        path.unlink(); path.symlink_to(target)
        with self.assertRaisesRegex(gate.PreflightError, 'SYMLINK'):
            gate.inspect(self.root)

    def test_rejects_mutated_offline_patch(self):
        (self.root / self.patch).write_text('changed')
        with self.assertRaisesRegex(gate.PreflightError, 'SHA256_MISMATCH'):
            gate.inspect(self.root)

    def test_rejects_missing_variant_guard(self):
        path = self.root / 'gradle/real-alpha-offline-ui.gradle'
        path.write_text(path.read_text().replace("if (flavor != 'realAlpha' || builder.buildType != 'debug')", ''))
        with self.assertRaisesRegex(gate.PreflightError, 'MISSING_OFFLINE_GRADLE_GUARD'):
            gate.inspect(self.root)

    def test_rejects_removed_automatic_combined_gate(self):
        path = self.root / 'TMessagesProj/build.gradle'
        path.write_text(path.read_text().replace("tasks.register('verifyCombinedRealAlphaSources', Exec)", ''))
        with self.assertRaisesRegex(gate.PreflightError, 'MISSING_LOCAL_LOGIN_GRADLE_GUARD'):
            gate.inspect(self.root)

    def test_rejects_network_permission_reintroduction(self):
        path = self.root / 'TMessagesProj/src/realAlpha/AndroidManifest.xml'
        path.write_text(path.read_text().replace('tools:node="remove"', 'tools:node="merge"'))
        with self.assertRaisesRegex(gate.PreflightError, 'REALALPHA_INTERNET_PERMISSION_NOT_REMOVED'):
            gate.inspect(self.root)

    def test_rejects_online_capability_reintroduction(self):
        path = self.root / 'gradle/real-alpha.json'
        policy = json.loads(path.read_text())
        policy['capabilities']['authentication'] = True
        path.write_text(json.dumps(policy))
        with self.assertRaisesRegex(gate.PreflightError, 'REALALPHA_ISOLATION_POLICY_CHANGED'):
            gate.inspect(self.root)

    def test_rejects_malicious_inventory_expansion(self):
        d = json.loads((self.root / self.offline_inv).read_text())
        d['sources']['../../Unexpected.java'] = {}
        self.save(self.offline_inv, d)
        with self.assertRaisesRegex(gate.PreflightError, 'OFFLINE_SOURCE_INVENTORY_CHANGED'):
            gate.inspect(self.root)

    def test_rejects_untrusted_login_patch_path(self):
        d = json.loads((self.root / self.login_inv).read_text())
        d['prerequisites'] = {'../../tmp/outside.patch': 'x'}
        self.save(self.login_inv, d)
        with self.assertRaisesRegex(gate.PreflightError, 'UNSAFE_PATCH_REFERENCE'):
            gate.inspect(self.root)

if __name__ == '__main__': unittest.main()
