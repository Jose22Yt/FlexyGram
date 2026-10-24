package app.flexygram.composer;

import static org.telegram.messenger.LocaleController.getString;
import static org.telegram.messenger.AndroidUtilities.dp;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import org.telegram.messenger.LocaleController;
import androidx.core.graphics.ColorUtils;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.RecyclerListView;
import tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity;

public final class FlexyComposerSettingsActivity extends BaseNekoSettingsActivity {
    private static final int POSITION = 100, GAP = 101, PREVIEW = 102;
    private int styleRow, previewRow, positionRow, positionResetRow, levelRow, gapRow, iconsRow, glassRow, resetRow, infoRow;
    private Preview preview;
    @Override protected void updateRows() {
        super.updateRows();
        styleRow = addRow("flexyComposerStyle");
        previewRow = addRow();
        positionRow = addRow("flexyComposerPosition");
        positionResetRow = addRow();
        levelRow = addRow("flexyComposerLevel");
        gapRow = addRow("flexyComposerGap");
        iconsRow = addRow("flexyComposerIcons");
        glassRow = addRow("flexyComposerGlass");
        resetRow = addRow("flexyComposerReset");
        infoRow = addRow();
    }
    @Override protected String getActionBarTitle() { return getString(R.string.FlexyComposerSettings); }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    private void refresh() { listAdapter.notifyDataSetChanged(); if (preview != null) preview.invalidate(); }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (position == styleRow) {
            showDialog(new AlertDialog.Builder(getParentActivity(), getResourceProvider())
                .setTitle(getString(R.string.FlexyComposerStyle))
                .setItems(new CharSequence[]{getString(R.string.FlexyComposerClassic), getString(R.string.FlexyComposerCompact)}, (dialog, which) -> {
                    FlexyComposerConfig.setStyle(which); refresh();
                }).create());
        } else if (position == levelRow && FlexyComposerConfig.compact()) {
            showDialog(new AlertDialog.Builder(getParentActivity(), getResourceProvider())
                .setTitle(getString(R.string.FlexyComposerLevel))
                .setItems(levels(), (dialog, which) -> { FlexyComposerConfig.setLevel(which); refresh(); }).create());
        } else if (position == iconsRow && FlexyComposerConfig.compact()) {
            showDialog(new AlertDialog.Builder(getParentActivity(), getResourceProvider())
                .setTitle(getString(R.string.FlexyComposerIcons))
                .setItems(new CharSequence[]{getString(R.string.FlexyComposerReferenceIcons), getString(R.string.FlexyComposerSmileIcons)},
                    (dialog, which) -> { FlexyComposerConfig.setReferenceIcons(which == 0); refresh(); }).create());
        } else if (position == glassRow && FlexyComposerConfig.compact()) {
            FlexyComposerConfig.setGlass(!FlexyComposerConfig.glass()); refresh();
        } else if (position == positionResetRow && FlexyComposerConfig.compact()) {
            FlexyComposerConfig.setPosition(0); refresh();
        } else if (position == resetRow) {
            FlexyComposerConfig.reset(); refresh();
        }
    }
    private CharSequence[] levels() { return new CharSequence[]{getString(R.string.FlexyComposerDefault),
        getString(R.string.FlexyComposerSmall), getString(R.string.FlexyComposerExtraSmall)}; }
    private final class Slider extends LinearLayout {
        final TextView label, valueLabel;
        final ComposerSliderTrack track = new ComposerSliderTrack();
        final SeekBar bar;
        final boolean vertical;
        boolean binding;
        Slider(Context c, boolean vertical) {
            super(c); this.vertical = vertical; setOrientation(VERTICAL); setPadding(dp(20), dp(8), dp(20), dp(8));
            setBackgroundColor(getThemedColor(Theme.key_windowBackgroundWhite));
            LinearLayout heading = new LinearLayout(c);
            heading.setGravity(Gravity.CENTER_VERTICAL);
            label = new TextView(c); label.setTextSize(16); label.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
            valueLabel = new TextView(c); valueLabel.setTextSize(16); valueLabel.setGravity(Gravity.END);
            heading.addView(label, new LinearLayout.LayoutParams(0, dp(32), 1));
            heading.addView(valueLabel, new LinearLayout.LayoutParams(-2, dp(32)));
            addView(heading, new LinearLayout.LayoutParams(-1, dp(32)));
            bar = new SeekBar(c); bar.setMax(vertical ? ComposerStyle.MAX_POSITION - ComposerStyle.MIN_POSITION : ComposerStyle.MAX_GAP - ComposerStyle.MIN_GAP);
            bar.setProgressDrawable(track); bar.setSplitTrack(false);
            bar.setPadding(dp(2), 0, dp(2), 0);
            bar.setThumbOffset(dp(2));
            addView(bar, new LinearLayout.LayoutParams(-1, dp(48)));
            bar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                public void onStartTrackingTouch(SeekBar b) { b.getParent().requestDisallowInterceptTouchEvent(true); }
                public void onStopTrackingTouch(SeekBar b) { b.getParent().requestDisallowInterceptTouchEvent(false); }
                public void onProgressChanged(SeekBar b, int progress, boolean user) {
                    track.setFraction(progress, b.getMax());
                    if (binding || !user) return;
                    int value = progress + (vertical ? ComposerStyle.MIN_POSITION : ComposerStyle.MIN_GAP);
                    if (vertical) FlexyComposerConfig.setPosition(value); else FlexyComposerConfig.setGap(value);
                    updateLabel(value);
                    if (preview != null) preview.invalidate();
                }
            });
        }
        void updateLabel(int v) {
            String title = getString(vertical ? R.string.FlexyComposerPosition : R.string.FlexyComposerGap);
            label.setText(title);
            valueLabel.setText((vertical && v > 0 ? "+" : "") + v + " dp");
            bar.setContentDescription(title + ", " + valueLabel.getText());
        }
        void bind() {
            binding = true;
            int accent = getThemedColor(Theme.key_windowBackgroundWhiteBlueText);
            valueLabel.setTextColor(accent);
            track.configure(accent, ColorUtils.blendARGB(getThemedColor(Theme.key_windowBackgroundWhite),
                getThemedColor(Theme.key_windowBackgroundWhiteBlackText), 0.16f), LocaleController.isRTL);
            GradientDrawable thumb = new GradientDrawable(); thumb.setColor(accent);
            thumb.setCornerRadius(dp(2)); thumb.setSize(dp(4), dp(26));
            bar.setThumb(thumb);
            int v = vertical ? FlexyComposerConfig.position() : FlexyComposerConfig.gap();
            bar.setProgress(v - (vertical ? ComposerStyle.MIN_POSITION : ComposerStyle.MIN_GAP)); updateLabel(v);
            bar.setEnabled(FlexyComposerConfig.compact()); setAlpha(bar.isEnabled() ? 1 : 0.5f); binding = false;
        }
    }
    /** Lightweight settings preview, never substitutes the real native composer. */
    private final class Preview extends View {
        final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        final Drawable plus, clip, smile, folded, voice;
        Preview(Context c) {
            super(c); setContentDescription(getString(R.string.FlexyComposerPreview));
            clip = c.getResources().getDrawable(R.drawable.flexy_composer_clip).mutate();
            folded = c.getResources().getDrawable(R.drawable.flexy_composer_folded).mutate();
            plus = c.getResources().getDrawable(R.drawable.flexy_composer_add).mutate();
            smile = c.getResources().getDrawable(R.drawable.flexy_composer_smile).mutate();
            voice = c.getResources().getDrawable(R.drawable.flexy_composer_voice).mutate();
        }
        private void icon(Canvas canvas, Drawable icon, float x, float y, int color) {
            int half = dp(14);
            icon.setTint(color);
            icon.setBounds(Math.round(x)-half, Math.round(y)-half, Math.round(x)+half, Math.round(y)+half);
            icon.draw(canvas);
        }
        @Override protected void onMeasure(int w, int h) { setMeasuredDimension(MeasureSpec.getSize(w), dp(96)); }
        @Override protected void onDraw(Canvas c) {
            if (!FlexyComposerConfig.compact()) {
                c.drawColor(getThemedColor(Theme.key_windowBackgroundGray));
                paint.setTextSize(dp(16)); paint.setColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
                paint.setTextAlign(Paint.Align.CENTER);
                c.drawText(getString(R.string.FlexyComposerClassic),getWidth()/2f,dp(54),paint); return;
            }
            int level = FlexyComposerConfig.level(); float radius = dp(ComposerStyle.diameter(level)) / 2f;
            float y = dp(54 - ComposerStyle.offset(FlexyComposerConfig.position())), gap = dp(FlexyComposerConfig.gap());
            boolean dark = ColorUtils.calculateLuminance(getThemedColor(Theme.key_chat_messagePanelBackground)) < 0.4;
            int surface = ComposerStyle.surface(dark, FlexyComposerConfig.glass()), ink = ComposerStyle.icon(dark);
            c.drawColor(getThemedColor(Theme.key_windowBackgroundGray)); paint.setColor(surface);
            float side = ComposerStyle.sideMargin(getWidth(), org.telegram.messenger.AndroidUtilities.density, dp(7));
            float left = side + dp(22), right = getWidth() - side - dp(22);
            c.drawCircle(left,y,radius,paint); c.drawCircle(right,y,radius,paint);
            c.drawRoundRect(left+radius+gap,y-radius,right-radius-gap,y+radius,radius,radius,paint);
            icon(c, FlexyComposerConfig.referenceIcons() ? clip : plus, left, y, ink); icon(c, voice, right, y, ink);
            icon(c, FlexyComposerConfig.referenceIcons() ? folded : smile, right-radius-gap-dp(20), y, ComposerStyle.innerIcon(dark));
            paint.setColor(ComposerStyle.innerIcon(dark));
            paint.setTextAlign(Paint.Align.LEFT); paint.setTextSize(dp(18));
            c.drawText(getString(R.string.TypeMessage),left+radius+gap+dp(ComposerStyle.padding(level)),y-(paint.ascent()+paint.descent())/2,paint);
        }
    }
    private final class Adapter extends BaseListAdapter {
        Adapter(Context context) { super(context); }
        @Override public int getItemViewType(int p) {
            if (p == positionRow) return POSITION; if (p == gapRow) return GAP; if (p == previewRow) return PREVIEW;
            return p == glassRow ? TYPE_CHECK : p == infoRow ? TYPE_INFO_PRIVACY : TYPE_SETTINGS;
        }
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int type) {
            if (type == POSITION || type == GAP) return new RecyclerListView.Holder(new Slider(parent.getContext(), type == POSITION));
            if (type == PREVIEW) return new RecyclerListView.Holder(preview = new Preview(parent.getContext()));
            return super.onCreateViewHolder(parent,type);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h, int p, boolean partial) {
            if (p == positionRow || p == gapRow) { ((Slider)h.itemView).bind(); return; }
            if (p == previewRow) { h.itemView.invalidate(); return; }
            if (p == glassRow) {
                TextCheckCell cell = (TextCheckCell)h.itemView;
                cell.setTextAndCheck(getString(R.string.FlexyComposerGlass),FlexyComposerConfig.glass(),true);
                cell.setEnabled(FlexyComposerConfig.compact(),null);
            } else if (p == infoRow) {
                ((TextInfoPrivacyCell)h.itemView).setText(getString(R.string.FlexyComposerInfo));
            } else {
                TextSettingsCell cell = (TextSettingsCell)h.itemView;
                if (p == styleRow) cell.setTextAndValue(getString(R.string.FlexyComposerStyle), getString(FlexyComposerConfig.compact() ? R.string.FlexyComposerCompact : R.string.FlexyComposerClassic), true);
                else if (p == iconsRow) cell.setTextAndValue(getString(R.string.FlexyComposerIcons), getString(FlexyComposerConfig.referenceIcons() ? R.string.FlexyComposerReferenceIcons : R.string.FlexyComposerSmileIcons), true);
                else if (p == levelRow) cell.setTextAndValue(getString(R.string.FlexyComposerLevel), levels()[FlexyComposerConfig.level()].toString(), true);
                else cell.setText(getString(p == resetRow ? R.string.FlexyComposerReset : R.string.FlexyComposerPositionReset), true);
                cell.setEnabled(p == styleRow || p == resetRow || FlexyComposerConfig.compact(), null);
            }
        }
    }
}
