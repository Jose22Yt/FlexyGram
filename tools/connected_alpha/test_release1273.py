"""Current native release identity and private delivery, beyond historical audits."""
import re,subprocess,unittest,yaml
from next_alpha_contract import ROOT,restore1272,RELEASE_PATHS
class Release1273(unittest.TestCase):
 def test_version_and_private_verifier_agree_without_identity_or_signing_changes(self):
  gradle=(ROOT/'TMessagesProj/build.gradle').read_text()
  self.assertEqual(re.search(r'def verCode = (\d+)',gradle)[1],'1273')
  old=subprocess.check_output(['git','show','8619ba40fbd8fd9d9d898ff307fb0c0716661254:TMessagesProj/build.gradle'],cwd=ROOT,text=True)
  self.assertEqual(gradle.replace('def verCode = 1273','def verCode = 1272'),old)
  builder=(ROOT/'tools/connected_alpha/build_private_apk.py').read_text()
  self.assertIn('FlexyGram_Alpha_1273_ARM64_TEST.apk',builder)
  self.assertIn("'--expected-version-code','1273'",builder)
  self.assertIn("CERT='c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c'",builder)
  self.assertIn("APP='io.github.jose22yt.flexygram.alpha'",builder)
  self.assertIn("report['elf_count']!=96",builder)
  self.assertIn('PRIVATE_DIRECT_SIGNED_APK',builder)
  for path in RELEASE_PATHS:
   data=(ROOT/path).read_bytes()
   restored=restore1272(path,data)
   self.assertEqual(restored,subprocess.check_output(['git','show','8619ba40fbd8fd9d9d898ff307fb0c0716661254:'+path],cwd=ROOT))
   with self.assertRaises(ValueError):restore1272(path,data+b'\nUNREVIEWED\n')
 def test_full_build_remains_guarded_and_plaintext_apk_is_never_uploaded(self):
  workflow=(ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text()
  self.assertIn('--expected-version-code 1273',workflow)
  jobs=yaml.safe_load(workflow)['jobs']
  self.assertEqual(jobs['build-arm64']['needs'],['source-checks','credentials-present'])
  self.assertIn("needs.credentials-present.outputs.ready == 'true'",jobs['build-arm64']['if'])
  build=jobs['build-arm64']['steps']
  self.assertFalse(any('upload-artifact' in step.get('uses','') for step in build))
  self.assertTrue(any(step.get('if')=='always()' and 'rm -f' in step.get('run','') for step in build))
  entry=yaml.safe_load((ROOT/'.github/workflows/pr.yml').read_text())['jobs']['connected-alpha-native']
  self.assertIn("github.event_name == 'push'",entry['if'])
  self.assertIn("refs/heads/integration/connected-alpha-1273-signature",entry['if'])
  self.assertEqual(entry['uses'],'./.github/workflows/connected-alpha-arm64.yml')
 def test_real_workflow_report_enforces_payload_and_pin_without_exposing_extra_fields(self):
  import json,os,sys,tempfile
  from pathlib import Path
  workflow=yaml.safe_load((ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text())
  step=next(s for s in workflow['jobs']['build-arm64']['steps'] if s.get('name')=='Verify APK against independently authorized certificate')
  script=step['run'].split("python3 - <<'PY'\n",1)[1].split('\nPY',1)[0]
  base=dict(sha256='0'*64,application_id='io.github.jose22yt.flexygram.alpha',version_code=1273,elf_count=96,bytes=1,certificate_sha256='c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c',elfs=['PRIVATE_DECOY_FIELD'])
  with tempfile.TemporaryDirectory() as d:
   env=dict(os.environ,COMMIT_ID='isolated-source-test',GITHUB_STEP_SUMMARY=str(Path(d)/'summary'))
   def execute(data):
    (Path(d)/'connected-alpha-verification.json').write_text(json.dumps(data))
    return subprocess.run([sys.executable,'-c',script],cwd=d,env=env,capture_output=True,text=True)
   result=execute(base);self.assertEqual(result.returncode,0,result.stderr)
   report=json.loads(result.stdout.removeprefix('PUBLIC_APK_VERIFICATION '))
   self.assertEqual(set(report),{'commit','sha256','application_id','version_code','elf_count','bytes'})
   self.assertNotIn('PRIVATE_DECOY_FIELD',result.stdout)
   for count in [0,95,97]:self.assertNotEqual(execute(dict(base,elf_count=count)).returncode,0)
   self.assertNotEqual(execute(dict(base,certificate_sha256='0'*64)).returncode,0)
