"""Combined exact-byte boundary; native/behavior suites execute actual integrated code."""
from pathlib import Path
import subprocess,unittest
import integration1279_contract as audit
ROOT=Path(__file__).resolve().parents[2]

class Integrated1279(unittest.TestCase):
    def test_full_review_and_every_unknown_mutation_is_rejected(self):
        audit.verify_current()
        for path in audit.spec()['reviewed']:
            raw=(ROOT/path).read_bytes()+b'\nUNREVIEWED_MUTATION'
            for scope in ('base','legacy','folders','previews','motion'):
                self.assertEqual(raw,audit.project(scope,path,raw),path)

    def test_previous_release_manifests_remain_byte_identical(self):
        for name in ('signature1278_review.json','stability1277_review.json'):
            path='tools/connected_alpha/'+name
            self.assertEqual(subprocess.check_output(['git','show',audit.BASE+':'+path],cwd=ROOT),(ROOT/path).read_bytes())

    def test_new_release_preserves_original_build_and_signing_gates(self):
        for path in ('TMessagesProj/build.gradle','.github/workflows/connected-alpha-arm64.yml','tools/connected_alpha/build_private_apk.py'):
            before=subprocess.check_output(['git','show',audit.BASE+':'+path],cwd=ROOT)
            from alpha1280_contract import restore
            current=restore(path,(ROOT/path).read_bytes())
            self.assertIn(b'1279',current)
            self.assertEqual(before,current.replace(b'1279',b'1278'),path)

if __name__=='__main__':unittest.main()
