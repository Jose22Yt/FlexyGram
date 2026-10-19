"""Frozen P0.3g source boundary. Never regenerates approved hashes during tests."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
BASE='8ed92d59f8e2c379851e13d3c45f24d8a36f92df'
SNAPSHOT=Path(__file__).with_name('reviewed_changes.json')
import sys
sys.path.insert(0,str(ROOT/'tests/build_variants'))
from scope import reviewed_variant_change, assert_variant_scope

def reviewed_change(path,previous):
 rows=json.loads(SNAPSHOT.read_text())['files']
 if path not in rows:return False
 row=rows[path]
 actual=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
 old=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
 before=hashlib.sha256(old.stdout).hexdigest() if old.returncode==0 else None
 # Previous guard may compare an older revision, but reviewed before must match the actual merged base.
 return (actual==row['after'] and before==row['before'] and (previous==before or previous==row.get('historical_guard'))) or reviewed_variant_change(path,previous)

def assert_scope(test):
 assert_variant_scope(test)
 rows=json.loads(SNAPSHOT.read_text())['files']
 changed=subprocess.check_output(['git','diff',BASE,'--name-only'],cwd=ROOT,text=True).splitlines()
 for path in changed:
  if path.startswith(('tests/translation_dependency/','tests/translation_staging/','docs/security-p03g/')):continue
  if path in ['tests/translation_runtime/test_runtime_policy.py','tests/translation_safety/test_preparation.py','tests/translation_safety/inventory.py','tests/translation_safety/callsites.json','tests/translation_safety/preserved_sources.json']:continue
  if reviewed_variant_change(path):continue
  # Documentary history from approved P0.4a must remain identical to its merged base.
  if path.startswith('docs/security-p04a/'):
   test.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show','d9f2b788cf23e830e84ba24e9f6cb2e71e13bd4d:'+path],cwd=ROOT));continue
  if path.startswith(('docs/security-p04b/','tests/build_variants/')):continue
  test.assertIn(path,rows,'Unexpected production or historical evidence change')
  test.assertTrue(reviewed_change(path,rows[path]['before']),path)
 # Freeze every integrated source, including newly added module files not yet in the index.
 for path,row in rows.items():
  test.assertTrue(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==row['after'] or reviewed_variant_change(path,row['after']),path)
