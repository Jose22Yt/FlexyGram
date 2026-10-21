"""Actual Java core with local adapters, no Android or Telegram execution."""
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'TMessagesProj_Modules/telegram-session-core/src/main/java'
CANARY='SYNTHETIC_PRIVATE_NOT_A_REAL_TOKEN_49127'
HARNESS=Path(__file__).with_name('SessionHarness.java')
CASES=re.findall(r'^        case "([^"]+)":',HARNESS.read_text(),re.M)

class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        home=Path(os.environ['JAVA_HOME']);cls.java=home/'bin/java'
        version=subprocess.run([str(cls.java),'-version'],capture_output=True,text=True,check=True)
        if 'version "21.' not in version.stderr:raise RuntimeError('JDK21_REQUIRED')
        cls.temp=tempfile.TemporaryDirectory();cls.classes=Path(cls.temp.name)/'classes'
        run=subprocess.run([str(home/'bin/javac'),'--release','8','-d',str(cls.classes),*map(str,SOURCE.rglob('*.java')),str(HARNESS)],capture_output=True,text=True)
        if run.returncode:raise RuntimeError(run.stderr)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,case):
        p=subprocess.run([str(self.java),'-cp',str(self.classes),'io.github.jose22yt.flexygram.session.SessionHarness',case],capture_output=True,text=True,timeout=15)
        self.assertNotIn(CANARY,p.stdout+p.stderr)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn('LOCAL_ADAPTERS_ONLY',p.stdout)
    def test_compiled_core_targets_java8_bytecode(self):
        classes=list(self.classes.rglob('*.class'))
        self.assertGreater(len(classes),4)
        for path in classes:
            with self.subTest(path=path.name):self.assertEqual(struct.unpack('>H',path.read_bytes()[6:8])[0],52)

for case in CASES:
    if case!='actualNativeAttestation':
        setattr(RuntimeTests,'test_'+case,lambda self,c=case:self.run_case(c))
