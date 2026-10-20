from pathlib import Path
from io import BytesIO
import hashlib,json,sys,tempfile,unittest,zipfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/native_compatibility'))
from compat_relink import version_map,link_args,BOUNDARIES
from experimental_wheels import record,repack,verify
from prepare_experiment import overlay,unsigned_diagnostic
from experiment_recipe import plugin_default
from abi_report import compare
class ExperimentalTests(unittest.TestCase):
 def test_version_nodes_are_explicit_and_functions_preserved(self):
  s='LIB_TEST {\n global:\n function_one;\n local: *;\n};'
  self.assertEqual(version_map(s,['LIB_TEST']),s.replace('global:','global:\n  LIB_TEST;'))
 def test_unknown_or_ambiguous_version_node_is_rejected(self):
  for s in ['OTHER { global: f; };','NODE { global: f; }; NODE { global: g; };']:
   with self.assertRaises(ValueError):version_map(s,['NODE'])
 def test_link_preserves_objects_and_limits_as_needed_to_zlib(self):
  a=link_args('clang -shared a.o b.a -lxml2 -lz -lm -o .libs/lib.so',Path('/compat.o'),Path('/compat.ld'),True)
  self.assertEqual(a[a.index('-lz')-1:a.index('-lz')+2],['-Wl,--as-needed','-lz','-Wl,--no-as-needed'])
  for x in ['a.o','b.a','-lxml2','-lm']:self.assertIn(x,a)
 def test_unexpected_link_shape_is_rejected(self):
  for s in ['clang a.o -o executable','clang -shared a.o -o lib.so','clang -shared -lz -lz -o lib.so']:
   with self.assertRaises(ValueError):link_args(s,Path('/o'),Path('/s'),True)
 def test_boundary_values_follow_new_layout_not_original_addresses(self):
  self.assertEqual(BOUNDARIES['_edata'],'ADDR(.data)+SIZEOF(.data)')
  self.assertEqual(BOUNDARIES['_end'],'ADDR(.bss)+SIZEOF(.bss)')
 def test_record_uses_content_hashes_and_empty_self_record(self):
  r=record({'a':b'FAKE','x.dist-info/RECORD':b'OLD'})
  self.assertIn(b'a,sha256=',r);self.assertIn(b'x.dist-info/RECORD,,\n',r);self.assertNotIn(b'OLD',r)
 def wheel(self):
  b=BytesIO()
  with zipfile.ZipFile(b,'w') as z:
   z.writestr('chaquopy/lib/libfake.so',b'ORIGINAL');z.writestr('p.dist-info/WHEEL','Wheel-Version: 1.0\nBuild: 2\nTag: py3-none-any\n')
   z.writestr('p.dist-info/METADATA','Name: p\nVersion: 1\n');z.writestr('p.dist-info/RECORD','')
  return b.getvalue()
 def test_wheel_bytes_are_deterministic_and_metadata_retained(self):
  with patch('experimental_wheels.elf',return_value={}),patch('experimental_wheels.candidate_contract',return_value={'static_contract_pass':True}):
   a=repack(self.wheel(),{'chaquopy/lib/libfake.so':b'CANDIDATE'});b=repack(self.wheel(),{'chaquopy/lib/libfake.so':b'CANDIDATE'})
  self.assertEqual(a,b)
  with zipfile.ZipFile(BytesIO(a)) as z:
   self.assertEqual(z.read('p.dist-info/METADATA'),b'Name: p\nVersion: 1\n');self.assertIn(b'Build: 3flexygram16k',z.read('p.dist-info/WHEEL'))
   self.assertEqual(z.read('chaquopy/lib/libfake.so'),b'CANDIDATE')
 def test_wheel_rejects_abi_loss(self):
  with patch('experimental_wheels.elf',return_value={}),patch('experimental_wheels.candidate_contract',return_value={'static_contract_pass':False}):
   with self.assertRaises(ValueError):repack(self.wheel(),{'chaquopy/lib/libfake.so':b'CANDIDATE'})
 def test_wheel_rejects_unlisted_library(self):
  with self.assertRaises(ValueError):repack(self.wheel(),{'secret.so':b'FAKE'})
 def test_experimental_wheelhouse_refuses_extra_file_or_symlink(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'p.whl';p.write_bytes(self.wheel());m={'wheels':[{'filename':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}
   self.assertEqual(verify(m,root),1);(root/'extra').write_text('FAKE')
   with self.assertRaises(ValueError):verify(m,root)
   (root/'extra').unlink();data=p.read_bytes();p.unlink();outside=root.parent/'synthetic-experimental-whl';outside.write_bytes(data)
   try:
    p.symlink_to(outside)
    with self.assertRaises(ValueError):verify(m,root)
   finally:outside.unlink()
 def test_unsigned_overlay_removes_only_diagnostic_assignment(self):
  text='before\nsigningConfig = signingConfigs.diagnosticLab\nafter'
  result=unsigned_diagnostic(text)
  self.assertNotIn('signingConfig =',result)
  self.assertNotIn('signingConfigs.diagnosticLab',result)
  self.assertTrue(result.startswith('before\n'));self.assertTrue(result.endswith('\nafter'))
 def test_unsigned_overlay_rejects_missing_or_duplicate_assignment(self):
  for text in ['', 'signingConfig = signingConfigs.diagnosticLab\n'*2]:
   with self.assertRaises(ValueError):unsigned_diagnostic(text)
 def test_overlay_rejects_modifying_source_checkout(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   with self.assertRaises(ValueError):overlay(root,root,root,root,root)
 def test_overlay_rejects_changed_disposable_build_file(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=root/'a';b=root/'b'
   for x in [a,b]:(x/'TMessagesProj').mkdir(parents=True)
   (a/'TMessagesProj/build.gradle').write_text('approved');(b/'TMessagesProj/build.gradle').write_text('unexpected')
   with self.assertRaises(ValueError):overlay(a,b,root,root,root)
 def abi_mutation(self,mutation):
  baseline={'symbols':{'operation':{'type':'STT_OBJECT','size':8,'bind':'STB_GLOBAL'}},'version_definitions':{'V2':{'parents':['V1'],'flags':0,'hash':17}},'hash_sections':['.gnu.hash']}
  import copy
  changed=copy.deepcopy(baseline);mutation(changed)
  with patch('abi_report.detail',side_effect=[baseline,changed]),patch('abi_report.elf',return_value={}),patch('abi_report.candidate_contract',return_value={'static_contract_pass':True}):
   self.assertFalse(compare(b'OLD',b'NEW','synthetic.so')['static_abi_pass'])
 def test_lost_gnu_parent_chain_is_not_accepted(self):
  self.abi_mutation(lambda x:x['version_definitions']['V2'].update(parents=[]))
 def test_changed_exported_data_size_is_not_accepted(self):
  self.abi_mutation(lambda x:x['symbols']['operation'].update(size=4))
 def test_changed_symbol_type_is_not_accepted(self):
  self.abi_mutation(lambda x:x['symbols']['operation'].update(type='STT_FUNC'))
 def test_changed_version_flags_are_not_accepted(self):
  self.abi_mutation(lambda x:x['version_definitions']['V2'].update(flags=2))
 def test_original_default_plugin_path_is_retained(self):
  self.assertEqual(plugin_default(b'\0/synthetic/original/libxslt-plugins\0'),'/synthetic/original/libxslt-plugins')
 def test_ambiguous_or_missing_plugin_default_is_rejected(self):
  for data in [b'NONE',b'\0/one/libxslt-plugins\0/two/libxslt-plugins\0']:
   with self.assertRaises(ValueError):plugin_default(data)
 def test_wheelhouse_directory_named_like_wheel_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'p.whl').mkdir()
   with self.assertRaises(ValueError):verify({'wheels':[{'filename':'p.whl','sha256':'0'*64}]},p)
 def test_rebuilt_wheel_metadata_targets_api24(self):
  original=BytesIO()
  with zipfile.ZipFile(BytesIO(self.wheel())) as source,zipfile.ZipFile(original,'w') as z:
   for n in source.namelist():
    data=source.read(n)
    if n.endswith('/WHEEL'):data=data.replace(b'py3-none-any',b'py3-none-android_21_arm64_v8a')
    z.writestr(n,data)
  with patch('experimental_wheels.elf',return_value={}),patch('experimental_wheels.candidate_contract',return_value={'static_contract_pass':True}):
   result=repack(original.getvalue(),{'chaquopy/lib/libfake.so':b'NEW'})
  with zipfile.ZipFile(BytesIO(result)) as z:
   text=z.read('p.dist-info/WHEEL');self.assertIn(b'android_24_arm64_v8a',text);self.assertNotIn(b'android_21_arm64_v8a',text)
if __name__=='__main__':unittest.main()
