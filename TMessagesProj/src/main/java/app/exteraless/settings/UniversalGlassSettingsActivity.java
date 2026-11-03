package app.exteraless.settings;

import android.content.Context;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import java.util.ArrayList;
import app.exteraless.appearance.AppearanceConfig;
import app.exteraless.appearance.FlexyGlassConfig;
import app.exteraless.appearance.UniversalGlassConfig;
import app.flexygram.effects.GlassSettings;
import app.flexygram.settings.FlexySignatureSlider;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.UItem;
import org.telegram.ui.Components.UniversalAdapter;
import org.telegram.ui.Components.UniversalRecyclerView;

/** Original effect, simple controls. Save once on release, rebuild underlying screens once on exit. */
public final class UniversalGlassSettingsActivity extends BaseFragment {
    private static final int ENABLE = -1, BLUR = -2, EDGE = -3, WIDTH = -4, STYLE = -5;
    private UniversalRecyclerView list;
    private View blurSlider, edgeSlider, widthSlider;
    private GlassSettings draft;
    private boolean pending, dirty;
    private static String text(int id) { return LocaleController.getString(id); }

    @Override public View createView(Context context) {
        if (draft == null) draft = UniversalGlassConfig.snapshot().with(0, FlexyGlassConfig.enabled() ? 1 : 0);
        actionBar.setTitle(text(R.string.FlexyUniversalGlass));
        actionBar.setBackButtonImage(R.drawable.ic_ab_back);
        actionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick() {
            @Override public void onItemClick(int id) { if (id == -1) finishFragment(); }
        });
        blurSlider = edgeSlider = widthSlider = null;
        FrameLayout root = new FrameLayout(context);
        root.setBackgroundColor(getThemedColor(Theme.key_windowBackgroundGray));
        list = new UniversalRecyclerView(this, this::fillItems, this::onClick, null);
        list.setSections(); list.adapter.setApplyBackground(false);
        root.addView(list, LayoutHelper.createFrame(-1, -1));
        actionBar.setAdaptiveBackground(list);
        fragmentView = root;
        return root;
    }
    private void fillItems(ArrayList<UItem> items, UniversalAdapter adapter) {
        adapter.whiteSectionStart();
        items.add(UItem.asCheck(ENABLE, text(R.string.FlexyGlassMasterSwitch)).setChecked(draft.enabled));
        if (draft.enabled) {
            if (blurSlider == null) blurSlider = slider(2, R.string.FlexyCrystalBlur, draft.blur, 48);
            if (edgeSlider == null) edgeSlider = slider(3, R.string.FlexyGlassEdge, draft.edge, 100);
            if (widthSlider == null) widthSlider = slider(4, R.string.FlexyCrystalWidth, draft.width, 30);
            items.add(UItem.asCustom(BLUR, blurSlider));
            items.add(UItem.asCustom(EDGE, edgeSlider));
            items.add(UItem.asCustom(WIDTH, widthSlider));
            items.add(UItem.asButton(STYLE, text(R.string.FlexyCrystalBorderStyle))
                    .setValue(styles()[Math.max(0, Math.min(2, AppearanceConfig.glassOutlineStyle()))]));
        }
        adapter.whiteSectionEnd();
        items.add(UItem.asShadow(text(R.string.FlexyUniversalGlassInfo)));
    }
    private String[] styles() {
        return new String[]{text(R.string.FlexyGlareDefault), text(R.string.FlexyGlareSolid), text(R.string.FlexyGlareDisabled)};
    }
    private View slider(int field, int title, int value, int max) {
        LinearLayout row = new LinearLayout(getContext()); row.setOrientation(LinearLayout.VERTICAL);
        TextSettingsCell label = new TextSettingsCell(getContext());
        label.setTextAndValue(text(title), format(field, value), false);
        row.addView(label, LayoutHelper.createLinear(-1, 48));
        FlexySignatureSlider control = new FlexySignatureSlider(getContext());
        control.setContentDescription(text(title)); control.setMax(max); control.setProgress(value);
        row.addView(control, LayoutHelper.createLinear(-1, 48, 18, 0, 18, 4));
        control.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                if (!fromUser) return;
                draft = draft.with(field, progress); pending = true;
                label.setTextAndValue(text(title), format(field, progress), false);
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) { }
            @Override public void onStopTrackingTouch(SeekBar seekBar) { savePending(); }
        });
        return row;
    }
    private String format(int field, int value) {
        return field == 4 ? String.format(java.util.Locale.getDefault(), "%.1f dp", value / 10f)
                : field == 3 ? value + " %" : String.valueOf(value);
    }
    private void savePending() {
        if (!pending) return;
        UniversalGlassConfig.save(draft); pending = false; dirty = true;
        org.telegram.ui.Components.blur3.GlassOutlineStyle.dispatchChange();
    }
    private void onClick(UItem item, View view, int position, float x, float y) {
        if (item.id == ENABLE) {
            draft = draft.with(0, draft.enabled ? 0 : 1); pending = true;
            savePending(); FlexyGlassConfig.setEnabled(draft.enabled); list.adapter.update(true);
        } else if (item.id == STYLE) {
            showDialog(new AlertDialog.Builder(getParentActivity(), getResourceProvider())
                    .setTitle(text(R.string.FlexyCrystalBorderStyle)).setItems(styles(), (dialog, which) -> {
                        AppearanceConfig.glassOutlineStyle.setConfigInt(which);
                        dirty = true; list.adapter.update(true);
                    }).create());
        }
    }
    @Override public void onFragmentDestroy() {
        savePending();
        final var parent = getParentLayout();
        super.onFragmentDestroy();
        if (dirty && parent != null) org.telegram.messenger.AndroidUtilities.runOnUIThread(() -> parent.rebuildFragments(0));
        list = null; blurSlider = edgeSlider = widthSlider = null;
    }
}
