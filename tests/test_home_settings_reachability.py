"""Run the production top-menu builder: Settings cannot disappear with the bottom bar."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_settings_is_unconditional_in_both_home_overflows(tmp_path):
    host=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    dialogs=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    menu=method(host,'private void addChatsMenuItems(')
    # The standalone dialogs menu must not depend on the obsolete tab switches.
    assert 'if (MainTabsHelper.isCallsTabShown(currentAccount) || hideBottomNavigationBar)' not in dialogs
    standalone=dialogs[dialogs.index('// Always reachable, including when the configurable bottom bar'):]
    assert standalone.index('presentFragment(new SettingsActivity())') < standalone.index('if (proxyMenuSubItem')
    probe(tmp_path,{'Probe.java': '''import java.util.*;
public class Probe {
 static class View{}static class Bundle{void putInt(String k,int v){}void putLong(String k,long v){}}
 static class SettingsActivity{}static class DialogsActivity{DialogsActivity(Bundle b){}}static class ChatActivity{ChatActivity(Bundle b){}}static class BookmarkManagerActivity{}
 static class ItemOptions{Map<String,Runnable> actions=new HashMap<>();void add(int icon,String label,Runnable r){if(actions.put(label,r)!=null)throw new AssertionError("duplicate");}void addGap(){}void dismiss(){}}
 static class R{static class drawable{static int msg_settings_old,menu_recent,msg_archive,msg_saved,msg_fave;}static class string{static int Settings=1,RecentChats=2,ArchivedChats=3,SavedMessages=4,BookmarksManager=5;}}
 static class BackButtonMenuRecent{static void show(int a,Object o,View v){}}
 static class N{boolean bookmark;boolean Bool(){return bookmark;}}static class NaConfig{static NaConfig INSTANCE=new NaConfig();N n=new N();N getShowAddToBookmark(){return n;}}
 static class UserConfig{static UserConfig getInstance(int a){return new UserConfig();}long getClientUserId(){return 1;}}
 int currentAccount;int opens;boolean barVisible;int[] destinations;
 String getString(int id){return "label"+id;}void presentFragment(Object f){}void openFlexySettings(){opens++;}
 MENU
 public static void main(String[]args){Probe p=new Probe();
 for(boolean bar:new boolean[]{true,false})for(int[] order:new int[][]{{},{0},{0,1,2,4}})for(boolean bookmarks:new boolean[]{false,true}){
 p.barVisible=bar;p.destinations=order;NaConfig.INSTANCE.n.bookmark=bookmarks;
 ItemOptions o=new ItemOptions();p.addChatsMenuItems(o,new View());Runnable settings=o.actions.get(p.getString(R.string.Settings));
 if(settings==null)throw new AssertionError("stranded settings");int before=p.opens;settings.run();if(p.opens!=before+1)throw new AssertionError("wrong dispatch");
 }
 }}'''.replace('MENU',menu)})
