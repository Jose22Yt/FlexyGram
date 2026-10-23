"""Compile the real API selection methods in isolation; never builds an APK."""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'TMessagesProj/src/main/java/tw/nekomimi/nekogram/NekoXConfig.java'


class ApiSelectionCompile(unittest.TestCase):
    def compile_selection(self, source, alpha, custom):
        # Preserve the production imports and method bodies, isolating Android UI
        # dependencies. All values below are deliberately nonfunctional fixtures.
        imports = '\n'.join(re.findall(
            r'^import org\.telegram\.messenger\.Build(?:Config|Vars);$', source, re.M))
        methods = '\n'.join(re.findall(
            r'    public static (?:int|String) currentApp(?:Id|Hash)\(\) \{.*?^    \}',
            source, re.M | re.S))
        self.assertEqual(methods.count('public static'), 2)
        self.assertIsNotNone(shutil.which('java'), 'JDK required for Java regression test')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            messenger = root/'org/telegram/messenger'
            messenger.mkdir(parents=True)
            (messenger/'BuildConfig.java').write_text(
                'package org.telegram.messenger; public class BuildConfig {'
                f'public static final boolean CONNECTED_ALPHA = {str(alpha).lower()};'
                'public static final int APP_ID = 101;'
                'public static final String APP_HASH = "fixture-default";}')
            (messenger/'BuildVars.java').write_text(
                'package org.telegram.messenger; public class BuildVars {'
                'public static final int APP_ID = 202;'
                'public static final String APP_HASH = "fixture-alpha";}')
            (root/'ApiSelection.java').write_text(
                imports + '\npublic class ApiSelection {\n'
                f'static int customApi = {3 if custom else 0};'
                'static final int API_TYPE_CUSTOM = 3; static int customAppId = 303;'
                'static String customAppHash = "fixture-custom";\n' + methods +
                '\npublic static void main(String[] args) {'
                'System.out.print(currentAppId() + ":" + currentAppHash());}}')
            result = subprocess.run(
                ['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main',
                 '-d', str(root), *map(str, root.rglob('*.java'))],
                capture_output=True, text=True)
            if result.returncode:
                return result, None
            output = subprocess.check_output(
                ['java', '-cp', str(root), 'ApiSelection'], text=True)
            return result, output

    def test_api_methods_compile_and_keep_alpha_and_legacy_selection(self):
        for alpha, custom, expected in (
            (True, False, '202:fixture-alpha'),
            (True, True, '202:fixture-alpha'),
            (False, False, '101:fixture-default'),
            (False, True, '303:fixture-custom'),
        ):
            with self.subTest(alpha=alpha, custom=custom):
                result, output = self.compile_selection(SOURCE.read_text(), alpha, custom)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output, expected)

    def test_missing_buildvars_import_reproduces_observed_javac_failure(self):
        broken = SOURCE.read_text().replace('import org.telegram.messenger.BuildVars;\n', '')
        result, _ = self.compile_selection(broken, True, False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('BuildVars', result.stderr)


if __name__ == '__main__':
    unittest.main()
