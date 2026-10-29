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

/** The existing opt-in preference, in a native Matte settings route. No motion controls. */
public final class BubbleInteractionSettingsActivity extends SignatureMatteSettingsActivity {
    private int toggle,info;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.FlexyContextInteractions);}
    @Override protected void updateRows(){super.updateRows();toggle=addRow("flexyContextPanel");info=addRow();}
    @Override protected BaseListAdapter createAdapter(Context context){return new Adapter(context);}
    @Override protected void onItemClick(View view,int position,float x,float y){
        if(position!=toggle)return;
        BubbleInteractionSettings.setSignaturePanel(getParentActivity(),!BubbleInteractionSettings.signaturePanel(getParentActivity()));
        listAdapter.notifyItemChanged(toggle);
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context){super(context);}
        @Override public int getItemViewType(int position){return position==toggle?TYPE_CHECK:TYPE_INFO_PRIVACY;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            if(position==toggle)((TextCheckCell)holder.itemView).setTextAndCheck(LocaleController.getString(R.string.FlexyContextPanel),BubbleInteractionSettings.signaturePanel(holder.itemView.getContext()),false);
            else ((TextInfoPrivacyCell)holder.itemView).setText(LocaleController.getString(R.string.FlexyContextDescription));
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return holder.getAdapterPosition()==toggle;}
    }
}
