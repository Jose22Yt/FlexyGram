/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Components.AlertsCreator;

/** Native controls embedded directly in Settings > Home. One intensity for both surfaces. */
public final class ScrollEffectsSettingsActivity extends SignatureMatteSettingsActivity {
    private int headerRow, chatsRow, conversationRow, intensityRow, infoRow;
    @Override protected String getActionBarTitle() { return text(R.string.FlexyScrollEffects); }
    @Override protected void updateRows() {
        super.updateRows(); ScrollEffectsConfig.load();
        headerRow = addRow("flexyScrollEffects");
        chatsRow = addRow("flexyScrollChats");
        conversationRow = addRow("flexyScrollConversation");
        intensityRow = addRow("flexyScrollIntensity");
        infoRow = addRow();
    }
    private String text(int id) { return LocaleController.getString(id); }
    private String[] styles() { return new String[]{text(R.string.FlexyScrollNone), text(R.string.FlexyScrollWheel),
            text(R.string.FlexyScrollPerspective), text(R.string.FlexyScrollLateral)}; }
    private String[] intensities() { return new String[]{text(R.string.FlexyScrollSoft),
            text(R.string.FlexyScrollMarked), text(R.string.FlexyScrollStrong)}; }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (getParentActivity() == null) return;
        if (position == chatsRow || position == conversationRow) {
            int surface = position == chatsRow ? ScrollEffectsConfig.CHATS : ScrollEffectsConfig.CONVERSATION;
            showDialog(AlertsCreator.createSingleChoiceDialog(getParentActivity(), styles(),
                    text(position == chatsRow ? R.string.FlexyScrollChats : R.string.FlexyScrollConversation),
                    ScrollEffectsConfig.style(surface), (dialog, which) -> {
                        ScrollEffectsConfig.setStyle(surface, which);
                        listAdapter.notifyItemChanged(position);
                    }));
        } else if (position == intensityRow) {
            showDialog(AlertsCreator.createSingleChoiceDialog(getParentActivity(), intensities(),
                    text(R.string.FlexyScrollIntensity), ScrollEffectsConfig.intensityIndex(), (dialog, which) -> {
                        ScrollEffectsConfig.setIntensity(which);
                        listAdapter.notifyItemChanged(intensityRow);
                    }));
        }
    }
    @Override protected BaseListAdapter createAdapter(Context context) {
        return new MatteListAdapter(context) {
            @Override public int getItemViewType(int position) {
                return position == headerRow ? TYPE_HEADER : position == infoRow ? TYPE_INFO_PRIVACY : TYPE_SETTINGS;
            }
            @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
                if (position == headerRow) ((tw.nekomimi.nekogram.ui.cells.HeaderCell) holder.itemView).setText(getActionBarTitle());
                else if (position == infoRow) ((TextInfoPrivacyCell) holder.itemView).setText(text(R.string.FlexyScrollInfo));
                else {
                    int title = position == chatsRow ? R.string.FlexyScrollChats
                            : position == conversationRow ? R.string.FlexyScrollConversation : R.string.FlexyScrollIntensity;
                    String value = position == intensityRow ? intensities()[ScrollEffectsConfig.intensityIndex()]
                            : styles()[ScrollEffectsConfig.style(position == chatsRow ? ScrollEffectsConfig.CHATS : ScrollEffectsConfig.CONVERSATION)];
                    ((TextSettingsCell) holder.itemView).setTextAndValue(text(title), value, position != intensityRow);
                }
            }
            @Override public boolean isEnabled(RecyclerView.ViewHolder holder) {
                int position = settingsRowPosition(holder);
                return position == chatsRow || position == conversationRow || position == intensityRow;
            }
        };
    }
}
