"""Synthetic regressions: no ELF load, network, real account or application execution."""
from pathlib import Path
import copy,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/native_compatibility'))
from acceptance import candidate_contract,artifact_acceptance

def row():
 return dict(machine='EM_AARCH64',path='synthetic.so',soname='synthetic.so',load_4k=True,load_16k=True,
             android_note_api=24,exports=[('synthetic_api',None)],needed=['libc.so'],relro=[],
             missing_needed_api24=[],strong_unresolved_api24=[],version_provider_mismatches_api24=[],strong_outside_needed_closure=[])
class AcceptanceTests(unittest.TestCase):
 def test_clean_contract_is_not_permission_to_replace_or_distribute(self):
  result=candidate_contract(row(),row());self.assertTrue(result['static_contract_pass']);self.assertTrue(result['runtime_required']);self.assertFalse(result['replacement_approved'])
 def test_aligning_does_not_excuse_loss_of_exports_or_versions(self):
  for symbols in [[],[('synthetic_api','NEW_VERSION')]]:
   after=row();after['exports']=symbols
   self.assertIn('export_contract_loss',candidate_contract(row(),after)['blockers'])
 def test_api_soname_machine_and_new_dependencies_are_fail_closed(self):
  for key,value,code in [('android_note_api',None,'api24_provenance_missing_or_newer'),('android_note_api',27,'api24_provenance_missing_or_newer'),('soname','changed.so','soname_changed'),('machine','EM_X86_64','wrong_machine'),('needed',['new_dependency.so'],'new_needed_requires_review')]:
   after=row();after[key]=value;self.assertIn(code,candidate_contract(row(),after)['blockers'])
 def test_4k_library_blocks_even_without_symbol_failures(self):
  after=row();after['load_16k']=False
  result=artifact_acceptance({'libraries':[after]});self.assertEqual(result['status'],'STATIC_BLOCKED');self.assertFalse(result['distribution_allowed'])
 def test_global_symbols_and_writable_relro_overlap_require_review(self):
  after=row();after['strong_outside_needed_closure']=[{'name':'synthetic_global'}]
  after['relro']=[{'writable_sections_in_roundup':['.synthetic']}]
  codes={b['code'] for b in artifact_acceptance({'libraries':[after]})['blockers']}
  self.assertEqual(codes,{'global_symbol_runtime_validation','relro_writable_overlap'})
 def test_empty_target_is_not_clean_and_other_architecture_is_not_hidden(self):
  after=row();after['machine']='EM_X86_64'
  result=artifact_acceptance({'libraries':[after]});self.assertEqual(result['non_target_payloads'],1);self.assertIn('no_arm64_elf',[b['code'] for b in result['blockers']])
if __name__=='__main__':unittest.main()
