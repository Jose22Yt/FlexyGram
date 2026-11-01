/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Typeface;
import android.text.Layout;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.files.core.SelectedDocument;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.RecyclerListView;

import java.util.ArrayList;
import java.util.Locale;

/**
 * One native Telegram-style read-only surface for the selected file.
 *
 * Created only when the user opens FlexyFiles. No WebView, extra Fragment,
 * animation clock, eager file scan or heavy work on the UI thread.
 * The archive index and the original editor remain owned by FlexyFilesSheet.
 */
final class FlexyFilesNativePreview extends LinearLayout {
    static final int MAX_IMAGE_BYTES = 4 * 1024 * 1024;
    private static final int MAX_IMAGE_PIXELS = 32_000_000;
    private static final int TEXT_CHUNK = 3072;

    private final TextView title;
    private final TextView info;
    private final TextView edit;
    private final RecyclerListView textList;
    private final ImageView image;
    private final ArrayList<String> pages = new ArrayList<>();
    private final TextAdapter adapter = new TextAdapter();

    static final class TextData {
        final ArrayList<String> chunks = new ArrayList<>();
        final String encoding;
        final String newline;
        TextData(SelectedDocument.Text text) {
            encoding = text.encoding;
            newline = text.newline;
            String value = text.value;
            int start = 0;
            while (start < value.length()) {
                int end = Math.min(start + TEXT_CHUNK, value.length());
                if (end < value.length()) {
                    int lastLine = value.lastIndexOf('\n', end - 1);
                    if (lastLine >= start + TEXT_CHUNK / 2) end = lastLine + 1;
                }
                chunks.add(value.substring(start, end));
                start = end;
            }
            if (chunks.isEmpty()) chunks.add("");
        }
    }

    FlexyFilesNativePreview(Context context, Theme.ResourcesProvider provider,
                            Runnable onBack, Runnable onEdit) {
        super(context);
        setOrientation(VERTICAL);
        setPadding(dp(6), dp(4), dp(6), dp(8));
        setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite, provider));

        LinearLayout toolbar = new LinearLayout(context);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        TextView back = action(context, getString(R.string.FlexyFilesNativeBack),
                Theme.getColor(Theme.key_windowBackgroundWhiteBlueText, provider));
        back.setOnClickListener(v -> onBack.run());
        toolbar.addView(back, new LayoutParams(0, dp(48), 1));

        edit = action(context, getString(R.string.FlexyFilesNativeEdit),
                Theme.getColor(Theme.key_windowBackgroundWhiteBlueText, provider));
        edit.setOnClickListener(v -> onEdit.run());
        toolbar.addView(edit, new LayoutParams(-2, dp(48)));
        addView(toolbar, new LayoutParams(-1, -2));

        title = new TextView(context);
        title.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText, provider));
        title.setTextSize(18);
        title.setTypeface(org.telegram.messenger.AndroidUtilities.bold());
        title.setSingleLine(true);
        title.setEllipsize(TextUtils.TruncateAt.MIDDLE);
        title.setPadding(dp(12), dp(6), dp(12), dp(4));
        addView(title, new LayoutParams(-1, -2));

        info = new TextView(context);
        info.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2, provider));
        info.setTextSize(12);
        info.setPadding(dp(12), dp(2), dp(12), dp(8));
        addView(info, new LayoutParams(-1, -2));

        textList = new RecyclerListView(context);
        textList.setLayoutManager(new LinearLayoutManager(context));
        textList.setAdapter(adapter);
        textList.setItemAnimator(null);
        textList.setItemViewCacheSize(3);
        textList.setHasFixedSize(true);
        textList.setClipToPadding(false);
        textList.setNestedScrollingEnabled(true);
        textList.setOverScrollMode(OVER_SCROLL_IF_CONTENT_SCROLLS);
        textList.setVisibility(GONE);
        addView(textList, new LayoutParams(-1, dp(440)));

        image = new ImageView(context);
        image.setAdjustViewBounds(true);
        image.setScaleType(ImageView.ScaleType.FIT_CENTER);
        image.setMaxHeight(dp(440));
        image.setVisibility(GONE);
        addView(image, new LayoutParams(-1, -2));
    }

    private static TextView action(Context context, String value, int color) {
        TextView view = new TextView(context);
        view.setText(value);
        view.setTextSize(15);
        view.setTextColor(color);
        view.setGravity(Gravity.CENTER_VERTICAL);
        view.setPadding(dp(12), 0, dp(12), 0);
        view.setBackground(Theme.createSimpleSelectorRoundRectDrawable(
                dp(12), 0x00000000, 0x12000000));
        return view;
    }

    void loading(String filename) {
        title.setText(filename);
        info.setText(getString(R.string.Loading));
        edit.setEnabled(false);
        edit.setAlpha(.5f);
        pages.clear();
        adapter.notifyDataSetChanged();
        image.setImageDrawable(null);
        textList.setVisibility(GONE);
        image.setVisibility(GONE);
    }

    void showText(TextData data) {
        pages.clear();
        pages.addAll(data.chunks);
        adapter.notifyDataSetChanged();
        textList.scrollToPosition(0);
        textList.setVisibility(VISIBLE);
        image.setVisibility(GONE);
        info.setText(data.encoding + " · " + data.newline);
        enableEdit();
    }

    void showImage(Bitmap bitmap) {
        pages.clear();
        adapter.notifyDataSetChanged();
        image.setImageBitmap(bitmap);
        image.setVisibility(VISIBLE);
        textList.setVisibility(GONE);
        info.setText(getString(R.string.FlexyFilesNativeImage));
        enableEdit();
    }

    void unavailable(boolean oversized) {
        pages.clear();
        adapter.notifyDataSetChanged();
        image.setImageDrawable(null);
        image.setVisibility(GONE);
        textList.setVisibility(GONE);
        info.setText(getString(oversized
                ? R.string.FlexyFilesNativeTooLarge
                : R.string.FlexyFilesNativeUnsupported));
        enableEdit();
    }

    void release() {
        image.setImageDrawable(null);
        pages.clear();
        adapter.notifyDataSetChanged();
        textList.setVisibility(GONE);
    }

    private void enableEdit() {
        edit.setEnabled(true);
        edit.setAlpha(1f);
    }

    static boolean isImage(String filename) {
        String n = filename.toLowerCase(Locale.ROOT);
        return n.endsWith(".png") || n.endsWith(".jpg") || n.endsWith(".jpeg") || n.endsWith(".webp");
    }

    /** Decode sampling and validation run on the selected-file worker, never UI. */
    static Bitmap decodeImage(byte[] bytes) {
        if (bytes.length > MAX_IMAGE_BYTES) return null;
        BitmapFactory.Options options = new BitmapFactory.Options();
        options.inJustDecodeBounds = true;
        BitmapFactory.decodeByteArray(bytes, 0, bytes.length, options);
        if (options.outWidth <= 0 || options.outHeight <= 0
                || (long) options.outWidth * options.outHeight > MAX_IMAGE_PIXELS) return null;
        options.inJustDecodeBounds = false;
        options.inPreferredConfig = Bitmap.Config.RGB_565;
        options.inSampleSize = 1;
        while (options.outWidth / options.inSampleSize > 1600
                || options.outHeight / options.inSampleSize > 1600) {
            options.inSampleSize *= 2;
        }
        try {
            return BitmapFactory.decodeByteArray(bytes, 0, bytes.length, options);
        } catch (OutOfMemoryError exhausted) {
            return null;
        }
    }

    private final class TextAdapter extends RecyclerListView.SelectionAdapter {
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) { return false; }
        @Override public int getItemCount() { return pages.size(); }
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int type) {
            TextView cell = new TextView(parent.getContext());
            cell.setTextSize(14);
            cell.setTypeface(Typeface.MONOSPACE);
            cell.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            cell.setBreakStrategy(Layout.BREAK_STRATEGY_SIMPLE);
            cell.setHyphenationFrequency(Layout.HYPHENATION_FREQUENCY_NONE);
            cell.setIncludeFontPadding(false);
            cell.setPadding(dp(12), 0, dp(12), 0);
            cell.setTextIsSelectable(true);
            cell.setLayoutParams(new RecyclerView.LayoutParams(-1, -2));
            return new RecyclerListView.Holder(cell);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position) {
            ((TextView) holder.itemView).setText(pages.get(position));
        }
    }
}
