"""Real Groovy/CMake profile checks, no SDK execution, account or service."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]


class BuildProfileTests(unittest.TestCase):
    def test_actual_groovy_validator_accepts_only_closed_identity(self):
        gradle=Path(os.environ['FLEXYGRAM_GRADLE_HOME'])
        tools=Path(os.environ['JAVA_HOME'])/'bin'
        policy=json.loads((ROOT/'gradle/beta-development.json').read_text())
        with tempfile.TemporaryDirectory()as d:
            folder=Path(d);script=folder/'check.groovy'
            script.write_text('def check = new GroovyShell().evaluate(new File(args[0])); check.call(new File(args[1])); println("CLOSED_PROFILE_ACCEPTED")\n')
            rows=[policy,dict(policy,applicationId='com.exteraless.app'),dict(policy,isolated=False),dict(policy,capabilities=dict(policy['capabilities'],authentication=True)),dict(policy,apiHash='SYNTHETIC_FORBIDDEN')]
            for i,row in enumerate(rows):
                path=folder/'policy.json';path.write_text(json.dumps(row))
                p=subprocess.run([str(tools/'java'),'-cp',str(gradle/'lib/*'),'groovy.ui.GroovyMain',str(script),str(ROOT/'gradle/beta-development.gradle'),str(path)],capture_output=True,text=True)
                with self.subTest(case=i):self.assertEqual(p.returncode==0,i==0,p.stderr)

    def test_actual_cmake_beta_scope_is_bound_to_profile(self):
        policy=ROOT/'gradle/beta-development.json';scope=hashlib.sha256(policy.read_bytes()).hexdigest()+':betaDevelopment'
        cmake=os.environ['FLEXYGRAM_CMAKE']
        with tempfile.TemporaryDirectory()as d:
            folder=Path(d);source=folder/'src';source.mkdir()
            (source/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject(BetaProfile NONE)\ninclude("'+str(ROOT/'TMessagesProj/jni/beta-development-policy.cmake')+'")\n')
            for name,flavor,value,accepted in [('valid','betaDevelopment',scope,True),('production','production',scope,False),('wrong-scope','betaDevelopment','0'*64+':diagnostic',False)]:
                p=subprocess.run([cmake,'-S',str(source),'-B',str(folder/name),'-DFLEXYGRAM_FLAVOR='+flavor,'-DFLEXYGRAM_POLICY_SCOPE='+value],capture_output=True,text=True)
                with self.subTest(case=name):self.assertEqual(p.returncode==0,accepted,p.stderr)
            header=(folder/'valid/flexygram-policy/VariantPolicy.generated.h').read_text()
            self.assertIn(scope,header)
            self.assertIn('#define FLEXYGRAM_BUILD_DIAGNOSTIC 1',header)

    def test_protected_policies_and_historical_contract_are_unchanged(self):
        files=['gradle/variant-policy.json','gradle/variant-policy.gradle','gradle/production-readiness.gradle',
               'TMessagesProj/jni/variant-policy.cmake','TMessagesProj/jni/tgnet/DiagnosticPolicy.h',
               'TMessagesProj/src/diagnostic/AndroidManifest.xml','TMessagesProj/src/production/AndroidManifest.xml',
               'TMessagesProj/src/main/java/org/telegram/messenger/DiagnosticPolicy.java',
               'TMessagesProj/src/main/java/org/telegram/messenger/BuildVariantPolicy.java',
               'tests/native_compatibility/android_lab/contract.json']
        for name in files:
            before=subprocess.check_output(['git','show','19200e843cc9bf31c27a99e7b6775494627b131e:'+name],cwd=ROOT)
            with self.subTest(path=name):self.assertEqual((ROOT/name).read_bytes(),before)
