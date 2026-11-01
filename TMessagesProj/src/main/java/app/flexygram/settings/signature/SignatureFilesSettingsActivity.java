/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;
import android.content.Context;
import android.view.*;
import androidx.recyclerview.widget.RecyclerView;
import app.exteraless.settings.OpenExteraGeneralActivity;
import org.telegram.messenger.*;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.*;
import org.telegram.ui.Components.RecyclerListView;
/** Original save-path dialogs/permissions plus the original FlexyFiles opt-in. */
public final class SignatureFilesSettingsActivity extends OpenExteraGeneralActivity {
    private int filesHeader=-1,enabled=-1,help=-1,shadow=-1;
    public SignatureFilesSettingsActivity(){useSignatureSettingsPage("general","files",R.string.Settings2_files);}
    @Override protected void updateRows(){super.updateRows();filesHeader=addRow("settings2FilesHeader");enabled=addRow("flexyfilesEnabled");help=addRow("flexyfilesHelp");shadow=addRow();}
    @Override protected void onItemClick(View v,int p,float x,float y){
        if(p==enabled){app.flexygram.files.FlexyFiles.enabled(!app.flexygram.files.FlexyFiles.enabled());listAdapter.notifyItemChanged(enabled);}
        else if(p==help)showDialog(new AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle("FlexyFiles").setMessage(LocaleController.getString(R.string.FlexyFilesHelp)).setPositiveButton(LocaleController.getString(R.string.OK),null).create());
        else super.onItemClick(v,p,x,y);
    }
    @Override protected BaseListAdapter createAdapter(Context context){
        BaseListAdapter original=super.createAdapter(context);
        return new MatteListAdapter(context){
            @Override public int getItemViewType(int p){return p==filesHeader?TYPE_HEADER:p==enabled?TYPE_CHECK:p==help?220:p==shadow?TYPE_SHADOW:original.getItemViewType(p);}
            @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){return type==220?new RecyclerListView.Holder(new Settings2Cell(parent.getContext(),resourcesProvider)):original.onCreateViewHolder(parent,type);}
            @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){
                if(p==filesHeader)((tw.nekomimi.nekogram.ui.cells.HeaderCell)h.itemView).setText("FlexyFiles");
                else if(p==enabled)((TextCheckCell)h.itemView).setTextAndValueAndCheck(LocaleController.getString(R.string.FlexyFilesEnable),LocaleController.getString(app.flexygram.files.FlexyFiles.enabled()?R.string.FlexyFilesDormant:R.string.FlexyFilesDisabled),app.flexygram.files.FlexyFiles.enabled(),true,true,false);
                else if(p==help)((Settings2Cell)h.itemView).bind(LocaleController.getString(R.string.FlexyFilesHow),"",R.drawable.msg_info,0xFF8B50DE,false);
                else if(p!=shadow)original.onBindViewHolder(h,p,partial);
            }
            @Override public boolean isEnabled(RecyclerView.ViewHolder h){return h.getItemViewType()==220||original.isEnabled(h);}
        };
    }
}
