package app.flexygram.header;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.RecyclerListView;

public final class HeaderSettingsActivity extends SignatureMatteSettingsActivity {
    private int previewRow, styleRow, sizeRow, opacityRow;
    private HeaderPreviewView preview;
    @Override protected void updateRows() { super.updateRows(); HeaderConfig.load(); previewRow=addRow(); styleRow=addRow("signatureHeaderStyle");sizeRow=addRow("signatureHeaderSize");opacityRow=addRow("signatureHeaderOpacity"); }
    @Override protected String getActionBarTitle() { return getString(R.string.FlexyHeaderTitle); }
    @Override protected BaseListAdapter createAdapter(Context c) { return new Adapter(c); }
    private void changed(int row) { listAdapter.notifyItemChanged(row); if(preview!=null)preview.settingsChanged(); }
    @Override protected void onItemClick(View v,int position,float x,float y) {
        if(position==styleRow||position==sizeRow){boolean style=position==styleRow;
            showDialog(new AlertDialog.Builder(getParentActivity(),resourcesProvider).setTitle(getString(style?R.string.FlexyHeaderStyle:R.string.FlexyHeaderSize)).setItems(style?new CharSequence[]{getString(R.string.FlexyHeaderSignature),getString(R.string.FlexyHeaderFusion),getString(R.string.FlexyHeaderClassic)}:new CharSequence[]{getString(R.string.FlexyHeaderNormal),getString(R.string.FlexyHeaderCompact)},(dialog,which)->{if(style)HeaderConfig.style(new int[]{0,2,1}[which]);else HeaderConfig.compact(which==1);changed(position);}).create());
        }
    }
    private final class OpacityCell extends LinearLayout implements Theme.Colorable {
        @Override public void updateColors(){label.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));slider.invalidate();}
        final TextView label; final SeekBar slider; boolean binding;
        OpacityCell(Context c){super(c);setOrientation(VERTICAL);setPadding(dp(20),dp(12),dp(20),dp(4));label=new TextView(c);label.setTextSize(16);label.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));addView(label,new LayoutParams(-1,-2));slider=new app.flexygram.settings.FlexySignatureSlider(c);slider.setMax(100);addView(slider,new LayoutParams(-1,dp(48)));slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onStartTrackingTouch(SeekBar b){b.getParent().requestDisallowInterceptTouchEvent(true);}public void onStopTrackingTouch(SeekBar b){b.getParent().requestDisallowInterceptTouchEvent(false);}public void onProgressChanged(SeekBar b,int value,boolean user){if(user&&!binding){HeaderConfig.opacity(value);if(preview!=null)preview.invalidate();}label(value);}});}
        void label(int value){String title=getString(R.string.FlexyHeaderOpacity)+" · "+value+" %";label.setText(title);slider.setContentDescription(title);}
        void bind(){binding=true;slider.setProgress(HeaderConfig.opacity());label(HeaderConfig.opacity());binding=false;}
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context c){super(c);}
        @Override public int getItemViewType(int p){return p==previewRow?111:p==opacityRow?112:TYPE_SETTINGS;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup p,int type){if(type==111){preview=new HeaderPreviewView(p.getContext());return new RecyclerListView.Holder(preview);}if(type==112)return new RecyclerListView.Holder(new OpacityCell(p.getContext()));return super.onCreateViewHolder(p,type);}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){if(p==previewRow){h.itemView.invalidate();return;}if(p==opacityRow){((OpacityCell)h.itemView).bind();return;}((TextSettingsCell)h.itemView).setTextAndValue(getString(p==styleRow?R.string.FlexyHeaderStyle:R.string.FlexyHeaderSize),getString(p==styleRow?(HeaderConfig.fusion()?R.string.FlexyHeaderFusion:HeaderConfig.signature()?R.string.FlexyHeaderSignature:R.string.FlexyHeaderClassic):(HeaderConfig.compact()?R.string.FlexyHeaderCompact:R.string.FlexyHeaderNormal)),true);}
        @Override public boolean isEnabled(RecyclerView.ViewHolder h){int p=h.getAdapterPosition();return p==styleRow||p==sizeRow;}
    }
}
