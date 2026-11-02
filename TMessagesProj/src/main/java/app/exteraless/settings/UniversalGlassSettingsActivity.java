package app.exteraless.settings;

import android.content.Context;
import android.view.View;
import android.widget.FrameLayout;
import java.util.ArrayList;

import app.exteraless.appearance.AppearanceConfig;
import app.exteraless.appearance.AvatarCornersSeekBar;
import app.exteraless.appearance.UniversalGlass;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.UItem;
import org.telegram.ui.Components.UniversalAdapter;
import org.telegram.ui.Components.UniversalRecyclerView;

/** Universal material controls; applying rebuilds native glass surfaces without forcing blur on. */
public final class UniversalGlassSettingsActivity extends BaseFragment {
    private static final int ENABLE = -1, OPACITY = -2, EDGE = -3, APPLY = -4;
    private UniversalRecyclerView list;
    private boolean dirty;

    @Override
    public View createView(Context context) {
        actionBar.setTitle(text(R.string.FlexyUniversalGlass));
        actionBar.setBackButtonImage(R.drawable.ic_ab_back);
        actionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick() {
            @Override public void onItemClick(int id) {
                if (id == -1) finishFragment();
            }
        });
        FrameLayout root = new FrameLayout(context);
        root.setBackgroundColor(getThemedColor(Theme.key_windowBackgroundGray));
        list = new UniversalRecyclerView(this, this::fillItems, this::onClick, null);
        list.setSections();
        list.adapter.setApplyBackground(false);
        root.addView(list, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.MATCH_PARENT));
        actionBar.setAdaptiveBackground(list);
        fragmentView = root;
        return root;
    }

    private static String text(int id) { return LocaleController.getString(id); }

    private void fillItems(ArrayList<UItem> items, UniversalAdapter adapter) {
        adapter.whiteSectionStart();
        items.add(UItem.asCheck(ENABLE, text(R.string.FlexyUniversalGlassEnable)).setChecked(AppearanceConfig.universalGlass.Bool()));
        adapter.whiteSectionEnd();
        items.add(UItem.asShadow(text(R.string.FlexyUniversalGlassInfo)));
        if (AppearanceConfig.universalGlass.Bool()) {
            adapter.whiteSectionStart();
            items.add(UItem.asCustom(OPACITY, slider(true)));
            items.add(UItem.asCustom(EDGE, slider(false)));
            adapter.whiteSectionEnd();
            items.add(UItem.asHeader(text(R.string.FlexyUniversalGlassSurfaces)));
            adapter.whiteSectionStart();
            int[] scopes = {UniversalGlass.INPUT, UniversalGlass.HEADER, UniversalGlass.NAVIGATION,
                    UniversalGlass.SEARCH, UniversalGlass.MENUS, UniversalGlass.FOLDERS};
            int[] labels = {R.string.FlexyGlassInput, R.string.FlexyGlassHeader, R.string.OEBottomNavigationBar,
                    R.string.Search, R.string.FlexyGlassMenus, R.string.FlexyGlassFolders};
            for (int i = 0; i < scopes.length; i++) {
                items.add(UItem.asCheck(scopes[i], text(labels[i]))
                        .setChecked((AppearanceConfig.universalGlassSurfaces.Int() & scopes[i]) != 0));
            }
            adapter.whiteSectionEnd();
            items.add(UItem.asShadow(text(R.string.FlexyGlassPerformance)));
        }
        items.add(UItem.asButton(APPLY, R.drawable.msg_theme, text(R.string.FlexyGlassApply)).accent());
    }

    private View slider(boolean opacity) {
        AvatarCornersSeekBar slider = new AvatarCornersSeekBar(getContext(), value -> {
            if (opacity) AppearanceConfig.universalGlassOpacity.setConfigInt(value);
            else AppearanceConfig.universalGlassEdge.setConfigInt(value);
            dirty = true;
        }, opacity ? 20 : 0, opacity ? 85 : 100,
                text(opacity ? R.string.FlexyGlassOpacity : R.string.FlexyGlassEdge), "", "");
        slider.setValueSuffix("%");
        slider.setValue(opacity ? AppearanceConfig.universalGlassOpacity.Int() : AppearanceConfig.universalGlassEdge.Int());
        return slider;
    }

    private void onClick(UItem item, View view, int position, float x, float y) {
        if (item.id == APPLY) {
            applyChanges();
            return;
        }
        if (item.id == ENABLE) {
            AppearanceConfig.universalGlass.setConfigBool(!AppearanceConfig.universalGlass.Bool());
        } else if (item.id > 0 && item.id <= UniversalGlass.FOLDERS) {
            AppearanceConfig.universalGlassSurfaces.setConfigInt(AppearanceConfig.universalGlassSurfaces.Int() ^ item.id);
        } else return;
        dirty = true;
        list.adapter.update(true);
    }

    private void applyChanges() {
        if (dirty && getParentLayout() != null) {
            dirty = false;
            getParentLayout().rebuildFragments(0);
        }
    }

    @Override
    public void onFragmentDestroy() {
        final var parent = getParentLayout();
        if (dirty && parent != null) {
            dirty = false;
            org.telegram.messenger.AndroidUtilities.runOnUIThread(() -> parent.rebuildFragments(0));
        }
        super.onFragmentDestroy();
    }
}
