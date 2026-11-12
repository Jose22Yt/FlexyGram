/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.SeekBar;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Components.RecyclerListView;

/** The sole 3D effect, independently enabled in each list, with shared continuous curvature. */
public final class ScrollEffectsSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int CURVATURE = 110;
    private int headerRow, chatsRow, conversationRow, curvatureRow, infoRow;
    @Override protected String getActionBarTitle() { return text(R.string.FlexyScrollEffects); }
    @Override protected void updateRows() {
        super.updateRows(); ScrollEffectsConfig.load();
        headerRow = addRow("flexyScrollEffects");
        chatsRow = addRow("flexyScrollChats"); conversationRow = addRow("flexyScrollConversation");
        curvatureRow = addRow("flexyScrollCurvature"); infoRow = addRow();
    }
    private String text(int id) { return LocaleController.getString(id); }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (position != chatsRow && position != conversationRow) return;
        int surface = position == chatsRow ? ScrollEffectsConfig.CHATS : ScrollEffectsConfig.CONVERSATION;
        ScrollEffectsConfig.setStyle(surface, ScrollEffectsConfig.style(surface) == ScrollEffectsConfig.NONE
                ? ScrollEffectsConfig.WHEEL : ScrollEffectsConfig.NONE);
        listAdapter.notifyItemChanged(position);
    }
    private final class CurvatureCell extends LinearLayout implements Theme.Colorable {
        private final TextView title;
        private final app.flexygram.settings.FlexySignatureSlider seek;
        private boolean tracking;
        CurvatureCell(Context context) {
            super(context); setOrientation(VERTICAL);
            setPadding(AndroidUtilities.dp(16), AndroidUtilities.dp(8), AndroidUtilities.dp(16), AndroidUtilities.dp(4));
            title = new TextView(context); title.setTextSize(15);
            addView(title, new LayoutParams(-1, -2));
            seek = new app.flexygram.settings.FlexySignatureSlider(context);
            seek.setMax(100); seek.setKeyProgressIncrement(1);
            addView(seek, new LayoutParams(-1, AndroidUtilities.dp(48)));
            seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                public void onStartTrackingTouch(SeekBar bar) { tracking = true; bar.getParent().requestDisallowInterceptTouchEvent(true); }
                public void onStopTrackingTouch(SeekBar bar) {
                    tracking = false; ScrollEffectsConfig.setCurvature(bar.getProgress());
                    bar.getParent().requestDisallowInterceptTouchEvent(false);
                }
                public void onProgressChanged(SeekBar bar, int value, boolean user) {
                    if (user) {
                        if (tracking) ScrollEffectsConfig.previewCurvature(value);
                        else ScrollEffectsConfig.setCurvature(value); // Keyboard/accessibility also persist.
                    }
                    label(value);
                }
            });
        }
        private void label(int value) {
            String label = text(R.string.FlexyScrollCurvature) + " · " + value + " %";
            title.setText(label); seek.setContentDescription(label);
        }
        void bind() { seek.setProgress(ScrollEffectsConfig.curvature()); label(seek.getProgress()); updateColors(); }
        @Override public void updateColors() { title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText)); seek.updateColors(); }
        @Override protected void onDetachedFromWindow() {
            if (tracking) { tracking = false; ScrollEffectsConfig.setCurvature(seek.getProgress()); }
            super.onDetachedFromWindow();
        }
    }
    @Override protected BaseListAdapter createAdapter(Context context) {
        return new MatteListAdapter(context) {
            @Override public int getItemViewType(int p) {
                return p == headerRow ? TYPE_HEADER : p == curvatureRow ? CURVATURE : p == infoRow ? TYPE_INFO_PRIVACY : TYPE_CHECK;
            }
            @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int type) {
                if (type != CURVATURE) return super.onCreateViewHolder(parent, type);
                CurvatureCell cell = new CurvatureCell(parent.getContext());
                cell.setLayoutParams(new RecyclerView.LayoutParams(-1, -2)); return new RecyclerListView.Holder(cell);
            }
            @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int p, boolean partial) {
                if (p == headerRow) ((tw.nekomimi.nekogram.ui.cells.HeaderCell) holder.itemView).setText(getActionBarTitle());
                else if (p == curvatureRow) ((CurvatureCell) holder.itemView).bind();
                else if (p == infoRow) ((TextInfoPrivacyCell) holder.itemView).setText(text(R.string.FlexyScrollInfo));
                else ((TextCheckCell) holder.itemView).setTextAndCheck(text(p == chatsRow ? R.string.FlexyScrollChats
                        : R.string.FlexyScrollConversation), ScrollEffectsConfig.style(p == chatsRow
                        ? ScrollEffectsConfig.CHATS : ScrollEffectsConfig.CONVERSATION) == ScrollEffectsConfig.WHEEL, p == chatsRow);
            }
            @Override public boolean isEnabled(RecyclerView.ViewHolder holder) {
                int p = settingsRowPosition(holder); return p == chatsRow || p == conversationRow;
            }
        };
    }
}
