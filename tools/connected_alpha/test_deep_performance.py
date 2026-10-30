"""P0 behavioral/operation regression probes; deliberately no physical performance claims."""
import importlib.util
import json
import subprocess
import unittest
import deep_performance_contract as audit


class DeepPerformance(unittest.TestCase):
    def test_baseline_and_candidate_production_probes(self):
        path = audit.ROOT/'tools/deep_performance/run_probes.py'
        spec = importlib.util.spec_from_file_location('deep_probes', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.run()
        actual = json.loads((audit.ROOT/'build/deep-performance/probe-results.json').read_text())
        expected = json.loads((audit.ROOT/'tools/deep_performance/operation-results.json').read_text())
        self.assertEqual(expected, actual)

    def test_reviewed_scope_and_unknown_mutation_rejection(self):
        audit.verify_current()
        for name in audit.spec()['reviewed']:
            data = (audit.ROOT/name).read_bytes()
            self.assertEqual(audit.original(name), audit.restore(name, data), name)
            self.assertEqual(data+b'UNKNOWN', audit.restore(name, data+b'UNKNOWN'), name)

    def test_identity_protocol_storage_and_work1_design_frozen(self):
        frozen = ['config/signing', 'gradle', 'TMessagesProj/build.gradle', '.github/workflows',
                  'TMessagesProj/src/main/AndroidManifest.xml','TMessagesProj/src/connectedAlpha',
                  'TMessagesProj/src/beta','TMessagesProj/jni','TMessagesProj/chaquopy',
                  'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleConfig.java',
                  'TMessagesProj/src/main/java/app/flexygram/bubbles/SignatureWallpaperBlur.java',
                  'TMessagesProj/src/main/java/app/flexygram/header',
                  'TMessagesProj/src/main/java/org/telegram/messenger',
                  'TMessagesProj/src/main/java/org/telegram/tgnet',
                  'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java',
                  'TMessagesProj/src/main/java/org/telegram/ui/Cells',
                  'TMessagesProj/src/main/res']
        self.assertEqual(b'', subprocess.check_output(['git','diff',audit.BASE,'--',*frozen],cwd=audit.ROOT))


if __name__ == '__main__':
    unittest.main()
