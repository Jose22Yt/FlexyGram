"""Production startup/report/import checks, separate from device ART and latency measurements."""
import importlib.util
import json
from pathlib import Path
import subprocess
import zipfile
import pytest
from test_composer_layout import method
from test_render_work_reuse import JAVA, ROOT, probe


def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools/startup_optimization'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_draw_reporter_waits_for_real_readiness_and_releases_pending_callbacks(tmp_path):
    probe(tmp_path,{
        'android/view/View.java':'''package android.view;import java.util.*;public class View{public boolean reject;public int posts;public List<Runnable>queue=new ArrayList<>();public boolean post(Runnable r){posts++;if(reject)return false;queue.add(r);return true;}public void removeCallbacks(Runnable r){queue.removeIf(x->x==r);}public void fire(){queue.remove(0).run();}}''',
        'Probe.java':'''import app.flexygram.performance.StartupDrawReporter;import android.view.View;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){View v=new View();boolean[]ready={false};int[]reports={0};StartupDrawReporter r=new StartupDrawReporter(v,()->ready[0],()->reports[0]++);
 for(int i=0;i<10000;i++)r.afterDraw();check(v.posts==0);ready[0]=true;for(int i=0;i<10000;i++)r.afterDraw();check(v.posts==1&&reports[0]==0);
 ready[0]=false;v.fire();check(reports[0]==0);ready[0]=true;r.afterDraw();v.fire();check(reports[0]==1);for(int i=0;i<10000;i++)r.afterDraw();check(v.posts==2);
 View other=new View();StartupDrawReporter closed=new StartupDrawReporter(other,()->true,()->reports[0]++);closed.afterDraw();Runnable stale=other.queue.get(0);closed.close();stale.run();check(other.queue.isEmpty()&&reports[0]==1);
 View rejected=new View();rejected.reject=true;StartupDrawReporter retry=new StartupDrawReporter(rejected,()->true,()->reports[0]++);retry.afterDraw();rejected.reject=false;retry.afterDraw();rejected.fire();check(reports[0]==2);
}}'''
    },[JAVA/'app/flexygram/performance/StartupDrawReporter.java'])


def test_readiness_requires_loaded_laid_out_visible_content_and_unlocked_activity(tmp_path):
    launch=(JAVA/'org/telegram/ui/LaunchActivity.java').read_text()
    ready=method(launch,'private boolean isStartupContentReady()')
    chat=method((JAVA/'org/telegram/ui/ChatActivity.java').read_text(),'public boolean isStartupContentReady()')
    dialogs=method((JAVA/'org/telegram/ui/DialogsActivity.java').read_text(),'public boolean isStartupContentReady()')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static class View{boolean shown=true,layout;boolean isShown(){return shown;}boolean isLayoutRequested(){return layout;}}
 static class SharedConfig{static boolean appLocked;}
 static class BaseFragment{boolean paused;View view=new View();boolean isPaused(){return paused;}View getFragmentView(){return view;}}
 static class ViewPagerActivity extends BaseFragment{BaseFragment current;BaseFragment getCurrentVisibleFragment(){return current;}}
 static class ChatActivity extends BaseFragment{boolean firstLoading=true;View chatListView=new View();CHAT}
 static class DialogsActivity extends BaseFragment{static class Controller{boolean dialogsLoaded;}static class Page{View listView=new View();}Page[]viewPages={new Page()};Controller controller=new Controller();Controller getMessagesController(){return controller;}DIALOGS}
 boolean isResumed=true,finishing,destroyed;BaseFragment current;boolean isFinishing(){return finishing;}boolean isDestroyed(){return destroyed;}BaseFragment getSafeLastFragment(){throw new AssertionError("global selection may belong to a bubble Activity");}
 class Layout{BaseFragment getSafeLastFragment(){return current;}} Layout actionBarLayout=new Layout();java.util.List<Layout>sheetFragmentsStack=new java.util.ArrayList<>();
 READY
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();check(!p.isStartupContentReady());DialogsActivity d=new DialogsActivity();ViewPagerActivity pager=new ViewPagerActivity();pager.current=d;p.current=pager;
 check(!p.isStartupContentReady());d.controller.dialogsLoaded=true;check(p.isStartupContentReady());d.viewPages[0].listView.layout=true;check(!p.isStartupContentReady());d.viewPages[0].listView.layout=false;
 SharedConfig.appLocked=true;check(!p.isStartupContentReady());SharedConfig.appLocked=false;p.isResumed=false;check(!p.isStartupContentReady());p.isResumed=true;
 ChatActivity chat=new ChatActivity();p.current=chat;check(!p.isStartupContentReady());chat.firstLoading=false;check(p.isStartupContentReady());chat.paused=true;check(!p.isStartupContentReady());
 p.current=new BaseFragment();check(p.isStartupContentReady());p.destroyed=true;check(!p.isStartupContentReady());
}}'''.replace('READY',ready).replace('CHAT',chat).replace('DIALOGS',dialogs)})


def test_auxiliary_work_starts_once_after_draw_and_not_after_activity_destruction(tmp_path):
    source=(JAVA/'org/telegram/ui/LaunchActivity.java').read_text()
    start=source.index('    private final Runnable startupAuxiliary =')
    field=source[start:source.index('    private boolean isStartupContentReady()',start)]
    root=source[source.index('    private class ActivityContentLayout'):]
    block=method(root,'if (!startupAuxiliaryScheduled)')
    probe(tmp_path,{'Probe.java':'''import java.util.*;public class Probe{
 static class Queue{List<Runnable>jobs=new ArrayList<>();void postRunnable(Runnable r){jobs.add(r);}void fire(){jobs.remove(0).run();}}
 static class Utilities{static Queue globalQueue=new Queue();}static class EmojiHelper{static int calls;static EmojiHelper getInstance(){return new EmojiHelper();}void checkEmojiPacks(){calls++;}}
 static class PagePreviewRulesHelper{static int calls;static PagePreviewRulesHelper getInstance(){return new PagePreviewRulesHelper();}void checkPagePreviewRules(){calls++;}}
 static class BuildConfig{static final boolean NATIVE_BASELINE_TEST=false;}static class ApplicationLoader{static void scheduleOptionalStartupWork(){}}
 boolean destroyed,startupAuxiliaryScheduled;Queue ui=new Queue();boolean isFinishing(){return false;}boolean isDestroyed(){return destroyed;}boolean post(Runnable r){ui.postRunnable(r);return true;}
 FIELD void draw(){BLOCK}
 public static void main(String[]args){Probe p=new Probe();if(!Utilities.globalQueue.jobs.isEmpty())throw new AssertionError();for(int i=0;i<10000;i++)p.draw();if(p.ui.jobs.size()!=1||EmojiHelper.calls!=0)throw new AssertionError();p.ui.fire();if(EmojiHelper.calls!=0)throw new AssertionError();Utilities.globalQueue.fire();if(EmojiHelper.calls!=1||PagePreviewRulesHelper.calls!=1)throw new AssertionError();
 Probe gone=new Probe();gone.draw();gone.destroyed=true;gone.ui.fire();if(!Utilities.globalQueue.jobs.isEmpty())throw new AssertionError();}
}'''.replace('FIELD',field).replace('BLOCK',block)})
    assert 'checkEmojiPacks' not in method(source,'protected void onCreate(Bundle savedInstanceState)')
    assert 'removeCallbacks(startupAuxiliary)' in method(source,'protected void onDestroy()')


def test_native_optimizer_wiring_replaces_global_disable_and_preserves_identity():
    script=(ROOT/'gradle/flexygram-performance.gradle').read_text()
    native=script[script.index('    if (startupOptimization) {'):]
    assert 'setProguardFiles(' in native and 'performance-shrink.pro' in native
    assert 'minifyDebugWithR8' in native and "project.findProperty('APP_PACKAGE') != 'com.flexygram.messenger.nativebaseline'" in script
    assert "source.findAll { it.trim() != '-dontoptimize' }" in script
    assert '-dontobfuscate' in (ROOT/'TMessagesProj/proguard-rules.pro').read_text()
    workflow=(ROOT/'.github/workflows/ui-beta-debug.yml').read_text()
    assert '-PflexyStartupOptimization=true' in workflow and 'verify_apk.py' in workflow
    assert ':performance:compileDebugJavaWithJavac' in workflow
    producer=(ROOT/'performance/src/main/java/com/flexygram/performance/ProfileGeneration.java').read_text()
    assert '"flexy_startup",true,true' in producer


def test_benchmark_comparison_keeps_signed_frame_deadline_deltas_and_requires_real_samples():
    compare = load('compare_benchmarks').compare
    def report(value, model='Poco'):
        return {
            'context': {'build': {'model': model, 'fingerprint': 'fixture', 'version': {'sdk': 37}}},
            'benchmarks': [
                {'name': 'homeScroll[mode=None]', 'sampledMetrics': {'frameOverrunMs': {'P95': value}}},
                {'name': 'openChatToVisibleHistory', 'metrics': {'openChatToVisibleHistoryFirstMs': {'median': 65}}},
            ],
        }
    rows = compare(report(3.5), report(-0.5), ['homeScroll', 'openChatToVisibleHistory'])
    assert rows == [('homeScroll', 'frameOverrunMs', 'P95', 3.5, -0.5, -4.0),
                    ('openChatToVisibleHistory', 'openChatToVisibleHistoryFirstMs', 'median', 65, 65, 0)]
    with pytest.raises(ValueError):
        compare(report(3.5), report(0, model='Other'), ['homeScroll'])
    with pytest.raises(ValueError):
        compare(report(3.5), report(0), ['messageScroll'])
    with pytest.raises(ValueError):
        compare(report(3.5), report(float('nan')), ['homeScroll'])


def test_apk_verifier_distinguishes_optimizer_from_packaged_profiles_and_device_aot(tmp_path):
    module=load('verify_apk');apk=tmp_path/'app.apk';config=tmp_path/'rules.pro';profiles=tmp_path/'profiles';profiles.mkdir()
    with zipfile.ZipFile(apk,'w')as z:z.writestr('classes.dex',b'fixture')
    config.write_text('-dontobfuscate\n')
    report=module.verify(apk,config,'com.flexygram.messenger.nativebaseline','a'*40,profiles)
    assert report['r8_optimization_enabled'] and not report['own_device_profiles_present'] and not report['device_aot_verified']
    config.write_text('-dontobfuscate\n-dontoptimize\n')
    with pytest.raises(ValueError):module.verify(apk,config,report['package'],'a'*40,profiles)
    config.write_text('-dontobfuscate\n');(profiles/'baseline-prof.txt').write_text('Lfixture/A;\n')
    with pytest.raises(ValueError):module.verify(apk,config,report['package'],'a'*40,profiles)
    (profiles/'startup-prof.txt').write_text('Lfixture/A;\n')
    with pytest.raises(ValueError):module.verify(apk,config,report['package'],'a'*40,profiles)


def git(root,*args):
    return subprocess.check_output(['git',*args],cwd=root,text=True).strip()


def test_profile_import_requires_successful_device_results_matching_code_and_preserves_order(tmp_path):
    module=load('profiles');repo=tmp_path/'repo';repo.mkdir();git(repo,'init','-q');git(repo,'config','user.name','Fixture');git(repo,'config','user.email','fixture@example.invalid')
    code=repo/'TMessagesProj/src/main/java/Fixture.java';code.parent.mkdir(parents=True);code.write_text('class Fixture {}\n');git(repo,'add','.');git(repo,'commit','-qm','fixture')
    commit=git(repo,'rev-parse','HEAD');report=tmp_path/'report.json';report.write_text(json.dumps({'package':module.PACKAGE,'r8_optimization_enabled':True,'source_commit':commit,'apk_sha256':'b'*64}))
    baseline=tmp_path/'baseline.txt';baseline.write_text('HSPLfixture/Z;->start()V\nLfixture/A;\n')
    startup=tmp_path/'startup.txt';startup.write_text('SLfixture/Z;->start()V\n')
    results=tmp_path/'results.xml';results.write_text('<testsuite>'+''.join('<testcase classname="com.flexygram.performance.ProfileGeneration" name="'+n+'"/>'for n in ['startup','chat','settings'])+'</testsuite>')
    metadata=module.import_profiles([baseline],startup,results,report,repo)
    dest=repo/'TMessagesProj/src/main/generated/baselineProfiles'
    assert metadata['baseline_rules']==2 and (dest/'baseline-prof.txt').read_text()==baseline.read_text()
    git(repo,'add','.');git(repo,'commit','-qm','captured fixture profiles')
    results.write_text('<testsuite><testcase classname="ProfileGeneration" name="startup"><skipped/></testcase></testsuite>')
    with pytest.raises(ValueError):module.import_profiles([baseline],startup,results,report,repo)
    code.write_text('class Fixture { int changed; }\n')
    with pytest.raises(ValueError):module.import_profiles([baseline],startup,results,report,repo)
    baseline.write_text('HSLfixture/**;\n')
    with pytest.raises(ValueError):module.read_rules(baseline)
