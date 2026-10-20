"""Real collector control flow with subprocess doubles. Never executes ADB or ip."""
from pathlib import Path
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/beta_diagnostics'))
import capture as c
from test_analyzers import meta, PKG, SECRET


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.adb=self.root/'adb';self.adb.touch()
        self.output=self.root/'evidence';self.calls=[]
        self.metadata=meta();self.metadata['source']='android_lab'
        self.receipt=dict(schema=1,serial='emulator-5554',package=PKG,
                          network_namespace='net:[fixture]',known_pids=[123],
                          **{x:True for x in c.ATTESTATIONS})
        self.receipt['metadata_sha256']=hashlib.sha256(json.dumps(self.metadata,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self.readlink=patch.object(c.os,'readlink',return_value='net:[fixture]');self.readlink.start();self.addCleanup(self.readlink.stop)
        self.glob=patch.object(c.Path,'glob',return_value=iter(()));self.glob.start();self.addCleanup(self.glob.stop)
        self.outputs={}

    def runner(self,command,**kwargs):
        self.calls.append((command,kwargs))
        if tuple(command) in self.outputs:return self.outputs[tuple(command)]
        if command[:4]==['ip','-j','link','show']:text='[{"ifname":"lo","flags":["UP"]}]'
        elif command[0]=='ip':text='[]'
        else:
            parts=command[3:]
            if parts==['get-state']:text='device\n'
            elif parts==['shell','getprop','ro.kernel.qemu']:text='1\n'
            elif parts==['shell','getprop','ro.build.version.sdk']:text='35\n'
            elif parts==['shell','getconf','PAGE_SIZE']:text='16384\n'
            elif parts==['shell','getprop','ro.product.cpu.abi']:text='arm64-v8a\n'
            elif parts==['shell','pm','path',PKG]:text='package:/data/app/synthetic/base.apk\n'
            elif parts==['shell','sha256sum','/data/app/synthetic/base.apk']:text=self.metadata['apk_sha256']+'  /data/app/synthetic/base.apk\n'
            elif parts==['shell','dumpsys','account']:text='Accounts: 0\n'
            elif parts==['shell','pidof',PKG]:text='123\n'
            elif parts[0]=='logcat':text='100.500 123 124 E AndroidRuntime: FATAL EXCEPTION '+SECRET
            elif parts==['shell','dumpsys','gfxinfo',PKG,'framestats']:text='No frames rendered'
            else:raise AssertionError('Unexpected command '+str(command))
        return SimpleNamespace(returncode=0,stdout=text,stderr='')

    def execute(self):return c.collect(self.adb,'emulator-5554',PKG,self.metadata,self.receipt,self.output,runner=self.runner)

    def override(self,tail,text='',code=0):
        self.outputs[tuple([str(self.adb),'-s','emulator-5554',*tail])]=SimpleNamespace(returncode=code,stdout=text,stderr=SECRET)

    def test_successful_double_capture_keeps_no_raw_secrets(self):
        result=self.execute()
        self.assertTrue(result['capture']['read_only'])
        self.assertFalse(result['android_execution_verified_by_analyzer'])
        self.assertNotIn(SECRET,(self.output/'report.json').read_text())
        self.assertEqual(list(p.name for p in self.output.iterdir()),['report.json'])

    def test_private_output_permissions(self):
        self.execute()
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode),0o700)
        self.assertEqual(stat.S_IMODE((self.output/'report.json').stat().st_mode),0o600)

    def test_invalid_serial_and_shell_package_cannot_run(self):
        for serial,package in [('emulator-65535',PKG),('localhost:5555',PKG),('emulator-5554',PKG+';reboot')]:
            with self.assertRaises(ValueError):c.command_plan(self.adb,serial,package)
        self.assertEqual(self.calls,[])

    def test_missing_authorization_never_contacts_device(self):
        self.receipt['authorized_read_only_capture']=False
        with self.assertRaises(ValueError):self.execute()
        self.assertEqual(self.calls,[])

    def test_receipt_scope_mismatch_blocks(self):
        self.receipt['package']='another.client'
        with self.assertRaises(ValueError):self.execute()
        self.assertEqual(self.calls,[])

    def test_changed_metadata_blocks_before_probes(self):
        self.metadata['conditions']['refresh_hz']=144
        with self.assertRaises(ValueError):self.execute()
        self.assertEqual(self.calls,[])

    def test_unknown_namespace_blocks_before_adb(self):
        self.receipt['network_namespace']='net:[wrong]'
        with self.assertRaises(ValueError):self.execute()
        self.assertEqual(self.calls,[])

    def test_uplink_blocks_before_adb(self):
        self.outputs[('ip','-j','link','show')]=SimpleNamespace(returncode=0,stdout='[{"ifname":"eth0","flags":["UP"]}]',stderr='')
        with self.assertRaises(ValueError):self.execute()
        self.assertTrue(all(command[0]=='ip' for command,_ in self.calls))

    def test_default_route_blocks_before_adb(self):
        self.outputs[('ip','-j','route','show','table','all')]=SimpleNamespace(returncode=0,stdout='[{"dev":"lo","dst":"default"}]',stderr='')
        with self.assertRaises(ValueError):self.execute()
        self.assertTrue(all(command[0]=='ip' for command,_ in self.calls))

    def test_installed_apk_digest_mismatch_blocks_collection(self):
        self.override(['shell','sha256sum','/data/app/synthetic/base.apk'],'b'*64+'  /data/app/synthetic/base.apk')
        with self.assertRaises(ValueError):self.execute()
        self.assertFalse(any('logcat' in command for command,_ in self.calls))

    def test_untrusted_package_path_cannot_inject_remote_shell(self):
        self.override(['shell','pm','path',PKG],'package:/data/app/synthetic/base.apk;reboot')
        with self.assertRaises(ValueError):self.execute()
        self.assertFalse(any('sha256sum' in command for command,_ in self.calls))

    def test_accounts_block_before_log_collection(self):
        self.override(['shell','dumpsys','account'],'Accounts: 1')
        with self.assertRaises(ValueError):self.execute()
        self.assertFalse(any('logcat' in command for command,_ in self.calls))
        self.assertFalse(self.output.exists())

    def test_physical_device_blocks(self):
        self.override(['shell','getprop','ro.kernel.qemu'],'0')
        with self.assertRaises(ValueError):self.execute()
        self.assertFalse(self.output.exists())

    def test_device_api_or_page_mismatch_blocks(self):
        self.override(['shell','getprop','ro.build.version.sdk'],'24')
        with self.assertRaises(ValueError):self.execute()
        self.assertFalse(any('logcat' in command for command,_ in self.calls))

    def test_x86_bridge_is_not_an_arm64_lab(self):
        self.override(['shell','getprop','ro.product.cpu.abi'],'x86_64')
        with self.assertRaises(ValueError):self.execute()

    def test_no_mutating_or_launch_commands(self):
        self.execute()
        for command,kwargs in self.calls:
            self.assertTrue(not any(x in command for x in ['install','root','start-server','start','instrument','input','reset','settings','reboot']))
            self.assertNotIn('shell',kwargs)
            self.assertEqual(kwargs['timeout'],30)

    def test_inherited_preload_proxy_and_java_agent_not_forwarded(self):
        with patch.dict(os.environ,{'HTTP_PROXY':SECRET,'LD_PRELOAD':SECRET,'JAVA_TOOL_OPTIONS':SECRET,'ANDROID_SERIAL':SECRET}):self.execute()
        for _,kwargs in self.calls:self.assertNotIn(SECRET,str(kwargs['env']))

    def test_dead_process_is_not_a_zero_frame_success(self):
        self.override(['shell','pidof',PKG],'',1)
        result=self.execute()
        self.assertFalse(result['capture']['target_running_at_snapshot'])
        self.assertIsNone(result['frames'])
        self.assertFalse(any('gfxinfo' in command for command,_ in self.calls))

    def test_bad_pid_output_is_not_misreported_dead_process(self):
        self.override(['shell','pidof',PKG],'malformed')
        with self.assertRaises(ValueError):self.execute()
        self.assertFalse(self.output.exists())

    def test_command_failure_is_not_silently_accepted(self):
        self.override(['get-state'],'',2)
        with self.assertRaises(ValueError):self.execute()

    def test_timeout_no_retry_or_output(self):
        def timeout(*args,**kwargs):raise subprocess.TimeoutExpired('synthetic',30)
        with self.assertRaises(subprocess.TimeoutExpired):c.collect(self.adb,'emulator-5554',PKG,self.metadata,self.receipt,self.output,runner=timeout)
        self.assertFalse(self.output.exists())

    def test_existing_output_never_overwritten(self):
        self.output.mkdir();(self.output/'keep.txt').write_text('KEEP')
        with self.assertRaises(ValueError):self.execute()
        self.assertEqual((self.output/'keep.txt').read_text(),'KEEP')
        self.assertEqual(self.calls,[])
