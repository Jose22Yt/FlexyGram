"""Synthetic host regressions for the lab controller, not Android runtime results."""
from pathlib import Path
from io import BytesIO
import copy,hashlib,json,re,struct,sys,tempfile,unittest,xml.etree.ElementTree as ET,zipfile
ROOT=Path(__file__).resolve().parents[2];LAB=ROOT/'tests/native_compatibility/android_lab';sys.path.insert(0,str(LAB))
from contract import load_contract,verify_inputs,validate_environment,validate_result,instrumentation_result,elf16
from run_lab import serial_ok,counters,matrix,offline_receipt,verify_runner

def elf(machine=183,align=16384):
    b=bytearray(4096);b[:64]=struct.pack('<16sHHIQQQIHHHHHH',b'\x7fELF'+bytes([2,1,1,0])+bytes(8),3,machine,1,0,64,0,0,64,56,1,64,0,0);b[64:120]=struct.pack('<IIQQQQQQ',1,6,0,0,0,4096,4096,align);return bytes(b)
def zipped(rows):
    b=BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        for name,data in rows:z.writestr(name,data)
    return b.getvalue()
def sha(b):return hashlib.sha256(b).hexdigest()
def environment(profile):return {'api':24 if profile=='api24-4k' else 37,'page_size':4096 if profile=='api24-4k' else 16384,'abi':'arm64-v8a','arch':'aarch64','native_bridge':'','emulator':True,'clean_lab':True,'strict_16k':profile=='arm64-16k'}
def result(c,profile='api24-4k',nonce='a'*32):
    p={'android_api':24 if profile=='api24-4k' else 37,'python_minor':'3.11','jni_sha256':c['jni_sha256'],'jni_scope_verified':True,'plugins_not_loaded':True,'cases':[{'id':n,'status':'PASS'} for n in c['case_ids']],'tests_run':12,'failures':0,'errors':0,'skipped':0,'expected_failures':0,'unexpected_successes':0,'libraries':[{'name':n,'sha256':h,'mapped_before':True,'mapped_after':True} for n,h in c['libraries'].items()]}
    return {'status':'PASS','run_id':nonce,'profile':profile,'environment':environment(profile),'apk_sha256':c['apk_sha256'],'certificate_sha256':c['certificate_sha256'],'internet_absent':True,'capabilities_closed':True,'jni_loaded':True,'python':p}
class AndroidLabTests(unittest.TestCase):
    def setUp(self):self.c=load_contract();self.temp=tempfile.TemporaryDirectory();self.dir=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def inputs(self):
        native=elf();c=copy.deepcopy(self.c);c['libraries']={n:sha(native) for n in c['libraries']};c['jni_sha256']=sha(native);c['wheels']=[];house=self.dir/'wheels';house.mkdir()
        groups=[['libfreetype.so'],['libxml2.so'],['libxslt.so','libexslt.so']]+[[]]*15
        for i,names in enumerate(groups):
            name='synthetic'+str(i)+'-1-py3-none-any.whl';data=zipped([('chaquopy/lib/'+n,native) for n in names] or [('synthetic.txt',b'FAKE_NO_CREDENTIALS')]);(house/name).write_bytes(data);c['wheels'].append({'filename':name,'sha256':sha(data),'rebuilt':bool(names)})
        imy=zipped([('chaquopy/lib/'+n,native) for n in c['libraries']]);data=zipped([('lib/arm64-v8a/'+c['jni_library'],native),('assets/chaquopy/requirements-common.imy',imy)]);apk=self.dir/'synthetic.apk';apk.write_bytes(data);c['apk_sha256']=sha(data);c['apk_bytes']=len(data);return apk,house,c
    def test_real_java_dictionary_lookup_uses_python_item_not_attribute(self):
        import subprocess,os
        source=(LAB/'java/io/github/jose22yt/flexygram/lab/LabInstrumentation.java').read_text()
        helpers=source[source.index('    private static Object callAttr('):source.index('    private static void guards(')]
        self.assertIn('Object function=dictionaryGet(pyObject,globals,"run_probe");',source)
        harness='import java.lang.reflect.*; public class LookupHarness { '+helpers+'''
          public static final class FakePyObject {
            public Object get(Object key) { throw new AssertionError("attribute lookup cannot retrieve dictionary item"); }
            public Object callAttr(String name,Object... args) {
              if (!name.equals("__getitem__") || args.length!=1 || !args[0].equals("run_probe")) throw new AssertionError("wrong item lookup");
              return "SYNTHETIC_FUNCTION";
            }
          }
          public static void main(String[] args) throws Exception {
            if (!"SYNTHETIC_FUNCTION".equals(dictionaryGet(FakePyObject.class,new FakePyObject(),"run_probe"))) throw new AssertionError();
          }
        }'''
        java=self.dir/'LookupHarness.java';java.write_text(harness)
        tools=Path(os.environ.get('JAVA_HOME','/usr'))/'bin'
        for command in [[tools/'javac',java],[tools/'java','-cp',self.dir,'LookupHarness']]:
            p=subprocess.run(list(map(str,command)),capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
    def test_python_build_api_is_not_used_as_runtime_api(self):
        import importlib.util,types
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('lab_probe_fixture',LAB/'assets/probe.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        fake=types.SimpleNamespace(jclass=lambda name:types.SimpleNamespace(SDK_INT=37))
        with patch.dict(sys.modules,{'java':fake}),patch.object(sys,'getandroidapilevel',lambda:24,create=True):self.assertEqual(probe.runtime_android_api(),37)
    def test_runtime_api_has_no_build_api_fallback(self):
        import importlib.util
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('lab_probe_no_java',LAB/'assets/probe.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        with patch.dict(sys.modules,{'java':None}),self.assertRaises(ModuleNotFoundError):probe.runtime_android_api()
    def test_reviewed_source_and_12_cases_are_preserved(self):
        self.assertEqual(self.c['reviewed_head'],'867e1178719ff0bda8d9b5381b17ecc3ae8391e5');self.assertEqual(len(self.c['case_ids']),12);self.assertEqual(self.c['runtime_cases_sha256'],'cabd6335f2711fd7b189a14ad535429481b611ee9b7be72bc526a87b7a012ad6')
    def test_exact_synthetic_artifacts_pass_readonly_gate(self):
        apk,house,c=self.inputs();self.assertEqual(verify_inputs(apk,house,c)['status'],'VERIFIED_INPUTS_ONLY')
    def test_changed_apk_is_rejected(self):
        apk,house,c=self.inputs();apk.write_bytes(apk.read_bytes()+b'FAKE');
        with self.assertRaises(ValueError):verify_inputs(apk,house,c)
    def test_changed_wheel_is_rejected(self):
        apk,house,c=self.inputs();next(house.iterdir()).write_bytes(b'FAKE')
        with self.assertRaises(ValueError):verify_inputs(apk,house,c)
    def test_missing_and_extra_wheels_rejected(self):
        apk,house,c=self.inputs();(house/'extra.txt').write_text('FAKE')
        with self.assertRaises(ValueError):verify_inputs(apk,house,c)
        (house/'extra.txt').unlink();next(house.iterdir()).unlink()
        with self.assertRaises(ValueError):verify_inputs(apk,house,c)
    def test_symlink_wheel_rejected(self):
        apk,house,c=self.inputs();p=next(house.iterdir());data=p.read_bytes();p.unlink();outside=self.dir/'original';outside.write_bytes(data);p.symlink_to(outside)
        with self.assertRaises(ValueError):verify_inputs(apk,house,c)
    def test_wrong_arm64_or_load_alignment_rejected(self):
        for b in [elf(62),elf(183,4096),elf(183,24576),b'NOT_ELF']:
            with self.assertRaises(ValueError):elf16(b)
    def test_api24_and_real_16k_profiles_pass(self):
        for p in ['api24-4k','arm64-16k']:validate_environment(environment(p),p)
    def test_wrong_api_or_page_rejected(self):
        for key,value in [('api',25),('page_size',16384)]:
            e=environment('api24-4k');e[key]=value
            with self.assertRaises(ValueError):validate_environment(e,'api24-4k')
        e=environment('arm64-16k');e['page_size']=4096
        with self.assertRaises(ValueError):validate_environment(e,'arm64-16k')
    def test_x86_native_bridge_and_physical_rejected(self):
        for key,value in [('abi','x86_64'),('arch','x86_64'),('native_bridge','libndk_translation.so'),('emulator',False),('clean_lab',False)]:
            e=environment('api24-4k');e[key]=value
            with self.assertRaises(ValueError):validate_environment(e,'api24-4k')
    def test_backcompat_is_not_strict_16kb(self):
        e=environment('arm64-16k');e['strict_16k']=False
        with self.assertRaises(ValueError):validate_environment(e,'arm64-16k')
    def test_complete_synthetic_runtime_report_passes(self):self.assertTrue(validate_result(result(self.c),self.c,'api24-4k','a'*32))
    def test_missing_case_and_duplicate_case_rejected(self):
        for mutate in [lambda p:p['cases'].pop(),lambda p:p['cases'].__setitem__(0,p['cases'][1])]:
            r=result(self.c);mutate(r['python'])
            with self.assertRaises(ValueError):validate_result(r,self.c,'api24-4k','a'*32)
    def test_failures_errors_skips_and_expected_failures_rejected(self):
        for key in ['failures','errors','skipped','expected_failures','unexpected_successes']:
            r=result(self.c);r['python'][key]=1
            with self.assertRaises(ValueError):validate_result(r,self.c,'api24-4k','a'*32)
    def test_test_count_not_inferred_from_pass_text(self):
        r=result(self.c);r['python']['tests_run']=0
        with self.assertRaises(ValueError):validate_result(r,self.c,'api24-4k','a'*32)
    def test_different_library_or_unmapped_library_rejected(self):
        for key,value in [('sha256','0'*64),('mapped_before',False),('mapped_after',False)]:
            r=result(self.c);r['python']['libraries'][0][key]=value
            with self.assertRaises(ValueError):validate_result(r,self.c,'api24-4k','a'*32)
    def test_capability_or_internet_and_jni_failures_rejected(self):
        for key in ['internet_absent','capabilities_closed','jni_loaded']:
            r=result(self.c);r[key]=False
            with self.assertRaises(ValueError):validate_result(r,self.c,'api24-4k','a'*32)
    def test_signature_and_apk_mismatch_rejected(self):
        for key in ['certificate_sha256','apk_sha256']:
            r=result(self.c);r[key]='0'*64
            with self.assertRaises(ValueError):validate_result(r,self.c,'api24-4k','a'*32)
    def test_replay_and_python_plugin_mismatch_rejected(self):
        with self.assertRaises(ValueError):validate_result(result(self.c),self.c,'api24-4k','b'*32)
        for key,value in [('plugins_not_loaded',False),('jni_scope_verified',False),('python_minor','3.12'),('android_api',37)]:
            r=result(self.c);r['python'][key]=value
            with self.assertRaises(ValueError):validate_result(r,self.c,'api24-4k','a'*32)
    def test_instrumentation_protocol_requires_unique_completion(self):
        text='INSTRUMENTATION_RESULT: lab_result='+json.dumps(result(self.c))+'\nINSTRUMENTATION_CODE: -1\n';self.assertEqual(instrumentation_result(text)['status'],'PASS')
        for bad in ['',text+text,text.replace('INSTRUMENTATION_CODE: -1','INSTRUMENTATION_CODE: 0')]:
            with self.assertRaises(ValueError):instrumentation_result(bad)
    def test_only_explicit_local_emulators_allowed(self):
        for x in ['emulator-5554','127.0.0.1:6520','localhost:6520']:self.assertTrue(serial_ok(x))
        for x in ['USB_PERSONAL','192.168.1.10:5555','emulator-5554;sh','']:self.assertFalse(serial_ok(x))
    def test_network_counter_must_be_present_and_unambiguous(self):
        self.assertEqual(counters('pkts bytes target\n0 0 DROP all -- * * 0.0.0.0/0 0.0.0.0/0'),{'packets':0,'bytes':0})
        for text in ['','0 0 ACCEPT all','0 0 DROP all\n0 0 DROP all']:
            with self.assertRaises(ValueError):counters(text)
    def test_no_implicit_offline_attestation(self):
        p=self.dir/'receipt.json';p.write_text('{}')
        with self.assertRaises(ValueError):offline_receipt(p)
    def test_unsigned_runner_is_not_installable(self):
        p=self.dir/'runner.apk';p.write_text('FAKE');receipt=self.dir/'receipt.json';receipt.write_text('{"signed_with_reviewed_lab_key":false}')
        with self.assertRaises(ValueError):verify_runner(p,receipt,self.dir,self.c)
    def test_test_manifest_requests_no_permissions_or_app_components(self):
        root=ET.parse(LAB/'AndroidManifest.xml').getroot();self.assertFalse(root.findall('uses-permission'));app=root.find('application');self.assertFalse(list(app));a='{http://schemas.android.com/apk/res/android}';self.assertEqual(root.find('instrumentation').get(a+'targetPackage'),self.c['target_package'])
    def test_normal_build_does_not_include_instrumentation(self):
        for p in ['settings.gradle','TMessagesProj/build.gradle']:
            text=(ROOT/p).read_text();self.assertNotIn('LabInstrumentation',text);self.assertNotIn('android_lab',text)
    def evidence_run(self,profile,nonce):
        directory=self.dir/profile;directory.mkdir();r=result(self.c,profile,nonce)
        texts={'instrumentation.log':'INSTRUMENTATION_RESULT: lab_result='+json.dumps(r)+'\nINSTRUMENTATION_CODE: -1\n','cold-launch.log':'Status: ok','logcat.log':'SYNTHETIC','crash.log':''}
        for tool in ['iptables','ip6tables']:
            for when in ['before','after']:texts[tool+'-'+when+'.log']='0 0 DROP all'
        for n,text in texts.items():(directory/n).write_text(text)
        summary={'status':'PASS','android_executed':True,'run_id':nonce,'profile':profile,'instrumentation':r,'network':{'before':{x:{'packets':0,'bytes':0} for x in ['iptables','ip6tables']},'after':{x:{'packets':0,'bytes':0} for x in ['iptables','ip6tables']}},'evidence_sha256':{n:sha(v.encode()) for n,v in texts.items()}}
        p=directory/'result.json';p.write_text(json.dumps(summary));return p
    def test_two_independent_synthetic_receipts_required(self):
        a=self.evidence_run('api24-4k','a'*32);b=self.evidence_run('arm64-16k','b'*32);self.assertEqual(matrix([a,b],self.c)['status'],'PASS_BOTH_ANDROID_LABS')
        with self.assertRaises(ValueError):matrix([a,a],self.c)
    def test_missing_or_altered_evidence_blocks_matrix(self):
        a=self.evidence_run('api24-4k','a'*32);b=self.evidence_run('arm64-16k','b'*32);(b.parent/'instrumentation.log').write_text('FORGED')
        with self.assertRaises(ValueError):matrix([a,b],self.c)
    def test_network_attempt_blocks_matrix_even_if_no_packet_left(self):
        a=self.evidence_run('api24-4k','a'*32);b=self.evidence_run('arm64-16k','b'*32);r=json.loads(b.read_text());r['network']['after']['ip6tables']['packets']=1;b.write_text(json.dumps(r))
        with self.assertRaises(ValueError):matrix([a,b],self.c)
if __name__=='__main__':unittest.main()
