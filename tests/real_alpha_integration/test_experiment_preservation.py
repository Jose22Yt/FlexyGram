"""Regression: the 16 KB build overlay must retain the combined source gate."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('prepare_experiment', ROOT / 'tools/native_compatibility/prepare_experiment.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ExperimentPreservationTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / 'TMessagesProj/build.gradle').read_text()

    def test_real_build_retains_all_following_safety_controls(self):
        marker = '// Independent, opt-in source overlay;'
        suffix = self.source[self.source.index(marker):]
        replacement = '// fixture Python verifier\n'
        result = module.replace_python_preparation(self.source, replacement)
        self.assertTrue(result.endswith(suffix))
        self.assertIn("tasks.named('preBuild').configure { dependsOn verifyCombinedRealAlphaSources }", result)
        self.assertIn('apply from: rootProject.file("gradle/real-alpha-offline-ui.gradle")', result)
        self.assertEqual(result.count(replacement), 1)
        self.assertNotIn("tasks.register('prepareLockedPython', Exec)", result)
        self.assertEqual(result[:result.index(replacement)], self.source[:self.source.index('// P0.4c: pip resolves exclusively')])

    def test_changed_or_ambiguous_task_wiring_fails_closed(self):
        for text in (self.source.replace('task.dependsOn(prepareLockedPython)', 'task.dependsOn(other)'),
                     self.source + '\n// P0.4c: pip resolves exclusively'):
            with self.subTest(text=text[-60:]), self.assertRaises(ValueError):
                module.replace_python_preparation(text, '// fixture\n')

if __name__ == '__main__':
    unittest.main()
