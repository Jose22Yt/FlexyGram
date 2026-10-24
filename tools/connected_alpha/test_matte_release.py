"""Only explicit version/delivery changes on top of approved PR79; no UI regressions."""
from pathlib import Path
import subprocess
import unittest
import yaml
ROOT=Path(__file__).resolve().parents[2]
BASE='8536b63d736399a56b6b4ab418bfdbe4e9096176'
STEP='''      - name: Verify native Signature Matte cell geometry and accessibility
        run: python3 tools/connected_alpha/matte_visual/run.py --sdk-root "$ANDROID_HOME"
'''
def restore_delivery_workflow(s):
    s = s.replace('--expected-version-code 1270','--expected-version-code 1269').replace('FlexyGram-Alpha1270-Encrypted','FlexyGram-Signature-Matte-1269-ARM64-encrypted').replace('FlexyGram-Alpha1270-ARM64.tar.age','FlexyGram-Signature-Matte-1269-arm64.tar.age').replace('      - name: Verify native iOS bubble paths, glass and saved preference policy\n        run: python3 tools/connected_alpha/bubble_visual/run.py --sdk-root "$ANDROID_HOME"\n','')
    return s.replace('--expected-version-code 1269','--expected-version-code 1267').replace('FlexyGram-Signature-Matte-1269-ARM64-encrypted','FlexyGram-Integrated-Signature-1267-ARM64-encrypted').replace('FlexyGram-Signature-Matte-1269-arm64.tar.age','FlexyGram-Alpha-arm64.tar.age').replace(STEP,'').replace('          retention-days: 7\n          if-no-files-found: error','          retention-days: 1\n          if-no-files-found: error')
class MatteReleaseTests(unittest.TestCase):
    def test_only_reviewed_build_metadata_changes_from_pr79(self):
        allowed={'TMessagesProj/build.gradle','.github/workflows/pr.yml','.github/workflows/connected-alpha-arm64.yml','tools/connected_alpha/test_signature_home.py','tools/connected_alpha/test_signature_matte.py','tools/connected_alpha/test_matte_release.py','tools/connected_alpha/test_signature_custom.py'}
        from release_1270_contract import PATHS
        allowed.update(PATHS)
        changes=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
        self.assertTrue(set(changes)<=allowed,set(changes)-allowed)
        previous=subprocess.check_output(['git','show',BASE+':.github/workflows/connected-alpha-arm64.yml'],cwd=ROOT,text=True)
        self.assertEqual(restore_delivery_workflow((ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text()),previous)
    def test_native_entry_and_version_1270_are_consistent(self):
        workflow=yaml.safe_load((ROOT/'.github/workflows/pr.yml').read_text())
        events=workflow.get('on',workflow.get(True))
        self.assertIn('fix/alpha2-signature-matte-build',events['push']['branches'])
        self.assertIn("refs/heads/fix/alpha2-signature-matte-build",workflow['jobs']['connected-alpha-native']['if'])
        gradle=(ROOT/'TMessagesProj/build.gradle').read_text()
        self.assertIn('def verCode = 1270',gradle)
        self.assertIn("versionNameSuffix = '-alpha2-ios-glass-home2'",gradle)
        build=yaml.safe_load((ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text())
        runs='\n'.join(s.get('run','') for s in build['jobs']['build-arm64']['steps'])
        self.assertIn('--expected-version-code 1270',runs)
        self.assertIn(':TMessagesProj:assembleConnectedAlpha',runs)
        self.assertNotIn('NATIVE_TARGET=SKIP',runs)
if __name__=='__main__':unittest.main()
