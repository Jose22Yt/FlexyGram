package app.flexygram.navigation;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.Theme;
import tw.nekomimi.nekogram.ui.cells.HeaderCell;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.RecyclerListView;

import java.util.ArrayList;

public final class BottomTabsSettingsActivity extends SignatureMatteSettingsActivity {

    private int previewRow;
    private DockPreviewCell previewCell;
    private int tabsHeaderRow, showTabsRow;
    private int appearanceHeaderRow, floatingDockRow, showTitlesRow;
    private int actionsHeaderRow, doubleTapChatsRow, doubleTapProfileRow, alwaysSearchChatsRow;
    private int orderHeaderRow;
    private int orderStartRow, orderEndRow;

    private final ArrayList<Integer> currentDestinations = new ArrayList<>();
    private final ArrayList<Integer> availableDestinations = new ArrayList<>();

    @Override
    protected void updateRows() {
        super.updateRows();
        LiquidNavigationConfig.load();

        currentDestinations.clear();
        for (int id : LiquidNavigationConfig.order()) {
            if (!currentDestinations.contains(id)) {
                currentDestinations.add(id);
            }
        }
        availableDestinations.clear();
        for (int id = 0; id < LiquidNavigationDestinations.COUNT; id++) {
            if (!currentDestinations.contains(id)) {
                availableDestinations.add(id);
            }
        }

        previewRow = addRow();

        tabsHeaderRow = addRow("FlexyBottomTabsSectionTabs");
        showTabsRow = addRow("flexyBottomTabsShow");

        appearanceHeaderRow = addRow("FlexyBottomTabsSectionAppearance");
        floatingDockRow = addRow("flexyBottomTabsFloatingDock");
        showTitlesRow = addRow("flexyBottomTabsShowTitles");

        actionsHeaderRow = addRow("FlexyBottomTabsSectionActions");
        doubleTapChatsRow = addRow("flexyBottomTabsDoubleTapChats");
        doubleTapProfileRow = addRow("flexyBottomTabsDoubleTapProfile");
        alwaysSearchChatsRow = addRow("flexyBottomTabsAlwaysSearchChats");

        orderHeaderRow = addRow("FlexyBottomTabsSectionOrder");
        orderStartRow = rowCount;
        for (int i = 0; i < currentDestinations.size(); i++) {
            addRow("flexy_dest_" + currentDestinations.get(i));
        }
        orderEndRow = rowCount;
    }

    @Override
    protected String getActionBarTitle() {
        return getString(R.string.FlexyBottomTabsTitle);
    }

    @Override
    protected BaseListAdapter createAdapter(Context c) {
        return new Adapter(c);
    }

    private void saveOrder() {
        int[] arr = new int[currentDestinations.size()];
        for (int i = 0; i < arr.length; i++) arr[i] = currentDestinations.get(i);
        LiquidNavigationConfig.setOrder(arr);
        updateRows();
        listAdapter.notifyDataSetChanged();
        if (previewCell != null) {
            previewCell.update();
        }
    }

    @Override
    protected void onItemClick(View v, int position, float x, float y) {
        if (position == showTabsRow) {
            LiquidNavigationConfig.setEnabled(!LiquidNavigationConfig.isEnabled());
            listAdapter.notifyItemChanged(showTabsRow);
            if (previewCell != null) previewCell.update();
        } else if (position == floatingDockRow) {
            LiquidNavigationConfig.setFloatingDock(!LiquidNavigationConfig.isFloatingDock());
            listAdapter.notifyItemChanged(floatingDockRow);
            if (previewCell != null) previewCell.update();
        } else if (position == showTitlesRow) {
            LiquidNavigationConfig.setShowTitles(!LiquidNavigationConfig.showTitles());
            listAdapter.notifyItemChanged(showTitlesRow);
            if (previewCell != null) previewCell.update();
        } else if (position == doubleTapChatsRow) {
            LiquidNavigationConfig.setDoubleTapChats(!LiquidNavigationConfig.doubleTapChats());
            listAdapter.notifyItemChanged(doubleTapChatsRow);
        } else if (position == doubleTapProfileRow) {
            LiquidNavigationConfig.setDoubleTapProfile(!LiquidNavigationConfig.doubleTapProfile());
            listAdapter.notifyItemChanged(doubleTapProfileRow);
        } else if (position == alwaysSearchChatsRow) {
            LiquidNavigationConfig.setAlwaysSearchChats(!LiquidNavigationConfig.alwaysSearchChats());
            listAdapter.notifyItemChanged(alwaysSearchChatsRow);
        } else if (position >= orderStartRow && position < orderEndRow) {
            int index = position - orderStartRow;
            if (index >= 0 && index < currentDestinations.size()) {
                showTabActionDialog(index);
            }
        }
    }

    private void showTabActionDialog(int index) {
        int id = currentDestinations.get(index);
        String title = getString(LiquidNavigationTabs.label(id));
        ArrayList<CharSequence> items = new ArrayList<>();
        ArrayList<Runnable> actions = new ArrayList<>();

        if (index > 0) {
            items.add("▲ Mover hacia la izquierda / arriba");
            actions.add(() -> {
                int temp = currentDestinations.get(index - 1);
                currentDestinations.set(index - 1, id);
                currentDestinations.set(index, temp);
                saveOrder();
            });
        }
        if (index < currentDestinations.size() - 1) {
            items.add("▼ Mover hacia la derecha / abajo");
            actions.add(() -> {
                int temp = currentDestinations.get(index + 1);
                currentDestinations.set(index + 1, id);
                currentDestinations.set(index, temp);
                saveOrder();
            });
        }
        if (id != LiquidNavigationDestinations.CHATS && currentDestinations.size() > 2) {
            items.add("✖ Quitar pestaña");
            actions.add(() -> {
                currentDestinations.remove(index);
                saveOrder();
            });
        }
        if (availableDestinations.size() > 0 && currentDestinations.size() < LiquidNavigationDestinations.MAX_VISIBLE) {
            items.add("➕ Agregar otra pestaña...");
            actions.add(this::showAddTabDialog);
        }

        CharSequence[] itemArray = items.toArray(new CharSequence[0]);
        showDialog(new AlertDialog.Builder(getParentActivity(), resourcesProvider)
                .setTitle(title)
                .setItems(itemArray, (d, which) -> actions.get(which).run())
                .create());
    }

    private void showAddTabDialog() {
        if (availableDestinations.isEmpty()) return;
        CharSequence[] items = new CharSequence[availableDestinations.size()];
        for (int i = 0; i < availableDestinations.size(); i++) {
            items[i] = getString(LiquidNavigationTabs.label(availableDestinations.get(i)));
        }
        showDialog(new AlertDialog.Builder(getParentActivity(), resourcesProvider)
                .setTitle("Agregar pestaña a la barra")
                .setItems(items, (d, which) -> {
                    currentDestinations.add(availableDestinations.get(which));
                    saveOrder();
                })
                .create());
    }

    private final class DockPreviewCell extends FrameLayout {
        private final GradientDrawable dockBg = new GradientDrawable();
        private final LinearLayout dockLayout;
        private final ArrayList<LinearLayout> tabItems = new ArrayList<>();
        private final ArrayList<ImageView> tabIcons = new ArrayList<>();
        private final ArrayList<TextView> tabTitles = new ArrayList<>();
        private final TextView offView;

        DockPreviewCell(Context context) {
            super(context);
            setLayoutParams(new RecyclerView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
            setPadding(dp(16), dp(12), dp(16), dp(12));

            dockLayout = new LinearLayout(context);
            dockLayout.setOrientation(LinearLayout.HORIZONTAL);
            dockLayout.setGravity(Gravity.CENTER);
            dockLayout.setPadding(dp(12), dp(8), dp(12), dp(8));

            dockBg.setColor((Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider) & 0xffffff) | 0xEE000000);
            dockLayout.setBackground(dockBg);

            LayoutParams lp = new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(64));
            lp.gravity = Gravity.CENTER;
            addView(dockLayout, lp);

            offView = new TextView(context);
            offView.setText("Barra inferior desactivada");
            offView.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider));
            offView.setTextSize(13);
            offView.setGravity(Gravity.CENTER);
            offView.setVisibility(View.GONE);
            dockLayout.addView(offView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

            for (int i = 0; i < 5; i++) {
                LinearLayout tabItem = new LinearLayout(context);
                tabItem.setOrientation(LinearLayout.VERTICAL);
                tabItem.setGravity(Gravity.CENTER);

                ImageView icon = new ImageView(context);
                icon.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
                tabItem.addView(icon, new LinearLayout.LayoutParams(dp(24), dp(24)));

                TextView text = new TextView(context);
                text.setTextSize(10);
                text.setSingleLine(true);
                text.setGravity(Gravity.CENTER);
                LinearLayout.LayoutParams textLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
                textLp.topMargin = dp(2);
                tabItem.addView(text, textLp);

                LinearLayout.LayoutParams itemLp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.MATCH_PARENT, 1f);
                dockLayout.addView(tabItem, itemLp);

                tabItems.add(tabItem);
                tabIcons.add(icon);
                tabTitles.add(text);
            }
            update();
        }

        void update() {
            boolean floating = LiquidNavigationConfig.isFloatingDock();
            boolean titles = LiquidNavigationConfig.showTitles();
            boolean enabled = LiquidNavigationConfig.isEnabled();

            dockBg.setCornerRadius(floating ? dp(28) : dp(14));
            dockBg.setColor((Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider) & 0xffffff) | 0xEE000000);

            if (!enabled) {
                offView.setVisibility(View.VISIBLE);
                for (LinearLayout item : tabItems) {
                    item.setVisibility(View.GONE);
                }
                return;
            }

            offView.setVisibility(View.GONE);
            int[] order = LiquidNavigationConfig.order();
            int slots = Math.min(order.length, 5);
            int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText, resourcesProvider);
            int normal = Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider);

            for (int i = 0; i < 5; i++) {
                LinearLayout tabItem = tabItems.get(i);
                if (i < slots) {
                    tabItem.setVisibility(View.VISIBLE);
                    int id = order[i];
                    ImageView icon = tabIcons.get(i);
                    TextView text = tabTitles.get(i);

                    int resId = R.drawable.tabs_chats_24;
                    switch (id) {
                        case 0: resId = R.drawable.tabs_chats_24; break;
                        case 1: resId = R.drawable.tabs_contacts_24; break;
                        case 2: resId = R.drawable.outline_profile_settings; break;
                        case 3: resId = R.drawable.tabs_calls_24; break;
                        case 4: resId = R.drawable.msg_contact; break;
                        case 5: resId = R.drawable.ic_feed; break;
                        case 6: resId = R.drawable.msg_groups; break;
                        case 7: resId = R.drawable.msg_channel; break;
                        case 8: resId = R.drawable.msg_saved; break;
                        default: resId = R.drawable.ic_ab_other; break;
                    }
                    icon.setImageResource(resId);
                    icon.setColorFilter(i == 0 ? accent : normal);

                    if (titles) {
                        text.setVisibility(View.VISIBLE);
                        text.setText(getString(LiquidNavigationTabs.label(id)));
                        text.setTextColor(i == 0 ? accent : normal);
                    } else {
                        text.setVisibility(View.GONE);
                    }
                } else {
                    tabItem.setVisibility(View.GONE);
                }
            }
        }
    }

    private final class Adapter extends MatteListAdapter {
        Adapter(Context c) { super(c); }

        @Override
        public int getItemViewType(int p) {
            if (p == previewRow) return 120;
            if (p == tabsHeaderRow || p == appearanceHeaderRow || p == actionsHeaderRow || p == orderHeaderRow) return TYPE_HEADER;
            if (p == showTabsRow || p == floatingDockRow || p == showTitlesRow || p == doubleTapChatsRow || p == doubleTapProfileRow || p == alwaysSearchChatsRow) return TYPE_CHECK;
            return TYPE_SETTINGS;
        }

        @Override
        public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup p, int type) {
            if (type == 120) {
                previewCell = new DockPreviewCell(p.getContext());
                return new RecyclerListView.Holder(previewCell);
            }
            return super.onCreateViewHolder(p, type);
        }

        @Override
        public void onBindViewHolder(RecyclerView.ViewHolder h, int p, boolean partial) {
            if (p == previewRow) {
                ((DockPreviewCell) h.itemView).update();
                return;
            }
            if (p == tabsHeaderRow) {
                ((HeaderCell) h.itemView).setText(getString(R.string.FlexyBottomTabsSectionTabs));
                return;
            }
            if (p == appearanceHeaderRow) {
                ((HeaderCell) h.itemView).setText(getString(R.string.FlexyBottomTabsSectionAppearance));
                return;
            }
            if (p == actionsHeaderRow) {
                ((HeaderCell) h.itemView).setText(getString(R.string.FlexyBottomTabsSectionActions));
                return;
            }
            if (p == orderHeaderRow) {
                ((HeaderCell) h.itemView).setText(getString(R.string.FlexyBottomTabsSectionOrder));
                return;
            }
            if (p == showTabsRow) {
                ((TextCheckCell) h.itemView).setTextAndValueAndCheck(getString(R.string.FlexyBottomTabsShow), getString(R.string.FlexyBottomTabsShowSub), LiquidNavigationConfig.isEnabled(), false, true);
                return;
            }
            if (p == floatingDockRow) {
                ((TextCheckCell) h.itemView).setTextAndValueAndCheck(getString(R.string.FlexyBottomTabsFloatingDock), getString(R.string.FlexyBottomTabsFloatingDockSub), LiquidNavigationConfig.isFloatingDock(), false, true);
                return;
            }
            if (p == showTitlesRow) {
                ((TextCheckCell) h.itemView).setTextAndCheck(getString(R.string.FlexyBottomTabsShowTitles), LiquidNavigationConfig.showTitles(), false);
                return;
            }
            if (p == doubleTapChatsRow) {
                ((TextCheckCell) h.itemView).setTextAndCheck(getString(R.string.FlexyBottomTabsDoubleTapChats), LiquidNavigationConfig.doubleTapChats(), true);
                return;
            }
            if (p == doubleTapProfileRow) {
                ((TextCheckCell) h.itemView).setTextAndCheck(getString(R.string.FlexyBottomTabsDoubleTapProfile), LiquidNavigationConfig.doubleTapProfile(), true);
                return;
            }
            if (p == alwaysSearchChatsRow) {
                ((TextCheckCell) h.itemView).setTextAndValueAndCheck(getString(R.string.FlexyBottomTabsAlwaysSearchChats), getString(R.string.FlexyBottomTabsAlwaysSearchChatsSub), LiquidNavigationConfig.alwaysSearchChats(), false, false);
                return;
            }
            if (p >= orderStartRow && p < orderEndRow) {
                int index = p - orderStartRow;
                int id = currentDestinations.get(index);
                ((TextSettingsCell) h.itemView).setTextAndValue(
                        (index + 1) + ". " + getString(LiquidNavigationTabs.label(id)),
                        "Configurar ›",
                        p != orderEndRow - 1
                );
            }
        }

        @Override
        public boolean isEnabled(RecyclerView.ViewHolder h) {
            int p = settingsRowPosition(h);
            return p != previewRow && p != tabsHeaderRow && p != appearanceHeaderRow && p != actionsHeaderRow && p != orderHeaderRow;
        }
    }
}
