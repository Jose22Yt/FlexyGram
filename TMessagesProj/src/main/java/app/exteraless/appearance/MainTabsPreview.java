package app.exteraless.appearance;

import android.content.ClipData;
import android.content.Context;
import android.os.Bundle;
import android.view.DragEvent;
import android.view.Gravity;
import android.view.View;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.glass.GlassTabView;

import java.util.List;

import tw.nekomimi.nekogram.helpers.MainTabsHelper;

/** Interactive, local-only preview. Dropping on another tab swaps the two stable slots. */
public final class MainTabsPreview extends LinearLayout {
    private final int account;
    private final Runnable onOrderChanged;
    private final Theme.ResourcesProvider resourcesProvider;
    private int selected = MainTabsOrder.CHATS;

    public MainTabsPreview(Context context, int account, Theme.ResourcesProvider provider, Runnable onOrderChanged) {
        super(context);
        this.account = account;
        this.resourcesProvider = provider;
        this.onOrderChanged = onOrderChanged;
        setOrientation(VERTICAL);
        setPadding(dp(12), dp(8), dp(12), dp(12));
        render();
    }

    private static int dp(float value) { return AndroidUtilities.dp(value); }

    private void render() {
        removeAllViews();
        TextView hint = new TextView(getContext());
        hint.setText(LocaleController.getString(R.string.FlexyTabsDragHint));
        hint.setTextSize(13);
        hint.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider));
        addView(hint, new LinearLayout.LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT));

        FrameLayout row = new FrameLayout(getContext()) {
            @Override
            protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
                if (getChildCount() > 0) {
                    FrameLayout.LayoutParams params = (FrameLayout.LayoutParams) getChildAt(0).getLayoutParams();
                    int reserve = AppearanceConfig.floatingSearch.Bool()
                            ? dp(Math.max(48, MainTabsHelper.getMainTabsHeight()) + 8) : 0;
                    int available = Math.max(0, MeasureSpec.getSize(widthMeasureSpec) - reserve);
                    params.width = AppearanceConfig.compactNavigation.Bool()
                            ? Math.min(available, dp(MainTabsHelper.getMainTabsPreferredTabWidth() * MainTabsOrder.visible().size() + 8))
                            : available;
                }
                super.onMeasure(widthMeasureSpec, heightMeasureSpec);
            }
        };
        int height = Math.max(48, MainTabsHelper.getMainTabsHeight());
        LinearLayout.LayoutParams rowParams = new LinearLayout.LayoutParams(LayoutParams.MATCH_PARENT, dp(height + 12));
        rowParams.topMargin = dp(8);
        addView(row, rowParams);
        LinearLayout tabs = new LinearLayout(getContext());
        tabs.setGravity(Gravity.CENTER_VERTICAL);
        tabs.setPadding(dp(4), 0, dp(4), 0);
        tabs.setBackground(Theme.createRoundRectDrawable(dp(height / 2f),
                Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider)));
        FrameLayout.LayoutParams tabsParams = new FrameLayout.LayoutParams(LayoutParams.MATCH_PARENT, dp(height), Gravity.CENTER_VERTICAL | Gravity.CENTER_HORIZONTAL);
        if (AppearanceConfig.floatingSearch.Bool()) tabsParams.setMarginEnd(dp(height + 8));
        row.addView(tabs, tabsParams);

        List<Integer> order = MainTabsOrder.visible();
        for (int slot : order) {
            GlassTabView tab = createTab(slot);
            tab.setMainTabsCompact(MainTabsHelper.isMainTabsHideTitleStyle());
            tab.setSelected(selected == slot, false);
            tabs.addView(tab, new LinearLayout.LayoutParams(0, LayoutParams.MATCH_PARENT, 1));
            tab.setOnClickListener(v -> {
                selected = slot;
                for (int i = 0; i < tabs.getChildCount(); i++) {
                    ((GlassTabView) tabs.getChildAt(i)).setSelected(order.get(i) == selected, true);
                }
            });
            tab.setOnLongClickListener(v -> {
                v.performHapticFeedback(android.view.HapticFeedbackConstants.LONG_PRESS);
                return v.startDragAndDrop(ClipData.newPlainText("FlexyGram tab", Integer.toString(slot)),
                        new View.DragShadowBuilder(v), v, 0);
            });
            tab.setOnDragListener((v, event) -> {
                if (!(event.getLocalState() instanceof View source) || source.getParent() != tabs) return false;
                switch (event.getAction()) {
                    case DragEvent.ACTION_DRAG_STARTED:
                        return true;
                    case DragEvent.ACTION_DRAG_ENTERED:
                        v.setAlpha(0.55f);
                        return true;
                    case DragEvent.ACTION_DRAG_EXITED:
                    case DragEvent.ACTION_DRAG_ENDED:
                        v.setAlpha(1f);
                        return true;
                    case DragEvent.ACTION_DROP:
                        int sourceIndex = tabs.indexOfChild(source);
                        if (sourceIndex >= 0 && source != v) exchange(order.get(sourceIndex), slot);
                        v.setAlpha(1f);
                        return true;
                    default:
                        return true;
                }
            });
            tab.setAccessibilityDelegate(new View.AccessibilityDelegate() {
                @Override
                public void onInitializeAccessibilityNodeInfo(View host, AccessibilityNodeInfo info) {
                    super.onInitializeAccessibilityNodeInfo(host, info);
                    int position = order.indexOf(slot);
                    info.setContentDescription(label(slot) + ", " + (position + 1) + "/" + order.size());
                    if (position > 0) info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_BACKWARD);
                    if (position + 1 < order.size()) info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_FORWARD);
                }
                @Override
                public boolean performAccessibilityAction(View host, int action, Bundle args) {
                    int position = order.indexOf(slot);
                    int target = action == AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD ? position - 1
                            : action == AccessibilityNodeInfo.ACTION_SCROLL_FORWARD ? position + 1 : -1;
                    if (target >= 0 && target < order.size()) {
                        exchange(slot, order.get(target));
                        return true;
                    }
                    return super.performAccessibilityAction(host, action, args);
                }
            });
        }
        if (AppearanceConfig.floatingSearch.Bool()) {
            ImageView search = new ImageView(getContext());
            search.setImageResource(R.drawable.outline_header_search);
            search.setScaleType(ImageView.ScaleType.CENTER);
            search.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText, resourcesProvider));
            search.setBackground(Theme.createCircleDrawable(dp(height), Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider)));
            search.setContentDescription(LocaleController.getString(R.string.Search));
            row.addView(search, new FrameLayout.LayoutParams(dp(height), dp(height), Gravity.END | Gravity.CENTER_VERTICAL));
        }
    }

    private void exchange(int first, int second) {
        MainTabsOrder.swap(first, second);
        // Finish the native drag dispatch before replacing any preview views.
        post(() -> {
            render();
            onOrderChanged.run();
        });
    }

    private String label(int slot) {
        return LocaleController.getString(slot == MainTabsOrder.CHATS ? R.string.MainTabsChats
                : slot == MainTabsOrder.CONTACTS ? (AppearanceConfig.showFeedTab() ? R.string.Feed : R.string.MainTabsContacts)
                : slot == MainTabsOrder.PROFILE ? R.string.MainTabsProfile
                : MainTabsHelper.isCallsTabShown(account) ? R.string.MainTabsCalls : R.string.Settings);
    }

    private GlassTabView createTab(int slot) {
        if (slot == MainTabsOrder.PROFILE) return GlassTabView.createAvatar(getContext(), resourcesProvider, account, R.string.MainTabsProfile);
        GlassTabView.TabAnimation animation = slot == MainTabsOrder.CHATS ? GlassTabView.TabAnimation.CHATS
                : slot == MainTabsOrder.CONTACTS ? (AppearanceConfig.showFeedTab() ? GlassTabView.TabAnimation.FEED : GlassTabView.TabAnimation.CONTACTS)
                : MainTabsHelper.isCallsTabShown(account) ? GlassTabView.TabAnimation.CALLS : GlassTabView.TabAnimation.SETTINGS;
        int text = slot == MainTabsOrder.CHATS ? R.string.MainTabsChats
                : slot == MainTabsOrder.CONTACTS ? (AppearanceConfig.showFeedTab() ? R.string.Feed : R.string.MainTabsContacts)
                : MainTabsHelper.isCallsTabShown(account) ? R.string.MainTabsCalls : R.string.Settings;
        return GlassTabView.createMainTab(getContext(), resourcesProvider, animation, text);
    }
}
