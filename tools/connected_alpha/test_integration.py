"""Concrete integration regressions: resource syntax, discovery and CI routing."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET

import yaml
from check_resources import A, APP, ROOT, check_resource_text, probe_manifest


class UnifiedIntegration(unittest.TestCase):
    def test_baseline_stray_text_rejected_and_current_values_clean(self):
        path = 'TMessagesProj/src/main/res/values/strings.xml'
        original = subprocess.check_output(['git', 'show', 'e5869928c812271f87489c7012978563716ebfc0:'+path], cwd=ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp)/'strings.xml'
            before.write_bytes(original)
            with self.assertRaisesRegex(ValueError, 'outside resource'):
                check_resource_text(before)
        for path in (ROOT/'TMessagesProj/src/main/res').glob('values*/*.xml'):
            with self.subTest(path=str(path.relative_to(ROOT))):
                check_resource_text(path)

    def test_resource_fix_does_not_change_any_displayed_string(self):
        path = 'TMessagesProj/src/main/res/values/strings.xml'
        before = subprocess.check_output(['git', 'show', 'e5869928c812271f87489c7012978563716ebfc0:'+path], cwd=ROOT)
        def strings(data):
            return {element.get('name'): ET.tostring(element, encoding='unicode').split('</string>')[0]
                    for element in ET.fromstring(data) if element.tag == 'string'}
        self.assertEqual(strings(before), strings((ROOT/path).read_bytes()))

    def test_root_discovery_includes_stability_cases(self):
        suite = unittest.TestLoader().discover(str(ROOT/'tools/connected_alpha'), pattern='test_*.py')
        def ids(tests):
            for test in tests:
                if isinstance(test, unittest.TestSuite):
                    yield from ids(test)
                else:
                    yield test.id()
        cases = set(ids(suite))
        self.assertIn('stability.test_stability.AttachmentConfiguration.test_overlay_exposes_saved_attachment_and_nested_media', cases)
        self.assertIn('stability.test_stability.DeviceCollector.test_both_page_sizes_leave_every_acceptance_pending', cases)

    def test_resource_probe_preserves_actual_provider_and_backup_contract(self):
        manifest = probe_manifest()
        app = manifest.find('application')
        self.assertEqual(manifest.get('package'), APP)
        self.assertEqual(app.get(A+'allowBackup'), 'false')
        self.assertEqual(app.get(A+'restoreAnyVersion'), 'false')
        provider = app.find('provider')
        self.assertEqual(provider.get(A+'authorities'), APP+'.provider')
        self.assertEqual(provider.get(A+'exported'), 'false')
        self.assertEqual(provider.get(A+'grantUriPermissions'), 'true')
        self.assertEqual(provider.find('meta-data').get(A+'resource'), '@xml/provider_paths')

    def test_unified_pr_routes_to_checks_without_legacy_debug_or_private_build(self):
        workflow = yaml.safe_load((ROOT/'.github/workflows/pr.yml').read_text())
        def enabled(job, event, head):
            # Evaluate only repository-owned boolean expressions used by these jobs.
            expression = workflow['jobs'][job]['if'].replace('&&', ' and ').replace('||', ' or ')
            expression = re.sub(r'!(?!=)', 'not ', expression)
            github = SimpleNamespace(event_name=event, head_ref=head, ref='refs/heads/'+head)
            return eval(expression, {'__builtins__': {}, 'startsWith': str.startswith}, {'github': github})
        for branch in ('integration/connected-alpha-unified', 'integration/connected-alpha-next'):
            with self.subTest(branch=branch):
                self.assertTrue(enabled('connected-alpha-static', 'pull_request', branch))
                self.assertFalse(enabled('build', 'pull_request', branch))
                self.assertFalse(enabled('connected-alpha-native', 'pull_request', branch))
        self.assertTrue(enabled('build', 'pull_request', 'unrelated/feature'))
        self.assertTrue(enabled('connected-alpha-native', 'push', 'support/connected-alpha-ci-20261022'))

    def test_both_source_jobs_run_complete_suite_and_real_resource_gate(self):
        for path, job in (('pr.yml', 'connected-alpha-static'), ('connected-alpha-arm64.yml', 'source-checks')):
            workflow = yaml.safe_load((ROOT/'.github/workflows'/path).read_text())
            runs = '\n'.join(step.get('run', '') for step in workflow['jobs'][job]['steps'])
            self.assertIn('python3 tools/connected_alpha/run_checks.py', runs)
            self.assertIn('python3 tools/connected_alpha/check_resources.py', runs)

    def test_source_jobs_fetch_pinned_media_before_plugin_alias_tests(self):
        for path, job in (('pr.yml', 'connected-alpha-static'), ('connected-alpha-arm64.yml', 'source-checks')):
            workflow = yaml.safe_load((ROOT/'.github/workflows'/path).read_text())
            runs = [step.get('run', '') for step in workflow['jobs'][job]['steps']]
            checkout = runs.index('git submodule update --init --depth 1 TMessagesProj_Modules/media')
            checks = runs.index('python3 tools/connected_alpha/run_checks.py')
            self.assertLess(checkout, checks)


if __name__ == '__main__':
    unittest.main()
