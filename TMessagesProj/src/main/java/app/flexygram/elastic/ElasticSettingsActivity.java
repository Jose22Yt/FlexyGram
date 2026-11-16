package app.flexygram.elastic;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Components.RecyclerListView;

public final class ElasticSettingsActivity extends SignatureMatteSettingsActivity {
    private int enabledRow, previewRow, infoRow;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.FlexyElasticTitle);}
    @Override protected void updateRows(){super.updateRows();enabledRow=addRow("elasticEnabled");previewRow=addRow("elasticPreview");infoRow=addRow("elasticInfo");}
    @Override protected void onItemClick(View view,int position,float x,float y){if(position==enabledRow){ElasticConfig.setEnabled(!ElasticConfig.enabled());listAdapter.notifyItemChanged(position);}}
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int p){return p==previewRow?170:p==enabledRow?TYPE_CHECK:TYPE_INFO_PRIVACY;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){
            if(type==170)return new RecyclerListView.Holder(new ElasticPreviewView(parent.getContext()));
            return super.onCreateViewHolder(parent,type);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int p,boolean partial){
            if(p==enabledRow)((TextCheckCell)holder.itemView).setTextAndValueAndCheck(LocaleController.getString(R.string.FlexyElasticTitle),LocaleController.getString(R.string.FlexyElasticSubtitle),ElasticConfig.enabled(),false,false);
            else if(p==previewRow)((ElasticPreviewView)holder.itemView).updateColors();
            else if(p==infoRow)((TextInfoPrivacyCell)holder.itemView).setText(LocaleController.getString(R.string.FlexyElasticInfo));
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return holder.getItemViewType()==TYPE_CHECK;}
    };}
}
