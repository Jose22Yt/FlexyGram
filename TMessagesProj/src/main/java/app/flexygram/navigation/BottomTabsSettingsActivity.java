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
import org.telegram.ui.Cells.HeaderCell;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.RecyclerListView;

import java.util.ArrayList;

public final class BottomTabsSettingsActivity extends SignatureMatteSettingsActivity {

    private int previewRow;
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

        tabsHeaderRow = addHeader("FlexyBottomTabsSectionTabs");
        showTabsRow = addRow("flexyBottomTabsShow");

        appearanceHeaderRow = addHeader("FlexyBottomTabsSectionAppearance");
        floatingDockRow = addRow("flexyBottomTabsFloatingDock");
        showTitlesRow = addRow("flexyBottomTabsShowTitles");

        actionsHeaderRow = addHeader("FlexyBottomTabsSectionActions");
        doubleTapChatsRow = addRow("flexyBottomTabsDoubleTapChats");
        doubleTapProfileRow = addRow("flexyBottomTabsDoubleTapProfile");
        alwaysSearchChatsRow = addRow("flexyBottomTabsAlwaysSearchChats");

        orderHeaderRow = addHeader("FlexyBottomTabsSectionOrder");
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
    }

    @Override
    protected void onItemClick(View v, int position, float x, float y) {
        if (position == showTabsRow) {
            LiquidNavigationConfig.setEnabled(!LiquidNavigationConfig.isEnabled());
            listAdapter.notifyItemChanged(showTabsRow);
            listAdapter.notifyItemChanged(previewRow);
        } else if (position == floatingDockRow) {
            LiquidNavigationConfig.setFloatingDock(!LiquidNavigationConfig.isFloatingDock());
            listAdapter.notifyItemChanged(floatingDockRow);
            listAdapter.notifyItemChanged(previewRow);
        } else if (position == showTitlesRow) {
            LiquidNavigationConfig.setShowTitles(!LiquidNavigationConfig.showTitles());
            listAdapter.notifyItemChanged(showTitlesRow);
            listAdapter.notifyItemChanged(previewRow);
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

        DockPreviewCell(Context context) {
            super(context);
            setPadding(dp(16), dp(16), dp(16), dp(16));

            dockLayout = new LinearLayout(context);
            dockLayout.setOrientation(LinearLayout.HORIZONTAL);
            dockLayout.setGravity(Gravity.CENTER);
            dockLayout.setPadding(dp(8), dp(6), dp(8), dp(6));

            dockBg.setColor(Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider));
            dockLayout.setBackground(dockBg);

            LayoutParams lp = new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(64));
            lp.gravity = Gravity.CENTER;
            addView(dockLayout, lp);
        }

        void update() {
            dockLayout.removeAllViews();
            boolean floating = LiquidNavigationConfig.isFloatingDock();
            boolean titles = LiquidNavigationConfig.showTitles();
            boolean enabled = LiquidNavigationConfig.isEnabled();

            dockBg.setCornerRadius(floating ? dp(28) : dp(8));
            dockBg.setColor((Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider) & 0xffffff) | 0xEE000000);

            if (!enabled) {
                TextView offView = new TextView(getContext());
                offView.setText("Barra inferior desactivada");
                offView.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider));
                offView.setTextSize(13);
                dockLayout.addView(offView);
                return;
            }

            int[] order = LiquidNavigationConfig.order();
            int slots = Math.min(order.length, 5);
            int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText, resourcesProvider);
            int normal = Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider);

            for (int i = 0; i < slots; i++) {
                int id = order[i];
                LinearLayout tabItem = new LinearLayout(getContext());
                tabItem.setOrientation(LinearLayout.VERTICAL);
                tabItem.setGravity(Gravity.CENTER);

                ImageView icon = new ImageView(getContext());
                icon.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
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
                tabItem.addView(icon, new LinearLayout.LayoutParams(dp(22), dp(22)));

                if (titles) {
                    TextView text = new TextView(getContext());
                    text.setText(getString(LiquidNavigationTabs.label(id)));
                    text.setTextSize(10);
                    text.setTextColor(i == 0 ? accent : normal);
                    text.setSingleLine(true);
                    tabItem.addView(text, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT));
                }

                LinearLayout.LayoutParams itemLp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
                dockLayout.addView(tabItem, itemLp);
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
                return new RecyclerListView.Holder(new DockPreviewCell(p.getContext()));
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
            int p = h.getAdapterPosition();
            return p != previewRow && p != tabsHeaderRow && p != appearanceHeaderRow && p != actionsHeaderRow && p != orderHeaderRow;
        }
    }
}
