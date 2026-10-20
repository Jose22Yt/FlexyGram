"""Synthetic observations only. No Android, accounts, network or device commands."""
from pathlib import Path
import copy
import json
import math
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/beta_diagnostics'))
import analyze as a

PKG = 'io.github.jose22yt.flexygram.diagnostic'
SECRET = 'SYNTHETIC_SECRET_DO_NOT_EXPORT'


def meta(run='run0', repetition=0):
    conditions = dict.fromkeys(a.CONDITIONS, 'fixture')
    conditions.update(android_api=35, page_bytes=16384, refresh_hz=120, resolution='1080x2400',
                      charging=False, power_save=False, animation_scales=[1, 1, 1], observer_lost_events=0)
    return dict(schema=1, client='FlexyGram', apk_sha256='a'*64, source='synthetic',
                run_id=run, repetition=repetition, conditions=conditions)


def event(ident, phase, ms, op='chat_open'):
    return json.dumps(dict(id=ident, phase=phase, timestamp_ns=int(ms*1e6), op=op, clock='android_monotonic_ns'))


def sequence(duration=20, count=10, op='chat_open'):
    return '\n'.join(event('e'+str(i), phase, i*1000+offset, op) for i in range(count)
                     for phase, offset in [('request', 0), ('accepted', 2), ('presented', duration)])


def gfx(rows, extra=''):
    return '---PROFILEDATA---\nFlags,IntendedVsync,FrameCompleted'+extra+'\n'+rows+'\n---PROFILEDATA---\n'


def run_report(i, candidate=False):
    result = a.report(meta(('candidate' if candidate else 'base')+str(i), i), PKG, [],
                      event_text=sequence(40 if candidate else 20))
    return result


class LogTests(unittest.TestCase):
    def row(self, text, pid=123, tag='AndroidRuntime', stamp='100.500'):
        return f'{stamp} {pid} 125 E {tag}: {text}'

    def test_java_crash_scoped_to_target(self):
        r=a.logs(self.row('FATAL EXCEPTION: main '+SECRET), PKG, [123])
        self.assertEqual(r['signal_counts']['java_fatal'], 1)
        self.assertNotIn(SECRET, json.dumps(r))

    def test_quoted_crash_text_in_app_log_is_not_java_fatal(self):
        r=a.logs(self.row('Received message: FATAL EXCEPTION '+SECRET,tag='FileLog'),PKG,[123])
        self.assertEqual(r['signal_counts']['java_fatal'],0)

    def test_quoted_anr_text_in_app_log_is_not_system_anr(self):
        r=a.logs(self.row('Received message: ANR in '+PKG,tag='FileLog'),PKG,[123])
        self.assertEqual(r['signal_counts']['anr'],0)

    def test_other_process_does_not_count(self):
        self.assertIsNone(a.logs(self.row('FATAL EXCEPTION: main', pid=999), PKG, [123])['signal_counts'])

    def test_system_anr_exact_package(self):
        self.assertEqual(a.logs(self.row('ANR in '+PKG, pid=1,tag='ActivityManager'), PKG, [])['signal_counts']['anr'],1)

    def test_package_prefix_does_not_attribute_other_client(self):
        self.assertIsNone(a.logs(self.row('ANR in '+PKG+'.other',pid=1), PKG, [])['signal_counts'])

    def test_threadtime_supported_without_epoch_claim(self):
        r=a.logs('10-20 10:20:30.123 123 124 F libc: Fatal signal 11',PKG,[123])
        self.assertEqual(r['signal_counts']['native_crash'],1)
        self.assertFalse(r['epoch_window_scoped'])

    def test_threadtime_excluded_when_epoch_window_required(self):
        r=a.logs('10-20 10:20:30.123 123 124 F libc: Fatal signal 11',PKG,[123],[100,101])
        self.assertIsNone(r['signal_counts'])

    def test_window_rejects_old_errors(self):
        self.assertIsNone(a.logs(self.row('FATAL EXCEPTION',stamp='99.500'),PKG,[123],[100,101])['signal_counts'])

    def test_jni_python_and_native_load(self):
        r=a.logs('\n'.join(self.row(x+' '+SECRET) for x in ['JNI DETECTED ERROR','com.chaquo.python.PyException: ImportError','java.lang.UnsatisfiedLinkError: dlopen failed']),PKG,[123])
        self.assertEqual([r['signal_counts'][x] for x in ['jni','python','native_load']],[1,1,1])
        self.assertNotIn(SECRET,json.dumps(r))

    def test_choreographer_count_is_explicitly_reported(self):
        r=a.logs(self.row('Skipped 8 frames!',tag='Choreographer'),PKG,[123])
        self.assertEqual(r['choreographer_reported_skipped_frames'],8)

    def test_empty_or_unformatted_is_unknown(self):
        for text in ['',SECRET,'--------- beginning of main']:
            self.assertEqual(a.logs(text,PKG,[])['status'],'NO_ATTRIBUTED_DATA')

    def test_bad_scope_inputs_rejected(self):
        for package,pids,window in [('a;reboot',[123],None),(PKG,[True],None),(PKG,[],[200,100])]:
            with self.assertRaises(ValueError): a.logs('',package,pids,window)


class FrameTests(unittest.TestCase):
    def test_nanosecond_duration_and_refresh_budget(self):
        r=a.frames(gfx('0,1000000000,1010000000'),120)
        self.assertEqual(r['metrics']['p95_ms'],10)
        self.assertEqual(r['metrics']['over_budget_frames'],1)
        self.assertIsNone(r['presented_fps'])
        self.assertIsNone(r['actual_dropped_frames'])

    def test_high_refresh_does_not_use_60hz_budget(self):
        r=a.frames(gfx('0,1000000000,1010000000'),60)
        self.assertEqual(r['metrics']['over_budget_frames'],0)

    def test_flags_nonzero_excluded(self):
        r=a.frames(gfx('1,1,999999999'),120)
        self.assertEqual(r['metrics']['n'],0)
        self.assertIsNone(r['metrics']['p95_ms'])
        self.assertEqual(r['metrics']['excluded_flags'],1)

    def test_sentinels_and_reversed_timestamps_rejected(self):
        r=a.frames(gfx('0,1,9223372036854775807\n0,4,3\n0,0,100'),120)
        self.assertEqual(r['metrics']['invalid_rows'],3)
        self.assertEqual(r['metrics']['n'],0)

    def test_duplicates_do_not_inflate_samples(self):
        r=a.frames(gfx('0,100,200\n0,100,200'),120)
        self.assertEqual((r['metrics']['n'],r['metrics']['duplicates']),(1,1))

    def test_multiple_windows_require_selection(self):
        text=gfx('0,1,10000001')+gfx('0,2,20000002')
        self.assertIsNone(a.frames(text,120)['metrics'])
        self.assertEqual(a.frames(text,120,1)['metrics']['p95_ms'],20)

    def test_unknown_extra_columns_and_trailing_comma(self):
        text='---PROFILEDATA---\nFlags,IntendedVsync,FrameCompleted,GpuCompleted,\n0,1,10000001,10000002,\n---PROFILEDATA---'
        self.assertEqual(a.frames(text,120)['metrics']['n'],1)

    def test_real_deadline_optional(self):
        r=a.frames(gfx('0,100,100000100,50000000',',FrameDeadline'),120)
        self.assertEqual((r['metrics']['deadline_misses'],r['metrics']['deadline_samples']),(1,1))

    def test_bad_deadline_does_not_add_partial_valid_frame(self):
        r=a.frames(gfx('0,100,100000100,not-a-number',',FrameDeadline'),120)
        self.assertEqual((r['metrics']['invalid_rows'],r['metrics']['n']),(1,0))

    def test_window_limits_sample(self):
        r=a.frames(gfx('0,100,200\n0,300,500'),120,window_ns=[90,250])
        self.assertEqual((r['metrics']['n'],r['metrics']['outside_window']),(1,1))

    def test_missing_columns_and_truncation_fail(self):
        for text in ['---PROFILEDATA---\nFlags,IntendedVsync\n---PROFILEDATA---','---PROFILEDATA---\nFlags,IntendedVsync,FrameCompleted']:
            with self.assertRaises(ValueError): a.frames(text,120)

    def test_invalid_refresh_is_not_defaulted(self):
        for hz in [None,0,True,float('nan'),float('inf'),1000]:
            with self.assertRaises(ValueError): a.frames('',hz)

    def test_no_frames_is_not_zero_ms(self):
        self.assertIsNone(a.frames('No process found',120)['metrics'])


class EventTests(unittest.TestCase):
    def test_measures_only_matched_observed_phases(self):
        r=a.interactions(sequence())['operations']['chat_open']
        self.assertEqual((r['requested'],r['presented'],r['request_to_present']['p95_ms']),(10,10,20))

    def test_two_overlapping_taps_are_independently_paired(self):
        text='\n'.join([event('a','request',0),event('b','request',1),event('a','accepted',2),event('b','accepted',3),event('b','presented',4),event('a','presented',10)])
        self.assertEqual(a.interactions(text)['operations']['chat_open']['request_to_present']['max_ms'],10)

    def test_interrupted_transition_is_not_counted_completed(self):
        r=a.interactions(event('a','request',0,'transition_interrupt')+'\n'+event('a','cancelled',5,'transition_interrupt'))['operations']['transition_interrupt']
        self.assertEqual((r['cancelled'],r['presented']),(1,0))
        self.assertIsNone(r['request_to_present']['p95_ms'])
        self.assertEqual(r['request_to_cancel']['p95_ms'],5)

    def test_timeout_and_incomplete_stay_separate(self):
        r=a.interactions(event('a','request',0)+'\n'+event('b','request',1)+'\n'+event('a','timeout',100))['operations']['chat_open']
        self.assertEqual((r['timeout'],r['incomplete']),(1,1))

    def test_orphan_and_duplicate_rejected(self):
        for text in [event('a','accepted',1),event('a','request',1)+'\n'+event('a','request',2)]:
            with self.assertRaises(ValueError): a.interactions(text)

    def test_presentation_requires_acceptance(self):
        with self.assertRaises(ValueError): a.interactions(event('a','request',0)+'\n'+event('a','presented',1))

    def test_clock_regression_rejected(self):
        with self.assertRaises(ValueError): a.interactions(event('a','request',10)+'\n'+event('a','accepted',9))

    def test_mixed_clock_and_private_fields_rejected(self):
        for change in [{'clock':'wall_clock'},{'message':SECRET},{'timestamp_ns':True}]:
            row=json.loads(event('a','request',1));row.update(change)
            with self.assertRaises(ValueError): a.interactions(json.dumps(row))

    def test_theme_operations_are_distinct(self):
        r=a.interactions(sequence(op='theme_dark'))['operations']
        self.assertEqual(r['theme_dark']['presented'],10)
        self.assertEqual(r['theme_light']['presented'],0)

    def test_empty_events_are_unknown(self):
        self.assertEqual(a.interactions('')['status'],'NO_EVENT_DATA')


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.left=[run_report(i) for i in range(5)]
        self.right=[run_report(i,True) for i in range(5)]

    def test_synthetic_does_not_become_android_result(self):
        r=a.compare(self.left,self.right)
        self.assertEqual(r['status'],'SYNTHETIC_COMPARISON_ONLY')
        self.assertEqual(r['metrics']['chat_open']['status'],'CONSISTENT_OBSERVED_SLOWDOWN')

    def test_environment_mismatch_blocks(self):
        self.right[0]['metadata']['conditions']['refresh_hz']=144
        self.assertEqual(a.compare(self.left,self.right)['status'],'INCOMPARABLE')

    def test_unmeasured_thermal_condition_blocks(self):
        for r in self.left+self.right:r['metadata']['conditions']['thermal_state']='unknown'
        self.assertEqual(a.compare(self.left,self.right)['status'],'INCOMPARABLE')

    def test_missing_runs_and_duplicate_run_ids_block(self):
        self.assertEqual(a.compare(self.left[:1],self.right)['status'],'INCOMPARABLE')
        self.right[0]['metadata']['run_id']=self.left[0]['metadata']['run_id']
        self.assertEqual(a.compare(self.left,self.right)['status'],'INCOMPARABLE')

    def test_mixed_build_group_is_rejected(self):
        self.left[0]['metadata']['apk_sha256']='b'*64
        self.assertEqual(a.compare(self.left,self.right)['status'],'INCOMPARABLE')

    def test_unpaired_repetitions_are_rejected(self):
        self.right[0]['metadata']['repetition']=99
        self.assertEqual(a.compare(self.left,self.right)['status'],'INCOMPARABLE')

    def test_no_events_is_insufficient_not_improved(self):
        self.right[0]['interactions']=None
        result=a.compare(self.left,self.right)
        self.assertEqual(result['metrics']['chat_open']['status'],'INSUFFICIENT_OBSERVATIONS')
        self.assertEqual(result['status'],'INSUFFICIENT_OBSERVATIONS')

    def test_incomplete_interaction_blocks_latency_comparison(self):
        self.right[0]['interactions']['operations']['chat_open']['incomplete']=1
        self.assertEqual(a.compare(self.left,self.right)['metrics']['chat_open']['status'],'INSUFFICIENT_OBSERVATIONS')

    def test_timed_out_requests_cannot_make_surviving_samples_look_faster(self):
        row=self.right[0]['interactions']['operations']['chat_open']
        row.update(requested=20,timeout=10)
        self.assertEqual(a.compare(self.left,self.right)['metrics']['chat_open']['status'],'INSUFFICIENT_OBSERVATIONS')

    def test_lost_observer_events_block_comparison(self):
        for r in self.left+self.right:r['metadata']['conditions']['observer_lost_events']=1
        self.assertEqual(a.compare(self.left,self.right)['status'],'INCOMPARABLE')

    def test_noise_or_small_change_is_not_consistent_slowdown(self):
        self.right[0]['interactions']=a.interactions(sequence(21))
        self.assertEqual(a.compare(self.left,self.right)['metrics']['chat_open']['status'],'NO_CONSISTENT_SLOWDOWN_AT_THRESHOLD')

    def test_cross_client_comparison_allowed_with_equal_conditions(self):
        for r in self.right:r['metadata']['client']='Exteraless'
        self.assertEqual(a.compare(self.left,self.right)['status'],'SYNTHETIC_COMPARISON_ONLY')

    def test_frame_samples_must_be_scoped_and_large_enough(self):
        for r in self.left+self.right:r['frames']=a.frames(gfx('0,1,10000001'),120)
        self.assertEqual(a.compare(self.left,self.right)['metrics']['frame_p95_ms']['status'],'INSUFFICIENT_SCOPED_FRAMES')

    def test_scoped_frame_regression(self):
        for group,duration in [(self.left,10_000_000),(self.right,20_000_000)]:
            for r in group:
                text='\n'.join(f'0,{1+i*100_000_000},{1+i*100_000_000+duration}' for i in range(30))
                r['frames']=a.frames(gfx(text),120,window_ns=[0,4_000_000_000])
        self.assertEqual(a.compare(self.left,self.right)['metrics']['frame_p95_ms']['status'],'CONSISTENT_OBSERVED_SLOWDOWN')

    def test_metadata_forbids_secrets(self):
        m=meta();m['api_hash']=SECRET
        with self.assertRaises(ValueError):a.metadata(m)

    def test_strict_json_rejects_duplicates_and_nonfinite(self):
        for text in ['{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}']:
            with self.assertRaises(ValueError):a.strict_json(text)

    def test_missing_inputs_stay_null(self):
        r=a.report(meta(),PKG,[])
        self.assertIsNone(r['frames']);self.assertIsNone(r['logcat']);self.assertIsNone(r['interactions'])
        self.assertFalse(r['android_execution_verified_by_analyzer'])
