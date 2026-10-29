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
    private int previewRow,tabsRow,enabledRow,labelsRow,resetRow,profileRow,expansionRow,compactionRow,distributionRow,qualityRow;
    private final int[] sections=new int[4],parameterRows=new int[Parameter.values().length];
    private LiquidNavigationPreviewView preview;
    public LiquidNavigationSettingsActivity(){this(0);}
    private LiquidNavigationSettingsActivity(int section){this.section=section;}
    private int sectionLabel(int s){return s==1?R.string.FlexyLiquidNavMotion:s==2?R.string.FlexyLiquidNavLensAppearance:s==3?R.string.FlexyLiquidNavDimensions:R.string.FlexyLiquidNavPresets;}
    @Override protected String getActionBarTitle(){return getString(section==0?R.string.FlexyLiquidNavTitle:sectionLabel(section));}
    private void parameters(Parameter... values){for(Parameter p:values)parameterRows[p.ordinal()]=addRow("flexyLiquid"+p.name());}
    @Override protected void updateRows(){
        super.updateRows();java.util.Arrays.fill(sections,-1);java.util.Arrays.fill(parameterRows,-1);
        tabsRow=enabledRow=labelsRow=resetRow=profileRow=expansionRow=compactionRow=distributionRow=qualityRow=-1;
        previewRow=addRow();
        if(section==0){tabsRow=addRow("flexyLiquidTabs");for(int i=0;i<4;i++)sections[i]=addRow("flexyLiquidSection"+i);}
        else if(section==1){enabledRow=addRow("flexyLiquidEnabled");expansionRow=addRow("flexyLiquidExpansion");parameters(Parameter.EXPAND_X,Parameter.EXPAND_Y,Parameter.ELASTICITY,Parameter.DEFORMATION,Parameter.SPEED,Parameter.DAMPING,Parameter.REBOUND,Parameter.FOLLOW,Parameter.SETTLE);}
        else if(section==2){parameters(Parameter.LENS_SIZE,Parameter.LENS_HEIGHT,Parameter.OPACITY,Parameter.OUTLINE,Parameter.REFLECTION,Parameter.REFRACTION,Parameter.INTENSITY);qualityRow=addRow("flexyLiquidQuality");}
        else if(section==3){compactionRow=addRow("flexyLiquidCompaction");distributionRow=addRow("flexyLiquidDistribution");labelsRow=addRow("flexyLiquidLabels");parameters(Parameter.HEIGHT,Parameter.COMPACT,Parameter.WIDTH,Parameter.SPACING,Parameter.ICON,Parameter.LABEL_GAP,Parameter.INNER_MARGIN,Parameter.BOTTOM_GAP,Parameter.SIDE_GAP);}
        else{profileRow=addRow("flexyLiquidProfile");resetRow=addRow("flexyLiquidReset");}
    }
    @Override public void onResume(){super.onResume();if(preview!=null)preview.settingsChanged();if(listAdapter!=null)listAdapter.notifyDataSetChanged();}
    @Override protected BaseListAdapter createAdapter(Context c){return new Adapter(c);}
    private void changed(){if(preview!=null)preview.settingsChanged();listAdapter.notifyDataSetChanged();}
    private void choose(String title,String[] values,java.util.function.IntConsumer selected){showDialog(new org.telegram.ui.ActionBar.AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle(title).setItems(values,(dialog,which)->{selected.accept(which);changed();}).create());}
    @Override protected void onItemClick(View view,int pos,float x,float y){
        for(int i=0;i<sections.length;i++)if(pos==sections[i]){var next=new LiquidNavigationSettingsActivity(i+1);next.setCurrentAccount(currentAccount);presentFragment(next);return;}
        if(pos==tabsRow){LiquidNavigationTabsActivity editor=new LiquidNavigationTabsActivity();editor.setCurrentAccount(currentAccount);presentFragment(editor);return;}
        if(pos==profileRow){choose(getString(R.string.FlexyLiquidNavProfilePreset),new String[]{getString(R.string.FlexyLiquidNavFluid),"Liquid Signature",getString(R.string.FlexyLiquidNavMinimal)},which->LiquidNavigationConfig.profile(LiquidNavigationConfig.Profile.values()[which]));return;}
        if(pos==compactionRow){choose(getString(R.string.FlexyLiquidNavCompaction),compactionNames(),LiquidNavigationConfig::compaction);return;}
        if(pos==distributionRow){choose(getString(R.string.FlexyLiquidNavDistribution),new String[]{getString(R.string.FlexyLiquidNavScrollable),getString(R.string.FlexyLiquidNavOverflow)},LiquidNavigationConfig::distribution);return;}
        if(pos==enabledRow)LiquidNavigationConfig.enabled(!LiquidNavigationConfig.enabled());
        else if(pos==labelsRow)LiquidNavigationConfig.labels(!LiquidNavigationConfig.labels());
        else if(pos==expansionRow)LiquidNavigationConfig.expansion(!LiquidNavigationConfig.expansion());
        else if(pos==qualityRow)LiquidNavigationConfig.adaptiveQuality(!LiquidNavigationConfig.adaptiveQuality());
        else if(pos==resetRow)LiquidNavigationConfig.reset();else return;
        changed();
    }
    private String[] compactionNames(){return new String[]{getString(R.string.FlexyLiquidNavNormal),getString(R.string.FlexyLiquidNavCompact),getString(R.string.FlexyLiquidNavVeryCompact),getString(R.string.FlexyLiquidNavAutomatic),getString(R.string.FlexyLiquidNavCustom)};}
    private Parameter parameter(int row){for(Parameter p:Parameter.values())if(parameterRows[p.ordinal()]==row)return p;return null;}
    private int label(Parameter p){
        switch(p){
            case EXPAND_X:return R.string.FlexyLiquidNavExpandX;case EXPAND_Y:return R.string.FlexyLiquidNavExpandY;
            case LENS_HEIGHT:return R.string.FlexyLiquidNavLensHeight;case REFRACTION:return R.string.FlexyLiquidNavRefraction;
            case LABEL_GAP:return R.string.FlexyLiquidNavLabelGap;case INNER_MARGIN:return R.string.FlexyLiquidNavInnerMargin;
            case BOTTOM_GAP:return R.string.FlexyLiquidNavBottomGap;case SIDE_GAP:return R.string.FlexyLiquidNavSideGap;
            case REFLECTION:return R.string.FlexyLiquidNavReflection;case OUTLINE:return R.string.FlexyLiquidNavOutline;
            case INTENSITY:return R.string.FlexyLiquidNavIntensity;case LENS_SIZE:return R.string.FlexyLiquidNavLensSize;
            case OPACITY:return R.string.FlexyLiquidNavOpacity;case ELASTICITY:return R.string.FlexyLiquidNavElasticity;
            case DEFORMATION:return R.string.FlexyLiquidNavDeformation;case SPEED:return R.string.FlexyLiquidNavSpeed;
            case DAMPING:return R.string.FlexyLiquidNavDamping;case REBOUND:return R.string.FlexyLiquidNavRebound;
            case FOLLOW:return R.string.FlexyLiquidNavFollow;case SETTLE:return R.string.FlexyLiquidNavSettle;
            case HEIGHT:return R.string.FlexyLiquidNavHeight;case COMPACT:return R.string.FlexyLiquidNavCompact;
            case SPACING:return R.string.FlexyLiquidNavSpacing;case ICON:return R.string.FlexyLiquidNavIcon;default:return R.string.FlexyLiquidNavWidth;
        }
    }
    private final class MotionSlider extends LinearLayout implements Theme.Colorable {
        final TextView title;final SeekBar seek;Parameter parameter;boolean binding;
        MotionSlider(Context c){super(c);setOrientation(VERTICAL);setPadding(dp(20),dp(10),dp(20),dp(5));title=new TextView(c);title.setTextSize(16);addView(title,new LayoutParams(-1,-2));seek=new app.flexygram.settings.FlexySignatureSlider(c);seek.setMax(100);addView(seek,new LayoutParams(-1,dp(48)));updateColors();
            seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
                public void onStartTrackingTouch(SeekBar b){if(b.getParent()!=null)b.getParent().requestDisallowInterceptTouchEvent(true);}
                public void onStopTrackingTouch(SeekBar b){if(b.getParent()!=null)b.getParent().requestDisallowInterceptTouchEvent(false);}
                public void onProgressChanged(SeekBar b,int v,boolean user){if(user&&!binding&&parameter!=null){LiquidNavigationConfig.value(parameter,v);if(section==3)LiquidNavigationConfig.compaction(4);if(preview!=null){if(section==3)preview.settingsChanged();else preview.motionSettingsChanged();}}show(v);}
            });
        }
        public void updateColors(){title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));seek.invalidate();}
        void show(int v){if(parameter==null)return;String text=getString(label(parameter))+" · "+v+" %";title.setText(text);seek.setContentDescription(text);}
        void bind(Parameter p){binding=true;parameter=p;int v=LiquidNavigationConfig.value(p);seek.setProgress(v);show(v);binding=false;}
    }
    private boolean settingsRow(int p){if(p==tabsRow||p==resetRow||p==profileRow||p==compactionRow||p==distributionRow)return true;for(int row:sections)if(row==p)return true;return false;}
    private final class Adapter extends MatteListAdapter {
        Adapter(Context c){super(c);}
        @Override public int getItemViewType(int p){return p==previewRow?PREVIEW:parameter(p)!=null?SLIDER:settingsRow(p)?TYPE_SETTINGS:TYPE_CHECK;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){if(type==PREVIEW){preview=new LiquidNavigationPreviewView(parent.getContext());return new RecyclerListView.Holder(preview);}if(type==SLIDER)return new RecyclerListView.Holder(new MotionSlider(parent.getContext()));return super.onCreateViewHolder(parent,type);}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){
            if(p==previewRow){preview.settingsChanged();return;}Parameter param=parameter(p);if(param!=null){((MotionSlider)h.itemView).bind(param);return;}
            if(settingsRow(p)){
                String text=p==tabsRow?getString(R.string.FlexyLiquidNavTabs):p==profileRow?getString(R.string.FlexyLiquidNavProfilePreset):p==resetRow?getString(R.string.Reset):p==compactionRow?getString(R.string.FlexyLiquidNavCompaction)+" · "+compactionNames()[LiquidNavigationConfig.compaction()]:p==distributionRow?getString(LiquidNavigationConfig.distribution()==0?R.string.FlexyLiquidNavScrollable:R.string.FlexyLiquidNavOverflow):"";
                for(int i=0;i<sections.length;i++)if(p==sections[i])text=getString(sectionLabel(i+1));((TextSettingsCell)h.itemView).setText(text,true);return;
            }
            int label=p==enabledRow?R.string.FlexyLiquidNavEnabled:p==labelsRow?R.string.FlexyLiquidNavLabels:p==expansionRow?R.string.FlexyLiquidNavExpansion:R.string.FlexyLiquidNavAdaptiveQuality;
            boolean checked=p==enabledRow?LiquidNavigationConfig.enabled():p==labelsRow?LiquidNavigationConfig.labels():p==expansionRow?LiquidNavigationConfig.expansion():LiquidNavigationConfig.adaptiveQuality();
            ((TextCheckCell)h.itemView).setTextAndCheck(getString(label),checked,true);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder h){int p=h.getAdapterPosition();return settingsRow(p)||p==enabledRow||p==labelsRow||p==expansionRow||p==qualityRow;}
    }
}
