package app.flexygram.bubbles;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.SeekBar;
import android.graphics.drawable.GradientDrawable;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Components.RecyclerListView;
import app.flexygram.settings.SignatureMatteSettingsActivity;

/** Four controls only; all values belong to this installation, never to a Telegram account. */
public final class BubbleSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int SLIDER = 110;
    private int glassRow, transparencyRow, borderRow, edgesRow, infoRow;
    @Override protected void updateRows() {
        super.updateRows(); BubbleConfig.load();
        glassRow = addRow("flexyBubbleGlass"); transparencyRow = addRow("flexyBubbleTransparency");
        borderRow = addRow("flexyBubbleBorder"); edgesRow = addRow("flexyBubbleEdges"); infoRow = addRow();
    }
    @Override protected String getActionBarTitle() { return getString(R.string.FlexyBubblesTitle); }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (position == glassRow) BubbleConfig.setGlass(!BubbleConfig.glass());
        else if (position == borderRow) BubbleConfig.setBorder(!BubbleConfig.border());
        else if (position == edgesRow) BubbleConfig.setEdges(!BubbleConfig.edges());
        else return;
        listAdapter.notifyItemChanged(position);
        if (position == glassRow) listAdapter.notifyItemChanged(transparencyRow);
    }
    private final class TransparencyCell extends LinearLayout {
        final TextView title;
        final SeekBar seek;
        boolean binding;
        TransparencyCell(Context context) {
            super(context); setOrientation(VERTICAL); setPadding(dp(20), dp(12), dp(20), dp(4));
            title = new TextView(context); title.setTextSize(16);
            title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
            addView(title, new LinearLayout.LayoutParams(-1, -2));
            seek = new SeekBar(context); seek.setMax(100);
            int accent = getThemedColor(Theme.key_windowBackgroundWhiteBlueText);
            seek.setProgressTintList(android.content.res.ColorStateList.valueOf(accent));
            GradientDrawable thumb = new GradientDrawable(); thumb.setShape(GradientDrawable.OVAL);
            thumb.setSize(dp(22), dp(22)); thumb.setColor(accent); seek.setThumb(thumb);
            addView(seek, new LinearLayout.LayoutParams(-1, dp(48)));
            seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                public void onStartTrackingTouch(SeekBar bar) { bar.getParent().requestDisallowInterceptTouchEvent(true); }
                public void onStopTrackingTouch(SeekBar bar) { bar.getParent().requestDisallowInterceptTouchEvent(false); }
                public void onProgressChanged(SeekBar bar, int value, boolean user) {
                    if (user && !binding) BubbleConfig.setTransparency(value);
                    label(value);
                }
            });
        }
        void label(int value) {
            String text = getString(R.string.FlexyBubblesTransparency) + " · " + value + " %";
            title.setText(text); seek.setContentDescription(text);
        }
        void bind() {
            binding = true; seek.setProgress(BubbleConfig.transparency()); label(BubbleConfig.transparency());
            seek.setEnabled(BubbleConfig.glass()); setAlpha(BubbleConfig.glass() ? 1f : .5f); binding = false;
        }
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context) { super(context); }
        @Override public int getItemViewType(int position) {
            return position == transparencyRow ? SLIDER : position == infoRow ? TYPE_INFO_PRIVACY : TYPE_CHECK;
        }
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int type) {
            if (type == SLIDER) return new RecyclerListView.Holder(new TransparencyCell(parent.getContext()));
            return super.onCreateViewHolder(parent, type);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            if (position == transparencyRow) { ((TransparencyCell)holder.itemView).bind(); return; }
            if (position == infoRow) { ((TextInfoPrivacyCell)holder.itemView).setText(getString(R.string.FlexyBubblesInfo)); return; }
            TextCheckCell cell = (TextCheckCell)holder.itemView;
            if (position == glassRow) cell.setTextAndCheck(getString(R.string.FlexyBubblesGlass), BubbleConfig.glass(), true);
            else if (position == borderRow) cell.setTextAndCheck(getString(R.string.FlexyBubblesBorder), BubbleConfig.border(), true);
            else cell.setTextAndCheck(getString(R.string.FlexyBubblesEdges), BubbleConfig.edges(), false);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) { return holder.getItemViewType() == TYPE_CHECK; }
    }
}
