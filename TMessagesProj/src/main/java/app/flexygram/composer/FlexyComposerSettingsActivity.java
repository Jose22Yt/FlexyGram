package app.flexygram.composer;

import static org.telegram.messenger.LocaleController.getString;
import static org.telegram.messenger.AndroidUtilities.dp;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Canvas;
import android.graphics.Paint;
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
    private int styleRow, previewRow, positionRow, positionResetRow, levelRow, gapRow, glassRow, resetRow, infoRow;
    private Preview preview;
    @Override protected void updateRows() {
        super.updateRows();
        styleRow = addRow("flexyComposerStyle");
        previewRow = addRow();
        positionRow = addRow("flexyComposerPosition");
        positionResetRow = addRow();
        levelRow = addRow("flexyComposerLevel");
        gapRow = addRow("flexyComposerGap");
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
        final TextView label;
        final SeekBar bar;
        final boolean vertical;
        boolean binding;
        Slider(Context c, boolean vertical) {
            super(c); this.vertical = vertical; setOrientation(VERTICAL); setPadding(dp(20), dp(8), dp(20), dp(8));
            setBackgroundColor(getThemedColor(Theme.key_windowBackgroundWhite));
            label = new TextView(c); label.setTextSize(16); label.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
            addView(label, new LinearLayout.LayoutParams(-1, dp(30)));
            bar = new SeekBar(c); bar.setMax(vertical ? ComposerStyle.MAX_POSITION - ComposerStyle.MIN_POSITION : ComposerStyle.MAX_GAP - ComposerStyle.MIN_GAP);
            bar.setProgressTintList(ColorStateList.valueOf(getThemedColor(Theme.key_windowBackgroundWhiteBlueText)));
            bar.setThumbTintList(ColorStateList.valueOf(getThemedColor(Theme.key_windowBackgroundWhiteBlueText)));
            addView(bar, new LinearLayout.LayoutParams(-1, dp(48)));
            bar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                public void onStartTrackingTouch(SeekBar b) { b.getParent().requestDisallowInterceptTouchEvent(true); }
                public void onStopTrackingTouch(SeekBar b) { b.getParent().requestDisallowInterceptTouchEvent(false); }
                public void onProgressChanged(SeekBar b, int progress, boolean user) {
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
            label.setText(title + " · " + (vertical && v > 0 ? "+" : "") + v + " dp");
            bar.setContentDescription(label.getText());
        }
        void bind() {
            binding = true;
            int v = vertical ? FlexyComposerConfig.position() : FlexyComposerConfig.gap();
            bar.setProgress(v - (vertical ? ComposerStyle.MIN_POSITION : ComposerStyle.MIN_GAP)); updateLabel(v);
            bar.setEnabled(FlexyComposerConfig.compact()); setAlpha(bar.isEnabled() ? 1 : 0.5f); binding = false;
        }
    }
    /** Lightweight settings preview, never substitutes the real native composer. */
    private final class Preview extends View {
        final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        Preview(Context c) { super(c); setContentDescription(getString(R.string.FlexyComposerPreview)); }
        @Override protected void onMeasure(int w, int h) { setMeasuredDimension(MeasureSpec.getSize(w), dp(96)); }
        @Override protected void onDraw(Canvas c) {
            if (!FlexyComposerConfig.compact()) {
                c.drawColor(getThemedColor(Theme.key_windowBackgroundGray));
                paint.setTextSize(dp(16)); paint.setColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
                paint.setTextAlign(Paint.Align.CENTER);
                c.drawText(getString(R.string.FlexyComposerClassic),getWidth()/2f,dp(54),paint); return;
            }
            int level = FlexyComposerConfig.level(); float radius = dp(ComposerStyle.diameter(level)) / 2f;
            float y = dp(54 - FlexyComposerConfig.position()), gap = dp(FlexyComposerConfig.gap());
            int surface = getThemedColor(Theme.key_chat_messagePanelBackground), ink = getThemedColor(Theme.key_windowBackgroundWhiteBlackText);
            c.drawColor(getThemedColor(Theme.key_windowBackgroundGray)); paint.setColor(surface);
            float left = dp(30), right = getWidth() - dp(30);
            c.drawCircle(left,y,radius,paint); c.drawCircle(right,y,radius,paint);
            c.drawRoundRect(left+radius+gap,y-radius,right-radius-gap,y+radius,radius,radius,paint);
            paint.setColor(ink); paint.setTextAlign(Paint.Align.CENTER); paint.setTextSize(dp(23));
            float baseline = y - (paint.ascent()+paint.descent())/2;
            c.drawText("+",left,baseline,paint); c.drawText("↑",right,baseline,paint);
            c.drawText("☺",right-radius-gap-dp(20),baseline,paint);
            paint.setTextAlign(Paint.Align.LEFT); paint.setTextSize(dp(16));
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
                else if (p == levelRow) cell.setTextAndValue(getString(R.string.FlexyComposerLevel), levels()[FlexyComposerConfig.level()].toString(), true);
                else cell.setText(getString(p == resetRow ? R.string.FlexyComposerReset : R.string.FlexyComposerPositionReset), true);
                cell.setEnabled(p == styleRow || p == resetRow || FlexyComposerConfig.compact(), null);
            }
        }
    }
}
