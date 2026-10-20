"""Real controller methods with synthetic subprocess results; never executes ADB."""
from pathlib import Path
import sys,subprocess,unittest
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/native_compatibility/android_lab'))
import run_lab

class ControllerRegressions(unittest.TestCase):
    def response(self,stdout='device\n',stderr='',code=0):
        with patch.object(run_lab.subprocess,'run',return_value=SimpleNamespace(stdout=stdout,stderr=stderr,returncode=code)) as call:
            value=run_lab.Adb(Path('/synthetic/adb'),'emulator-5554').run('get-state')
            self.assertEqual(call.call_args.args[0],['/synthetic/adb','-s','emulator-5554','get-state'])
            return value
    def test_startup_banner_does_not_corrupt_get_state(self):
        self.assertEqual(self.response(stderr='* daemon not running; starting now at tcp:5037\n* daemon started successfully\n'),'device\n')
    def test_unknown_stderr_is_preserved(self):
        self.assertIn('SYNTHETIC_WARNING',self.response(stderr='SYNTHETIC_WARNING\n'))
    def test_stdout_is_never_filtered_as_host_banner(self):
        text='* daemon started successfully\n'
        self.assertEqual(self.response(stdout=text),text)
    def test_partial_banner_or_similar_error_is_preserved(self):
        self.assertIn('failed',self.response(stderr='* daemon started successfully but failed\n'))
    def test_nonzero_exit_still_blocks(self):
        with self.assertRaises(ValueError):self.response(stderr='SYNTHETIC_ERROR',code=1)
    def test_invalid_tcp_port_is_not_a_local_emulator(self):
        for serial in ['localhost:0','127.0.0.1:65536','emulator-0','emulator-65535','emulator-99999999']:
            with self.subTest(serial=serial):self.assertFalse(run_lab.serial_ok(serial))
    def test_supported_serials_preserved(self):
        for serial in ['emulator-5554','127.0.0.1:6520','localhost:6520','localhost:65535']:
            self.assertTrue(run_lab.serial_ok(serial))
    def test_timeout_propagates_without_retry_or_side_effect(self):
        with patch.object(run_lab.subprocess,'run',side_effect=subprocess.TimeoutExpired('synthetic',45)) as call:
            with self.assertRaises(subprocess.TimeoutExpired):run_lab.Adb(Path('/synthetic/adb'),'emulator-5554').run('get-state')
            self.assertEqual(call.call_count,1)

if __name__=='__main__':unittest.main()
