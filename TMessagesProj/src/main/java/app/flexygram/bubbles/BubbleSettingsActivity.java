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

/** One fill-opacity control; all values belong to this installation, never to a Telegram account. */
public final class BubbleSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int SLIDER = 110;
    private int transparencyRow, infoRow;
    @Override protected void updateRows() {
        super.updateRows(); BubbleConfig.load();
        transparencyRow = addRow("flexyBubbleTransparency"); infoRow = addRow();
    }
    @Override protected String getActionBarTitle() { return getString(R.string.FlexyBubblesTitle); }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    @Override protected void onItemClick(View view, int position, float x, float y) { }
    private final class TransparencyCell extends LinearLayout {
        final TextView title;
        final SeekBar seek;
        boolean binding;
        TransparencyCell(Context context) {
            super(context); setOrientation(VERTICAL); setPadding(dp(20), dp(12), dp(20), dp(4));
            title = new TextView(context); title.setTextSize(16);
            title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
            addView(title, new LinearLayout.LayoutParams(-1, -2));
            seek = new app.flexygram.settings.FlexySignatureSlider(context); seek.setMax(100);
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
            seek.setEnabled(true); setAlpha(1f); binding = false;
        }
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context) { super(context); }
        @Override public int getItemViewType(int position) {
            return position == transparencyRow ? SLIDER : TYPE_INFO_PRIVACY;
        }
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int type) {
            if (type == SLIDER) return new RecyclerListView.Holder(new TransparencyCell(parent.getContext()));
            return super.onCreateViewHolder(parent, type);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            if (position == transparencyRow) { ((TransparencyCell)holder.itemView).bind(); return; }
            if (position == infoRow) { ((TextInfoPrivacyCell)holder.itemView).setText(getString(R.string.FlexyBubblesInfo)); return; }

        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) { return false; }
    }
}
