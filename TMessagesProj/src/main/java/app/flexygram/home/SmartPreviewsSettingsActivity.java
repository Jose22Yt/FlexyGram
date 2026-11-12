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
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.AlertsCreator;
import org.telegram.ui.Components.RecyclerListView;

/** Compact selector; the demonstration view is created only when explicitly requested. */
public final class SmartPreviewsSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int PREVIEW=121;
    private static final int[] MODES={SignatureSmartPreviewPalette.ADAPTIVE,SignatureSmartPreviewPalette.MULTICOLOR,
            SignatureSmartPreviewPalette.MATTE,SignatureSmartPreviewPalette.OFF};
    private int styleRow,previewToggleRow,previewRow;
    private boolean showPreview;
    private SmartPreviewsDemoView preview;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.FlexySmartMiniPills);}
    @Override protected void updateRows(){
        super.updateRows();styleRow=addRow("flexySmartPreviews","flexySmartAdaptive","flexySmartMulticolor","flexySmartMatte","flexySmartOff");
        previewToggleRow=addRow("flexySmartPreviewDemo");previewRow=showPreview?addRow():-1;
    }
    @Override public void saveSelfArgs(android.os.Bundle args){super.saveSelfArgs(args);args.putBoolean("compactMiniPillPreview",showPreview);}
    @Override public void restoreSelfArgs(android.os.Bundle args){super.restoreSelfArgs(args);showPreview=args.getBoolean("compactMiniPillPreview",false);}
    @Override public int getSearchGuid(){return app.flexygram.settings.signature.SignatureSettingsRegistry.searchGuid("smart_previews");}
    private int label(int mode){return mode==SignatureSmartPreviewPalette.ADAPTIVE?R.string.FlexySmartPreviewAdaptive:
            mode==SignatureSmartPreviewPalette.MULTICOLOR?R.string.FlexySmartPreviewMulticolor:
            mode==SignatureSmartPreviewPalette.MATTE?R.string.FlexySmartPreviewMatte:R.string.FlexySmartPreviewOff;}
    @Override protected BaseListAdapter createAdapter(Context c){return new Adapter(c);}
    @Override protected void onItemClick(View view,int position,float x,float y){
        if(position==previewToggleRow){
            showPreview=!showPreview;preview=null;updateRows();listAdapter.notifyDataSetChanged();return;
        }
        if(position!=styleRow||getParentActivity()==null)return;
        String[] choices=new String[MODES.length];int selected=0;
        for(int i=0;i<MODES.length;i++){choices[i]=LocaleController.getString(label(MODES[i]));if(MODES[i]==SignatureSmartPreviews.mode())selected=i;}
        showDialog(AlertsCreator.createSingleChoiceDialog(getParentActivity(),choices,getActionBarTitle(),selected,(dialog,which)->{
                    int old=SignatureSmartPreviews.mode(),next=MODES[which];
                    if(old!=next){SignatureSmartPreviews.setMode(next);listAdapter.notifyItemChanged(styleRow,PARTIAL);if(preview!=null)preview.styleChanged(old,next);}
                }));
    }
    @Override public ArrayList<ThemeDescription> getThemeDescriptions(){
        ArrayList<ThemeDescription> colors=super.getThemeDescriptions();
        colors.add(new ThemeDescription(listView,0,new Class[]{SmartPreviewsDemoView.class},null,null,null,()->{if(preview!=null)preview.updateColors();},Theme.key_windowBackgroundWhite));
        return colors;
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context c){super(c);}
        @Override public int getItemViewType(int position){return previewRow>=0&&position==previewRow?PREVIEW:TYPE_SETTINGS;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){
            if(type==PREVIEW)return new RecyclerListView.Holder(new SmartPreviewsDemoView(parent.getContext(),resourcesProvider));
            return super.onCreateViewHolder(parent,type);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            if(position==previewRow&&previewRow>=0){preview=(SmartPreviewsDemoView)holder.itemView;preview.updateColors();}
            else if(position==styleRow)((TextSettingsCell)holder.itemView).setTextAndValue(getActionBarTitle(),LocaleController.getString(label(SignatureSmartPreviews.mode())),true);
            else ((TextSettingsCell)holder.itemView).setTextAndValue(LocaleController.getString(showPreview?R.string.CompactHidePreview:R.string.CompactPreview),"",false);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){int p=settingsRowPosition(holder);return p==styleRow||p==previewToggleRow;}
    }
}
