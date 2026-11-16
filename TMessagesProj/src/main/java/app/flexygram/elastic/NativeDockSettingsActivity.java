package app.flexygram.elastic;

import android.content.Context;
import android.os.Build;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;

/** Only the new material switch. No legacy dock editor, ordering or retired customization. */
public final class NativeDockSettingsActivity extends SignatureMatteSettingsActivity {
    private int dockRow, infoRow;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.CompactTabs);}
    @Override protected void updateRows(){super.updateRows();dockRow=addRow("kyantHomeDock");infoRow=addRow("kyantHomeDockInfo");}
    @Override protected void onItemClick(View view,int position,float x,float y){if(position==dockRow&&Build.VERSION.SDK_INT>=33){ElasticConfig.setKyantDock(!ElasticConfig.kyantDock());listAdapter.notifyItemChanged(position);}}
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int p){return p==dockRow?TYPE_CHECK:TYPE_INFO_PRIVACY;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int p,boolean partial){
            if(p==dockRow)((TextCheckCell)holder.itemView).setTextAndValueAndCheck(LocaleController.getString(R.string.FlexyKyantDockTitle),LocaleController.getString(R.string.FlexyKyantDockSubtitle),ElasticConfig.kyantDock(),false,false);
            else ((TextInfoPrivacyCell)holder.itemView).setText(LocaleController.getString(R.string.FlexyKyantDockInfo));
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return Build.VERSION.SDK_INT>=33&&holder.getItemViewType()==TYPE_CHECK;}
    };}
}
