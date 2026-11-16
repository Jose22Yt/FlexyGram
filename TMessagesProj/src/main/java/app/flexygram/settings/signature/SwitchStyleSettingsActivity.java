package app.flexygram.settings.signature;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.Switch;
import xyz.nextalone.nagram.NaConfig;

/** Reuses the existing switch state, drawing and accessibility; no second preference or renderer. */
public final class SwitchStyleSettingsActivity extends SignatureMatteSettingsActivity {
    private int styleRow;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.FlexySwitchStyleTitle);}
    @Override protected void updateRows(){super.updateRows();styleRow=addRow("conversationSwitchStyle");}
    @Override protected void onItemClick(View view,int position,float x,float y){
        if(position!=styleRow)return;
        showDialog(new AlertDialog.Builder(getParentActivity(),resourcesProvider)
            .setTitle(LocaleController.getString(R.string.FlexySwitchStyleTitle))
            .setItems(new CharSequence[]{LocaleController.getString(R.string.FlexySwitchCurrent),LocaleController.getString(R.string.FlexySwitchOutlined)},(dialog,which)->{
                NaConfig.INSTANCE.getSwitchStyle().setConfigInt(which==1?Switch.SWITCH_STYLE_OUTLINED:Switch.SWITCH_STYLE_MD3);
                listAdapter.notifyItemChanged(styleRow);
                listView.invalidateViews();
            }).create());
    }
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int position){return TYPE_SETTINGS;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            ((TextSettingsCell)holder.itemView).setTextAndValue(LocaleController.getString(R.string.FlexySwitchStyleTitle),LocaleController.getString(NaConfig.INSTANCE.getSwitchStyle().Int()==Switch.SWITCH_STYLE_OUTLINED?R.string.FlexySwitchOutlined:R.string.FlexySwitchCurrent),false);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return true;}
    };}
}
