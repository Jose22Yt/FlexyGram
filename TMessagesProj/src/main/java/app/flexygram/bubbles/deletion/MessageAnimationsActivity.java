/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.deletion;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextSettingsCell;

/** Compact native route: Animations -> Message animations -> On delete. */
public final class MessageAnimationsActivity extends SignatureMatteSettingsActivity {
    private final boolean messages;
    private int row;
    public MessageAnimationsActivity(boolean messages) { this.messages = messages; }
    @Override protected String getActionBarTitle() {
        return LocaleController.getString(messages ? R.string.FlexyMessageAnimations : R.string.FlexyAnimationsTitle);
    }
    @Override protected void updateRows() { super.updateRows(); row=addRow(messages?"deleteMotion":"messageAnimations"); }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    @Override protected void onItemClick(View view,int position,float x,float y) {
        if (position != row || getParentActivity() == null) return;
        if (messages) DeleteMotionSettingsDialog.show(getParentActivity());
        else presentFragment(new MessageAnimationsActivity(true));
    }
    @Override public void onResume() { super.onResume(); if (listAdapter != null) listAdapter.notifyDataSetChanged(); }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context) { super(context); }
        @Override public int getItemViewType(int position) { return TYPE_SETTINGS; }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial) {
            TextSettingsCell cell=(TextSettingsCell)holder.itemView;
            cell.setTextAndValue(LocaleController.getString(messages?R.string.FlexyDeleteTitle:R.string.FlexyMessageAnimations),
                messages?DeleteMotionSettings.labels()[DeleteMotionSettings.get(holder.itemView.getContext())]:"",false);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) { return holder.getAdapterPosition()==row; }
    }
}
