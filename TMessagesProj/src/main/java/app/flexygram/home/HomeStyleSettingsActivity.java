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
    private int styleRow, dividerRow;
    private boolean chatDividersEnabled() {
        return app.exteraless.appearance.AppearanceConfig.dividerStyle() == app.exteraless.appearance.AppearanceConfig.DIVIDER_LINE
                && !xyz.nextalone.nagram.NaConfig.INSTANCE.getHideDividers().Bool();
    }
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.FlexyHomeStyle);}
    @Override protected void updateRows(){super.updateRows();HomeStyleConfig.load();styleRow=addRow("flexyHomeStyle");dividerRow=addRow("dividerStyle");}
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int position){return position==dividerRow?TYPE_CHECK:TYPE_SETTINGS;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            if(position==dividerRow){
                ((org.telegram.ui.Cells.TextCheckCell)holder.itemView).setTextAndCheck(LocaleController.getString(R.string.FlexyHomeChatDividers),chatDividersEnabled(),false);
                return;
            }
            ((TextSettingsCell)holder.itemView).setTextAndValue(getActionBarTitle(),LocaleController.getString(HomeStyleConfig.isIos()?R.string.FlexyHomeIos:R.string.Default),false);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return true;}
    };}
    @Override protected void onItemClick(View view,int position,float x,float y){
        if(position==dividerRow){
            boolean enabled=!chatDividersEnabled();
            xyz.nextalone.nagram.NaConfig.INSTANCE.getHideDividers().setConfigBool(!enabled);
            app.exteraless.appearance.AppearanceConfig.dividerStyle.setConfigInt(enabled?app.exteraless.appearance.AppearanceConfig.DIVIDER_LINE:app.exteraless.appearance.AppearanceConfig.DIVIDER_HIDDEN);
            app.exteraless.appearance.AppearanceConfig.invalidateDividerStyle();
            org.telegram.ui.ActionBar.Theme.applyCommonTheme();
            listAdapter.notifyItemChanged(dividerRow);
            if(getParentLayout()!=null)getParentLayout().rebuildFragments(0);
            return;
        }
        if(position!=styleRow)return;
        showDialog(new AlertDialog.Builder(getParentActivity(),resourcesProvider).setTitle(getActionBarTitle())
            .setItems(new CharSequence[]{LocaleController.getString(R.string.Default),LocaleController.getString(R.string.FlexyHomeIos)},(dialog,which)->{
                int style=HomeStyleConfig.optionStyle(which);
                if(HomeStyleConfig.style()==style)return;
                HomeStyleConfig.setStyle(style);listAdapter.notifyItemChanged(styleRow);
                if(getParentLayout()!=null)getParentLayout().rebuildFragments(0);
            }).create());
    }
}
