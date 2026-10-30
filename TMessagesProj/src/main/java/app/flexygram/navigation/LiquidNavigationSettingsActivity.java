/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;
import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.*;
import org.telegram.ui.Components.RecyclerListView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import app.flexygram.navigation.LiquidNavigationConfig.Parameter;

/** Compact root with focused native subpages; no recreated fragment while sliding. */
public final class LiquidNavigationSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int PREVIEW=111,SLIDER=112;
    private final int section;
    private int previewRow,tabsRow,enabledRow,labelsRow,resetRow,compactionRow;
    private final int[] sections=new int[4],parameterRows=new int[Parameter.values().length];
    private LiquidNavigationPreviewView preview;
    public LiquidNavigationSettingsActivity(){this(0);}
    private LiquidNavigationSettingsActivity(int section){this.section=section;}
    private int sectionLabel(int s){return s==1?R.string.FlexyLiquidNavDimensions:s==2?R.string.FlexyLiquidNavTabs:s==3?R.string.FlexyBottomSelection:R.string.FlexyLiquidNavCompaction;}
    @Override protected String getActionBarTitle(){return getString(section==0?R.string.FlexyLiquidNavTitle:sectionLabel(section));}
    private void parameters(Parameter... values){for(Parameter p:values)parameterRows[p.ordinal()]=addRow("flexyLiquid"+p.name());}
    @Override protected void updateRows(){
        super.updateRows();java.util.Arrays.fill(sections,-1);java.util.Arrays.fill(parameterRows,-1);
        tabsRow=enabledRow=labelsRow=resetRow=compactionRow=-1;
        previewRow=addRow();
        if(section==0){for(int i=0;i<4;i++)sections[i]=addRow("flexyBottomSection"+i);}
        else if(section==1){parameters(Parameter.HEIGHT,Parameter.WIDTH,Parameter.SIDE_GAP,Parameter.BOTTOM_GAP,Parameter.RADIUS,Parameter.INNER_MARGIN);}
        else if(section==2){tabsRow=addRow("flexyBottomTabs");labelsRow=addRow("flexyBottomLabels");parameters(Parameter.ICON,Parameter.LABEL_GAP);}
        else if(section==3){enabledRow=addRow("flexyBottomAnimation");parameters(Parameter.SPEED,Parameter.DAMPING);}
        else{compactionRow=addRow("flexyBottomCompaction");parameters(Parameter.COMPACT);resetRow=addRow("flexyBottomReset");}

    }
    @Override public void onResume(){super.onResume();if(preview!=null)preview.settingsChanged();if(listAdapter!=null)listAdapter.notifyDataSetChanged();}
    @Override protected BaseListAdapter createAdapter(Context c){return new Adapter(c);}
    private void changed(){if(preview!=null)preview.settingsChanged();listAdapter.notifyDataSetChanged();}
    private void choose(String title,String[] values,java.util.function.IntConsumer selected){showDialog(new org.telegram.ui.ActionBar.AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle(title).setItems(values,(dialog,which)->{selected.accept(which);changed();}).create());}
    @Override protected void onItemClick(View view,int pos,float x,float y){
        for(int i=0;i<sections.length;i++)if(pos==sections[i]){var next=new LiquidNavigationSettingsActivity(i+1);next.setCurrentAccount(currentAccount);presentFragment(next);return;}
        if(pos==tabsRow){LiquidNavigationTabsActivity editor=new LiquidNavigationTabsActivity();editor.setCurrentAccount(currentAccount);presentFragment(editor);return;}
        if(pos==compactionRow){choose(getString(R.string.FlexyLiquidNavCompaction),compactionNames(),LiquidNavigationConfig::compaction);return;}
        if(pos==enabledRow)LiquidNavigationConfig.animation(!LiquidNavigationConfig.animation());
        else if(pos==labelsRow)LiquidNavigationConfig.labels(!LiquidNavigationConfig.labels());
        else if(pos==resetRow)LiquidNavigationConfig.reset();else return;
        changed();
    }
    private String[] compactionNames(){return new String[]{getString(R.string.FlexyLiquidNavNormal),getString(R.string.FlexyLiquidNavCompact),getString(R.string.FlexyLiquidNavVeryCompact),getString(R.string.FlexyLiquidNavCustom)};}
    private Parameter parameter(int row){for(Parameter p:Parameter.values())if(parameterRows[p.ordinal()]==row)return p;return null;}
    private int label(Parameter p){
        switch(p){
            case HEIGHT:return R.string.FlexyLiquidNavHeight;case WIDTH:return R.string.FlexyLiquidNavWidth;
            case SIDE_GAP:return R.string.FlexyLiquidNavSideGap;case BOTTOM_GAP:return R.string.FlexyLiquidNavBottomGap;
            case RADIUS:return R.string.FlexyBottomRadius;case INNER_MARGIN:return R.string.FlexyLiquidNavInnerMargin;
            case ICON:return R.string.FlexyLiquidNavIcon;case LABEL_GAP:return R.string.FlexyLiquidNavLabelGap;
            case SPEED:return R.string.FlexyLiquidNavSpeed;case DAMPING:return R.string.FlexyBottomSmoothness;
            default:return R.string.FlexyLiquidNavCompact;
        }
    }

    private final class MotionSlider extends LinearLayout implements Theme.Colorable {
        final TextView title;final SeekBar seek;Parameter parameter;boolean binding;
        MotionSlider(Context c){super(c);setOrientation(VERTICAL);setPadding(dp(20),dp(10),dp(20),dp(5));title=new TextView(c);title.setTextSize(16);addView(title,new LayoutParams(-1,-2));seek=new app.flexygram.settings.FlexySignatureSlider(c);seek.setMax(100);addView(seek,new LayoutParams(-1,dp(48)));updateColors();
            seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
                public void onStartTrackingTouch(SeekBar b){if(b.getParent()!=null)b.getParent().requestDisallowInterceptTouchEvent(true);}
                public void onStopTrackingTouch(SeekBar b){if(b.getParent()!=null)b.getParent().requestDisallowInterceptTouchEvent(false);}
                public void onProgressChanged(SeekBar b,int v,boolean user){if(user&&!binding&&parameter!=null){LiquidNavigationConfig.value(parameter,v);if(parameter==Parameter.HEIGHT||parameter==Parameter.COMPACT)LiquidNavigationConfig.compaction(3);if(preview!=null){preview.settingsChanged();}}show(v);}
            });
        }
        public void updateColors(){title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));seek.invalidate();}
        void show(int v){if(parameter==null)return;String text=getString(label(parameter))+" · "+v+" %";title.setText(text);seek.setContentDescription(text);}
        void bind(Parameter p){binding=true;parameter=p;int v=LiquidNavigationConfig.value(p);seek.setProgress(v);show(v);binding=false;}
    }
    private boolean settingsRow(int p){if(p==tabsRow||p==resetRow||p==compactionRow)return true;for(int row:sections)if(row==p)return true;return false;}
    private final class Adapter extends MatteListAdapter {
        Adapter(Context c){super(c);}
        @Override public int getItemViewType(int p){return p==previewRow?PREVIEW:parameter(p)!=null?SLIDER:settingsRow(p)?TYPE_SETTINGS:TYPE_CHECK;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){if(type==PREVIEW){preview=new LiquidNavigationPreviewView(parent.getContext());return new RecyclerListView.Holder(preview);}if(type==SLIDER)return new RecyclerListView.Holder(new MotionSlider(parent.getContext()));return super.onCreateViewHolder(parent,type);}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){
            if(p==previewRow){preview.settingsChanged();return;}Parameter param=parameter(p);if(param!=null){((MotionSlider)h.itemView).bind(param);return;}
            if(settingsRow(p)){
                String text=p==tabsRow?getString(R.string.FlexyLiquidNavTabs):p==resetRow?getString(R.string.Reset):p==compactionRow?getString(R.string.FlexyLiquidNavCompaction)+" · "+compactionNames()[LiquidNavigationConfig.compaction()]:"";
                for(int i=0;i<sections.length;i++)if(p==sections[i])text=getString(sectionLabel(i+1));((TextSettingsCell)h.itemView).setText(text,true);return;
            }
            int label=p==enabledRow?R.string.FlexyBottomAnimation:R.string.FlexyLiquidNavLabels;
            boolean checked=p==enabledRow?LiquidNavigationConfig.animation():LiquidNavigationConfig.labels();
            ((TextCheckCell)h.itemView).setTextAndCheck(getString(label),checked,true);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder h){int p=h.getAdapterPosition();return settingsRow(p)||p==enabledRow||p==labelsRow;}
    }
}
