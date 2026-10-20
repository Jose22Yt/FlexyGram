package org.telegram.ui.beta;

import android.app.Activity;
import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ScrollView;

import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.BuildConfig;
import org.telegram.messenger.BuildVariantPolicy;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.ActionBarLayout;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.DialogCell;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Cells.ThemePreviewMessagesCell;

import java.util.ArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

/** Offline synthetic routes using real client cells/navigation, never an account or session. */
public final class BetaPreviewActivity extends Activity {
    private ActionBarLayout navigation;
    private Theme.ThemeInfo initialTheme;
    private LatestNavigation requests;
    private final ExecutorService localRuntime = Executors.newSingleThreadExecutor();
    private boolean pythonProbePending;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        if (!"io.github.jose22yt.flexygram.beta.development".equals(BuildConfig.APPLICATION_ID)
                || !BuildConfig.ISOLATED_DIAGNOSTIC || BuildConfig.APP_ID != 0
                || !BuildConfig.APP_HASH.isEmpty() || BuildVariantPolicy.authenticationAllowed()
                || BuildVariantPolicy.telegramTransportAllowed() || BuildVariantPolicy.pushAllowed()
                || BuildVariantPolicy.pluginsAllowed() || BuildVariantPolicy.translationAllowed()
                || BuildVariantPolicy.sessionRestoreAllowed()) {
            finish();
            return;
        }
        ApplicationLoader.postInitApplication();
        initialTheme = Theme.getCurrentTheme();
        navigation = new ActionBarLayout(this, false);
        navigation.setFragmentStack(new ArrayList<>());
        setContentView(navigation);
        requests = new LatestNavigation(new LatestNavigation.Scheduler() {
            @Override public void postFrame(Runnable action) { navigation.postOnAnimation(action); }
            @Override public void cancel(Runnable action) { navigation.removeCallbacks(action); }
        }, navigation::checkTransitionAnimation);
        navigation.addFragmentToStack(new Routes());
        navigation.showLastFragment();
    }

    @Override protected void onResume() { super.onResume(); if (navigation != null) navigation.onResume(); }
    @Override protected void onPause() {
        if (requests != null) requests.cancel();
        if (navigation != null) navigation.onPause();
        super.onPause();
    }
    @Override public void onBackPressed() {
        if (requests != null) requests.cancel();
        if (navigation != null && navigation.getFragmentStack().size() > 1) navigation.onBackPressed();
        else super.onBackPressed();
    }
    @Override protected void onDestroy() {
        if (requests != null) requests.close();
        localRuntime.shutdownNow();
        if (navigation != null) navigation.removeAllFragments();
        if (initialTheme != null) Theme.applyTheme(initialTheme, false, false);
        super.onDestroy();
    }

    private final class Routes extends BaseFragment {
        @Override public View createView(Context context) {
            actionBar.setTitle("FlexyGram · Offline Development");
            LinearLayout list = list(context);
            DialogCell dialog = new DialogCell(null, context, false, false);
            DialogCell.CustomDialog data = new DialogCell.CustomDialog();
            data.id = 1;
            data.name = "Synthetic conversation";
            data.message = "Local UI fixture — no account or network";
            data.date = 1700000000;
            dialog.setDialog(data);
            dialog.setOnClickListener(v -> requests.submit(() -> {
                if (!(navigation.getLastFragment() instanceof Conversation)) presentFragment(new Conversation());
            }));
            list.addView(dialog);
            TextSettingsCell settings = new TextSettingsCell(context);
            settings.setTextAndValue("Settings", "Offline preview", false);
            settings.setOnClickListener(v -> requests.submit(() -> {
                if (!(navigation.getLastFragment() instanceof Settings)) presentFragment(new Settings());
            }));
            list.addView(settings);
            return fragmentView = list;
        }
    }

    private final class Conversation extends BaseFragment {
        @Override public View createView(Context context) {
            back(this, "Synthetic conversation");
            ScrollView scroll = new ScrollView(context);
            scroll.setFillViewport(true);
            ThemePreviewMessagesCell messages = new ThemePreviewMessagesCell(context, navigation, 0);
            messages.fragment = this;
            scroll.addView(messages);
            return fragmentView = scroll;
        }
    }

    private final class Settings extends BaseFragment {
        @Override public View createView(Context context) {
            back(this, "Offline settings preview");
            LinearLayout list = list(context);
            TextSettingsCell theme = new TextSettingsCell(context);
            theme.setTextAndValue("Dark mode", Theme.isCurrentThemeDark() ? "On" : "Off", false);
            theme.setOnClickListener(v -> {
                Theme.ThemeInfo next = Theme.getTheme(Theme.isCurrentThemeDark() ? "Blue" : "Dark Blue");
                if (next == null || navigation.checkTransitionAnimation()) return;
                Theme.applyTheme(next, false, false);
                navigation.rebuildAllFragmentViews(true, true);
            });
            list.addView(theme);
            TextSettingsCell status = new TextSettingsCell(context);
            status.setTextAndValue("Services", "All external capabilities disabled", false);
            list.addView(status);
            TextSettingsCell python = new TextSettingsCell(context);
            python.setTextAndValue("Local Python", "Tap to initialize without plugins", false);
            python.setOnClickListener(v -> {
                if (pythonProbePending) return;
                pythonProbePending = true;
                python.setEnabled(false);
                localRuntime.execute(() -> {
                    String outcome;
                    try {
                        if (!org.telegram.messenger.NativeLoader.loaded()) {
                            throw new IllegalStateException("JNI unavailable");
                        }
                        synchronized (Python.class) {
                            if (!Python.isStarted()) Python.start(new AndroidPlatform(getApplicationContext()));
                        }
                        Python.getInstance().getModule("sys"); // local standard library only
                        outcome = "JNI and Python initialized; plugins disabled";
                    } catch (Exception | LinkageError error) {
                        // No traceback, paths, tokens or private content in UI/logs.
                        outcome = "Initialization blocked: " + error.getClass().getSimpleName();
                    }
                    final String value = outcome;
                    runOnUiThread(() -> {
                        if (isFinishing() || isDestroyed()) return;
                        pythonProbePending = false;
                        python.setEnabled(true);
                        python.setTextAndValue("Local Python", value, false);
                    });
                });
            });
            list.addView(python);
            return fragmentView = list;
        }
    }

    private LinearLayout list(Context context) {
        LinearLayout list = new LinearLayout(context);
        list.setOrientation(LinearLayout.VERTICAL);
        list.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));
        return list;
    }

    private void back(BaseFragment fragment, String title) {
        fragment.getActionBar().setTitle(title);
        fragment.getActionBar().setBackButtonImage(org.telegram.messenger.R.drawable.ic_ab_back);
        fragment.getActionBar().setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick() {
            @Override public void onItemClick(int id) {
                if (id == -1) {
                    requests.cancel();
                    fragment.finishFragment();
                }
            }
        });
    }
}
