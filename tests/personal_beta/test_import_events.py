"""Only the new batch importer, using synthetic PR23 exports and real pinned PR24 code."""
import contextlib
import io
from unittest.mock import patch
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/personal_beta'))
import import_events as importer


class PersonalImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # An explicit pinned checkout is required; no download or silent skip.
        source = Path(os.environ['FLEXYGRAM_DIAGNOSTICS_SOURCE'])
        cls.analyzer, _ = importer.load_reviewed(source)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def event(self, phase, stamp, sid='b1_abc'):
        return dict(id=sid + '_1', op='chat_open', phase=phase,
                    timestamp_ns=stamp, clock='android_monotonic_ns')

    def batch(self, ident, events, sid='b1_abc', lost=0, abandoned=0):
        folder = self.root / (sid + '_' + str(ident))
        folder.mkdir()
        header = dict(session_id=sid, export_id=ident, observer_lost_events=lost,
                      observer_abandoned_operations=abandoned, records=len(events),
                      event_endpoint=importer.ENDPOINT, clock='android_monotonic_ns',
                      source='beta_local_synthetic_fixture')
        (folder / 'observer.json').write_text(json.dumps(header))
        (folder / 'events.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in events))
        return folder

    def test_cross_batch_operation_and_numeric_order(self):
        one = self.batch(1, [self.event('request', 100), self.event('accepted', 200)])
        two = self.batch(2, [self.event('presented', 300)])
        result = importer.assemble(self.analyzer, [two, one])
        self.assertEqual(result['records'], 3)
        self.assertEqual(result['quality'], 'COMPLETE_EVENT_SAMPLE_ONLY')
        self.assertEqual(result['interactions']['operations']['chat_open']['presented'], 1)

    def test_missing_first_batch_rejected_before_orphan_acceptance(self):
        two = self.batch(2, [self.event('presented', 300)])
        with self.assertRaisesRegex(ValueError, 'MISSING_OR_DUPLICATE_EXPORT_BATCH'):
            importer.assemble(self.analyzer, [two])

    def test_mixed_sessions_and_duplicate_batch_rejected(self):
        one = self.batch(1, [])
        other = self.batch(1, [], sid='b2_def')
        with self.assertRaisesRegex(ValueError, 'MIXED_ACTIVITY_SESSIONS'):
            importer.assemble(self.analyzer, [one, other])
        with self.assertRaisesRegex(ValueError, 'MISSING_OR_DUPLICATE_EXPORT_BATCH'):
            importer.assemble(self.analyzer, [one, one])

    def test_partial_export_and_wrong_record_count_rejected(self):
        one = self.batch(1, [])
        partial = one.with_name(one.name + '.partial')
        one.rename(partial)
        with self.assertRaisesRegex(ValueError, 'INCOMPLETE_OR_UNSAFE_EXPORT'):
            importer.assemble(self.analyzer, [partial])
        partial.rename(one)
        header = json.loads((one / 'observer.json').read_text())
        header['records'] = 1
        (one / 'observer.json').write_text(json.dumps(header))
        with self.assertRaisesRegex(ValueError, 'EXPORT_RECORD_COUNT_MISMATCH'):
            importer.assemble(self.analyzer, [one])

    def test_loss_abandonment_or_pending_never_certifies_performance(self):
        for lost, abandoned in ((0, 0), (1, 0), (0, 1)):
            with tempfile.TemporaryDirectory() as tmp:
                old = self.root
                self.root = Path(tmp)
                one = self.batch(1, [self.event('request', 100)], lost=lost, abandoned=abandoned)
                result = importer.assemble(self.analyzer, [one])
                self.assertEqual(result['quality'], 'INSUFFICIENT_FOR_PERFORMANCE_CLAIMS')
                self.assertEqual(result['observer_abandoned_operations'], abandoned)
                self.root = old

    def test_false_counter_and_event_session_spoof_rejected(self):
        one = self.batch(1, [self.event('request', 100, sid='b2_def')])
        with self.assertRaisesRegex(ValueError, 'EVENT_SESSION_MISMATCH'):
            importer.assemble(self.analyzer, [one])
        header = json.loads((one / 'observer.json').read_text())
        header['records'] = True
        (one / 'observer.json').write_text(json.dumps(header))
        with self.assertRaisesRegex(ValueError, 'INVALID_OBSERVER_COUNTER'):
            importer.assemble(self.analyzer, [one])

    def test_profile_is_declared_not_device_or_strict_16k_attestation(self):
        profile = dict(android_api=37, abi='arm64-v8a', page_bytes=16384, compat_mode_disabled=True)
        result = importer.device_profile(profile)
        self.assertFalse(result['observed_by_tool'])
        self.assertFalse(result['strict_16k_runtime_proven'])
        profile['page_bytes'] = 8192
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_PAGE_SIZE'):
            importer.device_profile(profile)

    def test_loss_counters_cannot_regress(self):
        one = self.batch(1, [], lost=2)
        two = self.batch(2, [], lost=1)
        with self.assertRaisesRegex(ValueError, 'REGRESSING_OBSERVER_COUNTER'):
            importer.assemble(self.analyzer, [one, two])

    def test_user_text_cannot_add_private_observer_fields(self):
        one = self.batch(1, [])
        header = json.loads((one / 'observer.json').read_text())
        header['conversation_text'] = 'SYNTHETIC_PRIVATE_TEXT'
        (one / 'observer.json').write_text(json.dumps(header))
        with self.assertRaisesRegex(ValueError, 'INVALID_OBSERVER_FIELDS'):
            importer.assemble(self.analyzer, [one])

    def test_early_crash_without_events_reuses_real_log_parser(self):
        log = self.root / 'private.log'
        log.write_text('123.000 10 10 E AndroidRuntime: FATAL EXCEPTION: main\n')
        profile = self.root / 'profile.json'
        profile.write_text(json.dumps(dict(android_api=37, abi='arm64-v8a', page_bytes=4096, compat_mode_disabled=None)))
        output = self.root / 'report.json'
        args = ['import_events.py', '--source-dir', os.environ['FLEXYGRAM_DIAGNOSTICS_SOURCE'],
                '--logcat', str(log), '--pids', '10', '--profile', str(profile), '--environment', 'synthetic',
                '--apk-sha256', '0' * 64, '--output', str(output)]
        with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(importer.main(), 0)
        result = json.loads(output.read_text())
        self.assertEqual(result['capture_environment'], 'synthetic')
        self.assertIsNone(result['events'])
        self.assertIsNone(result['frames'])
        self.assertFalse(result['android_execution_verified_by_importer'])
        self.assertEqual(result['logcat']['signal_counts']['java_fatal'], 1)
        self.assertNotIn('FATAL EXCEPTION', output.read_text())
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        with patch.object(sys, 'argv', args), self.assertRaises(FileExistsError):
            importer.main()  # never overwrite a prior report


    def test_framestats_requires_real_refresh_input_and_keeps_fps_unknown(self):
        frames = self.root / 'gfxinfo.txt'
        frames.write_text('---PROFILEDATA---\nFlags,IntendedVsync,FrameCompleted\n0,1000000,9000000\n---PROFILEDATA---\n')
        profile = self.root / 'profile.json'
        profile.write_text(json.dumps(dict(android_api=37, abi='arm64-v8a', page_bytes=4096, compat_mode_disabled=None)))
        output = self.root / 'report.json'
        args = ['import_events.py', '--source-dir', os.environ['FLEXYGRAM_DIAGNOSTICS_SOURCE'],
                '--gfxinfo', str(frames), '--profile', str(profile), '--environment', 'synthetic',
                '--apk-sha256', '0' * 64, '--output', str(output)]
        with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(importer.main(), 1)
        self.assertFalse(output.exists())
        args += ['--refresh-hz', '120']
        with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(importer.main(), 0)
        result = json.loads(output.read_text())
        self.assertEqual(result['frames']['metrics']['n'], 1)
        self.assertIsNone(result['frames']['presented_fps'])
        self.assertIsNone(result['frames']['actual_dropped_frames'])



if __name__ == '__main__':
    unittest.main()
