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
/** Specialized managers only. Simple preferences belong to the directly embedded native rows. */
final class Settings3LinksSection extends SignatureMatteSettingsActivity {
    private final String[] ids;private final int[] titles,icons;
    Settings3LinksSection(String[] ids,int[] titles,int[] icons){this.ids=ids;this.titles=titles;this.icons=icons;}
    @Override protected String getActionBarTitle(){return "";}
    @Override protected void updateRows(){super.updateRows();for(String id:ids)addRow(id);}
    @Override protected void onItemClick(View view,int p,float x,float y){
        BaseFragment f;
        switch(ids[p]){
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
        @Override public int getItemViewType(int p){return 240;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup p,int type){return new RecyclerListView.Holder(new Settings2Cell(p.getContext(),resourcesProvider));}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){((Settings2Cell)h.itemView).bind(LocaleController.getString(titles[p]),"",icons[p],0,p+1<ids.length);}
        @Override public boolean isEnabled(RecyclerView.ViewHolder h){return true;}
    };}
}
