"""Real collector/parsers with synthetic ADB; never touches Android or signs files."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/personal_beta'))
import first_start as tool

HEADER = 'ACTIVITY MANAGER PROCESS EXIT INFO (dumpsys activity exit-info)\n'
PRIVATE = 'SYNTHETIC_PRIVATE_TOKEN_URL_PASSWORD'


def exit_text(reason=4, process=tool.PACKAGE, index=0):
    return HEADER + f'''  package: {tool.PACKAGE}
    Historical Process Exit for uid=12345
      ApplicationExitInfo #{index}:
        timestamp=2026-10-20 13:00:00.000 pid=123 realUid=12345 packageUid=12345 definingUid=12345 user=0
        process={process} reason={reason} (TEST) subreason=0 (UNKNOWN) status=0
        importance=100 pss=1MB rss=1MB description={PRIVATE} state=empty trace=null
'''


class FakeAdb:
    def __init__(self):
        self.guard = tool.Adb(Path('/not-executed/adb'),'USB_TEST')
        self.calls = []
        self.clock_calls = self.exit_calls = self.stat_calls = 0
        self.before = HEADER
        self.after = HEADER
        self.version = f'  Package [{tool.PACKAGE}] (abcd):\n    versionCode=1261 minSdk=24 targetSdk=36\n    versionName=13.0.2\n'
        self.installed_hash = 'a'*64
        self.pid = '123\n'
        self.reuse = False
        self.uid = 12345
        self.log = '\n'.join([
            '10.100000 123 123 E linker: dlopen failed: '+PRIVATE,
            '10.200000 123 123 E python.stderr: ModuleNotFoundError: '+PRIVATE,
            '10.300000 123 123 E AndroidRuntime: FATAL EXCEPTION: main',
            '10.400000 123 123 E art: JNI DETECTED ERROR '+PRIVATE,
            '10.500000 999 999 E libc: Fatal signal 11 '+PRIVATE,
            '10.600000 123 123 E ChatMessage: ImportError quoted conversation '+PRIVATE])
        self.frames = '---PROFILEDATA---\nFlags,IntendedVsync,FrameCompleted\n0,1000000,18000000\n---PROFILEDATA---\n'
        self.batches = {}

    def allowed(self, args):
        return self.guard.allowed(args)

    def read(self, args, *, hash_only=False):
        if not self.allowed(args):
            raise AssertionError('Unsafe collector command')
        self.calls.append(args)
        if args == ['get-state']: return 'device\n'
        if args == ['get-devpath']: return 'usb:1:2\n'
        if args == ['shell','am','get-current-user']: return '0\n'
        if args[:3] == ['shell','dumpsys','package']: return self.version
        if args[:3] == ['shell','pm','path']: return 'package:/data/app/test/base.apk\n'
        if args[:2] == ['exec-out','cat']:
            if not hash_only: raise AssertionError('APK bytes should only be hashed')
            return self.installed_hash
        if args[:4] == ['shell','dumpsys','activity','exit-info']:
            self.exit_calls += 1
            return self.before if self.exit_calls == 1 else self.after
        if args[:2] == ['shell','pidof']: return self.pid
        if args[:2] == ['shell','date']:
            self.clock_calls += 1
            return '10.000000000\n' if self.clock_calls == 1 else '11.000000000\n'
        if args[:2] == ['shell','cat']:
            if args[2].endswith('/cmdline'): return tool.PACKAGE+'\0'
            if args[2].endswith('/status'): return f'Name:\tbeta\nUid:\t{self.uid}\t{self.uid}\t{self.uid}\t{self.uid}\n'
            self.stat_calls += 1
            stamp = '222' if self.reuse and self.stat_calls > 1 else '111'
            return '123 (beta app) '+' '.join(['S']+['0']*18+[stamp])
        if args[0] == 'logcat': return self.log
        if args[:4] == ['shell','dumpsys','activity','activities']:
            return '  mResumedActivity: ActivityRecord{abc u0 '+tool.PACKAGE+'/'+tool.ENTRY+' t1}\n'
        if args[:3] == ['shell','dumpsys','gfxinfo']: return self.frames
        if args[:2] == ['shell','getprop']:
            return '37\n' if args[-1].endswith('sdk') else 'arm64-v8a\n'
        if args[:2] == ['shell','getconf']: return '4096\n'
        if args[:2] == ['exec-out','run-as']: return self.batches[args[-1]]
        raise AssertionError('Unexpected collector command')


class FirstStartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(os.environ['PR24_SOURCE_DIR'])
        cls.analyzer, _ = tool.import_events.load_reviewed(source)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        apk = self.directory/'approved.apk'
        apk.write_bytes(b'synthetic not an APK')
        self.args = SimpleNamespace(approved_apk=apk, apk_sha256=tool.digest(apk),
            apksigner=self.directory/'inert-apksigner', certificate_sha256='b'*64,
            version_code='1261',version_name='13.0.2',commit='c'*40,
            observe_seconds=0,refresh_hz=60,stream=None,exports=[])
        self.adb = FakeAdb()
        self.adb.installed_hash = self.args.apk_sha256
        self.enterContext(patch.object(tool,'check_signature',return_value='b'*64))

    def capture(self):
        with redirect_stdout(io.StringIO()):
            return tool.collect(self.args,self.adb,self.analyzer,self.directory,sleeper=lambda _:None)

    def test_plan_has_no_subprocess_and_no_authorization(self):
        with patch.object(subprocess,'Popen',side_effect=AssertionError('No process')), redirect_stdout(io.StringIO()) as out:
            self.assertEqual(tool.main([]),0)
        self.assertFalse(json.loads(out.getvalue())['adb_executed'])

    def test_jni_python_and_fatal_signals_are_sanitized(self):
        result = self.capture()
        signals = result['logcat']['signal_counts']
        self.assertEqual(signals['native_load'],1)
        self.assertEqual(signals['jni'],1)
        self.assertEqual(signals['python'],1)
        self.assertEqual(signals['java_fatal'],1)
        self.assertEqual(signals['native_crash'],0)
        self.assertNotIn(PRIVATE,json.dumps(result))
        self.assertNotIn('USB_TEST',json.dumps(result))
        self.assertEqual(result['python_initialized'],'UNKNOWN_REQUIRES_LOCAL_PYTHON_PROBE')
        self.assertEqual(result['activity']['oncreate_completed'],'UNKNOWN')

    def test_other_pid_and_quoted_app_messages_not_classified(self):
        self.adb.log = '10.2 999 999 E AndroidRuntime: FATAL EXCEPTION: other\n10.3 123 123 E ChatMessage: ModuleNotFoundError quoted\n'
        result = self.capture()
        self.assertIsNone(result['logcat']['signal_counts'])
        self.assertNotEqual(result['status'],'OBSERVED_ERROR_EVIDENCE')

    def test_os_crash_native_anr_and_initialization_are_not_normal_exit(self):
        for reason in (4,5,6,7):
            with self.subTest(reason=reason):
                self.adb.exit_calls=0
                self.adb.after=exit_text(reason)
                result=self.capture()
                self.assertEqual(result['exit_history']['confirmed_error_reasons'],[reason])

    def test_exit_self_and_user_requested_not_falsely_called_crashes(self):
        for reason in (1,10,11,3):
            observed=tool.exit_delta(set(),tool.exits(exit_text(reason)))
            self.assertEqual(observed['confirmed_error_reasons'],[])
            self.assertEqual(observed['exit_self'],int(reason==1))

    def test_foreign_process_and_package_prefix_ignored(self):
        foreign=exit_text(4,tool.PACKAGE+'.unrelated')
        self.assertEqual(tool.exits(foreign),set())
        other_user=exit_text().replace(' user=0',' user=10')
        self.assertEqual(tool.exits(other_user,0),set())
        foreign=exit_text().replace('package: '+tool.PACKAGE,'package: '+tool.PACKAGE+'.unrelated')
        self.assertEqual(tool.exits(foreign),set())

    def test_history_indices_can_shift_without_new_crash(self):
        before=tool.exits(exit_text(index=0))
        after=tool.exits(exit_text(index=3))
        self.assertEqual(tool.exit_delta(before,after)['confirmed_error_reasons'],[])

    def test_truncated_or_denied_history_is_unknown(self):
        for value in (None,'Permission Denial\n',exit_text().replace(' status=0',''),HEADER+'unexpected output'):
            self.assertIsNone(tool.exits(value))
        self.assertEqual(tool.exit_delta(None,set())['status'],'UNKNOWN')
        self.assertEqual(tool.exits(HEADER+'Last Timestamp of Persistence Into Persistent Storage: 2026-10-20 13:00:00.000\n'),set())

    def test_no_live_process_does_not_assert_success_or_call_global_logcat(self):
        self.adb.pid=''
        result=self.capture()
        self.assertEqual(result['logcat']['status'],'UNKNOWN_NO_VERIFIED_LIVE_MAIN_PROCESS')
        self.assertFalse(any(c[0]=='logcat' for c in self.adb.calls))

    def test_pid_reuse_discards_messages(self):
        self.adb.reuse=True
        result=self.capture()
        self.assertEqual(result['logcat']['status'],'UNKNOWN_PROCESS_ENDED_OR_REUSED_LOGS_DISCARDED')
        self.assertNotIn('signal_counts',result['logcat'])
        self.adb.uid=1012345
        self.adb.calls=[]
        result=self.capture()
        self.assertEqual(result['logcat']['status'],'UNKNOWN_PROCESS_OR_CLOCK_UNAVAILABLE')
        self.assertFalse(any(c[0]=='logcat' for c in self.adb.calls))

    def test_unavailable_or_malformed_logs_tolerated(self):
        self.adb.log='unparsed private line '+PRIVATE
        result=self.capture()
        self.assertIsNone(result['logcat']['signal_counts'])
        self.assertNotIn(PRIVATE,json.dumps(result))

    def test_real_pinned_framestats_parser_not_invented_fps(self):
        result=self.capture()['framestats']
        self.assertEqual(result['metrics']['n'],1)
        self.assertEqual(result['metrics']['p95_ms'],17)
        self.assertIsNone(result['presented_fps'])
        self.adb.frames=self.adb.frames.replace('---PROFILEDATA---\n','',1)
        result=self.capture()
        self.assertIsNone(result['framestats']['presented_fps'] if result['framestats'] else None)

    def test_installed_apk_mismatch_blocks_before_logs(self):
        self.adb.installed_hash='d'*64
        with self.assertRaises(ValueError):self.capture()
        self.assertFalse(any(c[0]=='logcat' for c in self.adb.calls))

    def test_installed_version_and_similar_package_fail_closed(self):
        original=self.adb.version
        for value in (original.replace('1261','1262'),original.replace(tool.PACKAGE,tool.PACKAGE+'.evil')):
            self.adb.version=value
            with self.assertRaises(ValueError):self.capture()

    def test_command_allowlist_rejects_all_mutating_or_broad_commands(self):
        dangerous=[['install','file.apk'],['shell','am','start',tool.PACKAGE],['shell','input','keyevent','4'],
                   ['shell','settings','put','x','y'],['logcat','-c'],['logcat','-d'],['root'],
                   ['shell','dumpsys','account'],['exec-out','run-as',tool.PACKAGE,'cat','shared_prefs/x.xml'],
                   ['exec-out','cat','/data/app/../other/base.apk'],['shell','dumpsys','activity','exit-info']]
        for command in dangerous:
            with self.subTest(command=command):self.assertFalse(self.adb.allowed(command))
        for serial in ('host:5555','-s','emulator-5554','USB;reboot','USB\nSERIAL'):
            with self.assertRaises(ValueError):tool.Adb(Path('/adb'),serial)

    def test_authorization_requires_exact_scope_hash_certificate_and_device(self):
        path=self.directory/'authorization.json'
        self.args.authorization=path
        self.args.serial='USB_TEST'
        valid=dict(schema=1,scope=tool.SCOPE,package=tool.PACKAGE,authorized=True,
                   apk_sha256=self.args.apk_sha256,certificate_sha256='b'*64,
                   device_serial='USB_TEST',approval_reference='synthetic authorization')
        path.write_text(json.dumps(valid))
        tool.authorize(self.args)
        for field,value in [('scope','Diagnostic_lab_only'),('authorized',False),('apk_sha256','0'*64),
                            ('certificate_sha256','0'*64),('device_serial','OTHER')]:
            data=dict(valid);data[field]=value;path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):tool.authorize(self.args)

    def test_cli_missing_authorization_never_contacts_adb(self):
        with patch.object(tool.socket,'create_connection',side_effect=AssertionError('No device')), redirect_stdout(io.StringIO()) as out:
            self.assertEqual(tool.main(['--execute']),1)
        self.assertIn('BLOCKED',out.getvalue())

    def test_log_window_begins_before_operator_actions(self):
        def actions(_):
            self.assertEqual(self.adb.clock_calls,1)
            self.assertFalse(any(c[0]=='logcat' for c in self.adb.calls))
        with redirect_stdout(io.StringIO()):
            tool.collect(self.args,self.adb,self.analyzer,self.directory,sleeper=actions)

    def test_exports_reuse_pr26_and_discard_invalid_private_input(self):
        name='babc_123_1'
        self.adb.batches={f'files/beta-observer/{name}/observer.json':PRIVATE,
                          f'files/beta-observer/{name}/events.jsonl':PRIVATE}
        with self.assertRaises(ValueError):
            tool.export_batches(self.adb,self.analyzer,[name],self.directory)
        self.assertFalse((self.directory/name).exists())
        self.assertFalse(any(PRIVATE in p.read_text() for p in self.directory.rglob('*') if p.is_file()))
        for bad in ('../escape','babc_123_1.partial','babc_123_1;cat'):
            with self.assertRaises(ValueError):
                tool.export_batches(self.adb,self.analyzer,[bad],self.directory)

    def test_valid_exports_go_through_existing_importer(self):
        name='babc_123_1'
        header=dict(session_id='babc_123',export_id=1,observer_lost_events=0,
                    observer_abandoned_operations=0,records=3,event_endpoint=tool.import_events.ENDPOINT,
                    clock='android_monotonic_ns',source='beta_local_synthetic_fixture')
        records='\n'.join(json.dumps(dict(id='babc_123_1',op='startup',phase=phase,timestamp_ns=stamp,
                                           clock='android_monotonic_ns'))
                          for phase,stamp in [('request',1),('accepted',2),('presented',3)])+'\n'
        self.adb.batches={f'files/beta-observer/{name}/observer.json':json.dumps(header),
                          f'files/beta-observer/{name}/events.jsonl':records}
        self.args.exports=[name]
        result=self.capture()
        self.assertEqual(result['events']['quality'],'COMPLETE_EVENT_SAMPLE_ONLY')
        self.assertEqual(result['activity']['first_scene_observer'],'PRESENTED_EVENT_OBSERVED')
        self.assertEqual(os.stat(self.directory/name/'events.jsonl').st_mode & 0o777,0o600)

    def test_adb_transport_env_is_local_and_failures_do_not_expose_stderr(self):
        calls=[]
        class FakeProcess:
            returncode=0
            def __init__(self,command,**kwargs):
                calls.append((command,kwargs['env']))
                kwargs['stdout'].write(b'device\n')
                kwargs['stdout'].flush()
                kwargs['stderr'].write(PRIVATE.encode())
            def poll(self):return self.returncode
        with patch.dict(os.environ,{'ADB_SERVER_SOCKET':'tcp:external:5555','ADB_VENDOR_KEYS':PRIVATE}), patch.object(tool.subprocess,'Popen',FakeProcess):
            actual=tool.Adb(Path('/not-executed/adb'),'USB_TEST').read(['get-state'])
        self.assertEqual(actual,'device\n')
        self.assertEqual(calls[0][0][1:5],['-H','127.0.0.1','-P','5037'])
        self.assertNotIn('ADB_VENDOR_KEYS',calls[0][1])
        self.assertNotIn(PRIVATE,str(calls))
        self.assertEqual(tool.error_code(OSError(PRIVATE)),'READ_OR_FORMAT_UNAVAILABLE')

    def test_cli_private_report_and_existing_output_not_overwritten(self):
        authorization=self.directory/'authorization.json'
        authorization.write_text(json.dumps(dict(schema=1,scope=tool.SCOPE,package=tool.PACKAGE,
            authorized=True,apk_sha256=self.args.apk_sha256,certificate_sha256='b'*64,
            device_serial='USB_TEST',approval_reference='synthetic authorization')))
        output=self.directory/'new-report'
        argv=['--execute','--authorization',str(authorization),'--source-dir',os.environ['PR24_SOURCE_DIR'],
              '--output-dir',str(output),'--adb','/not-executed/adb','--serial','USB_TEST',
              '--approved-apk',str(self.args.approved_apk),'--apksigner','/not-executed/apksigner',
              '--apk-sha256',self.args.apk_sha256,'--certificate-sha256','b'*64,'--commit','c'*40,
              '--version-code','1261','--version-name','13.0.2','--observe-seconds','0']
        with patch.object(tool.socket,'create_connection'), patch.object(tool,'Adb',return_value=self.adb), redirect_stdout(io.StringIO()):
            self.assertEqual(tool.main(argv),0)
            previous=(output/'report.json').read_bytes()
            self.assertEqual(tool.main(argv),1)
        self.assertEqual(previous,(output/'report.json').read_bytes())
        self.assertEqual(os.stat(output).st_mode & 0o777,0o700)
        self.assertEqual(os.stat(output/'report.json').st_mode & 0o777,0o600)
        self.assertNotIn(PRIVATE,previous.decode())


if __name__=='__main__':unittest.main()
