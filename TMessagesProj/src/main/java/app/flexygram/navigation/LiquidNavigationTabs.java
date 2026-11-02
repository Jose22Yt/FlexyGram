/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;
import android.content.Context;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.glass.GlassTabView;

/** Native tab views shared by the real bar and its live settings preview. */
public final class LiquidNavigationTabs {
    private LiquidNavigationTabs(){}
    public static int label(int id){
        switch(id){
            case 0:return R.string.MainTabsChats;case 1:return R.string.MainTabsContacts;
            case 2:return R.string.Settings;case 3:return R.string.MainTabsCalls;
            case 4:return R.string.MainTabsProfile;case 5:return R.string.Feed;
            case 6:return R.string.FlexyLiquidNavGroups;case 7:return R.string.FlexyLiquidNavChannels;
            case 8:return R.string.FlexyLiquidNavSaved;case 10:return R.string.Search;default:return R.string.FlexyContextMore;
        }
    }
    public static GlassTabView createPreview(Context context,int id){
        // Never binds a real account/avatar in the simulated scene.
        return id==LiquidNavigationDestinations.PROFILE?GlassTabView.createMainTab(context,null,GlassTabView.TabAnimation.NAV_PROFILE,label(id)):create(context,null,0,id);
    }
    public static GlassTabView create(Context context,Theme.ResourcesProvider provider,int account,int id){
        if(id==4)return GlassTabView.createAvatar(context,provider,account,label(id));
        GlassTabView.TabAnimation animation;
        switch(id){
            case 0:animation=GlassTabView.TabAnimation.CHATS;break;
            case 1:animation=GlassTabView.TabAnimation.CONTACTS;break;
            case 2:animation=GlassTabView.TabAnimation.SETTINGS;break;
            case 3:animation=GlassTabView.TabAnimation.CALLS;break;
            case 5:animation=GlassTabView.TabAnimation.FEED;break;
            case 6:animation=GlassTabView.TabAnimation.NAV_GROUPS;break;
            case 7:animation=GlassTabView.TabAnimation.NAV_CHANNELS;break;
            case 8:animation=GlassTabView.TabAnimation.NAV_SAVED;break;
            case 10:animation=GlassTabView.TabAnimation.NAV_SEARCH;break;
            default:animation=GlassTabView.TabAnimation.NAV_MORE;
        }
        return GlassTabView.createMainTab(context,provider,animation,label(id));
    }
}
