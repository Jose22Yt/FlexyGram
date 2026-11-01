/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;
import android.content.Context;
import android.os.Bundle;
import android.view.*;
import android.widget.*;
import android.text.*;
import android.text.style.*;
import androidx.recyclerview.widget.RecyclerView;
import java.util.*;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.*;
import org.telegram.ui.ActionBar.*;
import org.telegram.ui.Components.RecyclerListView;
/** Root and small category hubs. Only visible native controls are created at the destination. */
public class SignatureSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int ENTRY=210,TEXT=211;
    private String page="root",query="";
    private final ArrayList<Object> rows=new ArrayList<>();
    public SignatureSettingsActivity(){}
    public SignatureSettingsActivity(String page){this.page=page;}
    @Override protected String getActionBarTitle(){return "root".equals(page)?LocaleController.getString(R.string.FlexyBrandName):LocaleController.getString(SignatureSettingsRegistry.entry(page).title);}
    @Override protected void updateRows(){
        super.updateRows();rows.clear();
        if(!query.isEmpty()){
            for(SignatureSettingsRegistry.Entry e:SignatureSettingsRegistry.all())if(SignatureSettingsRegistry.visible(e.id)&&
                    (LocaleController.getString(e.title)+" "+LocaleController.getString(e.description)).toLowerCase(Locale.ROOT).contains(query))rows.add(e);
        }else{
            if("root".equals(page))rows.add(R.string.Settings2Title);
            int previous=0;
            for(SignatureSettingsRegistry.Entry e:SignatureSettingsRegistry.children(page)){if(previous!=e.group){rows.add(e.group);previous=e.group;}rows.add(e);}
            if("root".equals(page)){rows.add(0);rows.add("about");}
        }
        rowCount=rows.size();
    }
    @Override public View createView(Context context){
        View v=super.createView(context);actionBar.centerTitle();listView.setSections(AndroidUtilities.dp(16),AndroidUtilities.dp(20),true);listView.setItemAnimator(null);
        if("root".equals(page))actionBar.createMenu().addItem(7,R.drawable.ic_ab_search_solar).setIsSearchField(true).setActionBarMenuItemSearchListener(new ActionBarMenuItem.ActionBarMenuItemSearchListener(){
            @Override public void onTextChanged(EditText field){query=field.getText().toString().trim().toLowerCase(Locale.ROOT);updateRows();listAdapter.notifyDataSetChanged();}
            @Override public void onSearchCollapse(){query="";updateRows();listAdapter.notifyDataSetChanged();}
        }).setSearchFieldHint(LocaleController.getString(R.string.Settings2Search));
        return v;
    }
    @Override protected BaseListAdapter createAdapter(Context c){return new Adapter(c);}
    @Override protected void onItemClick(View v,int p,float x,float y){
        if(p<0||p>=rows.size())return;Object row=rows.get(p);
        if(row instanceof SignatureSettingsRegistry.Entry)presentFragment(SignatureSettingsRegistry.open(((SignatureSettingsRegistry.Entry)row).id));
        else if("about".equals(row))showDialog(new AlertDialog.Builder(getParentActivity(),resourcesProvider)
            .setTitle(LocaleController.getString(R.string.FlexySettingsAbout))
            .setMessage(LocaleController.getString(R.string.FlexySettingsAboutBody)+"\n\n"+LocaleController.getString(R.string.FlexySettingsCreditsBody))
            .setPositiveButton(LocaleController.getString(R.string.FlexySettingsLicenseAction),(d,w)->org.telegram.messenger.browser.Browser.openUrl(getParentActivity(),"https://github.com/Jose22Yt/FlexyGram/blob/main/LICENSE"))
            .setNeutralButton(LocaleController.getString(R.string.OpenExteraSource),(d,w)->org.telegram.messenger.browser.Browser.openUrl(getParentActivity(),"https://github.com/Jose22Yt/FlexyGram"))
            .setNegativeButton(LocaleController.getString(R.string.OK),null).create());
    }
    @Override public void saveSelfArgs(Bundle args){super.saveSelfArgs(args);args.putString("settings2Page",page);}
    @Override public void restoreSelfArgs(Bundle args){super.restoreSelfArgs(args);page=args.getString("settings2Page","root");}
    private final class Adapter extends MatteListAdapter {
        Adapter(Context c){super(c);}
        @Override public int getItemViewType(int p){return rows.get(p) instanceof Integer?TEXT:ENTRY;}
        @Override protected boolean isSectionContent(int type){return type==ENTRY;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){
            View v;if(type==ENTRY)v=new Settings2Cell(parent.getContext(),resourcesProvider);
            else{TextView t=new TextView(parent.getContext());t.setTag(RecyclerListView.TAG_NOT_SECTION);t.setPadding(AndroidUtilities.dp(22),AndroidUtilities.dp(24),AndroidUtilities.dp(22),AndroidUtilities.dp(10));t.setTextSize(13);t.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);v=t;}
            v.setLayoutParams(new RecyclerView.LayoutParams(-1,-2));return new RecyclerListView.Holder(v);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int p,boolean partial){
            Object item=rows.get(p);
            if(item instanceof Integer){TextView t=(TextView)holder.itemView;int id=(Integer)item;t.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteGrayText2));t.setTextSize(id==R.string.Settings2Title?32:13);t.setTypeface(id==R.string.Settings2Title?AndroidUtilities.bold():null);
                t.setText(id==0?"":id==R.string.Settings2Title?LocaleController.getString(id)+"\n"+LocaleController.getString(R.string.Settings2Subtitle):LocaleController.getString(id));
                if(id==R.string.Settings2Title){SpannableString span=new SpannableString(t.getText());int n=span.toString().indexOf('\n');t.setTypeface(android.graphics.Typeface.DEFAULT);span.setSpan(new StyleSpan(android.graphics.Typeface.BOLD),0,n,0);span.setSpan(new ForegroundColorSpan(getThemedColor(Theme.key_windowBackgroundWhiteGrayText2)),n+1,span.length(),0);span.setSpan(new AbsoluteSizeSpan(14,true),n+1,span.length(),0);span.setSpan(new StyleSpan(android.graphics.Typeface.NORMAL),n+1,span.length(),0);t.setText(span);t.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));}
            }else{
                Settings2Cell c=(Settings2Cell)holder.itemView;boolean divider=p+1<rows.size()&&!(rows.get(p+1)instanceof Integer);
                if(item instanceof SignatureSettingsRegistry.Entry){var e=(SignatureSettingsRegistry.Entry)item;c.bind(LocaleController.getString(e.title),LocaleController.getString(e.description),e.icon,e.color,divider);}
                else c.bind(LocaleController.getString(R.string.FlexyBrandName),LocaleController.getString(R.string.Settings2About),R.drawable.msg_info,0xFF168BEA,false);
            }
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return holder.getItemViewType()==ENTRY;}
    }
}
