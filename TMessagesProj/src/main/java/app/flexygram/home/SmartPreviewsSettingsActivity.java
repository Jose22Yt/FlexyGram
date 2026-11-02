/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import java.util.ArrayList;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.ActionBar.ThemeDescription;
import org.telegram.ui.Cells.TextRadioCell;
import org.telegram.ui.Components.RecyclerListView;

/** Embedded by Home in the same native scrolling list; legacy/search routes remain valid. */
public final class SmartPreviewsSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int PREVIEW=121;
    private static final int[] MODES={SignatureSmartPreviewPalette.ADAPTIVE,SignatureSmartPreviewPalette.MULTICOLOR,
            SignatureSmartPreviewPalette.MATTE,SignatureSmartPreviewPalette.OFF};
    private int headerRow,firstStyleRow,previewRow;
    private SmartPreviewsDemoView preview;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.FlexySmartMiniPills);}
    @Override protected void updateRows(){super.updateRows();headerRow=addRow("flexySmartPreviews");firstStyleRow=addRow("flexySmartAdaptive");addRow("flexySmartMulticolor");addRow("flexySmartMatte");addRow("flexySmartOff");previewRow=addRow();}
    @Override public int getSearchGuid(){return app.flexygram.settings.signature.SignatureSettingsRegistry.searchGuid("smart_previews");}
    private int label(int mode){return mode==SignatureSmartPreviewPalette.ADAPTIVE?R.string.FlexySmartPreviewAdaptive:
            mode==SignatureSmartPreviewPalette.MULTICOLOR?R.string.FlexySmartPreviewMulticolor:
            mode==SignatureSmartPreviewPalette.MATTE?R.string.FlexySmartPreviewMatte:R.string.FlexySmartPreviewOff;}
    @Override protected BaseListAdapter createAdapter(Context c){return new Adapter(c);}
    @Override protected void onItemClick(View view,int position,float x,float y){
        int index=position-firstStyleRow;if(index<0||index>=MODES.length)return;
        int old=SignatureSmartPreviews.mode(),next=MODES[index];if(old==next)return;
        SignatureSmartPreviews.setMode(next);
        for(int i=0;i<MODES.length;i++)if(MODES[i]==old||MODES[i]==next)listAdapter.notifyItemChanged(firstStyleRow+i,PARTIAL);
        if(preview!=null)preview.styleChanged(old,next);
    }
    @Override public ArrayList<ThemeDescription> getThemeDescriptions(){
        ArrayList<ThemeDescription> colors=super.getThemeDescriptions();
        colors.add(new ThemeDescription(listView,0,new Class[]{SmartPreviewsDemoView.class},null,null,null,()->{if(preview!=null)preview.updateColors();},Theme.key_windowBackgroundWhite));
        return colors;
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context c){super(c);}
        @Override public int getItemViewType(int position){return position==headerRow?TYPE_HEADER:position==previewRow?PREVIEW:TYPE_RADIO;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){
            if(type==PREVIEW){preview=new SmartPreviewsDemoView(parent.getContext(),resourcesProvider);return new RecyclerListView.Holder(preview);}
            return super.onCreateViewHolder(parent,type);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            if(position==headerRow)((tw.nekomimi.nekogram.ui.cells.HeaderCell)holder.itemView).setText(getActionBarTitle());
            else if(position==previewRow)holder.itemView.invalidate();
            else {int mode=MODES[position-firstStyleRow];((TextRadioCell)holder.itemView).setTextAndCheck(LocaleController.getString(label(mode)),SignatureSmartPreviews.mode()==mode,position<firstStyleRow+3);}
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){int p=settingsRowPosition(holder);return p>=firstStyleRow&&p<firstStyleRow+MODES.length;}
    }
}
