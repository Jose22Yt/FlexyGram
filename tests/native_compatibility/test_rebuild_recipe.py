"""Source-rebuild safety fixtures only; the actual build is recorded separately."""
from pathlib import Path
import hashlib,json,os,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/native_compatibility'))
from rebuild_candidates import verify_archive,patch_callback,environment,rebuild
class RebuildRecipeTests(unittest.TestCase):
 def test_source_hash_and_symlink_are_verified_before_build(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source.tar';p.write_bytes(b'SYNTHETIC_SOURCE');good=hashlib.sha256(p.read_bytes()).hexdigest()
   verify_archive(p,good)
   with self.assertRaises(ValueError):verify_archive(p,'0'*64)
   link=Path(d)/'link';link.symlink_to(p)
   with self.assertRaises(ValueError):verify_archive(link,good)
 def test_symlink_root_is_rejected_before_build_or_ndk_access(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);target=root/'target';target.mkdir();link=root/'output';link.symlink_to(target,target_is_directory=True)
   with self.assertRaisesRegex(ValueError,'Symlink'):
    rebuild(root/'sources',link,root/'ndk',root/'cmake',root/'wheels',{})
   self.assertEqual(list(target.iterdir()),[])
 def test_callback_patch_is_exact_and_does_not_suppress_compiler_errors(self):
  old='static void synthetic(xmlChar * name ATTRIBUTE_UNUSED) {}'
  new=patch_callback(old);self.assertEqual(new,'static void synthetic(const xmlChar * name ATTRIBUTE_UNUSED) {}')
  for s in ['',old+old]:
   with self.assertRaises(ValueError):patch_callback(s)
 def test_cross_environment_excludes_host_include_and_library_leaks(self):
  with patch.dict(os.environ,{'CPATH':'SYNTHETIC_HOST','LIBRARY_PATH':'SYNTHETIC_HOST','BASH_ENV':'SYNTHETIC_HOST'}):
   result=environment(Path('/synthetic/ndk'),Path('/synthetic/prefix'))
   for key in ['CPATH','LIBRARY_PATH','BASH_ENV']:self.assertNotIn(key,result)
   self.assertIn('aarch64-linux-android24-clang',result['CC']);self.assertIn('common-page-size=16384',result['LDFLAGS'])
   self.assertEqual(os.environ['CPATH'],'SYNTHETIC_HOST')
 def test_original_wheel_hashes_are_preserved_not_relabelled_as_rebuilt(self):
  m=json.loads((ROOT/'tools/native_compatibility/rebuild-sources.json').read_text())
  lock=json.loads((ROOT/'TMessagesProj/python/wheels.lock.json').read_text());files={f['filename']:f for p in lock['packages'] for f in p['files']}
  self.assertEqual(sum(len(r['libraries']) for r in m['original_wheels']),4)
  for row in m['original_wheels']:
   self.assertEqual(row['sha256'],files[row['filename']]['sha256']);self.assertEqual(row['url'],files[row['filename']]['url'])
if __name__=='__main__':unittest.main()
