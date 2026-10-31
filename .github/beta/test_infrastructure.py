"""Infrastructure tests only: synthetic APK/credentials and mocked Android build/verifier.
The age round trip is real. Its disposable encryption key is never an Android signing key.
"""
import base64
import contextlib
import copy
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import yaml
import audit_environment as audit
import private_build as build

ROOT = Path(__file__).resolve().parents[2]
RECIPIENT = 'age1'+'q'*58  # Syntax fixture only, never used for real encryption.


def protected():
    policy = json.loads((audit.ROOT/'policy.json').read_text())
    policy['environment_id'] = 123
    policy['reviewer_ids'] = [456]
    policy['ui_review'] = {k: True for k in policy['ui_review']}
    policy['ui_review'].update(reviewed_by='fixture-owner', reviewed_at='2026-10-30T00:00:00Z',
                               delivery_age_recipient=RECIPIENT)
    env = {'id': 123, 'name': 'flexygram-beta', 'protection_rules': [
        {'type': 'required_reviewers', 'prevent_self_review': True,
         'reviewers': [{'type': 'User', 'reviewer': {'id': 456, 'type': 'User'}}]}],
        'deployment_branch_policy': {'protected_branches': False, 'custom_branch_policies': True}}
    branches = {'total_count': 1, 'branch_policies': [{'name': 'main', 'type': 'branch'}]}
    return policy, env, branches, {'name': 'main', 'protected': True}


class ProtectionTests(unittest.TestCase):
    def test_pending_policy_is_blocked(self):
        policy, *api = protected()
        policy = json.loads((audit.ROOT/'policy.json').read_text())
        # A future reviewed policy can pass; the initial unconfigured record cannot.
        if policy['ui_review']['confirmed'] is False:
            with self.assertRaises(ValueError): audit.validate(policy, *api)

    def test_reviewed_environment_fixture_passes(self):
        self.assertEqual(audit.validate(*protected())['status'], 'PASS_API_AND_RECORDED_UI_REVIEW')

    def test_protection_drift_blocks(self):
        mutations = [
            lambda p,e,b,m: e.update(id=999),
            lambda p,e,b,m: e.update(protection_rules=[]),
            lambda p,e,b,m: e['protection_rules'][0].update(prevent_self_review=False),
            lambda p,e,b,m: e['protection_rules'][0]['reviewers'][0]['reviewer'].update(id=999),
            lambda p,e,b,m: e['protection_rules'][0]['reviewers'][0].update(type='Team'),
            lambda p,e,b,m: e.update(deployment_branch_policy={'protected_branches': True, 'custom_branch_policies': False}),
            lambda p,e,b,m: b.update(total_count=2),
            lambda p,e,b,m: b['branch_policies'][0].update(name='*'),
            lambda p,e,b,m: b['branch_policies'][0].update(type='tag'),
            lambda p,e,b,m: m.update(protected=False),
            lambda p,e,b,m: p['ui_review'].update(admin_bypass_disabled=False),
            lambda p,e,b,m: p['ui_review'].update(main_requires_pull_request_and_approval=False),
            lambda p,e,b,m: p['ui_review'].update(delivery_age_recipient=''),
            lambda p,e,b,m: p.update(source_commit='0'*40),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                data = protected(); mutate(*data)
                with self.assertRaises(ValueError): audit.validate(*data)

    def test_manual_main_provenance_only(self):
        env = {'GITHUB_REPOSITORY': audit.REPO, 'GITHUB_EVENT_NAME': 'workflow_dispatch',
               'GITHUB_REF': 'refs/heads/main', 'GITHUB_SHA': 'a'*40, 'GITHUB_WORKFLOW_SHA': 'a'*40,
               'GITHUB_WORKFLOW_REF': audit.REPO+'/.github/workflows/beta-private.yml@refs/heads/main'}
        audit.provenance(env)
        for key,value in [('GITHUB_REPOSITORY','attacker/fork'), ('GITHUB_EVENT_NAME','pull_request'),
                          ('GITHUB_REF','refs/heads/unreviewed'), ('GITHUB_WORKFLOW_SHA','b'*40),
                          ('GITHUB_WORKFLOW_REF',audit.REPO+'/.github/workflows/other.yml@refs/heads/main')]:
            with self.subTest(key=key), self.assertRaises(ValueError): audit.provenance(dict(env, **{key:value}))

    def test_api_error_is_fail_closed_and_does_not_echo_token(self):
        output = io.StringIO()
        with patch.object(audit, 'get', side_effect=RuntimeError('SENSITIVE_SENTINEL')), \
             patch.object(audit, 'provenance'), patch('sys.argv', ['audit']), contextlib.redirect_stderr(output):
            self.assertEqual(audit.main(), 1)
        self.assertNotIn('SENSITIVE_SENTINEL', output.getvalue())


class WorkflowTests(unittest.TestCase):
    def test_dispatch_and_secret_boundaries(self):
        workflow = yaml.safe_load((ROOT/'.github/workflows/beta-private.yml').read_text())
        triggers = workflow.get('on', workflow.get(True))
        self.assertEqual(set(triggers), {'workflow_dispatch'})
        self.assertEqual(set(triggers['workflow_dispatch']['inputs']), {'mode'})
        self.assertEqual(workflow['permissions'], {'contents':'read'})
        self.assertFalse(workflow['concurrency']['cancel-in-progress'])
        audit_job, job = workflow['jobs']['audit'], workflow['jobs']['build']
        self.assertEqual(job['needs'], 'audit')
        self.assertEqual(job['environment'], 'flexygram-beta')
        self.assertNotIn('secrets.', json.dumps(audit_job))
        secret_steps = [s for s in job['steps'] if 'secrets.' in json.dumps(s)]
        self.assertEqual(len(secret_steps), 1)
        self.assertEqual(secret_steps[0]['run'], 'python3 control/.github/beta/private_build.py build')
        for group in workflow['jobs'].values():
            for step in group['steps']:
                if 'uses' in step:
                    self.assertRegex(step['uses'], r'@[0-9a-f]{40}$')
                    if step['uses'].startswith('actions/checkout@'):
                        self.assertFalse(step['with']['persist-credentials'])
        uploads = [s for s in job['steps'] if s.get('uses','').startswith('actions/upload-artifact@')]
        self.assertEqual(len(uploads), 1)
        self.assertTrue(uploads[0]['with']['path'].endswith('/FlexyGram-Beta-1290.tar.age'))
        index = job['steps'].index(uploads[0])
        self.assertEqual(job['steps'][index-1]['if'], 'always()')
        self.assertTrue(job['steps'][index-1]['run'].endswith(' cleanup'))
        self.assertEqual(uploads[0]['with']['retention-days'], 1)
        source = [s for s in job['steps'] if s.get('with',{}).get('path') == 'source'][0]
        self.assertEqual(source['with']['ref'], audit.SOURCE)
        smoke = yaml.safe_load((ROOT/'.github/workflows/beta-private-tests.yml').read_text())
        self.assertNotIn('secrets.', json.dumps(smoke))
        self.assertNotIn('environment', smoke['jobs']['test'])

    def test_main_promotion_cannot_trigger_old_release_paths(self):
        files = [p.relative_to(ROOT).as_posix() for p in (ROOT/'.github/beta').glob('*') if p.is_file()]
        files += ['.github/workflows/beta-private.yml', '.github/workflows/beta-private-tests.yml']
        self.assertTrue(all(p.startswith('.github/') for p in files))
        old = yaml.safe_load((ROOT/'.github/workflows/release.yml').read_text())
        triggers = old.get('on', old.get(True))
        self.assertIn('.github/**', triggers['push']['paths-ignore'])
        self.assertNotIn('.github/workflows/release.yml', files)

    def test_base_runtime_and_verifier_untouched(self):
        # Stacked infrastructure branch only. Main activation has a different documentary baseline.
        subprocess.run(['git','cat-file','-e',audit.SOURCE+'^{commit}'],cwd=ROOT,check=True)
        if subprocess.run(['git','merge-base','--is-ancestor',audit.SOURCE,'HEAD'],cwd=ROOT).returncode:
            activation_base = 'db1bea24b7b705de33f8ff8c8e174011c153cac7'
            changed = subprocess.check_output(['git','diff','--name-only',activation_base],cwd=ROOT,text=True).splitlines()
            self.assertTrue(changed and all(p.startswith('.github/beta/') or p in [
                '.github/workflows/beta-private.yml','.github/workflows/beta-private-tests.yml'] for p in changed), changed)
            subprocess.run(['git','diff','--exit-code',activation_base,'--','.github/workflows/release.yml'],cwd=ROOT,check=True)
            return
        changed = subprocess.check_output(['git','diff','--name-only',audit.SOURCE],cwd=ROOT,text=True).splitlines()
        allowed = 'tools/connected_alpha/beta_release_contract.py'
        self.assertTrue(all(p.startswith('.github/') or p == allowed for p in changed), changed)
        for p in ['TMessagesProj', 'gradle', 'gradle.properties', 'config/signing',
                  'tools/beta_release/verify_beta_apk.py', 'tools/beta_release/review.json']:
            subprocess.run(['git','diff','--exit-code',audit.SOURCE,'--',p],cwd=ROOT,check=True)


class PrivateInputsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.workspace, self.runner = base/'workspace', base/'runner'
        self.workspace.mkdir(); self.runner.mkdir()
        self.source = self.workspace/'source'
        (self.source/'TMessagesProj/src/beta').mkdir(parents=True)
        self.private = self.runner/'flexygram-beta-private-fixture'
        self.private.mkdir()
        self.env = dict(os.environ, GITHUB_WORKSPACE=str(self.workspace), RUNNER_TEMP=str(self.runner),
                        GITHUB_SHA='a'*40, GITHUB_RUN_ID='42', GITHUB_RUN_ATTEMPT='1', ANDROID_HOME='/sdk')
        for name in build.SECRET_NAMES: self.env[name] = 'SENSITIVE_SENTINEL'
        self.env.update(FLEXYGRAM_RELEASE_KEY_ALIAS='flexygram-release', TELEGRAM_APP_ID='123456',
                        TELEGRAM_APP_HASH='a'*32,
                        FLEXYGRAM_RELEASE_KEYSTORE_B64=base64.b64encode(b'DUMMY_NOT_A_PKCS12').decode(),
                        FLEXYGRAM_BETA_FIREBASE_JSON_B64=base64.b64encode(json.dumps({'client':[
                            {'client_info':{'android_client_info':{'package_name':'com.flexygram.messenger'}}}]
                        }).encode()).decode())

    def test_external_restore_permissions_and_child_environment(self):
        child = build.restore(self.env, self.source, self.private)
        key = Path(child['FLEXYGRAM_RELEASE_KEYSTORE'])
        self.assertFalse(key.is_relative_to(self.workspace))
        self.assertEqual(key.stat().st_mode & 0o777, 0o600)
        firebase = self.source/'TMessagesProj/src/beta/google-services.json'
        self.assertTrue(firebase.is_symlink())
        self.assertFalse(firebase.resolve().is_relative_to(self.workspace))
        for name in ['FLEXYGRAM_RELEASE_KEYSTORE_B64','FLEXYGRAM_BETA_FIREBASE_JSON_B64']:
            self.assertNotIn(name, child)
        self.assertEqual(child['NATIVE_TARGET'], 'arm64-v8a')
        build.cleanup(self.env)
        self.assertFalse(self.source.exists()); self.assertFalse(self.private.exists())

    def test_invalid_or_missing_credentials_rejected(self):
        mutations = [(k,'') for k in build.SECRET_NAMES]
        mutations += [('FLEXYGRAM_RELEASE_KEY_ALIAS','debug'), ('FLEXYGRAM_RELEASE_KEYSTORE_B64','notbase64!'),
                      ('TELEGRAM_APP_ID','2040'), ('TELEGRAM_APP_HASH','bad'),
                      ('FLEXYGRAM_BETA_FIREBASE_JSON_B64',base64.b64encode(b'{"client":[]}').decode())]
        for key,value in mutations:
            with self.subTest(key=key), self.assertRaises(Exception):
                build.restore(dict(self.env, **{key:value}), self.source, self.private)

    def test_workspace_temp_overlap_and_symlink_rejected(self):
        with self.assertRaises(ValueError):
            build.locations(dict(self.env, RUNNER_TEMP=str(self.workspace)))
        shutil.rmtree(self.source); self.source.symlink_to(self.runner)
        with self.assertRaises(ValueError): build.cleanup(self.env)
        self.assertTrue(self.runner.exists())

    def test_real_age_round_trip_and_failures_after_mocked_android_stages(self):
        self.assertIsNotNone(shutil.which('age'), 'Install age for required real encryption test')
        self.assertIsNotNone(shutil.which('age-keygen'))
        key = self.runner/'disposable-delivery-encryption-key.txt'
        subprocess.run(['age-keygen','-o',str(key)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
        recipient = subprocess.check_output(['age-keygen','-y',str(key)],text=True).strip()
        for failure in [None, 'ASSEMBLE', 'VERIFY', 'ENCRYPT']:
            with self.subTest(failure=failure):
                self.source.mkdir(exist_ok=True)
                (self.source/'TMessagesProj/src/beta').mkdir(parents=True, exist_ok=True)
                (self.source/'gradle.properties').write_text('APP_PACKAGE=com.flexygram.messenger\nBETA_VERSION_CODE=1290\nBETA_VERSION_NAME=1.0.0-beta.1\n')
                control = self.runner/'control'; control.mkdir(exist_ok=True)
                policy = protected()[0]; policy['ui_review']['delivery_age_recipient'] = recipient
                (control/'policy.json').write_text(json.dumps(policy))
                env = dict(self.env, BETA_AGE_RECIPIENT=recipient)
                original = build.run_private
                def fake(args, source, child, log, output=None):
                    if args[0] == './gradlew':
                        self.assertEqual(args, ['./gradlew',':TMessagesProj:assembleBeta','--no-daemon','--console=plain'])
                        if failure == 'ASSEMBLE': raise RuntimeError('SENSITIVE_SENTINEL')
                        folder = source/'TMessagesProj/build/outputs/apk/beta'; folder.mkdir(parents=True)
                        with zipfile.ZipFile(folder/'synthetic.apk','w') as apk: apk.writestr('classes.dex',b'SYNTHETIC_NOT_INSTALLABLE')
                    elif args[0] == 'age':
                        self.assertFalse(any(name in child for name in build.SECRET_NAMES))
                        if failure == 'ENCRYPT': raise RuntimeError('SENSITIVE_SENTINEL')
                        original(args,source,child,log,output)
                    elif 'verify_beta_apk.py' in args[1]:
                        if failure == 'VERIFY': raise RuntimeError('SENSITIVE_SENTINEL')
                        self.assertEqual(args[1], 'tools/beta_release/verify_beta_apk.py')
                        import hashlib
                        data = {'status':'PASS_OFFICIAL_BETA_ARTIFACT_ONLY','version_code':1290,'elf_count':96,
                                'sha256':hashlib.sha256(Path(args[2]).read_bytes()).hexdigest()}
                        output.write_text(json.dumps(data))
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch.object(build,'HERE',control), patch.object(build,'run_private',side_effect=fake), \
                     patch.object(build.subprocess,'check_output',side_effect=[(audit.SOURCE+'\n').encode(),b'']) as git:
                    # Production check_output requests text=True.
                    git.side_effect = [audit.SOURCE+'\n', '']
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        if failure:
                            with self.assertRaises(Exception): build.build(env)
                        else:
                            build.build(env)
                self.assertNotIn('SENSITIVE_SENTINEL',stdout.getvalue()+stderr.getvalue())
                self.assertFalse(self.source.exists())
                self.assertEqual(list(self.runner.glob('flexygram-beta-private-*')), [])
                delivery = self.runner/'flexygram-beta-delivery/FlexyGram-Beta-1290.tar.age'
                if failure:
                    self.assertFalse(delivery.exists())
                else:
                    decoded = self.runner/'roundtrip.tar'
                    subprocess.run(['age','--decrypt','--identity',str(key),'--output',str(decoded),str(delivery)],check=True)
                    with tarfile.open(decoded) as archive:
                        self.assertEqual(sorted(archive.getnames()),['FlexyGram-Beta-1290-ARM64.apk','provenance.json','verification.json'])
                        self.assertEqual(json.load(archive.extractfile('provenance.json'))['source_commit'],audit.SOURCE)
                    build.cleanup(env,delivery=True)
