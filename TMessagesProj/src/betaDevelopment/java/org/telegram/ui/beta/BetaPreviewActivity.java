package org.telegram.ui.beta;

import android.app.Activity;
import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.BuildConfig;
import org.telegram.messenger.BuildVariantPolicy;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.ActionBarLayout;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.DialogCell;
import org.telegram.ui.Cells.TextSettingsCell;

import java.util.ArrayList;
import java.lang.ref.WeakReference;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Offline synthetic routes using real client cells/navigation, never an account or session. */
public final class BetaPreviewActivity extends Activity {
    private ActionBarLayout navigation;
    private Theme.ThemeInfo initialTheme, ownedTheme;
    private BetaNavigation requests;
    private BetaSystemBack systemBack;
    private NavigationEvents events;
    private SceneFrameObserver frameObserver;
    private final ProbeState probe = new ProbeState();
    private TextSettingsCell probeCell, exportCell;
    private boolean exportPending, closeAccepted;
    private String exportStatus = "Save app-private events";
    private long exportId;
    private final ExecutorService localRuntime = Executors.newSingleThreadExecutor();

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
        systemBack = new BetaSystemBack(this, () -> {
            if (isFinishing() || isDestroyed()) return;
            if (requests != null) requestClose(); else finish();
        });
        systemBack.register();
        if (!BetaPostInit.ensure(ApplicationLoader::postInitApplication)) {
            // A failed post-init stays blocked across Activity recreation in this process.
            // Application.onCreate/ART failures before this Activity remain outside this boundary.
            TextView failure = new TextView(this);
            failure.setText("FlexyGram offline startup stopped: POST_INIT_FAILED");
            setContentView(failure);
            return;
        }
        initialTheme = Theme.getCurrentTheme();
        BetaUiState restored = BetaUiState.restore(state, Theme.isCurrentThemeDark());
        if (restored.dark != Theme.isCurrentThemeDark()) {
            Theme.ThemeInfo next = Theme.getTheme(restored.dark ? "Dark Blue" : "Blue");
            if (next != null) Theme.applyTheme(next, false, false);
        }
        ownedTheme = Theme.getCurrentTheme();
        navigation = new ActionBarLayout(this, false);
        navigation.setFragmentStack(new ArrayList<>());
        setContentView(navigation);
        events = new NavigationEvents(4096, System::nanoTime);
        requests = new BetaNavigation(new LatestNavigation.Scheduler() {
            @Override public void postFrame(Runnable action) { navigation.postOnAnimation(action); }
            @Override public void cancel(Runnable action) { navigation.removeCallbacks(action); }
        }, new BetaNavigation.Host() {
            @Override public boolean busy() { return navigation.checkTransitionAnimation() || navigation.isTransitionAnimationInProgress()
                    || navigation.isSwipeInProgress() || navigation.isPreviewOpenAnimationInProgress(); }
            @Override public boolean perform(BetaNavigation.Destination destination) {
                switch (destination) {
                    case CONVERSATION:
                        if (!(navigation.getLastFragment() instanceof Routes)) return false;
                        return navigation.presentFragment(new Conversation());
                    case SETTINGS:
                        if (!(navigation.getLastFragment() instanceof Routes)) return false;
                        return navigation.presentFragment(new Settings());
                    case BACK:
                        if (navigation.getFragmentStack().size() <= 1) { finish(); return false; }
                        closeAccepted = false;
                        // finishFragment() returning true does NOT prove closeLastFragment accepted.
                        navigation.closeLastFragment(true);
                        return closeAccepted; // observed onTransitionAnimationStart(false, true)
                    case LIGHT: case DARK:
                        if (!(navigation.getLastFragment() instanceof Settings)) return false;
                        Theme.ThemeInfo next = Theme.getTheme(destination == BetaNavigation.Destination.DARK ? "Dark Blue" : "Blue");
                        if (next == null) return false;
                        Theme.applyTheme(next, false, false);
                        ownedTheme = Theme.getCurrentTheme();
                        navigation.rebuildAllFragmentViews(true, true);
                        return true;
                    default: return false;
                }
            }
            @Override public void observeFrame(java.util.function.Consumer<Boolean> complete) {
                BaseFragment target = navigation.getLastFragment();
                View view = target == null ? null : target.getFragmentView();
                if (view == null) { complete.accept(null); return; }
                frameObserver = new SceneFrameObserver(view,
                    () -> navigation.getLastFragment() == target && target.getFragmentView() == view
                        && !navigation.isTransitionAnimationInProgress() && !navigation.isSwipeInProgress()
                        && !navigation.isPreviewOpenAnimationInProgress(), result -> {
                            frameObserver = null;
                            complete.accept(result);
                        });
                frameObserver.start();
            }
            @Override public void cancelObservation() {
                if (frameObserver != null) { frameObserver.cancel(); frameObserver = null; }
            }
        }, events);
        navigation.addFragmentToStack(new Routes());
        if (restored.route == BetaUiState.Route.CONVERSATION) navigation.addFragmentToStack(new Conversation());
        else if (restored.route == BetaUiState.Route.SETTINGS) navigation.addFragmentToStack(new Settings());
        navigation.showLastFragment();
        requests.startup();
    }

    @Override protected void onResume() { super.onResume(); if (navigation != null) navigation.onResume(); if (requests != null) requests.resume(); }
    @Override protected void onPause() {
        if (requests != null) requests.pause();
        if (navigation != null) navigation.onPause();
        super.onPause();
    }
    @Override public void onBackPressed() {
        if (requests != null) requestClose(); else super.onBackPressed();
    }
    private void requestClose() {
        requests.request(BetaNavigation.Destination.BACK, navigation.getLastFragment() instanceof Conversation);
    }
    @Override protected void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        if (navigation == null) return;
        BaseFragment visible = navigation.getLastFragment();
        BetaUiState.Route route = visible instanceof Conversation ? BetaUiState.Route.CONVERSATION
                : visible instanceof Settings ? BetaUiState.Route.SETTINGS : BetaUiState.Route.HOME;
        new BetaUiState(route, Theme.isCurrentThemeDark()).save(state);
    }
    @Override protected void onDestroy() {
        if (systemBack != null) systemBack.close();
        if (requests != null) requests.close();
        probe.close();
        probeCell = null; exportCell = null;
        localRuntime.shutdownNow();
        if (navigation != null) navigation.removeAllFragments();
        // A config restart keeps its theme; an unrelated owner must not be overwritten on destruction.
        if (!isChangingConfigurations() && initialTheme != null && ownedTheme == Theme.getCurrentTheme())
            Theme.applyTheme(initialTheme, false, false);
        super.onDestroy();
    }

    private abstract class Scene extends BaseFragment {
        @Override public void onTransitionAnimationStart(boolean isOpen, boolean backward) {
            super.onTransitionAnimationStart(isOpen, backward);
            if (!isOpen && backward) closeAccepted = true;
        }
        @Override public void onFragmentDestroy() {
            if (this instanceof Settings) { probeCell = null; exportCell = null; }
            super.onFragmentDestroy();
        }
    }

    private final class Routes extends Scene {
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
            dialog.setOnClickListener(v -> requests.request(BetaNavigation.Destination.CONVERSATION, false));
            list.addView(dialog);
            TextSettingsCell settings = new TextSettingsCell(context);
            settings.setTextAndValue("Settings", "Offline preview", false);
            settings.setOnClickListener(v -> requests.request(BetaNavigation.Destination.SETTINGS, false));
            list.addView(settings);
            return fragmentView = list;
        }
    }

    private final class Conversation extends Scene {
        @Override public View createView(Context context) {
            back(this, "Synthetic conversation");
            return fragmentView = new OfflineConversationView(context, Theme.isCurrentThemeDark());
        }
    }

    private final class Settings extends Scene {
        @Override public View createView(Context context) {
            back(this, "Offline settings preview");
            LinearLayout list = list(context);
            TextSettingsCell theme = new TextSettingsCell(context);
            theme.setTextAndValue("Dark mode", Theme.isCurrentThemeDark() ? "On" : "Off", false);
            theme.setOnClickListener(v -> requests.request(Theme.isCurrentThemeDark()
                    ? BetaNavigation.Destination.LIGHT : BetaNavigation.Destination.DARK, false));
            list.addView(theme);
            TextSettingsCell status = new TextSettingsCell(context);
            status.setTextAndValue("Services", "All external capabilities disabled", false);
            list.addView(status);
            probeCell = new TextSettingsCell(context);
            renderProbe();
            probeCell.setOnClickListener(v -> startProbe());
            list.addView(probeCell);
            exportCell = new TextSettingsCell(context);
            renderExport();
            exportCell.setOnClickListener(v -> saveObservations());
            list.addView(exportCell);
            return fragmentView = list;
        }
    }

    private void renderProbe() {
        if (probeCell == null) return;
        String value;
        switch (probe.value()) {
            case RUNNING: value = "Initializing locally"; break;
            case READY: value = "Python initialized; JNI loaded; sys imported; plugins disabled"; break;
            case FAILED:
                switch (probe.outcome()) {
                    case JNI_UNAVAILABLE: value = "JNI not loaded"; break;
                    case PYTHON_START_FAILED: value = "Python start failed"; break;
                    default: value = "Python import failed";
                }
                break;
            default: value = "Tap to initialize without plugins";
        }
        probeCell.setEnabled(probe.value() != ProbeState.Value.RUNNING);
        probeCell.setTextAndValue("Local Python", value, false);
    }
    private void startProbe() {
        if (isFinishing() || isDestroyed() || !(navigation.getLastFragment() instanceof Settings) || !probe.begin()) return;
        renderProbe();
        final Context application = getApplicationContext();
        final WeakReference<BetaPreviewActivity> owner = new WeakReference<>(this);
        localRuntime.execute(() -> {
            final ProbeState.Outcome result = LocalPythonProbe.inspect(application);
            postProbeResult(owner, result);
        });
    }
    private static void postProbeResult(WeakReference<BetaPreviewActivity> owner, ProbeState.Outcome result) {
        BetaPreviewActivity activity = owner.get();
        if (activity == null) return;
        activity.runOnUiThread(() -> {
            BetaPreviewActivity current = owner.get();
            if (current == null || current.isFinishing() || current.isDestroyed()) return;
            if (current.probe.finish(result)) current.renderProbe();
        });
    }
    private void renderExport() {
        if (exportCell == null) return;
        exportCell.setEnabled(!exportPending);
        exportCell.setTextAndValue("Local observations", exportPending ? "Saving" : exportStatus, false);
    }
    private void saveObservations() {
        if (isFinishing() || isDestroyed() || !(navigation.getLastFragment() instanceof Settings) || exportPending) return;
        exportPending = true; renderExport();
        final Context application = getApplicationContext();
        final NavigationEvents capture = events;
        final long id = ++exportId;
        final WeakReference<BetaPreviewActivity> owner = new WeakReference<>(this);
        localRuntime.execute(() -> {
            final boolean success = BetaEventExport.save(application.getFilesDir(), capture, id);
            postExportResult(owner, success);
        });
    }
    private static void postExportResult(WeakReference<BetaPreviewActivity> owner, boolean success) {
        BetaPreviewActivity activity = owner.get();
        if (activity == null) return;
        activity.runOnUiThread(() -> {
            BetaPreviewActivity current = owner.get();
            if (current == null || current.isFinishing() || current.isDestroyed()) return;
            current.exportPending = false;
            current.exportStatus = success ? "Saved privately; observations only" : "Export incomplete";
            current.renderExport();
        });
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
                    requestClose();
                }
            }
        });
    }
}
