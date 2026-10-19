"""Offline source feasibility fixtures, not production/Android/linguistic parity."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,unittest,zipfile,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/translation_safety'))
from artifact_gate import scan
BASE='26f5c9fc03924fafcf3246b78b48946d09fba69d'
def run(args):
 r=subprocess.run(args,capture_output=True,text=True)
 if r.returncode:raise AssertionError(r.stdout+r.stderr)
 return r.stdout
class PrototypeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.out=Path(cls.temp.name)
  cls.jar=Path(os.environ['TRANSLATOR_CLASSES_JAR']);cls.gson=Path(os.environ['GSON_JAR'])
  assert hashlib.sha256(cls.jar.read_bytes()).hexdigest()==json.loads((ROOT/'docs/security-p03e/evidence/binary-provenance.json').read_text())['classes_jar_sha256']
  cls.cp=os.pathsep.join(map(str,[cls.out,cls.jar,cls.gson]))
  run(['javac','-cp',cls.cp,'-d',str(cls.out)]+list(map(str,(Path(__file__).parent/'java').rglob('*.java'))))
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def case(self,name,*args):
  result=run(['java','-cp',self.cp,'ParityHarness',name,*args]);self.assertNotIn('SYNTHETIC_PRIVATE',result)
 def test_actual_base_pipeline_and_result_contract(self):self.case('base')
 def test_frozen_inventory_regenerates_without_dropping_numeric_regions(self):
  from binary_inventory import languages
  actual=languages(self.jar)
  self.assertEqual(actual,json.loads((ROOT/'docs/security-p03e/evidence/language-inventory.json').read_text()))
  self.assertTrue(any(any(ch.isdigit() for ch in value) for row in actual.values() for value in row['constructor_languages']))
 def test_all_frozen_language_entries(self):
  d=json.loads((ROOT/'docs/security-p03e/evidence/language-inventory.json').read_text());self.case('languages',*[','.join(d[n]['constructor_languages']) for n in ['MicrosoftTranslator','DeepLTranslator']])
 def test_observed_normalization_pipeline(self):self.case('normalization')
 def test_wrapper_chinese_aliases(self):self.case('aliases')
 def test_text_html_unicode_passthrough_fixture(self):self.case('format')
 def test_explicit_formality_capabilities(self):self.case('formality')
 def test_errors_no_private_causes_or_provider_switch(self):self.case('errors')
 def test_pre_inflight_and_exception_cancellation(self):self.case('cancel')
 def test_invalid_config_never_invokes_transport(self):self.case('invalid')
 def test_prototype_jar_scans_clean_without_legacy_dependency(self):
  jar=self.out/'prototype.jar'
  with zipfile.ZipFile(jar,'w') as z:
   for f in (self.out/'lab').rglob('*.class'):z.write(f,str(f.relative_to(self.out)))
  registry=json.loads((ROOT/'tests/translation_safety/retired_fingerprints.json').read_text());result=scan(jar.read_bytes(),registry)
  self.assertTrue(result['passed']);self.assertTrue(result['complete'])
  if os.environ.get('PROTOTYPE_EVIDENCE_DIR'):
   Path(os.environ['PROTOTYPE_EVIDENCE_DIR'],'prototype-jar-scan.json').write_text(json.dumps(result,indent=2)+'\n')
 def test_production_and_all_previous_security_files_unchanged(self):
  changed=run(['git','diff',BASE,'--name-only']).splitlines()
  self.assertTrue(all(p.startswith(('docs/security-p03e/','tests/translation_dependency/')) for p in changed),changed)
  source=(ROOT/'tests/translation_dependency/java/lab/flexygram/translation/PrototypeAdapter.java').read_text()
  for forbidden in ['java.net','okhttp','http://','https://','getInstance','System.getenv']:self.assertNotIn(forbidden,source)
if __name__=='__main__':unittest.main()
