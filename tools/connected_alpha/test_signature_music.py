"""Source boundaries + executable JDK parser. Android interaction is in music_visual."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from music_contract import BASE, PRODUCTION
from stabilization_contract import restore1271
from integration_contract import WORK1,combined_paths,reviewed_work1
PATHS=combined_paths()
ROOT=Path(__file__).resolve().parents[2]
PLAYER=ROOT/'TMessagesProj/src/main/java/app/exteraless/player'

class SignatureMusicTests(unittest.TestCase):
    def test_exact_independent_scope_and_protected_services(self):
        changed=set(subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines())
        changed.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines())
        self.assertFalse(changed-PATHS,changed-PATHS)
        for path in ('TMessagesProj/build.gradle','gradle.properties','.github/workflows/connected-alpha-arm64.yml',
                     'TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java',
                     'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java',
                     'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java',
                     'TMessagesProj/src/main/java/org/telegram/messenger/MediaController.java',
                     'TMessagesProj/src/main/java/org/telegram/messenger/MusicPlayerService.java'):
            self.assertEqual(reviewed_work1(path),subprocess.check_output(['git','show',WORK1+':'+path],cwd=ROOT),path)
    def test_reviewed_patch_restores_exact_base(self):
        patch=(ROOT/'tools/connected_alpha/music_presentation.patch').read_bytes()
        files=[line[6:].decode() for line in patch.splitlines() if line.startswith(b'+++ b/')]
        self.assertTrue(set(files)<=PRODUCTION)
        with tempfile.TemporaryDirectory() as tmp:
            for path in files:
                f=Path(tmp)/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(restore1271(path,(ROOT/path).read_bytes()))
            subprocess.run(['git','apply','--reverse','-'],input=patch,cwd=tmp,check=True,capture_output=True)
            for path in files:self.assertEqual((Path(tmp)/path).read_bytes(),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT))
    def test_all_changed_production_java_parses_without_requiring_credentials(self):
        code='''import javax.tools.*;import com.sun.source.util.*;import java.util.*;
class ParseMusic {public static void main(String[] args)throws Exception{JavaCompiler c=ToolProvider.getSystemJavaCompiler();DiagnosticCollector<JavaFileObject> errors=new DiagnosticCollector<>();StandardJavaFileManager files=c.getStandardFileManager(errors,null,null);JavacTask task=(JavacTask)c.getTask(null,files,errors,List.of("-proc:none"),null,files.getJavaFileObjects(args));for(var ast:task.parse()){}for(var error:errors.getDiagnostics())if(error.getKind()==Diagnostic.Kind.ERROR)throw new AssertionError(error);files.close();}}'''
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'ParseMusic.java';file.write_text(code)
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',temp,str(file)],check=True,capture_output=True)
            subprocess.run(['java','-cp',temp,'ParseMusic']+[str(ROOT/p) for p in sorted(PRODUCTION)],check=True,capture_output=True)
    def test_one_playback_owner_no_overlay_or_new_observers(self):
        for name in ('SignatureMusicBubble','SignatureMusicHost','SignatureMusicPresentation'):
            s=(PLAYER/(name+'.java')).read_text()
            for forbidden in ('addObserver(', 'new MediaPlayer','new ExoPlayer','TYPE_APPLICATION_OVERLAY','SYSTEM_ALERT_WINDOW','WindowManager.addView','requestAudioFocus','new Thread','postOnAnimation'):
                self.assertNotIn(forbidden,s)
        bubble=(PLAYER/'SignatureMusicBubble.java').read_text()
        self.assertIn('WindowInsets.Type.ime()',bubble)
        self.assertIn('cancel.recycle()',bubble)
        self.assertIn('host.removeOnLayoutChangeListener',bubble)
        self.assertIn('SignatureMusicPresentation.setCompact(false)',bubble)
    def test_no_cover_extraction_or_layout_springs_in_alpha_path(self):
        colors=(PLAYER/'PlayerColors.java').read_text()
        self.assertIn('if (BuildConfig.CONNECTED_ALPHA) return dark ? MIDNIGHT : PEARL;',colors)
        sheet=(PLAYER/'PlayerSheet.java').read_text()
        self.assertIn('if (!BuildConfig.CONNECTED_ALPHA) cover.setListener',sheet)
        controls=(PLAYER/'ControlsRow.java').read_text().split('private void updateTargets(boolean animated) {')[1]
        branch=controls.split('        float prevW')[0]
        self.assertIn('return;',branch)
        self.assertNotIn('startTick()',branch)
        wave=(PLAYER/'WavySeekBar.java').read_text()
        self.assertIn('playing && visible && !LiteMode.isPowerSaverApplied()',wave)
        self.assertIn('postDelayed(waveFrame, 33)',wave)
    def test_context_music_delta_does_not_replace_voice_call_state_machine(self):
        path='TMessagesProj/src/main/java/org/telegram/ui/Components/FragmentContextView.java'
        before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
        after=(ROOT/path).read_text()
        # All original Telegram voice/call handlers remain verbatim.
        from test_signature_matte import body
        for method in ('public void checkCall(', 'public void checkImport(', 'private void checkLiveLocation(', 'private void checkLiveStory('):
            self.assertEqual(body(before,method),body(after,method),method)
        self.assertNotIn('signatureMusic',body(after,'public void checkCall('))

    def test_gfxinfo_parser_ignores_flagged_and_incomplete_frames(self):
        from measure_music import frames,stats
        sample="Flags,IntendedVsync,FrameCompleted\n0,1000000,17000000\n1,1000000,90000000\n0,20000000,43000000\n0,50000000,0\n"
        self.assertEqual(frames(sample),[16,23])
        self.assertEqual(stats(frames(sample),16.67)['over_budget_frames'],1)
        self.assertEqual(stats(frames(sample),16.67)['p95_frame_ms'],23)
        with self.assertRaises(ValueError):stats([],16.67)
