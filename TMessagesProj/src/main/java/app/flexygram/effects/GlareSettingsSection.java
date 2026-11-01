/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.effects;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.exteraless.appearance.AppearanceConfig;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Components.AlertsCreator;
import org.telegram.ui.Cells.TextSettingsCell;

/** Direct Chat control, functional reference: Cherrygram Glare effects. Original backend retained. */
public final class GlareSettingsSection extends SignatureMatteSettingsActivity {
    private int headerRow,typeRow;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.FlexyGlareEffects);}
    @Override protected String getKey(){return "exteraless_chats";}
    @Override public int getSearchGuid(){return 11_000_000;}
    @Override public int getSearchIcon(){return R.drawable.settings3_sliders;}
    @Override public String getSearchPrefix(){return "Flexy";}
    @Override protected void updateRows(){super.updateRows();headerRow=addRow("flexyGlareHeader");typeRow=addRow("glareEffects");}
    private String[] choices(){return new String[]{LocaleController.getString(R.string.FlexyGlareDisabled),LocaleController.getString(R.string.FlexyGlareDefault),LocaleController.getString(R.string.FlexyGlareSolid)};}
    @Override protected void onItemClick(View view,int position,float x,float y){
        if(position!=typeRow||getParentActivity()==null)return;
        showDialog(AlertsCreator.createSingleChoiceDialog(getParentActivity(),choices(),
            LocaleController.getString(R.string.FlexyGlareEffects),GlareMode.fromStored(AppearanceConfig.glassOutlineStyle()),(dialog,which)->{
                AppearanceConfig.glassOutlineStyle.setConfigInt(GlareMode.toStored(which));
                // The existing setter dispatches weak drawable listeners once, only on change.
                if(listAdapter!=null)listAdapter.notifyItemChanged(typeRow);
                if(listView!=null)listView.invalidate();
            }));
    }
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int p){return p==headerRow?TYPE_HEADER:TYPE_SETTINGS;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int p,boolean partial){
            if(p==headerRow)((tw.nekomimi.nekogram.ui.cells.HeaderCell)holder.itemView).setText(LocaleController.getString(R.string.FlexyGlareEffects));
            else ((TextSettingsCell)holder.itemView).setTextAndValue(LocaleController.getString(R.string.FlexyGlareType),choices()[GlareMode.fromStored(AppearanceConfig.glassOutlineStyle())],false);
        }
    };}
}
