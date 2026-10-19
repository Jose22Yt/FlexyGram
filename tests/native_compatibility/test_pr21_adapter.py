"""Synthetic offline adapter regressions, never Android evidence."""
from pathlib import Path
import hashlib,json,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];LAB=ROOT/'tests/native_compatibility/android_lab';sys.path.insert(0,str(LAB))
import pr21_adapter as adapter
from contract import load_contract
from test_android_lab import result,environment

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.c=load_contract()
        # Exact reviewed auxiliary source supplied externally; never downloaded by tests.
        import os
        if not os.environ.get('FLEXYGRAM_TEST_PR20') or not os.environ.get('FLEXYGRAM_TEST_PR21'):
            raise RuntimeError('Provide pinned PR20/PR21 source paths; offline adapter tests must not be skipped')
        self.pre=Path(os.environ['FLEXYGRAM_TEST_PR20']);self.gate=Path(os.environ['FLEXYGRAM_TEST_PR21'])
    def run_fixture(self,profile,nonce):
        d=self.root/profile;d.mkdir();c=self.c;p=result(c,profile,nonce)
        files={'instrumentation.log':'INSTRUMENTATION_RESULT: lab_result='+json.dumps(p)+'\nINSTRUMENTATION_CODE: -1\n','cold-launch.log':'Status: ok\n','logcat.log':'SYNTHETIC ONLY\n','crash.log':'','install-target.log':'Success\n','install-runner.log':'Success\n','package-before.log':c['target_package'],'package-after.log':c['target_package']}
        for family in ['iptables','ip6tables']:
            for when in ['before','after']:files[family+'-'+when+'.log']='0 0 DROP all\n'
        for name,text in files.items():(d/name).write_text(text)
        sources=[LAB/'java/io/github/jose22yt/flexygram/lab/LabInstrumentation.java',LAB/'AndroidManifest.xml',LAB/'assets/probe.py',LAB/'contract.json',ROOT/c['runtime_cases_path']]
        r={'status':'PASS','android_executed':True,'profile':profile,'run_id':nonce,'reviewed_head':c['reviewed_head'],'environment':environment(profile),'instrumentation':p,'inputs':{'status':'VERIFIED_INPUTS_ONLY','apk_sha256':c['apk_sha256'],'wheels':18,'rebuilt_wheels':3,'elf':4},'runner':{'status':'BUILT_SIGNED_NOT_RUN','signed_with_reviewed_lab_key':True,'reviewed_target_sha256':c['apk_sha256'],'apk_sha256':'a'*64,'source_hashes':{str(f.relative_to(ROOT)):adapter.digest(f) for f in sources}},'image':{'image_sha256':'b'*64,'image_origin':'synthetic','image_revision':'fixture-only'},'network':{when:{f:{'packets':0,'bytes':0} for f in ['iptables','ip6tables']} for when in ['before','after']},'evidence_sha256':{n:adapter.digest(d/n) for n in files}}
        path=d/'result.json';path.write_text(json.dumps(r));return path
    def pair(self):return [self.run_fixture('api24-4k','a'*32),self.run_fixture('arm64-16k','b'*32)]
    def edit(self,path,fn):
        r=json.loads(path.read_text());fn(r);path.write_text(json.dumps(r))
    def edit_log(self,path,name,text):
        (path.parent/name).write_text(text);self.edit(path,lambda r:r['evidence_sha256'].update({name:adapter.digest(path.parent/name)}))
    def export(self,paths):return adapter.prepare(paths,self.pre,self.gate)
    def test_positive_synthetic_mapping_preserves_false_certification(self):
        paths=self.pair();out,side=self.export(paths)
        self.assertEqual(set(out['profiles']),{'api24','16k'});self.assertFalse(side['runtime_certified']);self.assertEqual(len(side['runs']),2)
        self.assertTrue(all(len(x['cases'])==12 for x in out['profiles'].values()))
        self.assertEqual(side['derived_evidence_sha256'],hashlib.sha256((json.dumps(out,indent=2)+'\n').encode()).hexdigest())
    def test_wrong_auxiliary_code_rejected_before_import(self):
        p=self.root/'fake.py';p.write_text('raise Exception("MUST_NOT_EXECUTE")')
        with self.assertRaisesRegex(ValueError,'digest'):adapter.prepare(self.pair(),p,self.gate)
    def test_duplicate_and_nonfinite_json_rejected(self):
        for text in ['{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}']:
            with self.assertRaises(ValueError):adapter.strict(text)
    def test_primary_reports_cannot_be_passed_directly_to_secondary(self):
        m=adapter.pinned_module('pr21',self.gate);paths=self.pair();self.assertEqual(m.validate(json.loads(paths[0].read_text()))['status'],'BLOCKED')
    def test_missing_profile_or_repeated_nonce_rejected(self):
        paths=self.pair()
        with self.assertRaises(ValueError):self.export([paths[0],paths[0]])
    def test_missing_historical_provenance_not_filled_with_defaults(self):
        paths=self.pair();self.edit(paths[0],lambda r:r.pop('inputs'))
        with self.assertRaises(KeyError):self.export(paths)
    def test_missing_installation_evidence_rejected(self):
        paths=self.pair();self.edit(paths[0],lambda r:r['evidence_sha256'].pop('install-target.log'))
        with self.assertRaises(ValueError):self.export(paths)
    def test_critical_python_and_memory_indicators_rejected(self):
        for text in ['ModuleNotFoundError: SYNTHETIC','OutOfMemoryError SYNTHETIC']:
            with self.subTest(text=text):
                paths=self.pair() if not any(self.root.iterdir()) else None
                if paths is None:
                    import shutil
                    for p in self.root.iterdir():shutil.rmtree(p)
                    paths=self.pair()
                self.edit_log(paths[0],'logcat.log',text)
                with self.assertRaises(ValueError):self.export(paths)
    def test_counter_log_disagreement_rejected_even_with_updated_digest(self):
        paths=self.pair();self.edit_log(paths[0],'ip6tables-after.log','1 64 DROP all\n')
        with self.assertRaises(ValueError):self.export(paths)
    def test_counter_boolean_not_accepted_as_numeric_zero(self):
        paths=self.pair();self.edit(paths[0],lambda r:r['network']['after']['iptables'].update(packets=False))
        with self.assertRaises(ValueError):self.export(paths)
    def test_runner_source_receipt_mismatch_rejected(self):
        paths=self.pair();self.edit(paths[0],lambda r:r['runner'].update(source_hashes={}))
        with self.assertRaises(ValueError):self.export(paths)
    def test_environment_and_instrumentation_must_agree(self):
        paths=self.pair();self.edit(paths[0],lambda r:r['environment'].update(api=25))
        with self.assertRaises(ValueError):self.export(paths)
    def test_partial_cold_start_not_promoted_to_pass(self):
        paths=self.pair();self.edit_log(paths[0],'cold-launch.log','Status: timeout\n')
        with self.assertRaises(ValueError):self.export(paths)
    def test_missing_case_not_promoted_to_pass(self):
        paths=self.pair();self.edit(paths[0],lambda r:r['instrumentation']['python']['cases'].pop())
        with self.assertRaises(ValueError):self.export(paths)
    def test_changed_contract_does_not_silently_repin_secondary(self):
        paths=self.pair();c=dict(self.c,certificate_sha256='f'*64)
        with patch.object(adapter,'load_contract',lambda:c),self.assertRaises(ValueError):self.export(paths)
    def test_cli_missing_inputs_fails_without_creating_outputs(self):
        import contextlib,io
        output=self.root/'export';text=io.StringIO()
        with contextlib.redirect_stdout(text):rc=adapter.main([str(self.root/'absent1'),str(self.root/'absent2'),'--pr20-preflight',str(self.pre),'--pr21-validator',str(self.gate),'--output',str(output)])
        self.assertEqual(rc,1);self.assertFalse(output.exists());self.assertNotIn(str(self.root),text.getvalue())
if __name__=='__main__':unittest.main()
