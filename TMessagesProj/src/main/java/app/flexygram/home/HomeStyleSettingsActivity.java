/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.TextSettingsCell;

/** First embedded Home row: a text selector, without a preview or nested style gallery. */
public final class HomeStyleSettingsActivity extends SignatureMatteSettingsActivity {
    private int styleRow;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.FlexyHomeStyle);}
    @Override protected void updateRows(){super.updateRows();HomeStyleConfig.load();styleRow=addRow("flexyHomeStyle");}
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int position){return TYPE_SETTINGS;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            ((TextSettingsCell)holder.itemView).setTextAndValue(getActionBarTitle(),LocaleController.getString(HomeStyleConfig.style()==HomeStyleConfig.ESSENTIALS?R.string.FlexyHomeEssentials:R.string.Default),false);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return true;}
    };}
    @Override protected void onItemClick(View view,int position,float x,float y){
        if(position!=styleRow)return;
        showDialog(new AlertDialog.Builder(getParentActivity(),resourcesProvider).setTitle(getActionBarTitle())
            .setItems(new CharSequence[]{LocaleController.getString(R.string.Default),LocaleController.getString(R.string.FlexyHomeEssentials)},(dialog,which)->{
                if(HomeStyleConfig.style()==which)return;
                HomeStyleConfig.setStyle(which);listAdapter.notifyItemChanged(styleRow);
                if(getParentLayout()!=null)getParentLayout().rebuildFragments(0);
            }).create());
    }
}
