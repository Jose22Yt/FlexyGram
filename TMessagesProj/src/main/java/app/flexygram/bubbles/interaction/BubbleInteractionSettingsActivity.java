/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;
import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;

/** Chats -> Message interactions. All controls are wired to actual visible UI behavior. */
public final class BubbleInteractionSettingsActivity extends SignatureMatteSettingsActivity {
    private int panelRow, bounceRow, infoRow;
    @Override protected String getActionBarTitle() {
        return LocaleController.getString(R.string.FlexyContextInteractions);
    }
    @Override protected void updateRows() {
        super.updateRows();
        panelRow = addRow("flexyContextPanel");
        bounceRow = addRow("flexyContextBounce");
        infoRow = addRow();
    }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        Context context = getParentActivity();
        if (context == null) return;
        if (position == panelRow) {
            BubbleInteractionSettings.setSignaturePanel(context,
                    !BubbleInteractionSettings.signaturePanel(context));
        } else if (position == bounceRow) {
            BubbleInteractionSettings.setSpringBounce(context,
                    !BubbleInteractionSettings.springBounce(context));

        } else return;
        listAdapter.notifyItemChanged(position);
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context) { super(context); }
        @Override public int getItemViewType(int position) {
            return position == infoRow ? TYPE_INFO_PRIVACY : TYPE_CHECK;
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            Context context = holder.itemView.getContext();
            if (position == infoRow) {
                ((TextInfoPrivacyCell) holder.itemView).setText(
                        LocaleController.getString(R.string.FlexyContextDescription));
                return;
            }
            TextCheckCell cell = (TextCheckCell) holder.itemView;
            if (position == panelRow) {
                cell.setTextAndCheck(LocaleController.getString(R.string.FlexyContextPanel),
                        BubbleInteractionSettings.signaturePanel(context), true);
            } else if (position == bounceRow) {
                cell.setTextAndCheck(LocaleController.getString(R.string.FlexyContextBounce),
                        BubbleInteractionSettings.springBounce(context), false);

            }
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) {
            int position = holder.getAdapterPosition();
            return position == panelRow || position == bounceRow;
        }
    }
}
