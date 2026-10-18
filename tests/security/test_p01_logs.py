"""Offline P0.1 regressions. Run: python -m unittest discover -s tests/security -v.

Java harness uses production AuthTokensHelper/Gcm/Captcha/provider classes with
local Android/Firebase doubles. No Android runtime or network is involved.
"""
import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / 'TMessagesProj/src/main'
JAVA = MAIN / 'java/org/telegram/messenger'
CANARY = 'SYNTHETIC_SECRET_P01_NOT_REAL_937614'


def load_server():
    spec = importlib.util.spec_from_file_location('p01_dev_server', MAIN / 'python/dev_server.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._token = CANARY
    return module


class DevServerTests(unittest.TestCase):
    def setUp(self):
        self.server = load_server()
        self.output = io.StringIO()
        self.logs = []
        self.android = types.SimpleNamespace(log=self.logs.append)
        self.modules = patch.dict(sys.modules, {'android_utils': self.android})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def assertSafe(self, *extra):
        output = '\n'.join(self.logs) + self.output.getvalue() + str(extra)
        self.assertNotIn(CANARY, output)
        self.assertNotIn(CANARY.encode().hex(), output)

    def test_token_written_unchanged_but_not_logged(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = types.SimpleNamespace(get_plugins_dir=lambda: directory)
            with patch.dict(sys.modules, {'file_utils': fake}):
                self.server._publish_token(CANARY)
            self.assertEqual((Path(directory) / self.server.TOKEN_FILE).read_text(), CANARY)
        self.assertIn('token file written', str(self.logs))
        self.assertSafe()

    def test_token_file_failure_safe_in_android_and_stderr(self):
        fake = types.SimpleNamespace(get_plugins_dir=lambda: (_ for _ in ()).throw(OSError(CANARY)))
        with patch.dict(sys.modules, {'file_utils': fake}):
            self.server._publish_token(CANARY)
            self.android.log = lambda _: (_ for _ in ()).throw(RuntimeError(CANARY))
            with contextlib.redirect_stderr(self.output):
                self.server._publish_token(CANARY)
        self.assertIn('OSError', str(self.logs) + self.output.getvalue())
        self.assertSafe()

    def test_authentication_and_dispatch_preserved(self):
        server = self.server
        called = []
        server._COMMANDS['test'] = lambda req: called.append(req['value']) or {'result': 42}
        self.assertEqual(server.dispatch({'@': 'ping', '#': 1}), {'#': 1, 'ok': True, 'pong': True})
        self.assertFalse(server.dispatch({'@': 'test', 'token': 'wrong'})['ok'])
        self.assertFalse(server.dispatch({'@': 'test'})['ok'])
        self.assertFalse(called)
        result = server.dispatch({'@': 'test', '#': 2, 'token': CANARY, 'value': 7})
        self.assertEqual(result, {'#': 2, 'ok': True, 'result': 42})
        self.assertEqual(called, [7])
        self.assertSafe()

    def test_exception_and_unknown_command_reports_safe(self):
        self.server._COMMANDS['fail'] = lambda _: (_ for _ in ()).throw(ValueError(CANARY))
        failure = self.server.dispatch({'@': 'fail', 'token': CANARY})
        unknown = self.server.dispatch({'@': CANARY, 'token': CANARY})
        self.assertFalse(failure['ok'])
        self.assertIn('ValueError', failure['error'])
        self.assertSafe(failure, unknown)

    def test_malformed_stream_keeps_processing_without_echoing_input(self):
        handler = object.__new__(self.server._Handler)
        handler.rfile = io.BytesIO(b'"\xff' + CANARY.encode() + b'"\n' + b'{"@":"ping","#":3}\n')
        handler.wfile = io.BytesIO()
        handler.handle()
        responses = [json.loads(line) for line in handler.wfile.getvalue().splitlines()]
        self.assertFalse(responses[0]['ok'])
        self.assertTrue(responses[1]['pong'])
        self.assertSafe(responses)

    def test_socketserver_traceback_does_not_leak(self):
        server = object.__new__(self.server._Server)
        with contextlib.redirect_stderr(self.output):
            try:
                raise RuntimeError(CANARY)
            except RuntimeError:
                server.handle_error(None, (CANARY, 1))
        self.assertIn('RuntimeError', str(self.logs))
        self.assertSafe()

    def test_bind_failure_safe_and_start_disabled_after_failure(self):
        with patch.object(self.server, '_Server', side_effect=OSError(CANARY)) as constructor:
            self.assertFalse(self.server.start())
            self.assertFalse(self.server.start())
            self.assertEqual(constructor.call_count, 1)
        self.assertIn('OSError', str(self.logs))
        self.assertSafe()

    def test_debugger_errors_and_logs_safe(self):
        debugger = types.SimpleNamespace(listen=lambda _: (_ for _ in ()).throw(RuntimeError(CANARY)),
                                        stop_listening=lambda: (_ for _ in ()).throw(ValueError(CANARY)))
        with patch.dict(sys.modules, {'debugpy': debugger}):
            first = self.server._cmd_start_debugger({'platform': CANARY})
            second = self.server._cmd_stop_debugger({})
            debugger.listen = lambda _: None
            self.assertTrue('debugger' in self.server._cmd_start_debugger({'platform': CANARY}))
        self.assertSafe(first, second)

    def test_plugin_diagnostic_errors_safe(self):
        plugin = types.SimpleNamespace(id='test', name='test', version='1', author='test',
                                      enabled=True, loaded=False, hasSettings=False, loadError=CANARY)
        report = self.server._plugin_json(plugin)
        controller = types.SimpleNamespace(getPlugin=lambda _: plugin, reloadPlugin=lambda _: None,
                                           setPluginEnabled=lambda *_: False)
        with patch.object(self.server, '_controller', return_value=controller):
            reload = self.server._cmd_reload_plugin({'plugin_id': CANARY})
            enabled = self.server._cmd_set_enabled({'plugin_id': CANARY}, True)
        self.assertSafe(report, reload, enabled)

    def test_python_loader_start_boundary_safe(self):
        source = (MAIN / 'python/extera_utils/plugin_loader.py').read_text()
        function = next(node for node in ast.parse(source).body
                        if isinstance(node, ast.FunctionDef) and node.name == 'start_dev_server')
        module = ast.Module(body=[function], type_ignores=[])
        namespace = {'_dev_server_started': False, 'sys': sys}
        fake = types.SimpleNamespace(start=lambda: (_ for _ in ()).throw(RuntimeError(CANARY)))
        with patch.dict(sys.modules, {'dev_server': fake}), contextlib.redirect_stderr(self.output):
            exec(compile(module, '<production start_dev_server>', 'exec'), namespace)
            namespace['start_dev_server']()
        self.assertIn('RuntimeError', self.output.getvalue())
        self.assertSafe()


class JavaSourceContracts(unittest.TestCase):
    def test_sensitive_paths_never_forward_raw_throwables_or_payloads(self):
        # Additional static guard; this is not an Android execution test.
        forbidden = {
            'AuthTokensHelper': ('new String(token.future_auth_token', 'FileLog.e(e)'),
            'GcmPushListenerService': ('+ token', '+ data', '+ from'),
            'GooglePushListenerServiceProvider': ('+ currentPushString', 'error.getMessage()', 'FileLog.e(e)'),
            'PushListenerController': ('FileLog.e(e)', '+ jsonString', '+ loc_key', 'Utilities.bytesToHex(SharedConfig.pushAuthKey)'),
            'CaptchaController': ('+ token', '+key_id', 'e.getMessage()', 'failure", e)'),
        }
        for name, patterns in forbidden.items():
            source = (JAVA / (name + '.java')).read_text()
            log_lines = '\n'.join(line for line in source.splitlines() if 'FileLog.' in line)
            for pattern in patterns:
                self.assertNotIn(pattern, log_lines if pattern != 'e.getMessage()' else source, (name, pattern))

    def test_protocol_diagnostics_have_no_body_serializer_or_to_string_fallback(self):
        source = (JAVA / 'FileLog.java').read_text()
        sensitive = source[source.index('    private static void postProtocolDump'):source.index('    private static volatile boolean gsonDisabled')]
        for forbidden in ('gson.toJson', 'skipGson ? message', 'printStackTrace', ', e);'):
            self.assertNotIn(forbidden, sensitive)
        self.assertIn('error.code', sensitive)
        self.assertIn('response.getClass().getSimpleName()', sensitive)


def java_compiler():
    if shutil.which('javac'):
        return ['javac']
    if shutil.which('java'):
        command = ['java', '--module', 'jdk.compiler/com.sun.tools.javac.Main']
        if subprocess.run([*command, '-version'], capture_output=True).returncode == 0:
            return command
    return None


JAVA_COMPILER = java_compiler()


class JavaRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(JAVA_COMPILER and shutil.which('java'), 'JDK compiler unavailable')
    def test_actual_java_callbacks_with_synthetic_secrets(self):
        fixture = Path(__file__).with_name('java_harness.py')
        spec = importlib.util.spec_from_file_location('p01_harness', fixture)
        harness = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(harness)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            harness.write_sources(directory, JAVA, MAIN)
            sources = [str(path) for path in directory.rglob('*.java')]
            subprocess.run([*JAVA_COMPILER, '-encoding', 'UTF-8', '-d', str(directory), *sources], check=True, capture_output=True, text=True)
            production = [str(JAVA / (name + '.java')) for name in (
                'AuthTokensHelper', 'GcmPushListenerService', 'CaptchaController',
                'GooglePushListenerServiceProvider', 'PushListenerController', 'FileLog')]
            production.append(str(MAIN / 'java/app/exteraless/plugins/PythonPluginsEngine.java'))
            parsed = subprocess.run(['java', '-cp', str(directory), 'ParseSources', *production],
                                    check=True, capture_output=True, text=True)
            self.assertEqual(parsed.stdout.strip(), 'Java production syntax PASS')
            result = subprocess.run(['java', '-cp', str(directory), 'org.telegram.messenger.P01Harness'],
                                    check=True, capture_output=True, text=True)
            self.assertEqual(result.stdout.strip(), 'P0.1 Java harness PASS')
            self.assertEqual(result.stderr, '')


if __name__ == '__main__':
    unittest.main()
