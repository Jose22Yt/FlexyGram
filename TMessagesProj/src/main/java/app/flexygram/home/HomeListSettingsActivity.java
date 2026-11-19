/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.scroll.DirectionalScrollSettings;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;

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
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int position){return TYPE_CHECK;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            org.telegram.ui.Cells.TextCheckCell cell = (org.telegram.ui.Cells.TextCheckCell) holder.itemView;
            if (position == dividerRow) {
                cell.setTextAndCheck(LocaleController.getString(R.string.FlexyHomeChatDividers), chatDividersEnabled(), false);
            } else if (position == scrollEdgeRow) {
                cell.setTextAndValueAndCheck(
                        LocaleController.getString(R.string.FlexyHomeDirectionalScrollEdge),
                        LocaleController.getString(R.string.FlexyHomeDirectionalScrollEdgeHint),
                        DirectionalScrollSettings.enabled(), true, false);
            }
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return true;}
    };}
    @Override protected void onItemClick(View view,int position,float x,float y){
        if (position == scrollEdgeRow) {
            DirectionalScrollSettings.setEnabled(!DirectionalScrollSettings.enabled());
            ((org.telegram.ui.Cells.TextCheckCell) view).setChecked(DirectionalScrollSettings.enabled());
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
