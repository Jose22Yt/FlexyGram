/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.memberlens;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextCheckCell;
import tw.nekomimi.nekogram.ui.cells.HeaderCell;

/** One direct setting in Chat; no new category or intermediate page. */
public final class MemberLensSettingsSection extends SignatureMatteSettingsActivity {
    private int headerRow, enabledRow;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.MemberLensInteraction);}
    @Override protected String getKey(){return "exteraless_chats";}
    @Override public int getSearchGuid(){return 12_000_000;}
    @Override protected void updateRows(){super.updateRows();headerRow=addRow("memberLensInteraction");enabledRow=addRow(MemberLensConfig.KEY);}
    @Override protected void onItemClick(View v,int position,float x,float y){
        if(position==enabledRow){MemberLensConfig.setEnabled(!MemberLensConfig.enabled());if(listAdapter!=null)listAdapter.notifyItemChanged(enabledRow);}
    }
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int position){return position==headerRow?TYPE_HEADER:TYPE_CHECK;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            if(position==headerRow)((HeaderCell)holder.itemView).setText(LocaleController.getString(R.string.MemberLensInteraction));
            else ((TextCheckCell)holder.itemView).setTextAndValueAndCheck(LocaleController.getString(R.string.MemberLensSetting),LocaleController.getString(R.string.MemberLensSettingInfo),MemberLensConfig.enabled(),false,true);
        }
    };}
}
