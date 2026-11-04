/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.content.res.ColorStateList;
import android.view.View;
import android.view.ViewGroup;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import java.util.EnumSet;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.RecyclerListView;

/** Compact gallery and primary actions. Native message permissions remain authoritative. */
public final class BubbleInteractionSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int GALLERY=341;
    private int styleRow,galleryRow,actionsRow,infoRow;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.FlexyMenuTitle);}
    @Override protected void updateRows(){super.updateRows();styleRow=addRow("flexyContextStyle");galleryRow=addRow("flexyContextMenuLayout");actionsRow=addRow("flexyContextMenuActions");infoRow=addRow();}
    @Override public void onResume(){super.onResume();if(listAdapter!=null)listAdapter.notifyDataSetChanged();}
    @Override protected BaseListAdapter createAdapter(Context context){return new Adapter(context);}
    @Override protected void onItemClick(View view,int position,float x,float y){
        if(getParentActivity()==null)return;
        Context context=getParentActivity();
        if(position==actionsRow){chooseActions(context);return;}
        if(position!=styleRow)return;
        String[] labels={LocaleController.getString(R.string.FlexyContextNativeStyle),LocaleController.getString(R.string.FlexyContextSignatureStyle)};
        showDialog(new AlertDialog.Builder(context,getResourceProvider()).setTitle(LocaleController.getString(R.string.FlexyContextStyle)).setItems(labels,(dialog,which)->{
            if(which==0||which==1){BubbleInteractionSettings.setStyle(context,which);if(listAdapter!=null)listAdapter.notifyDataSetChanged();}
        }).create());
    }
    private void chooseActions(Context context){
        EnumSet<BubbleActionPanelView.Action> draft=BubbleMenuConfig.actions(context);
        LinearLayout content=new LinearLayout(context);content.setOrientation(LinearLayout.VERTICAL);
        for(BubbleActionPanelView.Action action:BubbleActionPanelView.Action.values()){
            if(action==BubbleActionPanelView.Action.MORE)continue;
            CheckBox check=new CheckBox(context);check.setText(BubbleActionPanelView.label(action));check.setTextSize(15);check.setMinHeight(BubbleActionPanelView.dp(context,44));
            check.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));check.setButtonTintList(ColorStateList.valueOf(getThemedColor(Theme.key_windowBackgroundWhiteBlueText)));
            check.setChecked(draft.contains(action));check.setOnCheckedChangeListener((button,checked)->{if(checked)draft.add(action);else draft.remove(action);});content.addView(check,new LinearLayout.LayoutParams(-1,-2));
        }
        ScrollView scroll=new ScrollView(context);scroll.addView(content);
        showDialog(new AlertDialog.Builder(context,getResourceProvider()).setTitle(LocaleController.getString(R.string.FlexyMenuActions)).setView(scroll)
            .setPositiveButton(LocaleController.getString(R.string.OK),(dialog,which)->{BubbleMenuConfig.actions(context,draft);if(listAdapter!=null)listAdapter.notifyDataSetChanged();})
            .setNeutralButton(LocaleController.getString(R.string.FlexyMenuReset),(dialog,which)->{BubbleMenuConfig.actions(context,BubbleMenuConfig.defaults());if(listAdapter!=null)listAdapter.notifyDataSetChanged();})
            .setNegativeButton(LocaleController.getString(R.string.Cancel),null).create());
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context){super(context);}
        @Override public int getItemViewType(int position){return position==galleryRow?GALLERY:position==infoRow?TYPE_INFO_PRIVACY:TYPE_SETTINGS;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){
            if(type==GALLERY)return new RecyclerListView.Holder(new BubbleMenuGallery(parent.getContext(),resourcesProvider,()->{if(listAdapter!=null)listAdapter.notifyItemChanged(styleRow);}));
            return super.onCreateViewHolder(parent,type);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            if(position==galleryRow){((BubbleMenuGallery)holder.itemView).refresh();return;}
            if(position==infoRow){((TextInfoPrivacyCell)holder.itemView).setText(LocaleController.getString(R.string.FlexyMenuActionsInfo));return;}
            if(position==actionsRow){((TextSettingsCell)holder.itemView).setTextAndValue(LocaleController.getString(R.string.FlexyMenuActions),String.valueOf(BubbleMenuConfig.actions(holder.itemView.getContext()).size()),false);return;}
            String selected=LocaleController.getString(BubbleInteractionSettings.signaturePanel(holder.itemView.getContext())?R.string.FlexyContextSignatureStyle:R.string.FlexyContextNativeStyle);
            ((TextSettingsCell)holder.itemView).setTextAndValue(LocaleController.getString(R.string.FlexyContextStyle),selected,false);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){int position=settingsRowPosition(holder);return position==styleRow||position==actionsRow;}
    }
}
