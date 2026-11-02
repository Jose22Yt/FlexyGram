"""Lab correctness and byte-exact boundaries; synthetic telemetry is not device evidence."""
import copy
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from performance.contract import BASE,ROOT,PATHS,PRODUCTION,RESERVED,restore
from integration_contract import combined_paths
from stabilization_contract import restore1271
from performance.metrics import gfxinfo,summary
from performance.capture import parse_health,memory,startup,run
from performance.compare import compare,ENVIRONMENT_KEYS
from performance.perfetto import plan

HEADER='Flags,IntendedVsync,FrameCompleted,FrameDeadline,FrameInterval\n'
SAMPLE=HEADER+'0,100000000,109000000,108333333,8333333\n0,120000000,126000000,128333333,8333333\n'

class PerformanceLab(unittest.TestCase):
    def test_120hz_budget_and_deadline_are_not_touch_latency_or_surface_jank(self):
        value=gfxinfo(SAMPLE)
        self.assertEqual(value['duration_ms']['median'],7.5)
        self.assertEqual(value['duration_ms']['p95'],9)
        self.assertEqual(value['over_interval_frames'],1)
        self.assertEqual(value['deadline_missed_frames'],1)
        self.assertEqual(value['budgeted_frame_count'],2)
        self.assertIsNone(value['touch_to_visible_ms'])
        self.assertEqual(value['jank'],'NOT_MEASURED_BY_GFXINFO')
    def test_refresh_change_is_per_frame_not_assumed_60hz(self):
        text=SAMPLE+ '0,140000000,149000000,156666666,16666666\n'
        value=gfxinfo(text)
        self.assertEqual(value['over_interval_frames'],1)
        self.assertEqual(len(value['interval_ms_histogram']),2)
    def test_flagged_missing_and_max_timestamp_frames_are_excluded(self):
        text=SAMPLE+'1,100,900,1000,8333333\n0,100,9223372036854775807,1000,8333333\n0,200,0,1000,8333333\n0,x,y,1000,8333333\n'
        value=gfxinfo(text)
        self.assertEqual(value['duration_ms']['count'],2)
        self.assertEqual(value['rejected']['flagged'],1)
        self.assertEqual(value['rejected']['incomplete_or_invalid'],2)
        self.assertEqual(value['rejected']['malformed'],1)
    def test_duplicate_in_one_section_but_distinct_windows_preserved(self):
        first=SAMPLE.splitlines()[1]+'\n'
        value=gfxinfo(HEADER+first+first+HEADER+first)
        self.assertEqual(value['duration_ms']['count'],2)
        self.assertEqual(value['rejected']['duplicate'],1)
    def test_missing_refresh_fails_comparison_budget_and_explicit_fallback_works(self):
        value=gfxinfo('Flags,IntendedVsync,FrameCompleted\n0,1000000,10000000\n')
        self.assertEqual(value['unbudgeted_frame_count'],1)
        fallback=gfxinfo('Flags,IntendedVsync,FrameCompleted\n0,1000000,10000000\n',120)
        self.assertEqual(fallback['over_interval_frames'],1)
        self.assertEqual(fallback['frames'][0]['budget_source'],'operator_verified_hz')
        for invalid in (float('nan'),float('inf'),-1):
            with self.assertRaises(ValueError):gfxinfo(SAMPLE,invalid)
    def test_summary_nearest_rank_empty_and_nonfinite(self):
        self.assertEqual(summary(list(range(1,21)))['p95'],19)
        self.assertIsNone(summary([])['median'])
        with self.assertRaises(ValueError):summary([float('nan')])
    def reports(self):
        env={k:'same-test-condition' for k in ENVIRONMENT_KEYS}
        capture={'frames':gfxinfo(SAMPLE),'health':{'eligible':True},'startup_ms':None}
        return [{'schema':1,'evidence':'test_device','prepared_test_device':True,'source_commit':BASE,
                 'scenario':'music_navigation','label':label,'environment':dict(env),
                 'captures':[copy.deepcopy(capture) for _ in range(20)]} for label in ('exteraless','alpha1271','candidate')]
    def test_equal_synthetic_schema_fixture_never_auto_proves_superiority(self):
        result=compare(self.reports())
        self.assertTrue(result['comparable'])
        self.assertEqual(result['superiority'],'NOT_AUTOMATICALLY_ESTABLISHED')
        self.assertEqual(result['rows'][0]['sample_medians_ms']['median'],7.5)
    def test_compare_rejects_every_unmatched_condition_and_incomplete_samples(self):
        for key in ENVIRONMENT_KEYS:
            reports=self.reports();reports[2]['environment'][key]='different'
            self.assertFalse(compare(reports)['comparable'],key)
        reports=self.reports();reports[2]['captures'].pop();self.assertFalse(compare(reports)['comparable'])
        reports=self.reports();reports[1]['evidence']='synthetic';self.assertFalse(compare(reports)['comparable'])
        reports=self.reports();reports[2]['captures'][0]['health']['eligible']=False;self.assertFalse(compare(reports)['comparable'])
        reports=self.reports();reports[2]['source_commit']='x'*40;self.assertFalse(compare(reports)['comparable'])
    def test_observed_refresh_distribution_not_just_mode_set_must_match(self):
        reports=self.reports()
        for report in reports:
            for c in report['captures']:c['frames']['interval_ms_histogram']={'8.33333':90,'16.66667':10}
        reports[2]['captures'][0]['frames']['interval_ms_histogram']={'8.33333':10,'16.66667':90}
        # One changed repetition stays within5percentage points, all repetitions do not.
        self.assertTrue(compare(reports)['comparable'])
        for c in reports[2]['captures']:c['frames']['interval_ms_histogram']={'8.33333':10,'16.66667':90}
        self.assertFalse(compare(reports)['comparable'])
    def test_health_memory_startup_parsers_do_not_infer_missing_or_failed_data(self):
        health=parse_health('Thermal Status: 1','level: 80\ntemperature: 350\nUSB powered: false',1,30,38)
        self.assertTrue(health['eligible']);self.assertFalse(parse_health('','',1,30,38)['eligible'])
        self.assertFalse(parse_health('Thermal Status: 3','level: 80\ntemperature: 350',1,30,38)['eligible'])
        self.assertEqual(memory('TOTAL PSS: 123\nTOTAL RSS: 400\nJava Heap: 50')['total_pss_kib'],123)
        self.assertIsNone(memory('')['gc_count'])
        self.assertEqual(startup('TotalTime: 234\n'),234)
        for value in ('Error: bad\nTotalTime: 0','Warning: Activity not started\nTotalTime: 4',''):
            with self.assertRaises(ValueError):startup(value)
    def test_capture_uses_only_readonly_telemetry_and_no_ui_or_owner_data(self):
        calls=[]
        args_holder=[]
        class FakeDevice:
            def shell(self,*args):
                calls.append(args)
                if args==('dumpsys','thermalservice'):return 'Thermal Status: 0'
                if args==('dumpsys','battery'):return 'level: 80\ntemperature: 300\nUSB powered: false'
                if args[0:2]==('am','start'):return 'TotalTime: 234\n'
                if args[0:2]==('dumpsys','gfxinfo'):return HEADER if args_holder[0].scenario=='cold_start' else SAMPLE
                if args[0:2]==('dumpsys','meminfo'):return 'TOTAL PSS: 123'
                return 'test'
        with tempfile.TemporaryDirectory() as directory:
            args=SimpleNamespace(serial='NEVER_SAVE_SERIAL',label='candidate',source_commit=BASE,scenario='music_navigation',package='test.app',iterations=1,verified_hz=None,max_thermal=1,min_battery=30,max_temperature_c=38,charging='unplugged',output=Path(directory)/'result.json',**{k:'test' for k in ('theme','cache_state','conversation_fixture','workload_id','music_state','refresh_profile','installation_state','test_session_state')})
            args_holder.append(args)
            report=run(args,FakeDevice(),prompt=lambda s:None)
            report['evidence']='synthetic' # explicitly not a physical measurement
            text=json.dumps(report)
            self.assertNotIn(args.serial,text)
            self.assertIsNone(report['captures'][0]['memory_after']['allocations'])
            args.scenario='cold_start';args.component='test.app/TestActivity';args.allow_test_force_stop=True
            cold=run(args,FakeDevice(),prompt=lambda s:None)
            self.assertEqual(cold['captures'][0]['startup_ms'],234)
            self.assertEqual(cold['captures'][0]['frames']['duration_ms']['count'],0)
        for args in calls:
            self.assertFalse(any(x in args for x in ('input','uiautomator','logcat','screencap','clear','install','setprop','put')))
    def test_perfetto_queries_execute_with_explicit_synthetic_tables(self):
        data=plan('test.app',20)
        self.assertIn('size_kb: 32768',data['config'])
        with sqlite3.connect(':memory:') as db:
            db.executescript("CREATE TABLE process(upid INT,pid INT,name TEXT);CREATE TABLE actual_frame_timeline_slice(upid INT,dur INT,jank_type TEXT,on_time_finish INT);CREATE TABLE thread(utid INT,upid INT,tid INT,name TEXT);CREATE TABLE sched(utid INT,dur INT);INSERT INTO process VALUES(1,10,'test.app'),(2,20,'other.app');INSERT INTO actual_frame_timeline_slice VALUES(1,9000000,'App Deadline Missed',0),(1,6000000,'None',1),(2,9000000,'App Deadline Missed',0);INSERT INTO thread VALUES(1,1,10,'main'),(2,1,11,'RenderThread');INSERT INTO sched VALUES(1,1000000),(2,2000000);")
            self.assertEqual(db.execute(data['frame_sql']).fetchone()[0:4],(2,1,0,1))
            self.assertEqual(len(db.execute(data['cpu_sql']).fetchall()),2)
        for package in ('test.app\' OR 1=1 --','test app','test;echo'):
            with self.assertRaises(ValueError):plan(package)
    def test_only_reviewed_files_change_and_work1_production_is_exact(self):
        changed=set(subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines())
        changed.update(subprocess.check_output(['git','ls-files','-o','--exclude-standard'],cwd=ROOT,text=True).splitlines())
        self.assertFalse(changed-(PATHS|combined_paths()),changed-(PATHS|combined_paths()))
        for path in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines():
            if Path(path).name in RESERVED or '/src/main/java/app/flexygram/bubbles/' in path:
                self.assertEqual(restore1271(path,(ROOT/path).read_bytes()),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),path)
        self.assertTrue(all(p.endswith(('/LyricsView.java','/LyricsFill.java')) for p in PRODUCTION))
    def test_exact_reversal_keeps_baseline_ui_and_rejects_unreviewed_code(self):
        path='TMessagesProj/src/main/java/app/exteraless/player/LyricsView.java'
        expected=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
        self.assertEqual(restore(path,(ROOT/path).read_bytes()),expected)
        mutant=(ROOT/path).read_bytes().replace(b'public void setPosition(long ms)',b'public void setPosition(long other)',1)
        try:restored=restore(path,mutant)
        except ValueError:return
        self.assertNotEqual(restored,expected)
    def test_no_new_renderer_or_animation_and_source_change_is_tiny(self):
        source=(ROOT/'TMessagesProj/src/main/java/app/exteraless/player/LyricsFill.java').read_text()
        for bad in ('Animator','postDelayed','new Thread','HashMap','Bitmap','RenderEffect'):
            self.assertNotIn(bad,source)
        self.assertEqual(source.count('new LinearGradient('),1)
    def test_existing_preview_model_survives_2000_cycles_without_editing_navigation(self):
        from test_preview_navigation import fixture
        path=ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java'
        code=fixture(path.read_text()).replace('for(int n=0;n<200;n++)','for(int n=0;n<2000;n++)')
        self.assertIn('n<2000',code)
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'PreviewRegression.java';source.write_text(code)
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',temp,str(source)],check=True,capture_output=True)
            subprocess.run(['java','-cp',temp,'PreviewRegression'],check=True,capture_output=True)
    def test_complete_changed_android_sources_parse_without_private_build_inputs(self):
        # Reuse the existing JDK AST parser; parsing is not semantic/full-module compilation.
        code='''import javax.tools.*;import com.sun.source.util.*;import java.util.*;class ParsePerf {public static void main(String[] args)throws Exception{JavaCompiler c=ToolProvider.getSystemJavaCompiler();DiagnosticCollector<JavaFileObject> d=new DiagnosticCollector<>();var f=c.getStandardFileManager(d,null,null);JavacTask t=(JavacTask)c.getTask(null,f,d,List.of("-proc:none"),null,f.getJavaFileObjects(args));for(var x:t.parse()){}for(var x:d.getDiagnostics())if(x.getKind()==Diagnostic.Kind.ERROR)throw new AssertionError(x);f.close();}}'''
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'ParsePerf.java';source.write_text(code)
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',temp,str(source)],check=True,capture_output=True)
            subprocess.run(['java','-cp',temp,'ParsePerf',*[str(ROOT/p) for p in PRODUCTION]],check=True,capture_output=True)

    def test_bad_summary_metrics_cannot_qualify(self):
        reports=self.reports();reports[2]['captures'][0]['frames']['duration_ms']['p95']=float('nan')
        self.assertFalse(compare(reports)['comparable'])
        reports=self.reports();reports[2]['captures'][0]['startup_ms']=-2
        self.assertFalse(compare(reports)['comparable'])
    def test_startup_query_schema_fixture_includes_warm_and_missing_fully_drawn(self):
        sql=plan('test.app')['startup_sql'].split(';',2)[2]
        with sqlite3.connect(':memory:') as db:
            db.executescript("CREATE TABLE android_startups(startup_id INT,package TEXT,startup_type TEXT,dur INT);CREATE TABLE android_startup_time_to_display(startup_id INT,time_to_initial_display INT,time_to_full_display INT);INSERT INTO android_startups VALUES(1,'test.app','warm',10000000);INSERT INTO android_startup_time_to_display VALUES(1,8000000,NULL);")
            self.assertEqual(db.execute(sql).fetchone(),('warm',10,8,None))

    def test_cold_start_can_compare_startup_without_fabricating_graphics(self):
        reports=self.reports()
        for report in reports:
            report['scenario']='cold_start'
            for capture in report['captures']:
                capture['startup_ms']=234
                capture['frames']=gfxinfo(HEADER)
        result=compare(reports)
        self.assertTrue(result['comparable'])
        self.assertEqual(result['rows'][0]['startup_ms']['median'],234)
        self.assertIsNone(result['rows'][0]['sample_medians_ms']['median'])
        self.assertEqual(result['rows'][0]['frame_count'],0)
        reports[0]['scenario']='warm_start'
        self.assertFalse(compare(reports)['comparable'])
