/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Cells.TextSettingsCell;

/**
 * Chats -> Message interactions. Exactly two built-in native styles.
 * No user-defined timing, deformation, speed or intensity controls.
 */
public final class BubbleInteractionSettingsActivity extends SignatureMatteSettingsActivity {
    private int styleRow, infoRow;

    @Override protected String getActionBarTitle() {
        return LocaleController.getString(R.string.FlexyContextInteractions);
    }

    @Override protected void updateRows() {
        super.updateRows();
        styleRow = addRow("flexyContextStyle");
        infoRow = addRow();
    }

    @Override protected BaseListAdapter createAdapter(Context context) {
        return new Adapter(context);
    }

    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (position != styleRow || getParentActivity() == null) return;
        final Context context = getParentActivity();
        final String[] labels = {
                LocaleController.getString(R.string.FlexyContextNativeStyle),
                LocaleController.getString(R.string.FlexyContextSignatureStyle)
        };
        showDialog(new AlertDialog.Builder(context, getResourceProvider())
                .setTitle(LocaleController.getString(R.string.FlexyContextStyle))
                .setItems(labels, (dialog, which) -> {
                    if (which == BubbleInteractionSettings.STYLE_DEFAULT
                            || which == BubbleInteractionSettings.STYLE_SIGNATURE) {
                        BubbleInteractionSettings.setStyle(context, which);
                        if (listAdapter != null) listAdapter.notifyItemChanged(styleRow);
                    }
                }).create());
    }

    private final class Adapter extends MatteListAdapter {
        Adapter(Context context) { super(context); }

        @Override public int getItemViewType(int position) {
            return position == infoRow ? TYPE_INFO_PRIVACY : TYPE_SETTINGS;
        }

        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            if (position == infoRow) {
                ((TextInfoPrivacyCell) holder.itemView)
                        .setText(LocaleController.getString(R.string.FlexyContextStyleDescription));
                return;
            }
            Context context = holder.itemView.getContext();
            String selected = LocaleController.getString(
                    BubbleInteractionSettings.style(context) == BubbleInteractionSettings.STYLE_SIGNATURE
                            ? R.string.FlexyContextSignatureStyle : R.string.FlexyContextNativeStyle);
            ((TextSettingsCell) holder.itemView).setTextAndValue(
                    LocaleController.getString(R.string.FlexyContextStyle), selected, false);
        }

        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) {
            return settingsRowPosition(holder) == styleRow;
        }
    }
}
