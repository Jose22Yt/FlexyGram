"""Real Gradle regression for the missing Diagnostic configuration in opt-in labs."""
from pathlib import Path
import json,os,subprocess,tempfile,unittest,zipfile

ROOT=Path(__file__).resolve().parents[2]

class ClasspathGateTests(unittest.TestCase):
    def exercise(self,login=False,offline=False,retired=False,missing=False):
        home=Path(os.environ['FLEXYGRAM_GRADLE_HOME'])
        source=(ROOT/'TMessagesProj/build.gradle').read_text()
        block=source.split("tasks.register('verifyDiagnosticTranslationClasspath')",1)[1].split("\ntasks.named('preBuild')",1)[0]
        block="tasks.register('verifyDiagnosticTranslationClasspath')"+block
        selected=['realAlphaDebugCompileClasspath','realAlphaDebugRuntimeClasspath'] if login or offline else [
            'diagnosticDebugCompileClasspath','diagnosticDebugRuntimeClasspath',
            'diagnosticStagingCompileClasspath','diagnosticStagingRuntimeClasspath']
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'settings.gradle').write_text("rootProject.name='classpath-gate-regression'\n")
            configurations='\n'.join("configurations.create('"+n+"') { canBeResolved=true }" for n in selected if not (missing and n==selected[0]))
            fixture="def localLoginPagesEnabled = providers.gradleProperty('flexygramLocalLoginPages').orNull == 'true'\n"+configurations+'\n'
            if retired:
                artifact=root/'repo/app/nekogram/translator/translator/1.0';artifact.mkdir(parents=True)
                (artifact/'translator-1.0.pom').write_text('<project><modelVersion>4.0.0</modelVersion><groupId>app.nekogram.translator</groupId><artifactId>translator</artifactId><version>1.0</version></project>')
                with zipfile.ZipFile(artifact/'translator-1.0.jar','w') as z:z.writestr('synthetic-test-only.txt','No retired code or key')
                fixture+="repositories { maven { url=uri('repo') } }\ndependencies { add('"+selected[0]+"','app.nekogram.translator:translator:1.0') }\n"
            (root/'build.gradle').write_text(fixture+block)
            args=[str(home/'bin/gradle'),'--no-daemon','--offline','--max-workers=1','--console=plain','verifyDiagnosticTranslationClasspath']
            if login:args.append('-PflexygramLocalLoginPages=true')
            if offline:args.append('-PflexygramOfflineDialogsUi=true')
            env=dict(os.environ);env.pop('GRADLE_OPTS',None)
            run=subprocess.run(args,cwd=root,env=env,capture_output=True,text=True,timeout=120)
            if retired:
                self.assertNotEqual(run.returncode,0);self.assertIn('Legacy translation dependency is forbidden',run.stdout+run.stderr)
            elif missing:
                self.assertNotEqual(run.returncode,0);self.assertIn(selected[0],run.stdout+run.stderr)
            else:
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                report=json.loads((root/'build/reports/translation-diagnostic-classpath.json').read_text())
                self.assertEqual(sorted(report),sorted(selected))
    def test_default_keeps_four_diagnostic_graphs(self):self.exercise()
    def test_login_only_checks_realalpha(self):self.exercise(login=True)
    def test_offline_only_checks_realalpha(self):self.exercise(offline=True)
    def test_both_flags_check_realalpha(self):self.exercise(login=True,offline=True)
    def test_retired_module_still_fails_closed(self):self.exercise(login=True,offline=True,retired=True)
    def test_missing_selected_graph_is_not_silently_skipped(self):self.exercise(login=True,offline=True,missing=True)

if __name__=='__main__':unittest.main()
