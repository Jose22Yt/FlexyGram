/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;

import android.content.Context;
import android.graphics.drawable.GradientDrawable;
// Solid surfaces only: no glass, blur, RenderEffect, or live backdrop sampling.
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.BottomSheet;
import org.telegram.ui.ActionBar.Theme;

/** Signature Matte UI only. No file read/write, idle work, or chat send on construction. */
final class FlexyEditorToolsSheet extends BottomSheet {
    interface Selection { void selected(int action); }
    private final Theme.ResourcesProvider provider;
    private final Selection selection;

    FlexyEditorToolsSheet(BaseFragment fragment, String fileName, boolean text,
                         boolean zipEntry, boolean html, Selection selection) {
        super(fragment.getParentActivity(), false, fragment.getResourceProvider());
        provider = fragment.getResourceProvider();
        this.selection = selection;
        setApplyTopPadding(false);
        setBackgroundColor(color(Theme.key_windowBackgroundGray));
        Context c = getContext();
        LinearLayout all = new LinearLayout(c);
        all.setOrientation(LinearLayout.VERTICAL);
        all.setPadding(dp(18), dp(14), dp(18), dp(18));

        TextView title = text(c, getString(R.string.FlexyEditorToolsTitle), 20,
                Theme.key_windowBackgroundWhiteBlackText);
        title.setTypeface(AndroidUtilities.bold());
        all.addView(title);
        TextView description = text(c, fileName, 13, Theme.key_windowBackgroundWhiteGrayText2);
        description.setSingleLine();
        description.setEllipsize(TextUtils.TruncateAt.MIDDLE);
        LinearLayout.LayoutParams desc = new LinearLayout.LayoutParams(-1, -2);
        desc.topMargin = dp(2); desc.bottomMargin = dp(14);
        all.addView(description, desc);

        section(all, getString(R.string.FlexyEditorToolsFile));
        LinearLayout actions = card(c);
        row(actions, R.drawable.flexy_studio_export, getString(R.string.FlexyFilesSave), 3, false);
        // Primary same-chat action: no chooser, never targets an arbitrary dialog.
        row(actions, R.drawable.msg_discussion, getString(R.string.FlexyFilesSendCopyToChat), 13, true);
        row(actions, R.drawable.flexy_studio_share, getString(R.string.FlexyFilesShare), 4, false);
        if (zipEntry && text) {
            row(actions, R.drawable.msg_folders_archive, getString(R.string.FlexyFilesZipCopy), 9, false);
        }
        all.addView(actions);

        if (text) {
            section(all, getString(R.string.FlexyEditorToolsEdit));
            LinearLayout editing = card(c);
            LinearLayout quick = new LinearLayout(c);
            quick.setOrientation(LinearLayout.HORIZONTAL);
            quickAction(quick, "↶", getString(R.string.FlexyFilesUndo), 1);
            quickAction(quick, "↷", getString(R.string.FlexyFilesRedo), 2);
            quickAction(quick, "⌕", getString(R.string.Search), 10);
            editing.addView(quick, new LinearLayout.LayoutParams(-1, dp(68)));
            row(editing, R.drawable.msg_info, getString(R.string.FlexyFilesReplace), 11, false);
            row(editing, R.drawable.msg_info, getString(R.string.FlexyFilesIndent), 12, false);
            all.addView(editing);

            section(all, getString(R.string.FlexyEditorToolsAdvanced));
            LinearLayout advanced = card(c);
            row(advanced, R.drawable.msg_info, getString(R.string.FlexyFilesValidate), 7, false);
            if (html) row(advanced, R.drawable.msg_info, getString(R.string.FlexyFilesHtml), 8, false);
            row(advanced, R.drawable.flexy_studio_document, getString(R.string.FlexyFilesDraft), 6, false);
            all.addView(advanced);
        }

        ScrollView scroll = new ScrollView(c) {
            @Override protected void onMeasure(int width, int height) {
                int maximum = Math.min(View.MeasureSpec.getSize(height),
                        Math.max(dp(180), (int) (AndroidUtilities.displaySize.y * .66f)));
                super.onMeasure(width, View.MeasureSpec.makeMeasureSpec(maximum, View.MeasureSpec.AT_MOST));
            }
        };
        scroll.setFillViewport(false);
        scroll.addView(all, new ScrollView.LayoutParams(-1, -2));
        setCustomView(scroll);
    }

    private int color(int key) { return Theme.getColor(key, provider); }

    private TextView text(Context c, String label, int sp, int key) {
        TextView t = new TextView(c);
        t.setText(label);
        t.setTextSize(sp);
        t.setTextColor(color(key));
        t.setTextDirection(View.TEXT_DIRECTION_LOCALE);
        t.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
        return t;
    }

    private LinearLayout card(Context c) {
        LinearLayout card = new LinearLayout(c);
        card.setOrientation(LinearLayout.VERTICAL);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(color(Theme.key_windowBackgroundWhite));
        bg.setCornerRadius(dp(18));
        bg.setStroke(dp(1), color(Theme.key_divider));
        card.setBackground(bg);
        card.setClipToOutline(true);
        return card;
    }

    private void section(LinearLayout all, String text) {
        TextView t = text(all.getContext(), text, 12, Theme.key_windowBackgroundWhiteGrayText2);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.topMargin = dp(12);
        lp.bottomMargin = dp(7);
        lp.leftMargin = dp(4);
        all.addView(t, lp);
    }

    /** Three compact native controls; avoids a 12-row popup obscuring the editor. */
    private void quickAction(LinearLayout container, String glyph, String label, int action) {
        Context c = getContext();
        LinearLayout cell = new LinearLayout(c);
        cell.setOrientation(LinearLayout.VERTICAL);
        cell.setGravity(Gravity.CENTER);
        cell.setMinimumHeight(dp(60));
        TextView symbol = text(c, glyph, 21, Theme.key_windowBackgroundWhiteBlueText);
        symbol.setGravity(Gravity.CENTER);
        cell.addView(symbol, new LinearLayout.LayoutParams(-1, dp(29)));
        TextView caption = text(c, label, 12, Theme.key_windowBackgroundWhiteGrayText2);
        caption.setGravity(Gravity.CENTER);
        caption.setMaxLines(1); caption.setEllipsize(TextUtils.TruncateAt.END);
        cell.addView(caption, new LinearLayout.LayoutParams(-1, dp(20)));
        cell.setBackground(Theme.createSimpleSelectorRoundRectDrawable(dp(12),
                0x00000000, color(Theme.key_listSelector)));
        cell.setContentDescription(label);
        cell.setFocusable(true);
        cell.setOnClickListener(v -> { dismiss(); selection.selected(action); });
        container.addView(cell, new LinearLayout.LayoutParams(0, -1, 1));
    }

    private void row(LinearLayout container, int icon, String label, int action, boolean primary) {
        Context c = getContext();
        if (container.getChildCount() > 0) {
            View separator = new View(c);
            separator.setBackgroundColor(color(Theme.key_divider));
            LinearLayout.LayoutParams line = new LinearLayout.LayoutParams(-1, dp(1));
            line.leftMargin = dp(52); line.rightMargin = dp(14);
            container.addView(separator, line);
        }
        LinearLayout item = new LinearLayout(c);
        item.setGravity(Gravity.CENTER_VERTICAL);
        item.setOrientation(LinearLayout.HORIZONTAL);
        item.setPadding(dp(14), dp(7), dp(14), dp(7));
        item.setMinimumHeight(dp(52));
        item.setBackground(Theme.createSimpleSelectorRoundRectDrawable(dp(18),
                0x00000000, color(Theme.key_listSelector)));
        ImageView glyph = new ImageView(c);
        glyph.setImageResource(icon);
        glyph.setColorFilter(color(primary ? Theme.key_windowBackgroundWhiteBlueText
                                           : Theme.key_windowBackgroundWhiteBlackText));
        glyph.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        item.addView(glyph, new LinearLayout.LayoutParams(dp(21), dp(21)));
        TextView value = text(c, label, 15,
                primary ? Theme.key_windowBackgroundWhiteBlueText
                        : Theme.key_windowBackgroundWhiteBlackText);
        value.setPaddingRelative(dp(14), 0, 0, 0);
        if (primary) value.setTypeface(AndroidUtilities.bold());
        item.addView(value, new LinearLayout.LayoutParams(0, -2, 1));
        item.setContentDescription(label);
        item.setFocusable(true);
        item.setOnClickListener(v -> { dismiss(); selection.selected(action); });
        container.addView(item, new LinearLayout.LayoutParams(-1, -2));
    }
}
