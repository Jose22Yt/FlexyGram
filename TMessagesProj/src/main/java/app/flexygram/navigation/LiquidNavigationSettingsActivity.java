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

public final class LiquidNavigationSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int PREVIEW=111,SLIDER=112;
    private int previewRow,tabsRow,enabledRow,labelsRow,resetRow;
    private int indicatorHeader,motionHeader,designHeader;
    private final int[] parameterRows=new int[Parameter.values().length];
    private LiquidNavigationPreviewView preview;
    @Override protected String getActionBarTitle(){return getString(R.string.FlexyLiquidNavTitle);}
    @Override protected void updateRows(){
        super.updateRows();previewRow=addRow();tabsRow=addRow("flexyLiquidTabs");
        indicatorHeader=addRow();enabledRow=addRow("flexyLiquidEnabled");
        for(Parameter p:new Parameter[]{Parameter.OPACITY,Parameter.ELASTICITY,Parameter.DEFORMATION})parameterRows[p.ordinal()]=addRow("flexyLiquid"+p.name());
        motionHeader=addRow();
        for(Parameter p:new Parameter[]{Parameter.SPEED,Parameter.DAMPING,Parameter.REBOUND,Parameter.FOLLOW,Parameter.SETTLE})parameterRows[p.ordinal()]=addRow("flexyLiquid"+p.name());
        designHeader=addRow();
        for(Parameter p:new Parameter[]{Parameter.HEIGHT,Parameter.COMPACT,Parameter.SPACING,Parameter.ICON,Parameter.WIDTH})parameterRows[p.ordinal()]=addRow("flexyLiquid"+p.name());
        labelsRow=addRow("flexyLiquidLabels");resetRow=addRow("flexyLiquidReset");
    }
    @Override public void onResume(){super.onResume();if(preview!=null)preview.settingsChanged();if(listAdapter!=null)listAdapter.notifyDataSetChanged();}
    @Override protected BaseListAdapter createAdapter(Context c){return new Adapter(c);}
    @Override protected void onItemClick(View view,int pos,float x,float y){
        if(pos==tabsRow){LiquidNavigationTabsActivity editor=new LiquidNavigationTabsActivity();editor.setCurrentAccount(currentAccount);presentFragment(editor);return;}
        if(pos==enabledRow)LiquidNavigationConfig.enabled(!LiquidNavigationConfig.enabled());
        else if(pos==labelsRow)LiquidNavigationConfig.labels(!LiquidNavigationConfig.labels());
        else if(pos==resetRow)LiquidNavigationConfig.reset();else return;
        if(preview!=null)preview.settingsChanged();listAdapter.notifyDataSetChanged();
    }
    private Parameter parameter(int row){for(Parameter p:Parameter.values())if(parameterRows[p.ordinal()]==row)return p;return null;}
    private int label(Parameter p){
        switch(p){
            case OPACITY:return R.string.FlexyLiquidNavOpacity;case ELASTICITY:return R.string.FlexyLiquidNavElasticity;
            case DEFORMATION:return R.string.FlexyLiquidNavDeformation;case SPEED:return R.string.FlexyLiquidNavSpeed;
            case DAMPING:return R.string.FlexyLiquidNavDamping;case REBOUND:return R.string.FlexyLiquidNavRebound;
            case FOLLOW:return R.string.FlexyLiquidNavFollow;case SETTLE:return R.string.FlexyLiquidNavSettle;
            case HEIGHT:return R.string.FlexyLiquidNavHeight;case COMPACT:return R.string.FlexyLiquidNavCompact;
            case SPACING:return R.string.FlexyLiquidNavSpacing;case ICON:return R.string.FlexyLiquidNavIcon;
            default:return R.string.FlexyLiquidNavWidth;
        }
    }
    private final class MotionSlider extends LinearLayout implements Theme.Colorable {
        final TextView title;final SeekBar seek;Parameter parameter;boolean binding;
        MotionSlider(Context c){super(c);setOrientation(VERTICAL);setPadding(dp(20),dp(10),dp(20),dp(5));
            title=new TextView(c);title.setTextSize(16);addView(title,new LayoutParams(-1,-2));
            seek=new app.flexygram.settings.FlexySignatureSlider(c);seek.setMax(100);addView(seek,new LayoutParams(-1,dp(48)));updateColors();
            seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
                public void onStartTrackingTouch(SeekBar b){if(b.getParent()!=null)b.getParent().requestDisallowInterceptTouchEvent(true);}
                public void onStopTrackingTouch(SeekBar b){if(b.getParent()!=null)b.getParent().requestDisallowInterceptTouchEvent(false);}
                public void onProgressChanged(SeekBar b,int v,boolean user){if(user&&!binding&&parameter!=null){LiquidNavigationConfig.value(parameter,v);if(preview!=null){if(parameter.ordinal()<Parameter.HEIGHT.ordinal())preview.motionSettingsChanged();else preview.settingsChanged();}}show(v);}
            });
        }
        public void updateColors(){title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));seek.invalidate();}
        void show(int v){if(parameter==null)return;String value=parameter==Parameter.HEIGHT?LiquidNavigationConfig.heightDp()+" dp":parameter==Parameter.ICON?LiquidNavigationConfig.iconDp()+" dp":parameter==Parameter.SPACING?LiquidNavigationConfig.spacingDp()+" dp":v+" %";String text=getString(label(parameter))+" · "+value;title.setText(text);seek.setContentDescription(text);}
        void bind(Parameter p){binding=true;parameter=p;int v=LiquidNavigationConfig.value(p);seek.setProgress(v);show(v);binding=false;}
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context c){super(c);}
        @Override public int getItemViewType(int p){if(p==previewRow)return PREVIEW;if(parameter(p)!=null)return SLIDER;if(p==indicatorHeader||p==motionHeader||p==designHeader)return TYPE_HEADER;if(p==tabsRow||p==resetRow)return TYPE_SETTINGS;return TYPE_CHECK;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){
            if(type==PREVIEW){preview=new LiquidNavigationPreviewView(parent.getContext());return new RecyclerListView.Holder(preview);}
            if(type==SLIDER)return new RecyclerListView.Holder(new MotionSlider(parent.getContext()));return super.onCreateViewHolder(parent,type);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){
            if(p==previewRow){preview.settingsChanged();return;}Parameter param=parameter(p);if(param!=null){((MotionSlider)h.itemView).bind(param);return;}
            if(p==indicatorHeader||p==motionHeader||p==designHeader){((tw.nekomimi.nekogram.ui.cells.HeaderCell)h.itemView).setText(getString(p==indicatorHeader?R.string.FlexyLiquidNavIndicator:p==motionHeader?R.string.FlexyLiquidNavMotion:R.string.FlexyLiquidNavDesign));return;}
            if(p==tabsRow||p==resetRow){((TextSettingsCell)h.itemView).setText(getString(p==tabsRow?R.string.FlexyLiquidNavTabs:R.string.Reset),true);return;}
            ((TextCheckCell)h.itemView).setTextAndCheck(getString(p==enabledRow?R.string.FlexyLiquidNavEnabled:R.string.FlexyLiquidNavLabels),p==enabledRow?LiquidNavigationConfig.enabled():LiquidNavigationConfig.labels(),true);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder h){int p=h.getAdapterPosition();return p==tabsRow||p==enabledRow||p==labelsRow||p==resetRow;}
    }
}
