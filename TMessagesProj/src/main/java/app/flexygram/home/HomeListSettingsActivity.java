/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.scroll.DirectionalScrollSettings;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.AlertsCreator;

/** Home list controls; there is no layout selector. */
public final class HomeListSettingsActivity extends SignatureMatteSettingsActivity {
    private int dividerRow, scrollEdgeRow;
    private boolean chatDividersEnabled() {
        return app.exteraless.appearance.AppearanceConfig.dividerStyle() == app.exteraless.appearance.AppearanceConfig.DIVIDER_LINE
                && !xyz.nextalone.nagram.NaConfig.INSTANCE.getHideDividers().Bool();
    }
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.ChatList);}
    @Override protected void updateRows() {
        super.updateRows();
        dividerRow = addRow("dividerStyle");
        scrollEdgeRow = addRow("flexyDirectionalScrollEdge");
    }
    private static String[] scrollStyles() {
        return new String[]{
                LocaleController.getString(R.string.FlexyHomeDirectionalScrollOff),
                LocaleController.getString(R.string.FlexyHomeDirectionalScrollCurve),
                LocaleController.getString(R.string.FlexyHomeDirectionalScrollTwist),
                LocaleController.getString(R.string.FlexyHomeDirectionalScrollCounterCurve),
                LocaleController.getString(R.string.FlexyHomeDirectionalScrollLens),
        };
    }

    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int position) {
            return position == dividerRow ? TYPE_CHECK : TYPE_SETTINGS;
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            if (position == dividerRow) {
                ((org.telegram.ui.Cells.TextCheckCell) holder.itemView).setTextAndCheck(
                        LocaleController.getString(R.string.FlexyHomeChatDividers), chatDividersEnabled(), false);
            } else if (position == scrollEdgeRow) {
                ((TextSettingsCell) holder.itemView).setTextAndValue(
                        LocaleController.getString(R.string.FlexyHomeDirectionalScrollEdge),
                        scrollStyles()[DirectionalScrollSettings.style()], false);
            }
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return true;}
    };}
    @Override protected void onItemClick(View view,int position,float x,float y){
        if (position == scrollEdgeRow) {
            if (getParentActivity() == null) return;
            showDialog(AlertsCreator.createSingleChoiceDialog(getParentActivity(), scrollStyles(),
                    LocaleController.getString(R.string.FlexyHomeDirectionalScrollEdge),
                    DirectionalScrollSettings.style(), (dialog, which) -> {
                        DirectionalScrollSettings.setStyle(which);
                        if (listAdapter != null) listAdapter.notifyItemChanged(scrollEdgeRow);
                    }));
        } else if(position==dividerRow){
            boolean enabled=!chatDividersEnabled();
            xyz.nextalone.nagram.NaConfig.INSTANCE.getHideDividers().setConfigBool(!enabled);
            app.exteraless.appearance.AppearanceConfig.dividerStyle.setConfigInt(enabled?app.exteraless.appearance.AppearanceConfig.DIVIDER_LINE:app.exteraless.appearance.AppearanceConfig.DIVIDER_HIDDEN);
            app.exteraless.appearance.AppearanceConfig.invalidateDividerStyle();
            org.telegram.ui.ActionBar.Theme.applyCommonTheme();
            listAdapter.notifyItemChanged(dividerRow);
            if(getParentLayout()!=null)getParentLayout().rebuildFragments(0);
            return;
        }
    }
}
