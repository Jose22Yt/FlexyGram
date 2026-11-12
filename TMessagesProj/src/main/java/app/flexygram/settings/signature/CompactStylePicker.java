/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.drawable.GradientDrawable;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.Gravity;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.ArrayList;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.ui.ActionBar.Theme;

/** One live preview and a responsive grid of small, independently rendered radio choices. */
public final class CompactStylePicker extends LinearLayout implements Theme.Colorable {
    private final Theme.ResourcesProvider provider;
    private final ChoiceGrid grid;
    private final View livePreview;
    private final ArrayList<Tile> choices = new ArrayList<>();
    public CompactStylePicker(Context context, Theme.ResourcesProvider provider, View preview, int columns) {
        super(context); this.provider = provider; livePreview=preview;
        setOrientation(VERTICAL); setPadding(dp(12), dp(8), dp(12), dp(8));
        setTag(org.telegram.ui.Components.RecyclerListView.TAG_NOT_SECTION);
        FrameLayout stage = new FrameLayout(context);
        GradientDrawable background = new GradientDrawable(); background.setCornerRadius(dp(20));
        background.setColor(Theme.getColor(Theme.key_windowBackgroundWhite, provider));
        stage.setBackground(background); stage.setClipToOutline(true);
        stage.addView(preview, new FrameLayout.LayoutParams(-1, -2));
        addView(stage, new LayoutParams(-1, -2));
        grid = new ChoiceGrid(context, columns);
        LayoutParams layout = new LayoutParams(-1, -2); layout.topMargin = dp(10);
        addView(grid, layout);
    }
    private static int dp(int value) { return AndroidUtilities.dp(value); }
    public void addChoice(int id, String name, View miniature, Runnable choose) {
        Tile tile = new Tile(getContext(), id, name, miniature, choose);
        choices.add(tile); grid.addView(tile, new ViewGroup.LayoutParams(-1, -2));
    }
    public void select(int id) { for (Tile tile : choices) tile.bind(tile.id == id); }
    public View previewView() { return livePreview; }
    public void refreshMiniatures() { for (Tile tile : choices) tile.preview.invalidate(); }
    @Override public void updateColors() { for (Tile tile : choices) tile.colors(); invalidate(); }
    @Override protected void dispatchDraw(Canvas canvas) { updateTileColors(); super.dispatchDraw(canvas); }
    private void updateTileColors() { for (Tile tile : choices) tile.colors(); }

    private final class Tile extends LinearLayout {
        final int id;
        final String name;
        final View preview;
        final TextView label;
        final GradientDrawable background = new GradientDrawable();
        int lastSurface, lastInk, lastStroke;
        boolean lastSelected;
        Tile(Context context, int id, String name, View preview, Runnable choose) {
            super(context); this.id = id; this.name = name; this.preview = preview;
            setOrientation(VERTICAL); setGravity(Gravity.CENTER); setPadding(dp(4), dp(4), dp(4), dp(6));
            background.setCornerRadius(dp(20));
            setFocusable(true); setClickable(true); setContentDescription(name);
            preview.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS);
            Miniature pill=new Miniature(context,preview);
            pill.setBackground(background);pill.setClipToOutline(true);
            addView(pill,new LayoutParams(-1,dp(56)));
            label = new TextView(context); label.setText(name); label.setTextSize(12);
            label.setGravity(Gravity.CENTER); label.setMinHeight(dp(32));
            label.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
            LayoutParams caption=new LayoutParams(-1,-2);caption.topMargin=dp(4);
            addView(label, caption);
            setOnClickListener(view -> choose.run()); colors();
        }
        void bind(boolean selected) { setSelected(selected); colors(); }
        void colors() {
            int surface = Theme.getColor(Theme.key_windowBackgroundWhite, provider);
            int ink = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText, provider);
            int stroke = Theme.getColor(isSelected() ? Theme.key_windowBackgroundWhiteBlueText : Theme.key_divider, provider);
            if (surface != lastSurface || ink != lastInk || stroke != lastStroke || lastSelected != isSelected()) {
                lastSurface = surface; lastInk = ink; lastStroke = stroke;
                lastSelected=isSelected();
                background.setColor(surface); background.setStroke(dp(isSelected() ? 2 : 1), stroke);
                label.setTextColor(ink);
            }
        }
        @Override public boolean onInterceptTouchEvent(MotionEvent event) { return true; }
        @Override public void onInitializeAccessibilityNodeInfo(AccessibilityNodeInfo info) {
            super.onInitializeAccessibilityNodeInfo(info); info.setClassName("android.widget.RadioButton");
            info.setCheckable(true); info.setChecked(isSelected()); info.setContentDescription(name);
        }
    }
    /** Measure at phone width, then scale the original renderer, preserving its aspect ratio. */
    private static final class Miniature extends ViewGroup {
        float scale;
        Miniature(Context context, View preview) { super(context); addView(preview); setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS); }
        @Override protected void onMeasure(int widthSpec, int heightSpec) {
            int width = MeasureSpec.getSize(widthSpec), height = MeasureSpec.getSize(heightSpec);
            View child = getChildAt(0);
            child.measure(MeasureSpec.makeMeasureSpec(dp(360), MeasureSpec.EXACTLY), MeasureSpec.makeMeasureSpec(0, MeasureSpec.UNSPECIFIED));
            scale = Math.min(width / (float) Math.max(1, child.getMeasuredWidth()), height / (float) Math.max(1, child.getMeasuredHeight()));
            setMeasuredDimension(width, height);
        }
        @Override protected void onLayout(boolean changed, int l, int t, int r, int b) { View child = getChildAt(0); child.layout(0, 0, child.getMeasuredWidth(), child.getMeasuredHeight()); }
        @Override protected void dispatchDraw(Canvas canvas) {
            View child = getChildAt(0); int save = canvas.save();
            canvas.translate((getWidth() - child.getWidth() * scale) / 2, (getHeight() - child.getHeight() * scale) / 2);
            canvas.scale(scale, scale); super.dispatchDraw(canvas); canvas.restoreToCount(save);
        }
    }
    private static final class ChoiceGrid extends ViewGroup {
        final int preferredColumns;
        int columns;
        final ArrayList<Integer> rowHeights = new ArrayList<>();
        ChoiceGrid(Context context, int columns) { super(context); preferredColumns = columns; }
        @Override protected void onMeasure(int widthSpec, int heightSpec) {
            int width = MeasureSpec.getSize(widthSpec), gap = dp(8);
            float fontScale = getResources().getConfiguration().fontScale;
            columns = Math.max(1, Math.min(preferredColumns, (width + gap) / Math.max(1, Math.round(dp(100) * Math.max(1, fontScale)))));
            int cellWidth = Math.max(1, (width - gap * (columns - 1)) / columns), height = 0;
            rowHeights.clear();
            for (int first = 0; first < getChildCount(); first += columns) {
                int rowHeight = 0;
                for (int i = first; i < Math.min(getChildCount(), first + columns); i++) {
                    View child = getChildAt(i); child.measure(MeasureSpec.makeMeasureSpec(cellWidth, MeasureSpec.EXACTLY), MeasureSpec.makeMeasureSpec(0, MeasureSpec.UNSPECIFIED));
                    rowHeight = Math.max(rowHeight, child.getMeasuredHeight());
                }
                rowHeights.add(rowHeight); height += rowHeight + (first == 0 ? 0 : gap);
            }
            setMeasuredDimension(width, height);
        }
        @Override protected void onLayout(boolean changed, int l, int t, int r, int b) {
            int y = 0, gap = dp(8), width = Math.max(1, (getWidth() - gap * (columns - 1)) / columns);
            for (int i = 0; i < getChildCount(); i++) {
                int row = i / columns, column = i % columns;
                if (i > 0 && column == 0) y += rowHeights.get(row - 1) + gap;
                int x = LocaleController.isRTL ? getWidth() - width - column * (width + gap) : column * (width + gap);
                getChildAt(i).layout(x, y, x + width, y + rowHeights.get(row));
            }
        }
    }
}
