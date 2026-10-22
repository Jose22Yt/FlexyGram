"""Host regressions. Android-dependent integration is deliberately not claimed here."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'tools/real_alpha_offline_ui/materialize.py'
spec = importlib.util.spec_from_file_location('offline_materialize', TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
JDK = Path(os.environ.get('JAVA_HOME', str(Path(shutil.which('javac') or '/unavailable/bin/javac').resolve().parents[1])))
POLICY = ROOT / 'TMessagesProj/src/realAlphaOfflineUi/java/org/telegram/ui/realalpha/offline/OfflineDialogsUi.java'

def method(text, signature):
    start = text.index(signature)
    opening = text.index('{', start)
    # Preserve offsets while masking comments and literals before counting braces.
    masked = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/',
                    lambda match: ' ' * len(match.group()), text)
    depth = 1
    for end in range(opening + 1, len(text)):
        depth += (masked[end] == '{') - (masked[end] == '}')
        if depth == 0:
            return text[start:end + 1]
    raise ValueError('unbalanced method')

def run(args, cwd=None):
    return subprocess.run([str(a) for a in args], cwd=cwd, text=True, capture_output=True, check=True, timeout=60).stdout

class OfflineUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        m.materialize()
        cls.lock = json.loads((ROOT / 'tools/real_alpha_offline_ui/sources.json').read_text())
        cls.original = {p: (ROOT / 'TMessagesProj/src/main/java' / p).read_text() for p in m.SOURCES}
        cls.overlay = {p: (ROOT / m.OUTPUT / p).read_text() for p in m.SOURCES}
        cls.activity, cls.adapter, cls.search = [cls.overlay[p] for p in m.SOURCES]
        cls.scratch = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls.scratch.name)
        pkg = cls.tmp / 'org/telegram/messenger'; pkg.mkdir(parents=True)
        (pkg / 'BuildConfig.java').write_text('''package org.telegram.messenger;
public class BuildConfig {
public static String FLEXYGRAM_VARIANT="realAlpha", APPLICATION_ID="io.github.jose22yt.flexygram.realalpha", APP_HASH="";
public static int APP_ID=0; public static boolean ISOLATED_DIAGNOSTIC=true;
public static boolean FLEXYGRAM_CAP_AUTHENTICATION=false,FLEXYGRAM_CAP_TELEGRAMTRANSPORT=false,FLEXYGRAM_CAP_PUSH=false,
FLEXYGRAM_CAP_TRANSLATION=false,FLEXYGRAM_CAP_PLUGINS=false,FLEXYGRAM_CAP_SESSIONRESTORE=false;
}''')
        for name in ('BuildVariantPolicy', 'DiagnosticPolicy'):
            shutil.copyfile(ROOT / f'TMessagesProj/src/main/java/org/telegram/messenger/{name}.java', pkg / f'{name}.java')
        shutil.copyfile(POLICY, cls.tmp / POLICY.name)
        run([JDK / 'bin/javac', '-d', cls.tmp, *pkg.glob('*.java'), cls.tmp / POLICY.name])

    @classmethod
    def tearDownClass(cls): cls.scratch.cleanup()

    def java(self, name, source):
        path = self.tmp / (name + '.java'); path.write_text(source)
        run([JDK / 'bin/javac', '-cp', self.tmp, '-d', self.tmp, path])
        return run([JDK / 'bin/java', '-cp', self.tmp, name])

    def test_policy_closed_profile_and_each_independent_capability(self):
        source = '''import org.telegram.messenger.*;
import org.telegram.ui.realalpha.offline.OfflineDialogsUi;
public class PolicyHarness { static void yes(boolean b){if(!b)throw new AssertionError();}
public static void main(String[]x)throws Exception {
yes(OfflineDialogsUi.isClosedRealAlpha());
for(String variant:new String[]{"diagnostic","betaDevelopment","production","realAlphaStartupDiagnostic"}){
BuildConfig.FLEXYGRAM_VARIANT=variant;yes(!OfflineDialogsUi.isClosedRealAlpha());}
BuildConfig.FLEXYGRAM_VARIANT="realAlpha";
for(java.lang.reflect.Field f:BuildConfig.class.getFields())if(f.getName().startsWith("FLEXYGRAM_CAP_")){
f.setBoolean(null,true);yes(!OfflineDialogsUi.isClosedRealAlpha());f.setBoolean(null,false);}
BuildConfig.ISOLATED_DIAGNOSTIC=false;yes(!OfflineDialogsUi.isClosedRealAlpha());BuildConfig.ISOLATED_DIAGNOSTIC=true;
BuildConfig.APP_ID=1;yes(!OfflineDialogsUi.isClosedRealAlpha());BuildConfig.APP_ID=0;
BuildConfig.APP_HASH="synthetic";yes(!OfflineDialogsUi.isClosedRealAlpha());BuildConfig.APP_HASH="";
BuildConfig.APPLICATION_ID="other";yes(!OfflineDialogsUi.isClosedRealAlpha());
System.out.println("PolicyHarness PASS");}}'''
        self.assertIn('PASS', self.java('PolicyHarness', source))

    def test_real_inserted_search_methods_execute_with_local_doubles(self):
        source = (Path(__file__).parent / 'fixtures/SearchHarness.java').read_text()
        methods = '\n'.join(method(self.search, sig) for sig in (
            'public void cancelOfflineSearch()', 'private void searchOfflineDialogs(String text, int folderId)'))
        self.assertIn('PASS', self.java('SearchHarness', source.replace('/* METHODS */', methods)))

    def test_complete_overlay_java_parses(self):
        source = (Path(__file__).parent / 'fixtures/ParseJava.java').read_text()
        path = self.tmp / 'ParseJava.java'; path.write_text(source)
        run([JDK / 'bin/javac', '-d', self.tmp, path])
        self.assertIn('PASS', run([JDK / 'bin/java', '-cp', self.tmp, 'ParseJava', *[ROOT / m.OUTPUT / p for p in m.SOURCES]]))

    def test_permission_block_unchanged_and_enclosed_without_skipping_lifecycle(self):
        old = method(self.original[m.SOURCES[0]], 'public void onResume()')
        new = method(self.activity, 'public void onResume()')
        block = old[old.index('        final boolean tosAccepted;'):old.index('        showFiltersHint();')]
        self.assertIn('if (!closedOfflineProfile()) {\n' + block + '        }', new)
        tail = old[old.index('        showFiltersHint();'):]
        self.assertTrue(new.endswith(tail))
        self.assertIn('super.onResume();', new)

    def test_direct_permission_callbacks_are_guarded(self):
        for sig in ('private void askForPermissons(boolean alert)',
                    'public void onRequestPermissionsResultFragment(int requestCode, String[] permissions, int[] grantResults)'):
            body = method(self.activity, sig)
            self.assertTrue(body.split('{', 1)[1].lstrip().startswith('if (closedOfflineProfile()) {\n            return;'))
        self.assertIn('forceImportContactsStart && !closedOfflineProfile()', self.activity)

    def test_no_controller_completion_or_connection_state_fabrication(self):
        patch = (ROOT / m.PATCH).read_text()
        added = '\n'.join(line[1:] for line in patch.splitlines() if line.startswith('+') and not line.startswith('+++'))
        for forbidden in ('dialogsLoaded[', '.dialogsLoaded =', '.setConnectionState(', 'ConnectionStateConnected', 'forceImportContacts(', '.sendRequest(', 'setDialogsEndReached(', 'BuildConfig.APP_ID ='):
            self.assertNotIn(forbidden, added)

    def test_legacy_loading_source_guard_preserves_original_body(self):
        sig = 'public static void loadDialogs(AccountInstance accountInstance)'
        old = method(self.original[m.SOURCES[0]], sig)
        new = method(self.activity, sig)
        self.assertEqual(new.replace('\n        if (closedOfflineProfile()) {\n            return;\n        }', '', 1), old)
        self.assertIn('if (isOfflineLabRoot()) {\n            return;', method(self.activity, 'private void checkListLoad(ViewPage viewPage, int firstVisibleItem, int lastVisibleItem, boolean loadAll)'))

    def test_static_empty_label_and_native_recycler_contract(self):
        body = method(self.activity, 'private View offlineAwareEmptyView(ViewPage page, boolean eligible)')
        for required in ('return eligible ? page.progressView : null;', 'new TextView(', 'setClickable(false)', 'setFocusable(false)', 'Theme.key_emptyListPlaceholder', 'page.progressView.setVisibility(View.GONE)'):
            self.assertIn(required, body)
        self.assertEqual(self.activity.count('setEmptyView(offlineAwareEmptyView('), 4)
        self.assertIn('refreshOfflineEmptyViews();', method(self.activity, 'public ArrayList<ThemeDescription> getThemeDescriptions()'))

    def test_root_scope_does_not_apply_to_selection_archive_community(self):
        body = method(self.activity, 'public boolean isOfflineLabRoot()')
        for condition in ('!onlySelect', 'folderId == 0', 'communityId == 0', 'initialDialogsType == DIALOGS_TYPE_DEFAULT', 'delegate == null', 'searchString == null'):
            self.assertIn(condition, body)

    def test_empty_adapter_guard_executes_without_controller_flags(self):
        sig = 'private void updateItemList()'
        body = method(self.adapter, sig)
        original = method(self.original[m.SOURCES[1]], sig)
        inserted = body[body.index('{')+1:body.index('        if (communityId != 0)')]
        self.assertEqual(body.replace(inserted, '\n', 1), original)
        self.assertIn('PASS', self.java('AdapterHarness', '''import java.util.*;
public class AdapterHarness {
boolean closed; Object onlineContacts=new Object(); boolean isEmpty,hasHints=true,forceUpdatingContacts=true; int dialogsCount=9;
ArrayList<Integer> itemInternals=new ArrayList<>(List.of(1));
class Parent { boolean isOfflineLabRoot(){return closed;} } Parent parentFragment=new Parent();
void update(){''' + inserted + '''itemInternals.add(2);}
public static void main(String[]x){ AdapterHarness h=new AdapterHarness();h.closed=true;h.update();
if(!h.itemInternals.isEmpty()||h.dialogsCount!=0||!h.isEmpty||h.hasHints||h.onlineContacts!=null||h.forceUpdatingContacts)throw new AssertionError();
h.closed=false;h.update();if(!h.itemInternals.equals(List.of(2)))throw new AssertionError();h.parentFragment=null;h.update();if(h.itemInternals.size()!=2)throw new AssertionError();System.out.println("PASS");}}'''))

    def test_search_entry_and_paging_guard_leave_original_other_profile_body(self):
        for sig, guard in (
                ('public void searchDialogs(String text, int folderId, boolean allowPublicPosts)',
                 '\n        if (org.telegram.ui.realalpha.offline.OfflineDialogsUi.isClosedRealAlpha()) {\n            searchOfflineDialogs(text, folderId);\n            return;\n        }'),
                ('public void loadMoreSearchMessages()',
                 '\n        if (org.telegram.ui.realalpha.offline.OfflineDialogsUi.isClosedRealAlpha()) {\n            return;\n        }')):
            self.assertEqual(method(self.search, sig).replace(guard, '', 1), method(self.original[m.SOURCES[2]], sig))

    def test_destroy_cancels_only_local_work_before_original_cleanup(self):
        body = method(self.activity, 'public void onFragmentDestroy()')
        self.assertLess(body.index('cancelOfflineSearch()'), body.index('super.onFragmentDestroy()'))
        self.assertIn('observersGroup.removeAllObservers();', body)
        cancel = method(self.search, 'public void cancelOfflineSearch()')
        self.assertNotIn('ConnectionsManager', cancel)
        self.assertIn('delegate = null', cancel)

    def test_actual_gradle_overlay_dsl_with_explicit_model(self):
        lib = Path(os.environ.get('GRADLE_GROOVY_LIB', str(Path(os.environ.get('GRADLE_HOME', '/unavailable')) / 'lib')))
        jars = sorted(lib.glob('groovy-*.jar'))
        self.assertTrue(jars, 'Groovy runtime required; not silently skipped')
        output = run([JDK / 'bin/java', '-cp', os.pathsep.join(map(str, jars)), 'groovy.ui.GroovyMain',
                      Path(__file__).parent / 'fixtures/GradleOverlayHarness.groovy', ROOT])
        self.assertIn('GradleOverlayHarness PASS', output)

    def test_remote_message_filter_does_not_create_loading_placeholder(self):
        self.assertEqual(self.search.count('if (!org.telegram.ui.realalpha.offline.OfflineDialogsUi.isClosedRealAlpha() && (currentMessagesFilter != Filter.All || forceLoadingMessages) && searchResultMessages.isEmpty())'), 4)

    def test_new_empty_view_api_compiles_against_android24_stubs(self):
        sdk = Path(os.environ.get('ANDROID24_JAR', str(Path(os.environ.get('ANDROID_HOME', '/unavailable')) / 'platforms/android-24/android.jar')))
        self.assertTrue(sdk.is_file(), 'API24 SDK stubs required; not silently skipped')
        body = method(self.activity, 'private View offlineAwareEmptyView(ViewPage page, boolean eligible)')
        source = """import android.view.*; import android.widget.*;
class AndroidEmptyViewApi {
class ViewPage extends FrameLayout { View progressView; TextView offlineEmptyView; ViewPage(android.content.Context c){super(c);} }
static class LayoutHelper {static int MATCH_PARENT=-1; static FrameLayout.LayoutParams createFrame(int w,int h){return new FrameLayout.LayoutParams(w,h);} }
static class R {static class string { static int FlexyGramOfflineDialogsEmpty=1;}}
static class LocaleController {static String getString(int id){return "";} }
static class Theme {static int key_emptyListPlaceholder=1;}
boolean isOfflineLabRoot(){return true;} int dp(int value){return value;} int getThemedColor(int key){return key;}
""" + body + "\n}"
        path = self.tmp / 'AndroidEmptyViewApi.java'; path.write_text(source)
        run([JDK / 'bin/javac', '-cp', sdk, '-d', self.tmp, path])

    def test_resources_are_localized_and_minimal(self):
        base = ROOT / 'TMessagesProj/src/realAlphaOfflineUi/res'
        expected = {'FlexyGramOfflineDialogsTitle','FlexyGramOfflineDialogsEmpty'}
        for path in base.glob('*/strings.xml'):
            nodes = ET.parse(path).getroot()
            self.assertEqual({n.attrib['name'] for n in nodes}, expected)
            self.assertNotIn('...', ''.join(n.text for n in nodes))

    def fixture_repository(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup); root = Path(tmp.name)
        for relative in [m.PATCH, Path('tools/real_alpha_offline_ui/sources.json'), *[Path('TMessagesProj/src/main/java') / p for p in m.SOURCES]]:
            target = root / relative; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT / relative, target)
        return root

    def test_materializer_idempotent_and_shared_sources_unchanged(self):
        root = self.fixture_repository()
        before = [(root / 'TMessagesProj/src/main/java' / p).read_bytes() for p in m.SOURCES]
        m.materialize(root); self.assertTrue(m.materialize(root, check=True)['verified'])
        self.assertEqual(before, [(root / 'TMessagesProj/src/main/java' / p).read_bytes() for p in m.SOURCES])

    def test_reject_missing_materialization(self):
        with self.assertRaisesRegex(ValueError, 'not materialized'): m.materialize(self.fixture_repository(), check=True)

    def test_reject_modified_original(self):
        root=self.fixture_repository(); path=root / 'TMessagesProj/src/main/java' / m.SOURCES[0]; path.write_text(path.read_text()+'\n')
        with self.assertRaisesRegex(ValueError, 'original hash'): m.materialize(root)

    def test_reject_modified_patch(self):
        root=self.fixture_repository(); path=root/m.PATCH; path.write_text(path.read_text()+'\n')
        with self.assertRaisesRegex(ValueError, 'patch hash'): m.materialize(root)

    def test_reject_modified_overlay(self):
        root=self.fixture_repository(); m.materialize(root); path=root/m.OUTPUT/m.SOURCES[0]; path.write_text(path.read_text()+'\n')
        with self.assertRaisesRegex(ValueError, 'overlay differs'): m.materialize(root)

    def test_reject_unexpected_generated_class(self):
        root=self.fixture_repository(); m.materialize(root); (root/m.OUTPUT/'Unexpected.java').write_text('class Unexpected {}')
        with self.assertRaisesRegex(ValueError, 'file inventory'): m.materialize(root)

    def test_reject_symlinked_output(self):
        root=self.fixture_repository(); destination=root/m.OUTPUT; destination.parent.mkdir(parents=True)
        target=root/'elsewhere'; target.mkdir(); destination.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlinked'): m.materialize(root)

    def test_reject_inventory_expansion(self):
        root=self.fixture_repository(); p=root/'tools/real_alpha_offline_ui/sources.json'; lock=json.loads(p.read_text()); lock['sources']['../Unexpected.java']={}; p.write_text(json.dumps(lock))
        with self.assertRaisesRegex(ValueError, 'source inventory'): m.materialize(root)

if __name__ == '__main__': unittest.main()
