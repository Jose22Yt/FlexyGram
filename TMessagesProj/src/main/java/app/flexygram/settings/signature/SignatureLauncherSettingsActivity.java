/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;
import android.content.Context;
import android.view.*;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.*;
import org.telegram.ui.Cells.AppIconsSelectorCell;
import org.telegram.ui.Components.RecyclerListView;
/** Existing selector/controller, moved as a unit; no new preference or launcher identity. */
public final class SignatureLauncherSettingsActivity extends SignatureMatteSettingsActivity {
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.Settings2_launcher);}
    @Override protected void updateRows(){super.updateRows();addRow("settings2Launcher");}
    @Override public View createView(Context c){View v=super.createView(c);actionBar.centerTitle();listView.setItemAnimator(null);return v;}
    @Override protected void onItemClick(View v,int p,float x,float y){}
    @Override protected BaseListAdapter createAdapter(Context c){return new MatteListAdapter(c){
        @Override public int getItemViewType(int p){return 230;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){return new RecyclerListView.Holder(new AppIconsSelectorCell(parent.getContext(),SignatureLauncherSettingsActivity.this,currentAccount));}
        @Override public boolean isEnabled(RecyclerView.ViewHolder h){return true;}
    };}
}
