package app.exteraless.settings;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.CheckBox;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TextView;
import androidx.core.graphics.ColorUtils;
import app.exteraless.appearance.FlexyGlassConfig;
import app.exteraless.appearance.UniversalGlassConfig;
import app.flexygram.effects.GlassPreviewView;
import app.flexygram.effects.GlassSettings;
import app.flexygram.settings.FlexySignatureSlider;
import java.util.ArrayList;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.ActionBar.ThemeDescription;
import org.telegram.ui.Components.ColorPicker;
import org.telegram.ui.Components.LayoutHelper;

/** Draft-only live preview above scrolling controls. Persistence and screen refresh happen once on Apply. */
public final class UniversalGlassSettingsActivity extends BaseFragment {
    private GlassSettings draft, original;
    private GlassPreviewView preview;
    private LinearLayout page, controls;
    private Segment scenes, modes, presets;
    private GradientDrawable colorSwatch;
    private int scene, previewMode = 2;
    private boolean applied;
    private static final int TEXT = 1, MUTED = 2, ACCENT = 3, PRIMARY = 4, CARD = 5;

    private static String text(int id) { return LocaleController.getString(id); }
    private static int dp(float value) { return AndroidUtilities.dp(value); }
    private int accent() { return getThemedColor(Theme.key_telegram_color); }
    private int foreground() { return getThemedColor(Theme.key_windowBackgroundWhiteBlackText); }
    private int primaryInk() { return ColorUtils.calculateContrast(Color.WHITE, accent() | 0xff000000)
            >= ColorUtils.calculateContrast(Color.BLACK, accent() | 0xff000000) ? Color.WHITE : Color.BLACK; }

    @Override public View createView(Context context) {
        if (draft == null) original = draft = UniversalGlassConfig.snapshot().with(0, FlexyGlassConfig.enabled() ? 1 : 0);
        actionBar.setTitle(text(R.string.FlexyCrystalTitle));
        actionBar.setBackButtonImage(R.drawable.ic_ab_back);
        actionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick() {
            @Override public void onItemClick(int id) {
                if (id == -1 && onBackPressed(true)) finishFragment();
                else if (id == 1) { draft = GlassSettings.defaults(); rebuildControls(); }
            }
        });
        actionBar.createMenu().addItem(1, R.drawable.msg_reset).setContentDescription(text(R.string.FlexyCrystalReset));
        FrameLayout root = new FrameLayout(context);
        page = new LinearLayout(context);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(12), dp(4), dp(12), dp(8));
        page.setLayoutDirection(LocaleController.isRTL ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        root.addView(page, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.MATCH_PARENT));
        scenes = new Segment(context, new int[]{R.string.FlexyCrystalChat, R.string.FlexyCrystalHome, R.string.FlexyCrystalProfile}, scene,
                index -> { scene = index; refreshPreview(); });
        page.addView(scenes, linear(44));
        preview = new GlassPreviewView(context) {
            @Override protected void onMeasure(int widthSpec, int heightSpec) {
                int available = root.getMeasuredHeight();
                int height = Math.min(dp(200), Math.max(dp(96), available > 0 ? available * 28 / 100 : dp(180)));
                super.onMeasure(widthSpec, MeasureSpec.makeMeasureSpec(height, MeasureSpec.EXACTLY));
            }
        };
        page.addView(preview, linear(180));
        modes = new Segment(context, new int[]{R.string.FlexyCrystalLight, R.string.FlexyCrystalDark, R.string.FlexyCrystalTheme}, previewMode,
                index -> { previewMode = index; refreshPreview(); });
        page.addView(modes, linear(44));
        ScrollView scroll = new ScrollView(context);
        scroll.setFillViewport(false); scroll.setClipToPadding(false);
        controls = new LinearLayout(context); controls.setOrientation(LinearLayout.VERTICAL);
        controls.setPadding(0, 0, 0, dp(8)); scroll.addView(controls);
        page.addView(scroll, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        TextView apply = label(text(R.string.FlexyCrystalApply), 15, PRIMARY);
        apply.setGravity(Gravity.CENTER); apply.setTypeface(AndroidUtilities.bold());
        apply.setOnClickListener(v -> apply());
        page.addView(apply, linear(48));
        if (context.getResources().getConfiguration().screenHeightDp < 520
                || context.getResources().getConfiguration().fontScale > 1.5f) {
            // Short/large-font windows scroll the preview too, so every control stays reachable.
            page.removeView(scroll); scroll.removeView(controls);
            page.removeView(apply); page.addView(controls, new LinearLayout.LayoutParams(-1, -2));
            root.removeView(page);
            ScrollView wholePage = new ScrollView(context); wholePage.addView(page, new ScrollView.LayoutParams(-1, -2));
            FrameLayout.LayoutParams body = new FrameLayout.LayoutParams(-1, -1);
            int applyHeight = linear(48).height;
            body.bottomMargin = applyHeight + dp(16); root.addView(wholePage, body);
            FrameLayout.LayoutParams button = new FrameLayout.LayoutParams(-1, applyHeight, Gravity.BOTTOM);
            button.leftMargin = button.rightMargin = dp(12); button.bottomMargin = dp(8);
            root.addView(apply, button);
        }
        fragmentView = root;
        rebuildControls();
        return root;
    }
    private LinearLayout.LayoutParams linear(int height) {
        float scale = getContext().getResources().getConfiguration().fontScale;
        int adjusted = height == 44 || height == 48 ? Math.round(height * Math.max(1f, Math.min(2f, scale))) : height;
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(adjusted));
    }
    private TextView label(String value, int size, int role) {
        TextView text = new TextView(getContext()); text.setText(value); text.setTextSize(size); text.setTag(role);
        text.setGravity(Gravity.CENTER_VERTICAL); text.setPadding(dp(8), 0, dp(8), 0);
        return text;
    }
    private void heading(int title) {
        TextView view = label(text(title), 12, ACCENT); view.setTypeface(AndroidUtilities.bold());
        controls.addView(view, linear(32));
    }
    private LinearLayout card() {
        LinearLayout card = new LinearLayout(getContext()); card.setOrientation(LinearLayout.VERTICAL);
        card.setTag(CARD); card.setPadding(dp(4), dp(4), dp(4), dp(4));
        controls.addView(card, new LinearLayout.LayoutParams(-1, -2)); return card;
    }
    private void rebuildControls() {
        if (controls == null) return;
        controls.removeAllViews();
        heading(R.string.FlexyCrystalSurface);
        LinearLayout surface = card();
        CheckBox enabled = new CheckBox(getContext()); enabled.setTag(TEXT);
        enabled.setText(text(R.string.FlexyCrystalEnabled)); enabled.setTextSize(14);
        enabled.setChecked(draft.enabled); enabled.setPadding(dp(8), 0, dp(8), 0);
        enabled.setOnCheckedChangeListener((button, value) -> { draft = draft.with(0, value ? 1 : 0); refreshPreview(); });
        surface.addView(enabled, linear(48));
        slider(surface, R.string.FlexyCrystalTransparency, 1, 0, 80, 100 - draft.opacity);
        slider(surface, R.string.FlexyCrystalBlur, 2, 0, 48, draft.blur);
        presets = new Segment(getContext(), new int[]{R.string.FlexyCrystalSubtle, R.string.FlexyCrystalBalanced, R.string.FlexyCrystalIntense}, presetIndex(),
                index -> { draft = draft.preset(index); rebuildControls(); });
        presets.setContentDescription(text(R.string.FlexyCrystalPreset)); surface.addView(presets, linear(48));
        heading(R.string.FlexyCrystalBorder);
        LinearLayout border = card();
        border.addView(new Segment(getContext(), new int[]{R.string.FlexyCrystalSubtle, R.string.FlexyCrystalCrystal, R.string.FlexyCrystalGlow}, draft.style,
                index -> { draft = draft.with(5, index); refreshPreview(); }), linear(48));
        slider(border, R.string.FlexyCrystalWidth, 4, 0, 30, draft.width);
        slider(border, R.string.FlexyCrystalIntensity, 3, 0, 100, draft.edge);
        TextView color = label(text(R.string.FlexyCrystalColor) + " · " + (draft.color == 0 ? text(R.string.FlexyCrystalAccent) : String.format("#%06X", draft.color & 0xffffff)) + "  ›", 14, TEXT);
        colorSwatch = new GradientDrawable(); colorSwatch.setSize(dp(18), dp(18)); colorSwatch.setCornerRadius(dp(5));
        color.setCompoundDrawablePadding(dp(8)); color.setCompoundDrawablesRelativeWithIntrinsicBounds(null, null, colorSwatch, null);
        color.setOnClickListener(v -> chooseColor()); border.addView(color, linear(48));
        heading(R.string.FlexyCrystalZonesTitle);
        LinearLayout zones = card();
        TextView areas = label(text(R.string.FlexyCrystalZones) + "  ·  " + Integer.bitCount(draft.zones) + "/7  ›", 14, TEXT);
        areas.setOnClickListener(v -> chooseZones()); zones.addView(areas, linear(48));
        TextView safety = label(text(R.string.FlexyCrystalSafety), 12, MUTED);
        safety.setPadding(dp(8), dp(8), dp(8), dp(8)); controls.addView(safety, new LinearLayout.LayoutParams(-1, -2));
        updateColors(); refreshPreview();
    }
    private int presetIndex() { return draft.presetIndex(); }
    private void slider(LinearLayout parent, int title, int field, int min, int max, int value) {
        LinearLayout row = new LinearLayout(getContext()); row.setGravity(Gravity.CENTER_VERTICAL);
        TextView name = label(text(title), 13, TEXT);
        row.addView(name, new LinearLayout.LayoutParams(dp(112), -1));
        FlexySignatureSlider slider = new FlexySignatureSlider(getContext()); slider.setMax(max - min); slider.setProgress(value - min);
        slider.setContentDescription(text(title)); row.addView(slider, new LinearLayout.LayoutParams(0, dp(48), 1));
        TextView amount = label(format(field, value), 13, TEXT); amount.setGravity(Gravity.CENTER);
        row.addView(amount, new LinearLayout.LayoutParams(dp(54), -1));
        slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onProgressChanged(SeekBar view, int progress, boolean fromUser) {
                if (!fromUser) return;
                int selected = progress + min;
                draft = draft.with(field, field == 1 ? 100 - selected : selected);
                amount.setText(format(field, selected)); refreshPreview();
            }
            public void onStartTrackingTouch(SeekBar view) { }
            public void onStopTrackingTouch(SeekBar view) { }
        });
        parent.addView(row, linear(48));
    }
    private String format(int field, int value) {
        return field == 4 ? String.format(java.util.Locale.getDefault(), "%.1f", value / 10f) : value + (field == 1 || field == 3 ? " %" : "");
    }
    private void chooseColor() {
        showDialog(new AlertDialog.Builder(getParentActivity(), getResourceProvider()).setTitle(text(R.string.FlexyCrystalColor))
                .setItems(new CharSequence[]{text(R.string.FlexyCrystalAccent), text(R.string.FlexyCrystalWhite), text(R.string.FlexyCrystalBlack), text(R.string.FlexyCrystalCustomColor)}, (dialog, which) -> {
                    if (which == 3) { customColor(); return; }
                    draft = draft.with(6, which == 0 ? 0 : which == 1 ? Color.WHITE : Color.BLACK); rebuildControls();
                }).create());
    }
    private void customColor() {
        final int[] color = {draft.color == 0 ? accent() : draft.color};
        ColorPicker picker = new ColorPicker(getContext(), false, (value, num, applyNow) -> color[0] = value | 0xff000000);
        picker.setResourcesProvider(getResourceProvider()); picker.setColor(color[0], 0);
        showDialog(new AlertDialog.Builder(getParentActivity(), getResourceProvider()).setTitle(text(R.string.FlexyCrystalCustomColor))
                .setView(picker, dp(320)).setPositiveButton(text(R.string.OK), (dialog, which) -> {
                    draft = draft.with(6, color[0]); rebuildControls();
                }).setNegativeButton(text(R.string.Cancel), null).create());
    }
    private void chooseZones() {
        final int[] mask = {draft.zones};
        int[] titles = {R.string.FlexyCrystalZoneInput, R.string.FlexyCrystalZoneHeader, R.string.FlexyCrystalZoneNavigation,
                R.string.FlexyCrystalZoneSearch, R.string.FlexyCrystalZoneMenus, R.string.FlexyCrystalZoneFolders, R.string.FlexyCrystalZoneProfile};
        LinearLayout rows = new LinearLayout(getContext()); rows.setOrientation(LinearLayout.VERTICAL);
        for (int i = 0; i < titles.length; i++) {
            final int bit = 1 << i;
            CheckBox check = new CheckBox(getContext()); check.setText(text(titles[i])); check.setTextSize(14);
            check.setTextColor(foreground()); check.setButtonTintList(ColorStateList.valueOf(accent())); check.setChecked((mask[0] & bit) != 0);
            check.setOnCheckedChangeListener((button, selected) -> mask[0] = selected ? mask[0] | bit : mask[0] & ~bit);
            rows.addView(check, linear(48));
        }
        ScrollView scroll = new ScrollView(getContext()); scroll.addView(rows);
        showDialog(new AlertDialog.Builder(getParentActivity(), getResourceProvider()).setTitle(text(R.string.FlexyCrystalZones))
                .setView(scroll, Math.min(dp(336), getParentActivity().getResources().getDisplayMetrics().heightPixels / 2))
                .setPositiveButton(text(R.string.OK), (dialog, which) -> { draft = draft.with(7, mask[0]); rebuildControls(); })
                .setNegativeButton(text(R.string.Cancel), null).create());
    }
    private void refreshPreview() {
        if (presets != null) presets.select(presetIndex());
        if (preview != null) preview.update(draft, scene, previewMode == 1 || previewMode == 2 && Theme.isCurrentThemeDark(), accent());
    }
    private void apply() {
        UniversalGlassConfig.save(draft);
        FlexyGlassConfig.setEnabled(draft.enabled);
        org.telegram.ui.Components.blur3.GlassOutlineStyle.dispatchChange();
        applied = true; finishFragment();
    }
    private boolean dirty() {
        return draft != null && (draft.enabled != original.enabled || draft.opacity != original.opacity || draft.blur != original.blur
                || draft.edge != original.edge || draft.width != original.width || draft.style != original.style
                || draft.color != original.color || draft.zones != original.zones);
    }
    @Override public boolean onBackPressed(boolean invoked) {
        if (!dirty() || applied) return super.onBackPressed(invoked);
        if (invoked) showDialog(new AlertDialog.Builder(getParentActivity(), getResourceProvider())
                .setTitle(text(R.string.FlexyCrystalSave)).setMessage(text(R.string.FlexyCrystalSaveInfo))
                .setPositiveButton(text(R.string.FlexyCrystalApply), (dialog, which) -> apply())
                .setNegativeButton(text(R.string.FlexyCrystalDiscard), (dialog, which) -> { original = draft; finishFragment(); })
                .setNeutralButton(text(R.string.Cancel), null).create());
        return false;
    }
    @Override public void onFragmentDestroy() {
        final var parent = getParentLayout();
        super.onFragmentDestroy();
        if (applied && parent != null) AndroidUtilities.runOnUIThread(() -> parent.rebuildFragments(0));
        preview = null; controls = null; page = null; presets = scenes = modes = null; colorSwatch = null;
    }
    @Override public void onResume() { super.onResume(); updateColors(); refreshPreview(); }
    private void updateColors() {
        if (fragmentView != null) fragmentView.setBackgroundColor(getThemedColor(Theme.key_windowBackgroundGray));
        if (colorSwatch != null) colorSwatch.setColor(draft.color == 0 ? accent() : draft.color);
        colorTree(fragmentView);
    }
    private void colorTree(View view) {
        if (view == null) return;
        Object role = view.getTag();
        if (role instanceof Integer) {
            int value = (Integer)role;
            if (view instanceof TextView) ((TextView)view).setTextColor(value == PRIMARY ? primaryInk() : value == ACCENT ? accent()
                    : value == MUTED ? getThemedColor(Theme.key_windowBackgroundWhiteGrayText2) : foreground());
            if (value == CARD) view.setBackground(round(getThemedColor(Theme.key_windowBackgroundWhite)));
            if (value == PRIMARY) view.setBackground(Theme.createSimpleSelectorRoundRectDrawable(dp(18), accent(),
                    ColorUtils.blendARGB(accent(), primaryInk(), .12f)));
        }
        if (view instanceof CheckBox) ((CheckBox)view).setButtonTintList(ColorStateList.valueOf(accent()));
        if (view instanceof FlexySignatureSlider) ((FlexySignatureSlider)view).updateColors();
        if (view instanceof Segment) ((Segment)view).recolor();
        if (view instanceof ViewGroup) for (int i = 0; i < ((ViewGroup)view).getChildCount(); i++) colorTree(((ViewGroup)view).getChildAt(i));
    }
    private GradientDrawable round(int color) { GradientDrawable d = new GradientDrawable(); d.setColor(color); d.setCornerRadius(dp(18)); return d; }
    @Override public ArrayList<ThemeDescription> getThemeDescriptions() {
        ArrayList<ThemeDescription> descriptions = new ArrayList<>();
        for (int key : new int[]{Theme.key_windowBackgroundGray, Theme.key_windowBackgroundWhite,
                Theme.key_windowBackgroundWhiteBlackText, Theme.key_windowBackgroundWhiteGrayText2, Theme.key_telegram_color}) {
            descriptions.add(new ThemeDescription(null, 0, null, (android.graphics.Paint)null, null,
                    () -> { updateColors(); refreshPreview(); }, key));
        }
        return descriptions;
    }
    private interface Selection { void choose(int index); }
    private final class Segment extends LinearLayout {
        private int selected;
        Segment(Context context, int[] titles, int selected, Selection callback) {
            super(context); this.selected = selected; setGravity(Gravity.CENTER_VERTICAL); setPadding(dp(2), dp(3), dp(2), dp(3));
            for (int i = 0; i < titles.length; i++) {
                final int index = i;
                TextView button = label(text(titles[i]), 13, 0); button.setGravity(Gravity.CENTER);
                button.setOnClickListener(v -> { this.selected = index; recolor(); callback.choose(index); });
                addView(button, new LinearLayout.LayoutParams(0, -1, 1));
            }
        }
        void select(int index) { if (selected != index) { selected = index; recolor(); } }
        void recolor() {
            setBackground(round(getThemedColor(Theme.key_windowBackgroundWhite)));
            for (int i = 0; i < getChildCount(); i++) {
                TextView button = (TextView)getChildAt(i);
                int fill = i == selected ? ColorUtils.blendARGB(getThemedColor(Theme.key_windowBackgroundWhite), accent(), .24f) : Color.TRANSPARENT;
                button.setBackground(Theme.createSimpleSelectorRoundRectDrawable(dp(18), fill,
                        ColorUtils.blendARGB(getThemedColor(Theme.key_windowBackgroundWhite), accent(), .16f)));
                button.setTextColor(foreground()); button.setSelected(i == selected);
            }
        }
    }
}
