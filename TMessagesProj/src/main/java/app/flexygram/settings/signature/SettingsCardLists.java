package app.flexygram.settings.signature;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.RecyclerListView;
import org.telegram.ui.Components.UniversalAdapter;
import org.telegram.ui.Components.UniversalRecyclerView;
import org.telegram.ui.Components.UItem;

/** Same cards for plugin/permission/navigation settings that use Telegram's UniversalAdapter. */
public final class SettingsCardLists {
    private SettingsCardLists() {}
    public static void apply(UniversalRecyclerView list, Theme.ResourcesProvider provider) {
        SettingsCardBackground background=new SettingsCardBackground();background.setResourcesProvider(provider);
        list.setForceSegmentedSettingsCards(true);
        list.setSections(view -> {
            if(view.getParent()!=list)return false;
            var holder=list.getChildViewHolder(view);
            int type=holder.getItemViewType();
            if(UniversalAdapter.isShadow(type)||UniversalAdapter.isHeader(type))return false;
            int position=holder.getAdapterPosition();
            if(position==RecyclerListView.NO_POSITION)return !Boolean.TRUE.equals(view.getTag(R.id.transparent_tag));
            UItem item=list.adapter.getItem(position);return item==null||!item.transparent;
        }, type -> !UniversalAdapter.isShadow(type)&&!UniversalAdapter.isHeader(type),
            AndroidUtilities.dp(SettingsCardStyle.INSET),AndroidUtilities.dp(SettingsCardStyle.OUTER_RADIUS),
            background::draw,false);
        list.adapter.setApplyBackground(false);
    }
}
