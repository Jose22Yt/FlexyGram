"""Offline synthetic regressions; neither Android execution nor provider access."""
from pathlib import Path
import hashlib,io,json,struct,sys,tempfile,unittest,zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/native_compatibility'))
from audit import elf,members,check_symbols
from wheelhouse import prepare,select

def fixture(align=16384,vaddr=0,relro=False,writable=False,machine=183):
    data=bytearray(4096);ident=b'\x7fELF'+bytes([2,1,1,0])+bytes(8)
    data[:64]=struct.pack('<16sHHIQQQIHHHHHH',ident,3,machine,1,0,64,512 if writable else 0,0,64,56,2 if relro else 1,64,3 if writable else 0,2 if writable else 0)
    data[64:120]=struct.pack('<IIQQQQQQ',1,6,0,vaddr,0,4096,8192,align)
    if relro:data[120:176]=struct.pack('<IIQQQQQQ',0x6474e552,4,256,vaddr+256,0,768,768,1)
    if writable:
        data[576:640]=struct.pack('<IIQQQQIIQQ',1,1,3,vaddr+1024,1024,64,0,0,8,0)
        names=b'\0.data\0.shstrtab\0';data[2048:2048+len(names)]=names
        data[640:704]=struct.pack('<IIQQQQIIQQ',7,3,0,0,2048,len(names),0,0,1,0)
    return bytes(data)
def provider(name,exports=(),needed=(),undefined=()):
    return dict(path=name,soname=name,exports=list(exports),needed=list(needed),undefined=list(undefined),machine='EM_AARCH64')
def symbol(name,version=None,library=None,weak=False):return dict(name=name,version=version,provider=library,weak=weak)
class NativeCompatibilityTests(unittest.TestCase):
    def test_4k_is_not_16k(self):
        r=elf(fixture(4096),'old.so');self.assertTrue(r['load_4k']);self.assertFalse(r['load_16k'])
    def test_16k_and_64k_are_supported_alignment(self):
        for size in [16384,65536]:self.assertTrue(elf(fixture(size),'aligned.so')['load_16k'])
    def test_offset_virtual_address_congruence_is_required(self):
        r=elf(fixture(vaddr=4096),'bad.so');self.assertFalse(r['load_4k']);self.assertFalse(r['load_16k'])
    def test_non_power_of_two_and_incongruent_declared_alignment_fail(self):
        self.assertFalse(elf(fixture(12288),'invalid.so')['load_4k'])
        self.assertFalse(elf(fixture(65536,vaddr=16384),'invalid.so')['load_16k'])
    def test_load_segment_cannot_exceed_file(self):
        self.assertFalse(elf(fixture()[:2048],'truncated.so')['load_4k'])
    def test_relro_advisory_is_not_a_load_alignment_failure(self):
        r=elf(fixture(relro=True),'advisory.so');self.assertTrue(r['load_16k']);self.assertFalse(r['relro'][0]['end_aligned_16k']);self.assertFalse(r['relro'][0]['writable_sections_in_roundup'])
    def test_writable_relro_overlap_is_distinct(self):
        r=elf(fixture(relro=True,writable=True),'overlap.so');self.assertEqual(r['relro'][0]['writable_sections_in_roundup'],['.data'])
    def test_nested_imy_payload_is_scanned(self):
        inner=io.BytesIO()
        with zipfile.ZipFile(inner,'w') as z:z.writestr('chaquopy/lib/libxml2.so',fixture(4096))
        outer=io.BytesIO()
        with zipfile.ZipFile(outer,'w') as z:z.writestr('assets/chaquopy/requirements-common.imy',inner.getvalue())
        rows=list(members(outer.getvalue(),'synthetic.apk'));self.assertEqual(len(rows),1);self.assertFalse(elf(*rows[0])['load_16k'])
    def test_foreign_machine_stays_visible(self):
        r=elf(fixture(machine=62),'attach_linux_amd64.so');self.assertEqual(r['machine'],'EM_X86_64');check_symbols([r],{});self.assertEqual(r['api24_audit'],'not_android_arm64')
    def test_symbol_versions_are_checked_against_named_provider(self):
        r=provider('app.so',needed=['libfoo.so'],undefined=[symbol('foo','V2','libfoo.so')]);check_symbols([r],{'libfoo.so':[provider('libfoo.so',[('foo','V1')])]})
        self.assertEqual(len(r['version_provider_mismatches_api24']),1);self.assertEqual(len(r['strong_unresolved_api24']),1)
    def test_symbols_outside_dependency_closure_are_not_silently_approved(self):
        r=provider('app.so',undefined=[symbol('python_global')]);other=provider('libpython.so',[('python_global',None)]);check_symbols([r,other],{})
        self.assertEqual(len(r['strong_outside_needed_closure']),1);self.assertFalse(r['strong_unresolved_api24'])
    def test_needed_closure_is_transitive_and_weak_symbols_are_not_hard_failures(self):
        r=provider('app.so',needed=['a.so'],undefined=[symbol('ok'),symbol('optional',weak=True)])
        a=provider('a.so',needed=['b.so']);b=provider('b.so',[('ok',None)]);check_symbols([r,a,b],{})
        self.assertFalse(r['strong_unresolved_api24']);self.assertFalse(r['strong_outside_needed_closure']);self.assertEqual(len(r['weak_imports']),1)
    def test_missing_needed_is_reported(self):
        r=provider('app.so',needed=['missing.so']);check_symbols([r],{});self.assertEqual(r['missing_needed_api24'],['missing.so'])
    def test_wheelhouse_rejects_tampering_and_foreign_files_without_network(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('synthetic.txt','NO_REAL_TOKEN')
        row={'filename':'synthetic-1-py3-none-any.whl','url':'https://files.pythonhosted.org/synthetic.whl','sha256':hashlib.sha256(b.getvalue()).hexdigest()}
        lock={'schema':1,'python':'3.11','abis':['arm64-v8a'],'packages':[{'name':'synthetic','version':'1','files':[row]}]}
        with tempfile.TemporaryDirectory() as d:
            cache=Path(d)/'cache';cache.mkdir();(cache/row['filename']).write_bytes(b.getvalue());out=Path(d)/'out'
            self.assertEqual(prepare(lock,out,['arm64-v8a'],True,cache),1)
            (out/row['filename']).write_text('SYNTHETIC_CORRUPTION')
            with self.assertRaisesRegex(ValueError,'digest mismatch'):prepare(lock,out,['arm64-v8a'],True,cache)
            (out/row['filename']).unlink();(out/'foreign.whl').write_bytes(b.getvalue())
            with self.assertRaisesRegex(ValueError,'unlisted'):prepare(lock,out,['arm64-v8a'],True,cache)
        with self.assertRaises(ValueError):select(lock,['armeabi-v7a'])
    def test_switching_supported_abis_preserves_hash_checks(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('synthetic.txt','NO_REAL_KEY')
        files=[{'filename':'synthetic-1-py3-none-android_21_'+tag+'.whl','url':'https://files.pythonhosted.org/synthetic.whl','sha256':hashlib.sha256(b.getvalue()).hexdigest()} for tag in ['arm64_v8a','x86_64']]
        lock={'schema':1,'python':'3.11','abis':['arm64-v8a','x86_64'],'packages':[{'name':'synthetic','version':'1','files':files}]}
        with tempfile.TemporaryDirectory() as d:
            cache=Path(d)/'cache';cache.mkdir();out=Path(d)/'out'
            for row in files:(cache/row['filename']).write_bytes(b.getvalue())
            for abi in ['arm64-v8a','x86_64']:self.assertEqual(prepare(lock,out,[abi],True,cache),1)
            self.assertEqual(len(list(out.glob('*.whl'))),2)
            (out/files[0]['filename']).write_text('SYNTHETIC_CORRUPTION')
            with self.assertRaisesRegex(ValueError,'digest mismatch'):prepare(lock,out,['x86_64'],True,cache)
    def test_every_runtime_wheel_is_pinned_and_hashed(self):
        lock=json.loads((ROOT/'TMessagesProj/python/wheels.lock.json').read_text());text=(ROOT/'TMessagesProj/python/requirements.lock').read_text()
        self.assertEqual(len(lock['packages']),18)
        for p in lock['packages']:
            self.assertIn(p['name']+'=='+p['version'],text)
            for f in p['files']:self.assertIn('--hash=sha256:'+f['sha256'],text)
        for abi in lock['abis']:self.assertEqual(len(select(lock,[abi])),18)
    def test_platform_matches_minimum_and_external_capabilities_remain_closed(self):
        s=(ROOT/'TMessagesProj/build.gradle').read_text();self.assertIn('-DANDROID_PLATFORM=android-24',s);self.assertNotIn('-DANDROID_PLATFORM=android-27',s)
        self.assertIn("'--require-hashes'",s);self.assertIn("'--no-index'",s)
        policy=json.loads((ROOT/'gradle/variant-policy.json').read_text());self.assertFalse(policy['variants']['production']['buildEnabled'])
        self.assertTrue(all(not x for v in policy['variants'].values() for x in v['capabilities'].values()))
    def test_reviewed_native_scope(self):
        from scope_native import assert_native_scope
        assert_native_scope(self)
if __name__=='__main__':unittest.main()
