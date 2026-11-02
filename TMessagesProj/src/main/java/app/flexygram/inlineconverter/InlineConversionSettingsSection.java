/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.inlineconverter;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import java.time.ZoneId;
import java.util.*;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextSettingsCell;
import tw.nekomimi.nekogram.ui.cells.HeaderCell;

/** Seven real controls, composed directly into the existing Chat scroll surface. */
public final class InlineConversionSettingsSection extends SignatureMatteSettingsActivity {
    private int header,enabled,currency,targetCurrency,time,targetZone,units,system;
    @Override protected String getActionBarTitle(){return text(R.string.InlineConversionTitle);}
    @Override protected String getKey(){return "exteraless_chats";}
    @Override public int getSearchGuid(){return 13_000_000;}
    @Override public int getSearchIcon(){return R.drawable.settings3_sliders;}
    @Override protected void updateRows(){super.updateRows();header=addRow("inlineConversionTitle");enabled=addRow(InlineConversionConfig.ENABLED);currency=addRow(InlineConversionConfig.CURRENCY);targetCurrency=addRow(InlineConversionConfig.TARGET_CURRENCY);time=addRow(InlineConversionConfig.TIME);targetZone=addRow(InlineConversionConfig.TARGET_ZONE);units=addRow(InlineConversionConfig.UNITS);system=addRow(InlineConversionConfig.SYSTEM);}
    private static String text(int id){return LocaleController.getString(id);}
    private String[] systems(){return new String[]{text(R.string.InlineConversionAuto),text(R.string.InlineConversionMetric),text(R.string.InlineConversionImperial)};}
    private void choose(String title,String[] values,int selected,java.util.function.IntConsumer action){
        if(getParentActivity()==null)return;
        // Native recycled choices: do not inflate hundreds of zone/currency rows at once.
        Context context=getParentActivity();
        org.telegram.ui.ActionBar.AlertDialog.Builder builder=new org.telegram.ui.ActionBar.AlertDialog.Builder(context,getResourceProvider());
        org.telegram.ui.Components.RecyclerListView choices=new org.telegram.ui.Components.RecyclerListView(context);
        androidx.recyclerview.widget.LinearLayoutManager manager=new androidx.recyclerview.widget.LinearLayoutManager(context);
        choices.setLayoutManager(manager);choices.setItemAnimator(null);
        choices.setAdapter(new org.telegram.ui.Components.RecyclerListView.SelectionAdapter(){
            @Override public int getItemCount(){return values.length;}
            @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return true;}
            @Override public RecyclerView.ViewHolder onCreateViewHolder(android.view.ViewGroup parent,int type){
                return new org.telegram.ui.Components.RecyclerListView.Holder(new org.telegram.ui.Cells.RadioColorCell(context,getResourceProvider()));
            }
            @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position){
                ((org.telegram.ui.Cells.RadioColorCell)holder.itemView).setTextAndValue(values[position],position==selected);
            }
        });
        choices.setOnItemClickListener((view,position)->{builder.getDismissRunnable().run();action.accept(position);});
        android.widget.FrameLayout frame=new android.widget.FrameLayout(context);
        frame.addView(choices,new android.widget.FrameLayout.LayoutParams(-1,org.telegram.messenger.AndroidUtilities.dp(Math.min(320,values.length*50))));
        builder.setTitle(title);builder.setView(frame);builder.setNegativeButton(text(R.string.Cancel),null);
        showDialog(builder.create());if(selected>=0)manager.scrollToPositionWithOffset(selected,0);
    }
    private void changed(String key,Object value,int row){InlineConversionConfig.set(key,value);if(listAdapter!=null)listAdapter.notifyItemChanged(row);}
    @Override protected void onItemClick(View v,int p,float x,float y){
        InlineConversionConfig.Snapshot c=InlineConversionConfig.get();
        if(p==enabled)changed(InlineConversionConfig.ENABLED,!c.enabled,p);
        else if(p==currency)changed(InlineConversionConfig.CURRENCY,!c.currency,p);
        else if(p==time)changed(InlineConversionConfig.TIME,!c.time,p);
        else if(p==units)changed(InlineConversionConfig.UNITS,!c.units,p);
        else if(p==system)choose(text(R.string.InlineConversionSystem),systems(),c.system,i->changed(InlineConversionConfig.SYSTEM,i,p));
        else if(p==targetCurrency){
            TreeSet<String> codes=new TreeSet<>();for(Currency coin:Currency.getAvailableCurrencies())if(!coin.getCurrencyCode().equals("XXX"))codes.add(coin.getCurrencyCode());
            String[] values=codes.toArray(new String[0]);choose(text(R.string.InlineConversionTargetCurrency),values,Arrays.asList(values).indexOf(c.targetCurrency),i->changed(InlineConversionConfig.TARGET_CURRENCY,values[i],p));
        }else if(p==targetZone){
            ArrayList<String> zones=new ArrayList<>(ZoneId.getAvailableZoneIds());Collections.sort(zones);zones.add(0,text(R.string.InlineConversionAuto));String[] values=zones.toArray(new String[0]);
            choose(text(R.string.InlineConversionTargetZone),values,c.targetZone.isEmpty()?0:zones.indexOf(c.targetZone),i->changed(InlineConversionConfig.TARGET_ZONE,i==0?"":values[i],p));
        }
    }
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int p){return p==header?TYPE_HEADER:p==targetCurrency||p==targetZone||p==system?TYPE_SETTINGS:TYPE_CHECK;}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){
            InlineConversionConfig.Snapshot c=InlineConversionConfig.get();
            if(p==header)((HeaderCell)h.itemView).setText(text(R.string.InlineConversionTitle));
            else if(p==targetCurrency||p==targetZone||p==system)((TextSettingsCell)h.itemView).setTextAndValue(text(p==targetCurrency?R.string.InlineConversionTargetCurrency:p==targetZone?R.string.InlineConversionTargetZone:R.string.InlineConversionSystem),p==targetCurrency?c.targetCurrency:p==targetZone?(c.targetZone.isEmpty()?text(R.string.InlineConversionAuto):c.targetZone):systems()[c.system],p!=system);
            else ((TextCheckCell)h.itemView).setTextAndValueAndCheck(text(p==enabled?R.string.InlineConversionEnable:p==currency?R.string.InlineConversionCurrency:p==time?R.string.InlineConversionTime:R.string.InlineConversionUnits),text(p==currency?R.string.InlineConversionCurrencyUnavailable:R.string.InlineConversionSettingInfo),p==enabled?c.enabled:p==currency?c.currency:p==time?c.time:c.units,false,true);
        }
    };}
}
