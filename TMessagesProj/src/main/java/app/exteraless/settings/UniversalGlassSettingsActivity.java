package app.exteraless.settings;

import android.content.Context;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import java.util.ArrayList;

import app.exteraless.appearance.FlexyGlassConfig;
import app.exteraless.appearance.UniversalGlassConfig;
import app.flexygram.settings.FlexySignatureSlider;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.UItem;
import org.telegram.ui.Components.UniversalAdapter;
import org.telegram.ui.Components.UniversalRecyclerView;

/** One global effect switch and the existing material controls, saved automatically. */
public final class UniversalGlassSettingsActivity extends BaseFragment {
    private static final int ENABLE = -1, OPACITY = -2, EDGE = -3;
    private UniversalRecyclerView list;
    private View opacitySlider, edgeSlider;
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
        opacitySlider = edgeSlider = null;
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
        items.add(UItem.asCheck(ENABLE, text(R.string.FlexyGlassMasterSwitch)).setChecked(FlexyGlassConfig.enabled()));
        if (FlexyGlassConfig.enabled()) {
            if (opacitySlider == null) opacitySlider = slider(true);
            if (edgeSlider == null) edgeSlider = slider(false);
            items.add(UItem.asCustom(OPACITY, opacitySlider));
            items.add(UItem.asCustom(EDGE, edgeSlider));
        }
        adapter.whiteSectionEnd();
        items.add(UItem.asShadow(text(R.string.FlexyUniversalGlassInfo)));
    }

    private View slider(boolean opacity) {
        Context context = getContext();
        int min = opacity ? 20 : 0;
        int value = opacity ? UniversalGlassConfig.opacity() : UniversalGlassConfig.edge();
        String title = text(opacity ? R.string.FlexyGlassOpacity : R.string.FlexyGlassEdge);
        LinearLayout row = new LinearLayout(context);
        row.setOrientation(LinearLayout.VERTICAL);
        TextSettingsCell label = new TextSettingsCell(context);
        label.setTextAndValue(title, value + "%", false);
        row.addView(label, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 48));
        FlexySignatureSlider slider = new FlexySignatureSlider(context);
        slider.setContentDescription(title);
        slider.setMax((opacity ? 85 : 100) - min);
        slider.setProgress(value - min);
        row.addView(slider, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 48, 18, 0, 18, 4));
        slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                if (!fromUser) return;
                int selected = progress + min;
                if (opacity) UniversalGlassConfig.setOpacity(selected);
                else UniversalGlassConfig.setEdge(selected);
                // The existing custom material is applied everywhere once its controls are edited.
                UniversalGlassConfig.setEnabled(true);
                label.setTextAndValue(title, selected + "%", false);
                dirty = true;
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) { }
            @Override public void onStopTrackingTouch(SeekBar seekBar) { }
        });
        return row;
    }

    private void onClick(UItem item, View view, int position, float x, float y) {
        if (item.id != ENABLE) return;
        FlexyGlassConfig.setEnabled(!FlexyGlassConfig.enabled());
        dirty = true;
        list.adapter.update(true);
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
