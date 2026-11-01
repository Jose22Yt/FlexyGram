package app.flexygram.navigation;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
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
            if (LiquidNavigationDestinations.isSelectable(id) && !currentDestinations.contains(id)) {
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


    /** Interactive editor: native tab glyphs, drag reordering and inline disabled-tab picker. */
    private final class DockPreviewCell extends FrameLayout {
        private final LinearLayout content;
        private final LinearLayout dockLayout;
        private final LinearLayout disabledLayout;
        private final TextView offView;
        private final GradientDrawable dockBackground = new GradientDrawable();

        DockPreviewCell(Context context) {
            super(context);
            setLayoutParams(new RecyclerView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
            setPadding(dp(16), dp(8), dp(16), dp(14));

            content = new LinearLayout(context);
            content.setOrientation(LinearLayout.VERTICAL);
            addView(content, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

            TextView guidance = new TextView(context);
            guidance.setText("Arrastra los iconos para ordenarlos. Toca uno para configurarlo.");
            guidance.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider));
            guidance.setTextSize(12);
            guidance.setPadding(dp(5), dp(2), dp(5), dp(11));
            content.addView(guidance, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

            dockLayout = new LinearLayout(context);
            dockLayout.setOrientation(LinearLayout.HORIZONTAL);
            dockLayout.setGravity(Gravity.CENTER);
            dockLayout.setPadding(dp(4), dp(3), dp(4), dp(3));
            dockLayout.setBackground(dockBackground);
            content.addView(dockLayout, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(64)));

            offView = new TextView(context);
            offView.setText("Barra inferior desactivada");
            offView.setTextSize(13);
            offView.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider));
            offView.setGravity(Gravity.CENTER);

            TextView availableLabel = new TextView(context);
            availableLabel.setText("Pestañas disponibles · Toca para agregar");
            availableLabel.setTextSize(12);
            availableLabel.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider));
            availableLabel.setPadding(dp(5), dp(14), dp(5), dp(8));
            content.addView(availableLabel, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

            android.widget.HorizontalScrollView scroller = new android.widget.HorizontalScrollView(context);
            scroller.setHorizontalScrollBarEnabled(false);
            scroller.setFillViewport(true);
            content.addView(scroller, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(42)));

            disabledLayout = new LinearLayout(context);
            disabledLayout.setGravity(Gravity.CENTER_VERTICAL);
            disabledLayout.setOrientation(LinearLayout.HORIZONTAL);
            scroller.addView(disabledLayout, new android.widget.HorizontalScrollView.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.MATCH_PARENT));
            update();
        }

        private void addEditableTab(int id, int index, boolean hideLabels) {
            org.telegram.ui.Components.glass.GlassTabView tab =
                    LiquidNavigationTabs.createPreview(getContext(), id);
            tab.setMainTabsAppearance(hideLabels, LiquidNavigationConfig.iconDp());
            tab.setMainTabsCompact(hideLabels);
            tab.setSkipDrawSelector(true);
            dockLayout.addView(tab, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.MATCH_PARENT, 1f));
            tab.setOnClickListener(v -> showTabActionDialog(index));
            final float[] downX = {0f};
            final boolean[] dragging = {false};
            tab.setOnTouchListener((v, event) -> {
                switch (event.getActionMasked()) {
                    case android.view.MotionEvent.ACTION_DOWN:
                        downX[0] = event.getRawX();
                        dragging[0] = false;
                        v.setTranslationX(0f);
                        v.getParent().requestDisallowInterceptTouchEvent(true);
                        return true;
                    case android.view.MotionEvent.ACTION_MOVE: {
                        float delta = event.getRawX() - downX[0];
                        if (Math.abs(delta) > dp(7)) dragging[0] = true;
                        if (dragging[0]) {
                            float slot = (float) dockLayout.getWidth() / Math.max(1, currentDestinations.size());
                            delta = Math.max(-index * slot, Math.min((currentDestinations.size() - 1 - index) * slot, delta));
                            v.setTranslationX(delta);
                        }
                        return true;
                    }
                    case android.view.MotionEvent.ACTION_UP: {
                        float delta = v.getTranslationX();
                        v.setTranslationX(0f);
                        if (!dragging[0]) {
                            v.performClick();
                        } else {
                            float slot = (float) dockLayout.getWidth() / Math.max(1, currentDestinations.size());
                            int destination = Math.max(0, Math.min(currentDestinations.size() - 1,
                                    index + Math.round(delta / Math.max(1f, slot))));
                            if (destination != index && index < currentDestinations.size()) {
                                Integer moved = currentDestinations.remove(index);
                                currentDestinations.add(destination, moved);
                                saveOrder();
                            }
                        }
                        return true;
                    }
                    case android.view.MotionEvent.ACTION_CANCEL:
                        v.setTranslationX(0f);
                        return true;
                    default:
                        return true;
                }
            });
        }

        private void addAvailableTab(int id, boolean capacityReached) {
            TextView chip = new TextView(getContext());
            chip.setText("＋ " + getString(LiquidNavigationTabs.label(id)));
            chip.setGravity(Gravity.CENTER);
            chip.setTextSize(12);
            chip.setSingleLine(true);
            chip.setPadding(dp(12), 0, dp(12), 0);
            int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText, resourcesProvider);
            chip.setTextColor(capacityReached ?
                    Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider) : accent);
            GradientDrawable background = new GradientDrawable();
            background.setCornerRadius(dp(19));
            background.setColor(Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider));
            background.setStroke(dp(1), Theme.multAlpha(accent, capacityReached ? .14f : .3f));
            chip.setBackground(background);
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT, dp(34));
            params.rightMargin = dp(7);
            disabledLayout.addView(chip, params);
            chip.setOnClickListener(v -> {
                if (currentDestinations.size() >= LiquidNavigationDestinations.MAX_VISIBLE) {
                    showDialog(new AlertDialog.Builder(getParentActivity(), resourcesProvider)
                            .setMessage("La barra admite hasta seis pestañas. Quita una para agregar otra.")
                            .setPositiveButton(R.string.OK, null).create());
                    return;
                }
                currentDestinations.add(id);
                saveOrder();
            });
        }

        void update() {
            if (dockLayout == null || disabledLayout == null) return;
            dockLayout.removeAllViews();
            disabledLayout.removeAllViews();
            boolean enabled = LiquidNavigationConfig.isEnabled();
            boolean floating = LiquidNavigationConfig.isFloatingDock();
            dockBackground.setCornerRadius(dp(floating ? 31 : 12));
            dockBackground.setColor(Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider));
            dockBackground.setStroke(dp(1),
                    Theme.multAlpha(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider), .24f));
            if (!enabled) {
                dockLayout.addView(offView, new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
            } else {
                // The editor displays all six configured tabs; unlike the old mock, it never drops slot six.
                int widthPx = Math.max(1, getWidth() > 0 ? getWidth() - dp(40) :
                        org.telegram.messenger.AndroidUtilities.displaySize.x - dp(40));
                boolean hideLabels = LiquidNavigationConfig.hideLabels(currentDestinations.size(),
                        (int) (widthPx / org.telegram.messenger.AndroidUtilities.density));
                for (int i = 0; i < currentDestinations.size(); i++) {
                    addEditableTab(currentDestinations.get(i), i, hideLabels);
                }
            }

            boolean full = currentDestinations.size() >= LiquidNavigationDestinations.MAX_VISIBLE;
            for (int id : availableDestinations) addAvailableTab(id, full);
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
            int p = h.getAdapterPosition();
            return p != previewRow && p != tabsHeaderRow && p != appearanceHeaderRow && p != actionsHeaderRow && p != orderHeaderRow;
        }
    }
}
