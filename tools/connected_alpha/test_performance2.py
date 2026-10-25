"""Navigation2 differential correctness, privacy boundaries and numerical lab contracts."""
import copy
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

from performance.navigation_contract import ROOT,BASE,PRODUCTION,PATHS,reserved,reverse,restore_reserved,validate_work1
from performance.radius_probe import run,sources
from performance.navigation import queries,csv_numbers,summarize,analyze
from performance.compare import compare
import test_performance
from performance.capture import collect_environment


class Navigation2(unittest.TestCase):
    def reports(self):
        old=test_performance.PerformanceLab().reports()
        labels=('exteraless','alpha1272','pr92','candidate')
        shas=('1ad6a60a6834ffca722b1a22f4fba27ecb29a061','8619ba40fbd8fd9d9d898ff307fb0c0716661254',BASE,'a'*40)
        result=[]
        for label,sha in zip(labels,shas):
            r=copy.deepcopy(old[0]);r.update(label=label,source_commit=sha)
            r['environment']['build_mode']='release-profileable'
            for c in r['captures']:
                c['memory_before']={'total_pss_kib':10000};c['memory_after']={'total_pss_kib':10500}
            result.append(r)
        return result

    def test_four_way_comparison_is_pinned_and_does_not_infer_superiority(self):
        result=compare(self.reports(),'navigation2')
        self.assertTrue(result['comparable']);self.assertEqual(len(result['rows']),4)
        self.assertEqual(result['superiority'],'NOT_AUTOMATICALLY_ESTABLISHED')
        self.assertEqual(result['rows'][0]['memory_after_pss_kib']['median'],10500)
        self.assertIsNone(result['rows'][0]['touch_to_visible_ms'])

    def test_four_way_rejects_wrong_build_modes_revisions_and_duplicate_candidate(self):
        for i in range(3):
            reports=self.reports();reports[i]['source_commit']='b'*40
            self.assertFalse(compare(reports,'navigation2')['comparable'])
        for bad in ('debug','unverified',None):
            reports=self.reports();reports[3]['environment']['build_mode']=bad
            self.assertFalse(compare(reports,'navigation2')['comparable'])
        reports=self.reports();reports[3]['source_commit']=BASE
        self.assertFalse(compare(reports,'navigation2')['comparable'])
        self.assertFalse(compare(self.reports()[:-1],'navigation2')['comparable'])

    def test_four_way_keeps_original_thermal_refresh_and_repetition_guards(self):
        for mutate in (lambda r:r['captures'].pop(),lambda r:r['captures'][0]['health'].update(eligible=False),
                       lambda r:r['environment'].update(refresh_profile='different')):
            reports=self.reports();mutate(reports[3]);self.assertFalse(compare(reports,'navigation2')['comparable'])
        with self.assertRaises(ValueError):compare(self.reports(),'bad')

    def test_bad_memory_snapshot_cannot_qualify(self):
        for value in (float('nan'),float('inf'),-1,True,'private-text'):
            reports=self.reports();reports[3]['captures'][0]['memory_after']['total_pss_kib']=value
            self.assertFalse(compare(reports,'navigation2')['comparable'])

    def test_build_mode_is_collected_without_account_queries(self):
        calls=[]
        class Device:
            def shell(self,*args):calls.append(args);return 'test'
        keys=('theme','cache_state','conversation_fixture','workload_id','music_state','refresh_profile','installation_state','test_session_state')
        a=SimpleNamespace(serial='private-serial',build_mode='release',max_thermal=1,max_temperature_c=38,min_battery=30,charging='unplugged',**{k:'same' for k in keys})
        value=collect_environment(Device(),a)
        self.assertEqual(value['build_mode'],'release');self.assertNotIn(a.serial,json.dumps(value))
        self.assertTrue(all(x[0] in ('settings','wm','getprop') for x in calls))

    def test_actual_radius_methods_differential_and_host_allocation(self):
        with tempfile.TemporaryDirectory() as temp:
            data=run(Path(temp)/'report.json')
            self.assertEqual(data['differential_steps'],30000)
            for mode in ('scaled','uniform'):
                self.assertGreater(data['baseline_'+mode+'_host_bytes'],data['candidate_'+mode+'_host_bytes'])
            self.assertIsNone(data['ART_bytes']);self.assertIsNone(data['physical_scroll_ms'])

    def test_exact_radius_patch_rejects_unreviewed_mutation(self):
        path=next(iter(PRODUCTION));data=(ROOT/path).read_bytes()
        self.assertEqual(reverse(data),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT))
        with self.assertRaises(ValueError):reverse(data.replace(b'forcePreview = value;',b'forcePreview = false;',1))

    def test_only_private_radius_calculation_changes_and_virtual_overloads_are_preserved(self):
        before,after=sources();anchor='    private void applyRoundRadiusInternal()'
        self.assertEqual(before[:before.index(anchor)],after[:after.index(anchor)])
        end='    public void setRoundRadiusEnabled'
        self.assertEqual(before[before.index(end):],after[after.index(end):])
        body=after[after.index(anchor):after.index(end)]
        self.assertNotIn('new ',body);self.assertIn('updateDrawableRadius(currentImageDrawable)',body)
        self.assertIn('setRoundRadius(new int[]{value, value, value, value})',after)

    def test_work1_reservations_and_entire_pr92_production_are_byte_exact(self):
        protected=reserved();self.assertGreater(len(protected),50)
        work1=validate_work1()
        from integration_contract import combined_paths
        for path in protected:
            self.assertEqual(restore_reserved(path,(ROOT/path).read_bytes()),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),path)
        changed=set(subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines())
        changed.update(subprocess.check_output(['git','ls-files','-o','--exclude-standard'],cwd=ROOT,text=True).splitlines())
        self.assertFalse(changed-(PATHS|combined_paths()),changed-(PATHS|combined_paths()))
        from studio_contract import PATHS as STUDIO_PATHS
        self.assertEqual({p for p in changed if p.startswith('TMessagesProj/') and p not in work1 and p not in STUDIO_PATHS},set(PRODUCTION))

    def test_window_and_package_validation_rejects_injection_and_invalid_clocks(self):
        for window in ((0,0),(20,10),(-1,10),(False,10),(0,60_000_000_001)):
            with self.assertRaises(ValueError):queries('test.app',*window)
        with self.assertRaises(ValueError):queries("test.app';SELECT 1",0,10)

    def database(self):
        db=sqlite3.connect(':memory:')
        db.executescript('''CREATE TABLE process(upid INT,pid INT,name TEXT);CREATE TABLE thread(utid INT,upid INT,tid INT,name TEXT);
CREATE TABLE sched(utid INT,ts INT,dur INT);CREATE TABLE thread_state(utid INT,ts INT,dur INT,state TEXT);
CREATE TABLE actual_frame_timeline_slice(upid INT,ts INT,dur INT,jank_type TEXT);
INSERT INTO process VALUES(1,10,'test.app'),(2,20,'private.app');INSERT INTO thread VALUES(1,1,10,'main'),(2,1,11,'RenderThread'),(3,2,20,'main');
INSERT INTO sched VALUES(1,50,100),(1,180,100),(2,120,20),(3,120,50);
INSERT INTO thread_state VALUES(1,50,100,'R'),(1,180,100,'R+'),(1,100,100,'S');
INSERT INTO actual_frame_timeline_slice VALUES(1,100,50,'None'),(1,150,50,'App Deadline Missed'),(1,50,100,'None'),(2,100,50,'None'),(1,110,30,NULL);''')
        return db

    def test_cpu_and_runnable_durations_clip_to_window_and_exclude_other_process(self):
        q=queries('test.app',100,200)
        with self.database() as db:
            self.assertEqual(db.execute(q['cpu']).fetchall(),[(0,70/1e6),(1,20/1e6)])
            self.assertEqual(db.execute(q['main_state']).fetchone(),(70/1e6,))
            rows=db.execute(q['frames']).fetchall()
            self.assertEqual(rows,[(50/1e6,0),(50/1e6,1),(30/1e6,None)])

    def test_exact_input_association_excludes_speculation_and_outside_present(self):
        db=sqlite3.connect(':memory:')
        db.executescript('''CREATE TABLE android_input_events(process_name TEXT,read_time INT,dispatch_latency_dur INT,handling_latency_dur INT,total_latency_dur INT,frame_id INT,is_speculative_frame INT,end_to_end_latency_dur INT);
INSERT INTO android_input_events VALUES('test.app',100,1,2,4,10,0,10),('test.app',100,1,2,4,11,1,20),('test.app',190,1,2,4,12,0,20),('test.app',100,1,2,4,NULL,0,NULL),('private.app',100,1,2,4,10,0,10);''')
        sql=queries('test.app',100,200)['input'].split(';',1)[1]
        rows=db.execute(sql).fetchall();self.assertEqual(len(rows),4)
        self.assertEqual([x[-1] for x in rows],[10/1e6,None,None,None])
        self.assertNotEqual(rows[0][-1],rows[0][-2])

    def test_gc_query_excludes_incomplete_cross_boundary_and_other_process(self):
        db=sqlite3.connect(':memory:');db.executescript('''CREATE TABLE android_garbage_collection_events(process_name TEXT,gc_ts INT,gc_dur INT,reclaimed_mb REAL);
INSERT INTO android_garbage_collection_events VALUES('test.app',110,20,3),('test.app',90,20,5),('test.app',110,-1,1),('private.app',110,20,3);''')
        self.assertEqual(db.execute(queries('test.app',100,200)['gc'].split(';',1)[1]).fetchall(),[(20/1e6,3)])

    def test_numeric_export_never_accepts_names_nonfinite_or_truncation(self):
        self.assertEqual(csv_numbers('"time_ms","other"\n3.5,"[NULL]"\n'),[{'time_ms':3.5,'other':None}])
        for text in ('x\nNaN\n','x\n-2\n','x\nsecret-message\n','x,y\n2\n'):
            with self.assertRaises(ValueError):csv_numbers(text)
        value=summarize({'input':[{'input_read_to_present_ms':None,'dispatch_to_ack_ms':2,'handling_ms':1}]})
        self.assertIsNone(value['input_read_to_present_ms']['median']);self.assertEqual(value['input_events_without_exact_present'],1)
        self.assertIsNone(value['first_interaction_possible_ms'])

    def test_local_analyzer_never_uploads_or_preserves_raw_errors_and_supports_old_cli(self):
        for modern in (False,True):
            calls=[]
            def execute(args,**kwargs):
                calls.append(args)
                if '--help' in args:return SimpleNamespace(returncode=0,stdout='--format' if modern else '',stderr='')
                name=Path(args[args.index('-f')+1]).stem
                if name=='gc':return SimpleNamespace(returncode=1,stdout='',stderr='PRIVATE_TRACE_DETAIL')
                return SimpleNamespace(returncode=0,stdout='numeric\n1\n',stderr='')
            result=analyze(Path('/local/binary'),Path('/local/test-trace'),'test.app',100,200,execute)
            self.assertEqual(result['unavailable_queries'],['gc'])
            self.assertNotIn('PRIVATE',json.dumps(result))
            self.assertTrue(all(a[0]=='/local/binary' and a[1]=='query' for a in calls))
            self.assertEqual('--format' in calls[1],modern)

    def test_complete_image_receiver_parses_and_has_no_other_production_changes(self):
        # Actual source AST only, not a semantic/full Android module compile.
        code='''import javax.tools.*;import com.sun.source.util.*;import java.util.*;class Parse {public static void main(String[] args)throws Exception{var c=ToolProvider.getSystemJavaCompiler();var d=new DiagnosticCollector<JavaFileObject>();try(var f=c.getStandardFileManager(d,null,null)){var t=(JavacTask)c.getTask(null,f,d,List.of("-proc:none"),null,f.getJavaFileObjects(args));for(var u:t.parse()){}for(var x:d.getDiagnostics())if(x.getKind()==Diagnostic.Kind.ERROR)throw new AssertionError(x);}}}'''
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'Parse.java';p.write_text(code)
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',temp,str(p)],check=True,capture_output=True)
            subprocess.run(['java','-cp',temp,'Parse',str(ROOT/next(iter(PRODUCTION)))],check=True,capture_output=True)

    def test_ci_no_apk_no_private_credentials_and_exact_source_revision(self):
        s=(ROOT/'.github/workflows/performance2.yml').read_text()
        self.assertIn('github.event.pull_request.head.sha || github.sha',s)
        for token in ('secrets:', 'assembleConnectedAlpha', 'upload-release', 'signing'):
            self.assertNotIn(token,s)
        self.assertIn("github.head_ref != 'perf/alpha1273-engineering2'",(ROOT/'.github/workflows/pr.yml').read_text())

if __name__=='__main__':unittest.main()
