"""Offline design/scanner regressions only; no Android or real translator calls."""
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import unittest
import zipfile
from artifact_gate import scan
from inventory import collect, ROOT, SNAPSHOT
from policy_model import Context, Grant, Request, Provider as P, authorize, dispatch

SCOPE = 'a' * 64
APP = 'io.github.jose22yt.flexygram.synthetic'
CANARY = 'SYNTHETIC_TRANSLATION_PRIVATE_TEXT_NOT_REAL_32'


def archive(entries):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, content in entries.items():
            z.writestr(name, content)
    return data.getvalue()


class PolicyScenarios(unittest.TestCase):
    def setUp(self):
        self.ctx = Context(False, APP, SCOPE, 100, True, False)
        self.grant = Grant(P.OWN_OFFICIAL, APP, SCOPE, 200, True,
                           frozenset(['text', 'entities', 'poll', 'article']),
                           'https://synthetic.invalid/translate',
                           'https://synthetic.invalid/translate')
        self.request = Request(P.OWN_OFFICIAL, P.OWN_OFFICIAL, text=CANARY)
        self.calls = []

    def adapter(self, request):
        self.calls.append(request)
        return {'text':request.text, 'entities':request.entities}

    def test_diagnostic_denies_every_provider_before_adapter(self):
        for provider in P:
            request = replace(self.request, requested=provider, effective=provider)
            result = dispatch(lambda:Context(), request, replace(self.grant, provider=provider), self.adapter)
            self.assertEqual(result.reason, 'diagnostic_denied')
        self.assertEqual(self.calls, [])

    def test_diagnostic_identity_cannot_be_enabled_by_other_flags(self):
        self.assertFalse(authorize(replace(self.ctx, android_id=Context().android_id),
                                   self.request, self.grant).allowed)

    def test_legacy_direct_calls_and_forged_grants_never_authorized(self):
        for provider in [P.LEGACY_LOCAL, P.LEGACY_LIBRARY, P.LEGACY_WEB]:
            request = replace(self.request, requested=provider, effective=provider)
            result = dispatch(lambda:self.ctx, request, replace(self.grant, provider=provider), self.adapter)
            self.assertEqual(result.reason, 'provider_not_authorized')
        self.assertEqual(self.calls, [])

    def test_missing_unverified_foreign_or_wrong_provider_grants(self):
        for grant in [None, replace(self.grant, rights_verified=False),
                      replace(self.grant, android_id='com.exteraless.app'),
                      replace(self.grant, provider=P.TELEGRAM)]:
            self.assertFalse(authorize(self.ctx, self.request, grant).allowed)

    def test_stale_scope_and_expiry_denied(self):
        for grant in [replace(self.grant, scope='b'*64),
                      replace(self.grant, expires_at=100)]:
            self.assertEqual(authorize(self.ctx, self.request, grant).reason, 'grant_stale')
        self.assertFalse(authorize(replace(self.ctx, scope=''), self.request, self.grant).allowed)

    def test_queue_rechecks_scope_and_isolation_at_execution(self):
        state = [self.ctx]
        queued = lambda:dispatch(lambda:state[0], self.request, self.grant, self.adapter)
        state[0] = replace(self.ctx, scope='b'*64)
        self.assertEqual(queued().reason, 'grant_stale')
        state[0] = replace(self.ctx, isolated=True)
        self.assertEqual(queued().reason, 'diagnostic_denied')
        self.assertEqual(self.calls, [])

    def test_silent_provider_switch_denied_and_selection_scoped(self):
        request = replace(self.request, requested=P.TELEGRAM)
        self.assertEqual(authorize(self.ctx, request, self.grant).reason, 'provider_switch_denied')
        self.assertFalse(authorize(self.ctx, replace(request, selected_scope='b'*64), self.grant).allowed)
        self.assertTrue(authorize(self.ctx, replace(request, selected_scope=SCOPE), self.grant).allowed)

    def test_unavailable_capability_is_not_remapped_to_google(self):
        request = replace(self.request, feature='rich_content_unreviewed')
        self.assertEqual(dispatch(lambda:self.ctx, request, self.grant, self.adapter).reason,
                         'capability_unavailable')
        self.assertEqual(self.calls, [])

    def test_foreign_insecure_or_changed_endpoints_denied(self):
        for endpoint in ['http://synthetic.invalid/', 'https://user:password@synthetic.invalid/',
                         'https://synthetic.invalid/?q='+CANARY, 'https://synthetic.invalid/#token',
                         'https://synthetic.invalid:444/', 'https://synthetic.invalid:bad/',
                         'https://translate-pa.googleapis.com/v1/translate',
                         'https://translate.google.com/translate_a/single']:
            grant = replace(self.grant, endpoint=endpoint, approved_endpoint=endpoint)
            self.assertFalse(authorize(self.ctx, self.request, grant).allowed)
        self.assertFalse(authorize(self.ctx, self.request,
                                   replace(self.grant, approved_endpoint='https://other.invalid/')).allowed)

    def test_network_and_telegram_session_are_separate_requirements(self):
        self.assertFalse(authorize(replace(self.ctx, network_permitted=False),
                                   self.request, self.grant).allowed)
        request = replace(self.request, requested=P.TELEGRAM, effective=P.TELEGRAM)
        grant = replace(self.grant, provider=P.TELEGRAM)
        self.assertEqual(authorize(self.ctx, request, grant).reason, 'session_denied')
        self.assertTrue(authorize(replace(self.ctx, telegram_session_authorized=True), request, grant).allowed)

    def test_local_model_absence_does_not_download_or_fall_back(self):
        request = replace(self.request, requested=P.LOCAL, effective=P.LOCAL)
        grant = replace(self.grant, provider=P.LOCAL, model_installed=False)
        self.assertEqual(dispatch(lambda:self.ctx, request, grant, self.adapter).reason, 'model_unavailable')
        self.assertEqual(self.calls, [])
        self.assertTrue(authorize(replace(self.ctx, network_permitted=False), request,
                                  replace(grant, model_installed=True)).allowed)

    def test_fake_dispatch_preserves_payload_without_logging_it(self):
        request = replace(self.request, entities=((0, 4, 'bold'),))
        result = dispatch(lambda:self.ctx, request, self.grant, self.adapter)
        self.assertEqual(result.value, {'text':CANARY, 'entities':request.entities})
        self.assertNotIn(CANARY, repr(result)+repr(request))
        self.assertEqual(len(self.calls), 1)

    def test_failure_is_terminal_and_exception_message_is_not_propagated(self):
        def failing(request):
            self.calls.append(request)
            raise OSError(CANARY)
        result = dispatch(lambda:self.ctx, self.request, self.grant, failing)
        self.assertEqual(result.reason, 'provider_failed')
        self.assertEqual(len(self.calls), 1)
        self.assertNotIn(CANARY, repr(result))

    def test_cancellation_is_not_converted_to_failure_or_fallback(self):
        import asyncio
        def cancelled(request):
            self.calls.append(request)
            raise asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            dispatch(lambda:self.ctx, self.request, self.grant, cancelled)
        self.assertEqual(len(self.calls), 1)

    def test_repeated_invocation_has_no_cached_authorization(self):
        self.assertEqual(dispatch(lambda:self.ctx, self.request, self.grant, self.adapter).reason, 'completed')
        self.assertEqual(dispatch(lambda:replace(self.ctx, now=201), self.request,
                                  self.grant, self.adapter).reason, 'grant_stale')
        self.assertEqual(len(self.calls), 1)


class ScannerScenarios(unittest.TestCase):
    def setUp(self):
        self.fake_key = b'AIza'+b'X'*35  # Synthetic syntax fixture, not a credential.
        self.cert = b'a'*40
        self.registry = {'retired_key_sha256':[hashlib.sha256(self.fake_key).hexdigest()],
                         'foreign_package_markers':['test.foreign.synthetic'],
                         'foreign_certificate_sha256':[hashlib.sha256(self.cert).hexdigest()]}

    def test_clean_synthetic_container(self):
        self.assertTrue(scan(archive({'classes.dex':b'empty'}), self.registry)['passed'])

    def test_known_key_in_nested_jar_fails_without_printing_value(self):
        result = scan(archive({'assets/runtime.imy':archive({'classes.jar':archive({'x.class':self.fake_key})})}), self.registry)
        self.assertGreater(result['known_key_occurrences'], 0)
        self.assertFalse(result['passed'])
        self.assertNotIn(self.fake_key.decode(), json.dumps(result))

    def test_utf16_key_and_foreign_identity_are_detected(self):
        payload = (self.fake_key.decode()+' test.foreign.synthetic '+self.cert.decode()).encode('utf-16le')
        result = scan(archive({'resources.arsc':payload}), self.registry)
        for field in ['known_key_occurrences','foreign_package_occurrences','foreign_certificate_occurrences']:
            self.assertGreater(result[field], 0)
        self.assertFalse(result['passed'])

    def test_unknown_client_key_is_reported_without_false_clean_claim(self):
        result = scan(archive({'classes.dex':b'AIza'+b'Y'*35}), self.registry)
        self.assertEqual(result['known_key_occurrences'], 0)
        self.assertGreater(result['client_key_candidates'], 0)
        self.assertFalse(result['passed'])

    def test_foreign_certificate_case_and_package_separately(self):
        for payload, field in [(self.cert.upper(), 'foreign_certificate_occurrences'),
                               (b'test.foreign.synthetic', 'foreign_package_occurrences')]:
            result = scan(archive({'classes.dex':payload}), self.registry)
            self.assertGreater(result[field], 0)
            self.assertFalse(result['passed'])

    def test_apk_structure_is_required_only_when_requested(self):
        self.assertFalse(scan(archive({'classes.jar':b'x'}), self.registry, require_apk=True)['complete'])
        result = scan(archive({'AndroidManifest.xml':b'synthetic','classes.dex':b'synthetic'}),
                      self.registry, require_apk=True)
        self.assertTrue(result['passed'])  # Shape only, not a valid/installable Android APK.

    def test_corrupt_archive_does_not_pass(self):
        result = scan(b'PK\x03\x04broken '+CANARY.encode(), self.registry)
        self.assertFalse(result['complete'])
        self.assertNotIn(CANARY, json.dumps(result))

    def test_nested_depth_and_expansion_limits_fail_closed(self):
        nested = archive({'child.imy':archive({'x':b'payload'})})
        self.assertFalse(scan(nested, self.registry, max_depth=1)['complete'])
        self.assertFalse(scan(nested, self.registry, max_expanded_bytes=8)['complete'])
        self.assertFalse(scan(archive({'x':b'a','y':b'b'}), self.registry, max_entries=1)['complete'])

    def test_embedded_service_configuration_is_reported(self):
        result = scan(archive({'assets/google-services.json':b'{}'}), self.registry)
        self.assertEqual(result['embedded_service_configurations'], 1)
        self.assertFalse(result['passed'])


class SourcePreparationChecks(unittest.TestCase):
    def test_source_inventory_matches_explicit_review(self):
        self.assertEqual(collect(), json.loads(SNAPSHOT.read_text()))

    def test_llm_direct_fallback_and_forced_google_rich_content_are_in_inventory(self):
        rows = collect()['callsites']
        llm = [r for r in rows if r['path'].endswith('/LLMTranslator.kt')
               and r['symbol']=='GoogleAppTranslator.doTranslate']
        self.assertEqual(len(llm), 3)
        self.assertTrue(any(r['path'].endswith('/MessageTrans.kt') and r['line']==389 for r in rows))

    def test_shared_engines_and_isolation_sources_preserved(self):
        snapshot = json.loads(Path(__file__).with_name('preserved_sources.json').read_text())
        for path, expected in snapshot['sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), expected, path)


if __name__ == '__main__':
    unittest.main()
