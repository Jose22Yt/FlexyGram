"""Private transport tests with explicit network doubles; no APK/account is used."""
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.parse
import yaml
import deliver as d


class Response(io.BytesIO):
    def __init__(self, body=b'', status=200, headers=None):
        super().__init__(body)
        self.status = status
        self.headers = headers or {}


class Tests(unittest.TestCase):
    def test_local_bytes_and_independent_report_identity_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'synthetic.bin'
            p.write_bytes(b'isolated transport fixture, not an APK')
            report = dict(commit=d.SOURCE, application_id=d.APP, version_code=1274,
                          certificate_sha256=d.CERT, elf_count=96, status='PASS_ARTIFACT_ONLY',
                          sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size)
            self.assertEqual(d.validate(report, p), (report['sha256'], report['bytes']))
            for key, value in [('commit', '0'*40), ('application_id', 'wrong'), ('version_code', 1272),
                               ('certificate_sha256', '0'*64), ('elf_count', 95), ('elf_count', 97),
                               ('status', 'NOT_VERIFIED'), ('sha256', '0'*64), ('bytes', 0)]:
                with self.subTest(key=key, value=value), self.assertRaises(d.DeliveryError):
                    d.validate(dict(report, **{key: value}), p)

    def test_credentials_are_host_bound_and_requests_do_not_follow_redirects(self):
        c = d.Client.__new__(d.Client)
        c.token = 'synthetic-repository-token'
        class Opener:
            def __init__(self): self.requests = []
            def open(self, req, timeout):
                self.requests.append(req)
                return Response()
        c.opener = Opener()
        for url in ['https://evil.invalid/upload', 'http://api.github.com/upload', 'https://user@api.github.com/upload']:
            with self.assertRaises(d.DeliveryError): c.request(url)
        self.assertEqual(c.opener.requests, [])
        c.request(d.API + '/releases/1')
        self.assertEqual(c.opener.requests[-1].get_header('Authorization'), 'Bearer synthetic-repository-token')
        c.request('https://release-assets.githubusercontent.com/blob?token=synthetic', authenticated=False)
        self.assertIsNone(c.opener.requests[-1].get_header('Authorization'))
        self.assertIsNone(d.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.invalid'))

    def test_private_storage_redirect_strips_auth_and_verifies_download_bytes(self):
        calls = []
        c = d.Client.__new__(d.Client)
        payload = b'synthetic bytes'
        def request(url, **kw):
            calls.append((url, kw))
            if len(calls) == 1: return Response(status=302, headers={'Location': 'https://release-assets.githubusercontent.com/blob?synthetic=1'})
            return Response(payload)
        c.request = request
        self.assertEqual(c.download_hash({'id': 2}), (hashlib.sha256(payload).hexdigest(), len(payload)))
        self.assertFalse(calls[1][1]['authenticated'])
        c.request = lambda *a, **k: Response(status=302, headers={'Location': 'https://evil.invalid/blob'})
        with self.assertRaises(d.DeliveryError): c.download_hash({'id': 2})

    def test_published_or_wrong_source_destination_is_rejected(self):
        c = d.Client.__new__(d.Client)
        good = dict(draft=True, published_at=None, target_commitish=d.SOURCE)
        c.json = lambda *a, **k: good
        self.assertEqual(c.draft(1), good)
        for change in [dict(draft=False), dict(published_at='published'), dict(target_commitish='main')]:
            c.json = lambda *a, value=dict(good, **change), **k: value
            with self.assertRaises(d.DeliveryError): c.draft(1)

    def test_anonymous_api_and_browser_must_both_deny_access(self):
        c = d.Client.__new__(d.Client)
        c.draft = lambda rid: None
        calls, deleted = [], []
        c.json = lambda path, **kw: deleted.append((path, kw))
        asset = dict(id=2, browser_download_url='https://github.com/'+d.REPO+'/releases/download/private/test.bin')
        def denied(url, **kw):
            calls.append((url, kw))
            return Response(status=404)
        c.request = denied
        c.private_asset(1, asset)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(call[1]['authenticated'] is False for call in calls))
        for status in [200, 302, 403]:
            c.request = lambda *a, s=status, **k: Response(status=s)
            with self.assertRaises(d.DeliveryError): c.private_asset(1, asset)
        self.assertEqual(len(deleted), 3)

    def test_upload_requires_a_real_roundtrip_not_only_asset_metadata(self):
        c = d.Client.__new__(d.Client)
        c.draft = lambda rid: None
        c.private_asset = lambda *args: None
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'fixture.bin'; p.write_bytes(b'fixture')
            asset = dict(id=2, state='uploaded', name='fixture.bin', size=7)
            c.request = lambda *a, **k: Response(json.dumps(asset).encode(), status=201)
            c.download_hash = lambda asset: ('0'*64, 7)
            with self.assertRaises(d.DeliveryError): c.upload(1, p, p.name)
            c.download_hash = lambda asset: (hashlib.sha256(p.read_bytes()).hexdigest(), 7)
            self.assertEqual(c.upload(1, p, p.name), asset)

    def test_probe_checks_destination_before_build_and_removes_its_own_file(self):
        calls = []
        class Client:
            def json(self, path, **kw):
                calls.append((path, kw))
                if kw.get('method') == 'POST':
                    self.data = kw['data']; return {'id': 123}
            def draft(self, rid): self.rid = rid
            def upload(self, rid, path, name):
                self.path = path
                self.payload = path.read_bytes()
                return {'id': 456}
        c = Client()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'outputs'
            with patch.dict(os.environ, {'GITHUB_RUN_ID':'123', 'GITHUB_RUN_ATTEMPT':'1', 'GITHUB_OUTPUT':str(output)}):
                d.preflight(c, Path(tmp))
            self.assertEqual(output.read_text(), 'release_id=123\n')
            self.assertTrue(c.data['draft'])
            self.assertEqual(c.data['target_commitish'], d.SOURCE)
            self.assertFalse(c.path.exists())
            self.assertEqual(len(c.payload), 64)
            self.assertEqual(calls[-1], ('/releases/assets/456', {'method':'DELETE'}))

    def test_workflow_freezes_application_and_transfers_before_cleanup(self):
        workflow = Path(__file__).resolve().parents[2]/'.github/workflows/private-alpha1274-delivery.yml'
        jobs = yaml.safe_load(workflow.read_text())['jobs']
        source_checkout = jobs['source-checks']['steps'][0]['with']
        self.assertEqual(source_checkout['ref'], d.SOURCE)
        build = jobs['build-arm64']
        self.assertEqual(build['env']['COMMIT_ID'], d.SOURCE)
        self.assertIn('private-destination', build['needs'])
        self.assertEqual(build['steps'][0]['with']['ref'], d.SOURCE)
        self.assertEqual(build['steps'][0]['with']['path'], 'approved')
        steps = build['steps']
        transfer = next(i for i,s in enumerate(steps) if 'Transfer verified APK' in s.get('name',''))
        verify = next(i for i,s in enumerate(steps) if s.get('name') == 'Verify APK against independently authorized certificate')
        cleanup = next(i for i,s in enumerate(steps) if s.get('if') == 'always()')
        self.assertLess(verify, transfer); self.assertLess(transfer, cleanup)
        self.assertTrue(any(':TMessagesProj:assembleConnectedAlpha' in s.get('run','') for s in steps))
        self.assertFalse(any('upload-artifact' in s.get('uses','') for s in steps))
        self.assertNotIn('age --', workflow.read_text())
        self.assertFalse(yaml.safe_load(workflow.read_text())['concurrency']['cancel-in-progress'])


if __name__ == '__main__': unittest.main()
