/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.Components.RecyclerListView;
/** Native navigation rows and section headings. No editor is created during binding. */
final class Settings3LinksSection extends SignatureMatteSettingsActivity {
    private final String[] ids;private final int[] titles,icons;
    Settings3LinksSection(String[] ids,int[] titles,int[] icons){this.ids=ids;this.titles=titles;this.icons=icons;}
    @Override protected String getActionBarTitle(){return "";}
    @Override protected void updateRows(){super.updateRows();for(String id:ids)addRow(id);}
    @Override protected void onItemClick(View view,int p,float x,float y){
        if(ids[p].startsWith("#"))return;
        if(ids[p].startsWith("section:")){
            String[] target=ids[p].split(":");
            presentFragment(new SignatureDirectSettingsActivity(target[1],target[2]));return;
        }
        BaseFragment f;
        switch(ids[p]){
            case "composer_style":f=new ConversationStyleSettingsActivity(false);break;
            case "header_style":f=new ConversationStyleSettingsActivity(true);break;
            case "bubble_style":f=new app.flexygram.bubbles.BubbleSettingsActivity();break;
            case "plugins":f=new app.exteraless.plugins.ui.PluginsActivity();break;
            case "ai":f=new app.exteraless.ai.ui.AiSettingsActivity();break;
            case "translator":f=new tw.nekomimi.nekogram.settings.NekoTranslatorSettingsActivity();break;
            case "pillstack":f=new app.exteraless.pillstack.PillStackSettingsActivity();break;
            case "navigationEditor":f=new app.exteraless.settings.OpenExteraAppNavigationActivity(true);break;
            case "context":f=new app.flexygram.bubbles.interaction.BubbleInteractionSettingsActivity();break;
            case "icon_packs":f=new app.exteraless.icons.IconPacksActivity();break;
            case "emoji":f=new tw.nekomimi.nekogram.settings.NekoEmojiSettingsActivity();break;
            case "animations":f=new app.flexygram.bubbles.deletion.MessageAnimationsActivity(false);break;
            case "passcode":f=new tw.nekomimi.nekogram.settings.NekoPasscodeSettingsActivity();break;
            case "cloud":f=new app.exteraless.settings.OpenExteraCloudActivity();break;
            default:throw new IllegalArgumentException("Unknown specialized manager");
        }
        presentFragment(f);
    }
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int p){return ids[p].startsWith("#")?TYPE_HEADER:240;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup p,int type){if(type==TYPE_HEADER)return super.onCreateViewHolder(p,type);return new RecyclerListView.Holder(new Settings2Cell(p.getContext(),resourcesProvider,true));}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){if(ids[p].startsWith("#")){((tw.nekomimi.nekogram.ui.cells.HeaderCell)h.itemView).setText(LocaleController.getString(titles[p]));return;}((Settings2Cell)h.itemView).bind(LocaleController.getString(titles[p]),"",icons[p],0,p+1<ids.length);}
        @Override public boolean isEnabled(RecyclerView.ViewHolder h){int p=settingsRowPosition(h);return p>=0&&p<ids.length&&!ids[p].startsWith("#");}
    };}
}
