"""Subprocesses only execute local Python tools with synthetic files, never Android."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from test_analyzers import meta, sequence, PKG, SECRET, run_report

ROOT=Path(__file__).resolve().parents[2]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.metadata=self.root/'metadata.json';self.metadata.write_text(json.dumps(meta()))
        self.events=self.root/'events.jsonl';self.events.write_text(sequence())

    def invoke(self,script,*args):
        flags=['-B']+(['-O'] if sys.flags.optimize else [])
        return subprocess.run([sys.executable,*flags,str(ROOT/'tools/beta_diagnostics'/script),*map(str,args)],capture_output=True,text=True,timeout=30)

    def test_actual_cli_analyzes_synthetic_events(self):
        p=self.invoke('analyze.py','analyze','--metadata',self.metadata,'--package',PKG,'--events',self.events)
        self.assertEqual(p.returncode,0,p.stderr)
        r=json.loads(p.stdout)
        self.assertEqual(r['interactions']['operations']['chat_open']['request_to_present']['p95_ms'],20)
        self.assertFalse(r['android_execution_verified_by_analyzer'])

    def test_missing_inputs_do_not_fabricate_metrics(self):
        p=self.invoke('analyze.py','analyze','--metadata',self.metadata,'--package',PKG)
        r=json.loads(p.stdout)
        self.assertIsNone(r['frames']);self.assertIsNone(r['interactions'])

    def test_malformed_private_input_has_safe_error(self):
        self.events.write_text(SECRET)
        p=self.invoke('analyze.py','analyze','--metadata',self.metadata,'--package',PKG,'--events',self.events)
        self.assertEqual(p.returncode,2)
        self.assertEqual(json.loads(p.stdout)['status'],'INVALID_INPUT')
        self.assertNotIn(SECRET,p.stdout+p.stderr)

    def test_invalid_cli_type_does_not_echo_secret(self):
        p=self.invoke('analyze.py','analyze','--metadata',self.metadata,'--package',PKG,'--pids',SECRET)
        self.assertEqual(p.returncode,2)
        self.assertNotIn(SECRET,p.stdout+p.stderr)

    def test_default_capture_plan_cannot_contact_missing_adb(self):
        p=self.invoke('capture.py','--adb',self.root/'nonexistent-adb','--serial','emulator-5554','--package',PKG)
        self.assertEqual(p.returncode,0,p.stderr)
        r=json.loads(p.stdout)
        self.assertEqual(r['status'],'PLAN_ONLY');self.assertFalse(r['device_contacted'])

    def test_capture_execution_requires_receipt(self):
        p=self.invoke('capture.py','--adb',self.root/'nonexistent-adb','--serial','emulator-5554','--package',PKG,'--execute')
        self.assertEqual(p.returncode,2)
        self.assertEqual(json.loads(p.stdout)['status'],'CAPTURE_BLOCKED')
        self.assertEqual(json.loads(p.stdout)['code'],'CAPTURE_ARGUMENTS_REQUIRED')

    def test_compare_cli_has_no_android_claim(self):
        left=[];right=[]
        for i in range(5):
            for target,candidate in [(left,False),(right,True)]:
                path=self.root/('candidate' if candidate else 'base')
                path=path.with_name(path.name+str(i)+'.json')
                path.write_text(json.dumps(run_report(i,candidate)));target.append(path)
        p=self.invoke('analyze.py','compare','--baseline',*left,'--candidate',*right)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout)['status'],'SYNTHETIC_COMPARISON_ONLY')

    def test_insufficient_comparison_exits_nonzero(self):
        path=self.root/'run.json';path.write_text(json.dumps(run_report(0)))
        p=self.invoke('analyze.py','compare','--baseline',path,'--candidate',path)
        self.assertEqual(p.returncode,2)
        self.assertEqual(json.loads(p.stdout)['status'],'INCOMPARABLE')

    def test_symlink_input_rejected(self):
        link=self.root/'link.json';link.symlink_to(self.metadata)
        p=self.invoke('analyze.py','analyze','--metadata',link,'--package',PKG)
        self.assertEqual(p.returncode,2)
