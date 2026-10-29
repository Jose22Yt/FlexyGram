/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;
import android.content.Context;
import android.view.View;
import android.widget.FrameLayout;
import java.util.ArrayList;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.*;
import static org.telegram.messenger.LocaleController.getString;

/** Reuses Telegram's native reorder list; all IDs are stable destinations, never pager indices. */
public final class LiquidNavigationTabsActivity extends BaseFragment {
    private UniversalRecyclerView list;
    private LiquidNavigationPreviewView preview;
    @Override public View createView(Context context){
        actionBar.setTitle(getString(R.string.FlexyLiquidNavTabs));
        actionBar.setBackButtonImage(R.drawable.ic_ab_back);
        actionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick(){public void onItemClick(int id){if(id==-1)finishFragment();}});
        actionBar.createMenu().addItem(1,R.drawable.msg_reset).setOnClickListener(v->{LiquidNavigationConfig.order(LiquidNavigationDestinations.defaults());if(preview!=null)preview.settingsChanged();list.adapter.update(true);});
        FrameLayout root=new FrameLayout(context);root.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));
        preview=new LiquidNavigationPreviewView(context);
        list=new UniversalRecyclerView(this,this::fill,this::click,(item,view,position,x,y)->false);
        list.setSections();list.allowReorder(true);list.setReorderClampToSection(true);
        list.listenReorder((section,rows)->{if(section!=0)return;int[] ids=new int[rows.size()];for(int i=0;i<ids.length;i++)ids[i]=rows.get(i).id-100;LiquidNavigationConfig.order(ids);preview.settingsChanged();});
        root.addView(list,LayoutHelper.createFrame(-1,-1));fragmentView=root;return root;
    }
    private void fill(ArrayList<UItem> rows,UniversalAdapter adapter){
        int[] order=LiquidNavigationConfig.order();
        rows.add(UItem.asCustom(preview));
        rows.add(UItem.asHeader(getString(R.string.FlexyLiquidNavVisible)));
        adapter.reorderSectionStart();
        for(int id:order)rows.add(UItem.asButton(100+id,R.drawable.msg_actions,getString(LiquidNavigationTabs.label(id))));
        adapter.reorderSectionEnd();
        rows.add(UItem.asShadow(getString(R.string.FlexyLiquidNavReorderHint)+"\n"+getString(R.string.FlexyLiquidNavLimit)));
        rows.add(UItem.asHeader(getString(R.string.FlexyLiquidNavAvailable)));
        for(int id=0;id<LiquidNavigationDestinations.COUNT;id++)if(!LiquidNavigationDestinations.contains(order,id))
            rows.add(UItem.asButton(200+id,R.drawable.msg_add,getString(LiquidNavigationTabs.label(id))));
    }
    private void click(UItem item,View view,int position,float x,float y){
        int[] order=LiquidNavigationConfig.order();
        if(item.id>=100 && item.id<100+LiquidNavigationDestinations.COUNT){
            int id=item.id-100;if(id==0 || order.length<=2)return;
            int[] next=new int[order.length-1];int n=0;for(int value:order)if(value!=id)next[n++]=value;
            LiquidNavigationConfig.order(next);
        }else if(item.id>=200 && item.id<200+LiquidNavigationDestinations.COUNT){
            if(order.length>=LiquidNavigationDestinations.MAX_VISIBLE)return;
            int[] next=java.util.Arrays.copyOf(order,order.length+1);next[order.length]=item.id-200;LiquidNavigationConfig.order(next);
        }else return;
        preview.settingsChanged();list.adapter.update(true);
    }
}
