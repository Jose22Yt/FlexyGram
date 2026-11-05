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
    private int headerRow,typeRow,widthRow;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.FlexyGlareEffects);}
    @Override protected String getKey(){return "exteraless_chats";}
    @Override public int getSearchGuid(){return 11_000_000;}
    @Override public int getSearchIcon(){return R.drawable.settings3_sliders;}
    @Override public String getSearchPrefix(){return "Flexy";}
    @Override protected void updateRows(){super.updateRows();headerRow=addRow("flexyGlareHeader");typeRow=addRow("glareEffects");widthRow=addRow("glareOutlineWidth");}
    private String[] choices(){return new String[]{LocaleController.getString(R.string.FlexyGlareDisabled),LocaleController.getString(R.string.FlexyGlareDefault),LocaleController.getString(R.string.FlexyGlareSolid)};}
    @Override protected void onItemClick(View view,int position,float x,float y){
        if (getParentActivity()==null) return;
        if (position==widthRow) { showWidthDialog();return; }
        if(position!=typeRow)return;
        showDialog(AlertsCreator.createSingleChoiceDialog(getParentActivity(),choices(),
            LocaleController.getString(R.string.FlexyGlareEffects),GlareMode.fromStored(AppearanceConfig.glassOutlineStyle()),(dialog,which)->{
                AppearanceConfig.glassOutlineStyle.setConfigInt(GlareMode.toStored(which));
                // The existing setter dispatches weak drawable listeners once, only on change.
                if(listAdapter!=null)listAdapter.notifyItemChanged(typeRow);
                if(listView!=null)listView.invalidate();
            }));
    }
    private String widthLabel(int value) { return String.format(java.util.Locale.getDefault(), "%.1f×", value/10f); }
    private void saveWidth(int value) {
        AppearanceConfig.glassOutlineWidth.setConfigInt(value);
        if (listAdapter!=null) listAdapter.notifyItemChanged(widthRow);
    }
    private void showWidthDialog() {
        android.widget.LinearLayout body=new android.widget.LinearLayout(getParentActivity());
        body.setOrientation(android.widget.LinearLayout.VERTICAL);
        int padding=org.telegram.messenger.AndroidUtilities.dp(24);body.setPadding(padding,0,padding,padding/2);
        android.widget.TextView value=new android.widget.TextView(getParentActivity());value.setGravity(android.view.Gravity.CENTER);
        value.setTextSize(20);value.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText,resourcesProvider));
        int[] pending={AppearanceConfig.glassOutlineWidth()};value.setText(widthLabel(pending[0]));body.addView(value);
        android.widget.SeekBar slider=new android.widget.SeekBar(getParentActivity());slider.setMax(25);slider.setProgress(pending[0]-5);
        int accent=org.telegram.ui.ActionBar.Theme.getColor(org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlueText,resourcesProvider);
        slider.setProgressTintList(android.content.res.ColorStateList.valueOf(accent));slider.setThumbTintList(android.content.res.ColorStateList.valueOf(accent));
        body.addView(slider,new android.widget.LinearLayout.LayoutParams(-1,org.telegram.messenger.AndroidUtilities.dp(48)));
        slider.setContentDescription(LocaleController.getString(R.string.FlexyGlareWidth));
        slider.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener(){
            public void onStartTrackingTouch(android.widget.SeekBar bar) {}
            public void onStopTrackingTouch(android.widget.SeekBar bar) {}
            public void onProgressChanged(android.widget.SeekBar bar,int progress,boolean user){pending[0]=5+progress;value.setText(widthLabel(pending[0]));}
        });
        showDialog(new org.telegram.ui.ActionBar.AlertDialog.Builder(getParentActivity(),resourcesProvider)
                .setTitle(LocaleController.getString(R.string.FlexyGlareWidth)).setView(body)
                .setPositiveButton(LocaleController.getString(R.string.Done),(dialog,which)->saveWidth(pending[0]))
                .setNegativeButton(LocaleController.getString(R.string.Cancel),null)
                .setNeutralButton(LocaleController.getString(R.string.FlexyGlareReset),(dialog,which)->saveWidth(10)).create());
    }
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int p){return p==headerRow?TYPE_HEADER:TYPE_SETTINGS;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int p,boolean partial){
            if(p==headerRow)((tw.nekomimi.nekogram.ui.cells.HeaderCell)holder.itemView).setText(LocaleController.getString(R.string.FlexyGlareEffects));
            else if(p==widthRow)((TextSettingsCell)holder.itemView).setTextAndValue(LocaleController.getString(R.string.FlexyGlareWidth),widthLabel(AppearanceConfig.glassOutlineWidth()),false);
            else ((TextSettingsCell)holder.itemView).setTextAndValue(LocaleController.getString(R.string.FlexyGlareType),choices()[GlareMode.fromStored(AppearanceConfig.glassOutlineStyle())],false);
        }
    };}
}
