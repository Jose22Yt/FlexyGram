/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextSettingsCell;
import app.flexygram.settings.SignatureMatteSettingsActivity;
/** Original local opt-in and help only; does not advertise unimplemented archive formats. */
public final class SignatureFlexyFilesActivity extends SignatureMatteSettingsActivity {
    private int enabled,help;
    @Override protected String getActionBarTitle(){return "FlexyFiles";}
    @Override protected void updateRows(){super.updateRows();enabled=addRow("flexyfilesEnabled");help=addRow("flexyfilesHelp");}
    @Override protected void onItemClick(View v,int p,float x,float y){
        if(p==enabled){app.flexygram.files.FlexyFiles.enabled(!app.flexygram.files.FlexyFiles.enabled());listAdapter.notifyItemChanged(enabled);}
        else if(p==help)showDialog(new AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle("FlexyFiles").setMessage(LocaleController.getString(R.string.FlexyFilesHelp)).setPositiveButton(LocaleController.getString(R.string.OK),null).create());
    }
    @Override protected BaseListAdapter createAdapter(Context c){return new MatteListAdapter(c){
        @Override public int getItemViewType(int p){return p==enabled?TYPE_CHECK:TYPE_SETTINGS;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int p,boolean partial){
            if(p==enabled)((TextCheckCell)holder.itemView).setTextAndValueAndCheck(LocaleController.getString(R.string.FlexyFilesEnable),LocaleController.getString(app.flexygram.files.FlexyFiles.enabled()?R.string.FlexyFilesDormant:R.string.FlexyFilesDisabled),app.flexygram.files.FlexyFiles.enabled(),false,true,false);
            else ((TextSettingsCell)holder.itemView).setText(LocaleController.getString(R.string.FlexyFilesHow),false);
        }
    };}
}
