"""Host-only CRASH-001 regressions: real beta wrappers, explicit framework doubles.
No Android runtime, account, network, APK installation or crash-cause certification.
Requires JAVA_HOME pointing to JDK 21; missing tools fail instead of skipping.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

from client_android_doubles import STUBS

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta"
HARNESS = r'''package org.telegram.ui.beta;

import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.telegram.ui.ActionBar.ActionBarLayout;
import org.telegram.ui.ActionBar.Theme;

public final class OfflineConversationHarness {
    static void need(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
    }
    static ActionBarLayout navigation(BetaPreviewActivity owner) throws Exception {
        java.lang.reflect.Field field = BetaPreviewActivity.class.getDeclaredField("navigation");
        field.setAccessible(true);
        return (ActionBarLayout) field.get(owner);
    }
    static void settle(ActionBarLayout nav) {
        // Explicit fake transition completion, not Android timing or rendering.
        for (int frame = 0; frame < 32; frame++) {
            nav.busy = false;
            nav.getLastFragment().getFragmentView().tree.draw();
            if (View.frames.isEmpty()) return;
            View.frame();
        }
        throw new AssertionError("host frame queue did not settle");
    }
    static void open(BetaPreviewActivity owner, int index) throws Exception {
        ActionBarLayout nav = navigation(owner);
        ((LinearLayout) nav.getLastFragment().getFragmentView()).children.get(index).performClick();
        View.frame();
        settle(nav);
    }
    static void back(BetaPreviewActivity owner) throws Exception {
        owner.dispatcher.dispatch(); View.frame(); settle(navigation(owner));
        need(navigation(owner).getFragmentStack().size() == 1 && !owner.isFinishing(),
                "Back did not return to home");
    }
    static OfflineConversationView conversation(ActionBarLayout nav) {
        View view = nav.getLastFragment().getFragmentView();
        need(view instanceof OfflineConversationView, "account-free view not installed");
        OfflineConversationView demo = (OfflineConversationView) view;
        LinearLayout rows = (LinearLayout) demo.children.get(0);
        need(rows.children.size() == 3, "missing synthetic messages");
        for (int index = 0; index < 3; index++) {
            LinearLayout row = (LinearLayout) rows.children.get(index);
            LinearLayout bubble = (LinearLayout) row.children.get(0);
            need(bubble.children.size() == 2, "missing text or local timestamp");
            need(!((TextView) bubble.children.get(0)).text.isBlank(), "blank demo message");
            need(((TextView) bubble.children.get(1)).text.endsWith("Local"), "non-local status");
            need(row.gravity == (index == 1 ? android.view.Gravity.END : android.view.Gravity.START),
                    "message direction changed");
            need(bubble.background instanceof android.graphics.drawable.GradientDrawable,
                    "missing bubble background");
        }
        return demo;
    }
    static void noOptionalRuntime() {
        need(!com.chaquo.python.Python.isStarted(), "conversation initialized Python");
        need(com.chaquo.python.Python.entered.getCount() == 1, "conversation imported Python");
        need(org.telegram.messenger.UserConfig.calls == 0, "conversation requested a session");
    }
    public static void main(String[] args) throws Exception {
        android.os.Build.VERSION.SDK_INT = 37;
        org.telegram.messenger.NativeLoader.ready = false;
        com.chaquo.python.Python.failStart = true;
        BetaPreviewActivity owner = new BetaPreviewActivity();
        owner.onCreate(null); owner.onResume();
        try {
            ActionBarLayout nav = navigation(owner);
            if (args[0].equals("standalone")) {
                need(new OfflineConversationView(new android.content.Context(), false).children.size() == 1,
                        "standalone content missing");
                need(new OfflineConversationView(new android.content.Context(), true).children.size() == 1,
                        "standalone dark content missing");
            } else if (args[0].equals("rapid")) {
                LinearLayout home = (LinearLayout) nav.getLastFragment().getFragmentView();
                for (int i = 0; i < 12; i++) home.children.get(0).performClick();
                View.frame();
                need(nav.getFragmentStack().size() == 2 && nav.busy, "rapid taps duplicated route");
                owner.dispatcher.dispatch(); View.frame();
                need(nav.getFragmentStack().size() == 2, "Back bypassed active transition");
                settle(nav);
                need(nav.getFragmentStack().size() == 1 && !owner.isFinishing(),
                        "queued Back lost after interrupted open");
                open(owner, 0); conversation(nav); back(owner);
            } else if (args[0].equals("theme")) {
                open(owner, 0); int light = conversation(nav).backgroundColor; back(owner);
                for (int i = 0; i < 2; i++) {
                    open(owner, 1);
                    ((LinearLayout) nav.getLastFragment().getFragmentView()).children.get(0).performClick();
                    View.frame(); settle(nav); back(owner);
                    open(owner, 0);
                    int color = conversation(nav).backgroundColor;
                    need((color != light) == (i == 0), "theme did not rebuild local palette");
                    back(owner);
                }
                need(!Theme.isCurrentThemeDark(), "light theme not restored");
            } else if (args[0].equals("recreate")) {
                open(owner, 0); conversation(nav);
                Bundle state = new Bundle(); owner.saveState(state);
                owner.changingConfigurations = true; owner.onPause(); owner.onDestroy();
                owner = new BetaPreviewActivity(); owner.onCreate(state); owner.onResume();
                nav = navigation(owner);
                need(nav.getFragmentStack().size() == 2 && !nav.busy, "conversation not restored idle");
                conversation(nav); settle(nav); back(owner);
            } else {
                int repeats = args[0].equals("repeat") ? 25 : 1;
                for (int i = 0; i < repeats; i++) {
                    open(owner, 0); conversation(nav);
                    need(nav.getFragmentStack().size() == 2, "conversation stack changed");
                    back(owner);
                }
            }
            noOptionalRuntime();
        } finally {
            owner.onPause(); owner.onDestroy();
        }
    }
}
'''

class OfflineConversationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.scratch.cleanup)
        cls.folder = Path(cls.scratch.name)
        cls.tools = Path(os.environ["JAVA_HOME"]) / "bin"
        for name, content in STUBS.items():
            target = cls.folder / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        # These dependencies deliberately reject access. This proves isolation in
        # the host fixture, not the exception observed on the user's Android.
        (cls.folder / "org/telegram/ui/Cells/ThemePreviewMessagesCell.java").write_text(
            'package org.telegram.ui.Cells;public class ThemePreviewMessagesCell extends android.view.View {'
            'public org.telegram.ui.ActionBar.BaseFragment fragment;'
            'public ThemePreviewMessagesCell(android.content.Context c,'
            'org.telegram.ui.ActionBar.ActionBarLayout n,int type){super(c);'
            'throw new AssertionError("ACCOUNT_RENDERER_USED");}}', encoding="utf-8")
        (cls.folder / "org/telegram/messenger/UserConfig.java").write_text(
            'package org.telegram.messenger;public class UserConfig {public static int calls;'
            'public static UserConfig getInstance(int account){calls++;'
            'throw new AssertionError("SESSION_ACCESS");}}', encoding="utf-8")
        beta = cls.folder / "org/telegram/ui/beta"
        beta.mkdir(parents=True)
        for source in SOURCE.glob("*.java"):
            (beta / source.name).write_bytes(source.read_bytes())
        (beta / "OfflineConversationHarness.java").write_text(HARNESS, encoding="utf-8")
        compiled = subprocess.run(
            [str(cls.tools / "javac"), "-encoding", "UTF-8", "--release", "21",
             "-d", str(cls.folder / "classes"),
             *map(str, cls.folder.rglob("*.java"))],
            capture_output=True, text=True, timeout=45)
        if compiled.returncode:
            raise AssertionError(compiled.stderr)

    def run_scenario(self, name):
        completed = subprocess.run(
            [str(self.tools / "java"), "-cp", str(self.folder / "classes"),
             "org.telegram.ui.beta.OfflineConversationHarness", name],
            capture_output=True, text=True, timeout=15)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_open_without_account_and_return_home(self):
        self.run_scenario("open")

    def test_fixed_messages_construct_without_optional_local_runtimes(self):
        self.run_scenario("standalone")

    def test_repeated_open_close_has_no_duplicate_routes(self):
        self.run_scenario("repeat")

    def test_rapid_taps_and_back_during_transition_preserve_queue(self):
        self.run_scenario("rapid")

    def test_dark_light_and_reenter_rebuild_message_palette(self):
        self.run_scenario("theme")

    def test_recreate_activity_restores_account_free_conversation(self):
        self.run_scenario("recreate")

    def test_view_has_no_telegram_or_optional_runtime_imports(self):
        source = (SOURCE / "OfflineConversationView.java").read_text(encoding="utf-8")
        imports = [line.strip() for line in source.splitlines() if line.startswith("import ")]
        self.assertTrue(imports)
        self.assertTrue(all(line.startswith("import android.") for line in imports))
        activity = (SOURCE / "BetaPreviewActivity.java").read_text(encoding="utf-8")
        self.assertNotIn("ThemePreviewMessagesCell", activity)
        self.assertIn("new OfflineConversationView(context, Theme.isCurrentThemeDark())", activity)


if __name__ == "__main__":
    unittest.main()
