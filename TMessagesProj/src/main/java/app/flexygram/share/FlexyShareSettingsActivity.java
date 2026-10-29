/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.share;
import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
public final class FlexyShareSettingsActivity extends SignatureMatteSettingsActivity {
    private int enabledRow,infoRow;
    @Override protected String getActionBarTitle(){return "Flexy Share Sheet";}
    @Override protected void updateRows(){super.updateRows();enabledRow=addRow("flexyShareEnabled");infoRow=addRow();}
    @Override protected BaseListAdapter createAdapter(Context c){return new Adapter(c);}
    @Override protected void onItemClick(View v,int p,float x,float y){if(p==enabledRow){FlexyShareConfig.enabled(v.getContext(),!FlexyShareConfig.enabled(v.getContext()));listAdapter.notifyItemChanged(p);}}
    private final class Adapter extends MatteListAdapter {
        Adapter(Context c){super(c);}
        @Override public int getItemViewType(int p){return p==enabledRow?TYPE_CHECK:TYPE_INFO_PRIVACY;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){if(p==enabledRow)((TextCheckCell)h.itemView).setTextAndCheck(LocaleController.getString(R.string.FlexyShareEnabled),FlexyShareConfig.enabled(h.itemView.getContext()),true);else ((TextInfoPrivacyCell)h.itemView).setText(LocaleController.getString(R.string.FlexyShareDescription));}
        @Override public boolean isEnabled(RecyclerView.ViewHolder h){return h.getAdapterPosition()==enabledRow;}
    }
}
