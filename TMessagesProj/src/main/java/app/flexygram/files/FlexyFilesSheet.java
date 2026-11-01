/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.drawable.GradientDrawable;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.files.core.SelectedDocument;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.BottomSheet;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.RecyclerListView;

import java.io.File;
import java.io.IOException;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;

/**
 * Signature Matte explorer for the *selected* local document only.
 *
 * Presentation-only successor to the original FlexyFilesSheet from PR #100.
 * Preserves SelectedDocument, FilesWork, ZIP filtering, explicit open, and
 * native Telegram editing/navigation. No global listener, background service,
 * WebView, new decoder, or work performed while FlexyFiles is dormant.
 */
final class FlexyFilesSheet extends BottomSheet {
    private final BaseFragment owner;
    private final File file;
    private final String name;
    private final long dialog;
    private final int account;
    private final FilesWork work = new FilesWork();
    private volatile SelectedDocument document;
    private List<SelectedDocument.Entry> entries = Collections.emptyList();
    private List<Row> rows = Collections.emptyList();
    // UI-thread-only, bounded folder cache: repeat ZIP navigation does no rescanning.
    private final LinkedHashMap<String, List<Row>> folderCache =
            new LinkedHashMap<String, List<Row>>(8, .75f, true) {
                @Override protected boolean removeEldestEntry(java.util.Map.Entry<String, List<Row>> oldest) {
                    return size() > 8;
                }
            };
    private String path = "";
    private boolean closed;
    private final boolean restored;
    private android.os.Parcelable pendingScroll;

    private final LinearLayout location;
    private final TextView breadcrumb;
    private final TextView status;
    private final TextView itemCount;
    private final TextView emptyLabel;
    private final ImageView navigateUp;
    private final EditText query;
    private final RecyclerListView list;
    private final Adapter adapter = new Adapter();
    private final int maximumListHeight;
    private final TextView browserLabel;
    private final LinearLayout browserPanel;
    private final FlexyFilesNativePreview previewPanel;
    private final ScrollView sheetScroll;
    private boolean previewing;
    private String previewEntry;

    private static final class Row {
        final String path;
        final String label;
        final boolean folder;
        final long size;

        Row(String path, String label, boolean folder, long size) {
            this.path = path;
            this.label = label;
            this.folder = folder;
            this.size = size;
        }
    }

    FlexyFilesSheet(BaseFragment owner, File file, String name, long dialog, int account) {
        this(owner, file, name, dialog, account, "");
    }
    /** Restore the ZIP folder after leaving the editor, without holding the old sheet alive. */
    FlexyFilesSheet(BaseFragment owner, File file, String name, long dialog, int account, String initialPath) {
        this(owner, file, name, dialog, account, initialPath, false);
    }
    /** Restored single-file overview prevents closing directly to Telegram chat. */
    FlexyFilesSheet(BaseFragment owner, File file, String name, long dialog, int account, String initialPath, boolean restored) {
        this(owner,file,name,dialog,account,initialPath,restored,"",null);
    }
    FlexyFilesSheet(BaseFragment owner,File file,String name,long dialog,int account,String initialPath,boolean restored,String initialQuery,android.os.Parcelable scroll){
        super(owner.getParentActivity(), true, owner.getResourceProvider());
        this.owner = owner;
        this.file = file;
        this.name = name;
        this.dialog = dialog;
        this.account = account;
        this.path = initialPath == null ? "" : initialPath;
        this.restored = restored;
        this.pendingScroll=scroll;

        Context c = getContext();
        setApplyTopPadding(false);
        setBackgroundColor(color(Theme.key_windowBackgroundGray));

        LinearLayout root = vertical(c);
        root.setPadding(dp(18), dp(18), dp(18), dp(16));
        root.setFocusableInTouchMode(true);root.requestFocus();

        TextView title = text(c, getString(R.string.FlexyFilesExplore), 21,
                Theme.key_windowBackgroundWhiteBlackText);
        title.setTypeface(AndroidUtilities.bold());
        add(root, title, 0, 14);

        // Same informational card vocabulary as FlexyStudioSheet (.flexyGram Apply).
        LinearLayout information = horizontal(c);
        information.setGravity(Gravity.CENTER_VERTICAL);
        information.setPadding(dp(14), dp(14), dp(14), dp(14));
        information.setBackground(card());

        ImageView documentIcon = icon(c, R.drawable.flexy_studio_document,
                Theme.key_windowBackgroundWhiteBlueText);
        information.addView(documentIcon, new LinearLayout.LayoutParams(dp(44), dp(54)));

        LinearLayout details = vertical(c);
        details.setPaddingRelative(dp(14), 0, 0, 0);
        TextView filename = text(c, name, 16, Theme.key_windowBackgroundWhiteBlackText);
        filename.setTypeface(AndroidUtilities.bold());
        filename.setMaxLines(2);
        filename.setEllipsize(TextUtils.TruncateAt.MIDDLE);
        details.addView(filename);

        status = text(c, getString(R.string.Loading), 13,
                Theme.key_windowBackgroundWhiteGrayText2);
        status.setMaxLines(2);
        status.setEllipsize(TextUtils.TruncateAt.END);
        add(details, status, 5, 0);
        information.addView(details, new LinearLayout.LayoutParams(0, -2, 1f));
        add(root, information, 0, 14);

        TextView sectionLabel = text(c,
                getString(R.string.FlexyFilesSignatureContents), 12,
                Theme.key_windowBackgroundWhiteBlueText);
        sectionLabel.setTypeface(AndroidUtilities.bold());
        add(root, sectionLabel, 0, 8);
        browserLabel = sectionLabel;

        LinearLayout content = vertical(c);
        content.setBackground(card());
        content.setPadding(dp(10), dp(6), dp(10), dp(8));

        location = horizontal(c);
        location.setGravity(Gravity.CENTER_VERTICAL);
        location.setMinimumHeight(dp(48));
        location.setBackground(Theme.createSimpleSelectorRoundRectDrawable(
                dp(12), 0x00000000, color(Theme.key_listSelector)));
        navigateUp = icon(c, R.drawable.ic_ab_back,
                Theme.key_windowBackgroundWhiteGrayIcon);
        LinearLayout.LayoutParams backParams = new LinearLayout.LayoutParams(dp(20), dp(20));
        backParams.setMarginStart(dp(10));
        backParams.setMarginEnd(dp(12));
        location.addView(navigateUp, backParams);
        breadcrumb = text(c, "/", 14, Theme.key_windowBackgroundWhiteBlackText);
        breadcrumb.setSingleLine(true);
        breadcrumb.setEllipsize(TextUtils.TruncateAt.MIDDLE);
        location.addView(breadcrumb, new LinearLayout.LayoutParams(0, -2, 1f));
        location.setOnClickListener(v -> goUp());
        location.setContentDescription(getString(R.string.FlexyFilesSignatureParent));
        add(content, location, 0, 6);

        LinearLayout search = horizontal(c);
        search.setGravity(Gravity.CENTER_VERTICAL);
        search.setPadding(dp(12), 0, dp(12), 0);
        search.setBackground(rounded(color(Theme.key_windowBackgroundGray), dp(13), 0, 0));
        SearchMark searchMark = new SearchMark(c,
                color(Theme.key_windowBackgroundWhiteGrayIcon));
        search.addView(searchMark, new LinearLayout.LayoutParams(dp(20), dp(20)));
        query = new EditText(c);
        query.setFocusableInTouchMode(true);
        query.setBackground(null);
        query.setSingleLine(true);
        query.setTextSize(15);
        query.setPaddingRelative(dp(10), 0, dp(4), 0);
        query.setHint(getString(R.string.Search));
        query.setTextColor(color(Theme.key_windowBackgroundWhiteBlackText));
        query.setHintTextColor(color(Theme.key_windowBackgroundWhiteGrayText2));
        query.setEnabled(false);
        query.setText(initialQuery);
        query.setMaxLines(1);
        query.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH);
        search.addView(query, new LinearLayout.LayoutParams(0, dp(48), 1f));
        add(content, search, 0, 8);

        itemCount = text(c, "", 12, Theme.key_windowBackgroundWhiteGrayText2);
        itemCount.setPaddingRelative(dp(10), dp(2), 0, dp(6));
        content.addView(itemCount);

        list = new RecyclerListView(c);
        list.setLayoutManager(new LinearLayoutManager(c));
        list.setAdapter(adapter);
        list.setClipToPadding(false);
        list.setNestedScrollingEnabled(true);
        list.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
        list.setOnItemClickListener((view, position) -> {
            if (closed || position < 0 || position >= rows.size()) return;
            Row selected = rows.get(position);
            if (selected.folder) {
                path = selected.path;
                if (query.length() == 0) filter();
                else query.setText("");
            } else {
                openPreview(document != null && document.isArchive() ? selected.path : null,
                        selected.label, selected.size);
            }
        });
        // Keep the sheet compact, even on phones using enlarged font scaling.
        maximumListHeight = Math.min(dp(306), Math.max(dp(132),
                (int) (AndroidUtilities.displaySize.y * .80f) - dp(385)));
        content.addView(list, new LinearLayout.LayoutParams(-1, dp(70)));

        emptyLabel = text(c, getString(R.string.FlexyFilesSignatureEmpty), 14,
                Theme.key_windowBackgroundWhiteGrayText2);
        emptyLabel.setGravity(Gravity.CENTER);
        emptyLabel.setMinHeight(dp(70));
        emptyLabel.setVisibility(View.GONE);
        content.addView(emptyLabel, new LinearLayout.LayoutParams(-1, -2));
        add(root, content, 0, 12);
        browserPanel = content;

        // Native bounded preview: same BottomSheet, no new fragment or sheet animation.
        previewPanel = new FlexyFilesNativePreview(c, owner.getResourceProvider(),
                this::leavePreview, this::editPreview);
        previewPanel.setVisibility(View.GONE);
        add(root, previewPanel, 0, 12);

        TextView reassurance = text(c,
                getString(R.string.FlexyFilesSignatureOriginal), 12,
                Theme.key_windowBackgroundWhiteGrayText2);
        reassurance.setGravity(Gravity.CENTER);
        add(root, reassurance, 0, 9);

        TextView close = text(c, getString(R.string.Close), 16,
                Theme.key_windowBackgroundWhiteBlueText);
        close.setGravity(Gravity.CENTER);
        close.setTypeface(AndroidUtilities.bold());
        close.setMinHeight(dp(48));
        close.setBackground(Theme.createSimpleSelectorRoundRectDrawable(
                dp(16), color(Theme.key_windowBackgroundWhite),
                color(Theme.key_listSelector)));
        close.setOnClickListener(v -> dismiss());
        close.setFocusable(true);
        close.setContentDescription(getString(R.string.Close));
        root.addView(close, new LinearLayout.LayoutParams(-1, -2));

        query.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int st, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int st, int before, int count) {
                filter();
            }
            @Override public void afterTextChanged(Editable value) {}
        });
        // Match FlexyStudioSheet: fit short phones, landscape and large-font UI.
        // ZIP rows remain in their own bounded/recycled list.
        ScrollView container = new ScrollView(c) {
            @Override protected void onMeasure(int widthSpec, int heightSpec) {
                int maximum = Math.max(dp(160), (int) (AndroidUtilities.displaySize.y * .86f));
                super.onMeasure(widthSpec, MeasureSpec.makeMeasureSpec(
                        Math.min(MeasureSpec.getSize(heightSpec), maximum), MeasureSpec.AT_MOST));
            }
        };
        container.setFillViewport(false);
        container.setVerticalScrollBarEnabled(false);
        container.addView(root, new android.widget.FrameLayout.LayoutParams(-1, -2));
        sheetScroll = container;
        setCustomView(container);
        setOnDismissListener(d -> dispose());
        refreshLocation();
        load();
    }

    private int color(int key) {
        return Theme.getColor(key, owner.getResourceProvider());
    }

    private GradientDrawable rounded(int fill, float radius, int stroke, int strokeColor) {
        GradientDrawable result = new GradientDrawable();
        result.setColor(fill);
        result.setCornerRadius(radius);
        if (stroke != 0) result.setStroke(stroke, strokeColor);
        return result;
    }

    private GradientDrawable card() {
        return rounded(color(Theme.key_windowBackgroundWhite), dp(18),
                dp(1), color(Theme.key_divider));
    }

    private static LinearLayout vertical(Context c) {
        LinearLayout v = new LinearLayout(c);
        v.setOrientation(LinearLayout.VERTICAL);
        return v;
    }

    private static LinearLayout horizontal(Context c) {
        LinearLayout v = new LinearLayout(c);
        v.setOrientation(LinearLayout.HORIZONTAL);
        return v;
    }

    private TextView text(Context c, String value, int size, int key) {
        TextView t = new TextView(c);
        t.setText(value);
        t.setTextSize(size);
        t.setTextColor(color(key));
        t.setTextDirection(View.TEXT_DIRECTION_LOCALE);
        t.setGravity(Gravity.START);
        return t;
    }

    private ImageView icon(Context c, int resource, int tint) {
        ImageView result = new ImageView(c);
        result.setImageResource(resource);
        result.setColorFilter(color(tint));
        result.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        return result;
    }

    private static void add(LinearLayout parent, View child, int top, int bottom) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.topMargin = dp(top);
        params.bottomMargin = dp(bottom);
        parent.addView(child, params);
    }

    private void refreshLocation() {
        breadcrumb.setText(path.isEmpty() ? "/" : "/" + path);
        navigateUp.setAlpha(path.isEmpty() ? .35f : 1f);
        location.setEnabled(!path.isEmpty());
        itemCount.setText(String.format(Locale.getDefault(),
                getString(R.string.FlexyFilesSignatureCount), rows.size()));
        emptyLabel.setVisibility(rows.isEmpty() && document != null ? View.VISIBLE : View.GONE);
        list.setVisibility(rows.isEmpty() ? View.GONE : View.VISIBLE);
        int height = Math.max(dp(70), Math.min(maximumListHeight,
                Math.min(5, rows.size()) * dp(61)));
        ViewGroup.LayoutParams layout = list.getLayoutParams();
        if (layout.height != height) {
            layout.height = height;
            list.setLayoutParams(layout);
        }
    }

    /** Back returns to the already-allocated explorer before touching ZIP navigation. */
    @Override public void onBackPressed() {
        if (previewing) { leavePreview(); return; }
        if (query != null && query.length() > 0) { query.setText(""); return; }
        if (!path.isEmpty()) { goUp(); return; }
        super.onBackPressed();
    }
    private void goUp() {
        if (path.isEmpty() || closed) return;
        String withoutSlash = path.substring(0, path.length() - 1);
        int last = withoutSlash.lastIndexOf('/');
        path = last < 0 ? "" : withoutSlash.substring(0, last + 1);
        if (query.length() == 0) filter();
        else query.setText("");
    }

    private void load() {
        WeakReference<FlexyFilesSheet> weak = new WeakReference<>(this);
        FilesWork tasks = work;
        File selected = file;
        int token = tasks.token() + 1;
        tasks.submit(() -> {
            SelectedDocument opened = null;
            try {
                opened = new SelectedDocument(selected);
                List<SelectedDocument.Entry> index = opened.entries();
                SelectedDocument ready = opened;
                if (!tasks.current(token)) {
                    opened.close();
                    return;
                }
                AndroidUtilities.runOnUIThread(() -> {
                    FlexyFilesSheet sheet = weak.get();
                    if (sheet == null || !tasks.current(token)) {
                        try { ready.close(); } catch (IOException ignored) {}
                        return;
                    }
                    sheet.document = ready;
                    sheet.entries = index;
                    sheet.status.setText((ready.isArchive() ? "ZIP" :
                            getString(R.string.FlexyFilesSignatureDocument)) + " · " +
                            AndroidUtilities.formatFileSize(ready.size()));
                    sheet.query.setEnabled(true);
                    if (!ready.isArchive()) {
                        sheet.rows = Collections.singletonList(new Row(sheet.name, sheet.name, false, ready.size()));
                        sheet.refreshLocation();
                        sheet.adapter.notifyDataSetChanged();
                        sheet.openPreview(null, sheet.name, ready.size());
                    } else sheet.filter();
                });
            } catch (Exception invalid) {
                if (opened != null) try { opened.close(); } catch (IOException ignored) {}
                AndroidUtilities.runOnUIThread(() -> {
                    FlexyFilesSheet sheet = weak.get();
                    if (sheet != null && tasks.current(token)) {
                        sheet.status.setText(getString(R.string.FlexyFilesError));
                        sheet.emptyLabel.setText(getString(R.string.FlexyFilesError));
                        sheet.emptyLabel.setVisibility(View.VISIBLE);
                        sheet.list.setVisibility(View.GONE);
                    }
                });
            }
        });
    }

    /**
     * Dispatch only one bounded read on the existing instance-owned worker.
     * Render either recycled text chunks or a sampled image inside this sheet.
     */
    private void openPreview(String entry, String label, long size) {
        if (closed || document == null) return;
        previewing = true;
        previewEntry = entry;
        browserLabel.setVisibility(View.GONE);
        browserPanel.setVisibility(View.GONE);
        previewPanel.setVisibility(View.VISIBLE);
        previewPanel.loading(label);
        sheetScroll.scrollTo(0, 0);

        boolean imageFile = FlexyFilesNativePreview.isImage(label);
        int limit = imageFile ? FlexyFilesNativePreview.MAX_IMAGE_BYTES : SelectedDocument.MAX_TEXT;
        // Never ask the worker to allocate a file larger than its preview budget.
        work.cancel();
        if (size > limit) {
            previewPanel.unavailable(true);
            return;
        }
        SelectedDocument selected = document;
        FilesWork tasks = work;
        int token = tasks.token() + 1;
        WeakReference<FlexyFilesSheet> weak = new WeakReference<>(this);
        tasks.submit(() -> {
            Object parsed = null;
            try {
                byte[] bytes = selected.read(entry, limit);
                if (imageFile) {
                    parsed = FlexyFilesNativePreview.decodeImage(bytes);
                } else {
                    parsed = new FlexyFilesNativePreview.TextData(SelectedDocument.text(bytes));
                }
            } catch (Exception invalid) {
                // Unsupported or malformed files stay in the read-only safety state.
            }
            Object ready = parsed;
            AndroidUtilities.runOnUIThread(() -> {
                FlexyFilesSheet sheet = weak.get();
                if (sheet == null || sheet.closed || !tasks.current(token)
                        || !sheet.previewing || !TextUtils.equals(sheet.previewEntry, entry)) {
                    if (ready instanceof android.graphics.Bitmap) {
                        ((android.graphics.Bitmap) ready).recycle();
                    }
                    return;
                }
                if (ready instanceof FlexyFilesNativePreview.TextData) {
                    sheet.previewPanel.showText((FlexyFilesNativePreview.TextData) ready);
                } else if (ready instanceof android.graphics.Bitmap) {
                    sheet.previewPanel.showImage((android.graphics.Bitmap) ready);
                } else {
                    sheet.previewPanel.unavailable(false);
                }
            });
        });
    }

    /** No IO, no re-indexing and no view reconstruction on returning to a folder. */
    private void leavePreview() {
        if (!previewing || closed) return;
        work.cancel();
        previewing = false;
        previewEntry = null;
        previewPanel.release();
        previewPanel.setVisibility(View.GONE);
        browserLabel.setVisibility(View.VISIBLE);
        browserPanel.setVisibility(View.VISIBLE);
        sheetScroll.scrollTo(0, 0);
    }

    /** Keep all existing editor tools and save-a-copy protections intact. */
    private void editPreview() {
        if (!previewing || closed || owner.getParentActivity() == null) return;
        if (owner.presentFragment(new FlexyFileEditorActivity(
                file, name, previewEntry, dialog, account, owner, path)
                .returnContext(query.getText().toString(),
                        list.getLayoutManager().onSaveInstanceState()))) {
            dismiss();
        }
    }

    private void filter() {
        if (document == null || closed) return;
        String prefix = path;
        String search = query.getText().toString().toLowerCase(Locale.ROOT);
        if (search.isEmpty()) {
            List<Row> cached = folderCache.get(prefix);
            if (cached != null) {
                work.cancel();
                rows = cached;
                refreshLocation();
                adapter.notifyDataSetChanged();
                return;
            }
        }
        List<SelectedDocument.Entry> source = entries;
        WeakReference<FlexyFilesSheet> weak = new WeakReference<>(this);
        FilesWork tasks = work;
        int token = tasks.token() + 1;
        tasks.submit(() -> {
            LinkedHashMap<String, Row> found = new LinkedHashMap<>();
            for (SelectedDocument.Entry entry : source) {
                if (Thread.currentThread().isInterrupted()) return;
                if (!entry.path.startsWith(prefix)) continue;
                String tail = entry.path.substring(prefix.length());
                if (tail.isEmpty()) continue;
                int slash = tail.indexOf('/');
                boolean folder = slash >= 0 || entry.directory;
                String label = search.isEmpty() ?
                        (slash < 0 ? tail : tail.substring(0, slash)) : tail;
                if (!search.isEmpty() && !tail.toLowerCase(Locale.ROOT).contains(search))
                    continue;
                String foundPath = search.isEmpty() ?
                        prefix + label + (folder ? "/" : "") :
                        entry.path + (entry.directory ? "/" : "");
                boolean directory = search.isEmpty() ? folder : entry.directory;
                long size = directory ? -1L : entry.size;
                found.put(foundPath, new Row(foundPath, label, directory, size));
            }
            ArrayList<Row> result = new ArrayList<>(found.values());
            result.sort(Comparator.comparing((Row r) -> !r.folder)
                    .thenComparing(r -> r.label, String.CASE_INSENSITIVE_ORDER));
            AndroidUtilities.runOnUIThread(() -> {
                FlexyFilesSheet sheet = weak.get();
                if (sheet == null || !tasks.current(token)) return;
                sheet.rows = result;
                if (search.isEmpty() && result.size() <= 128) {
                    sheet.folderCache.put(prefix, result);
                }
                sheet.refreshLocation();
                sheet.adapter.notifyDataSetChanged();
                if(sheet.pendingScroll!=null){sheet.list.getLayoutManager().onRestoreInstanceState(sheet.pendingScroll);sheet.pendingScroll=null;}
            });
        });
    }

    private static String extension(String filename) {
        int separator = filename.lastIndexOf('/');
        int index = filename.lastIndexOf('.');
        if (index <= separator || index < 0 || index == filename.length() - 1)
            return "";
        String extension = filename.substring(index + 1);
        return extension.length() > 8 ? "" : extension.toUpperCase(Locale.ROOT);
    }

    private void dispose() {
        if (closed) return;
        closed = true;
        work.close();
        previewPanel.release();
        SelectedDocument old = document;
        document = null;
        if (old != null) try { old.close(); } catch (IOException ignored) {}
        entries = Collections.emptyList();
        rows = Collections.emptyList();
        folderCache.clear();
        query.clearFocus();
    }

    @Override public void dismiss() {
        dispose();
        super.dismiss();
    }

    /** Lightweight icon, used only while the selected file sheet is visible. */
    private static final class SearchMark extends View {
        private final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
        SearchMark(Context c, int color) {
            super(c);
            stroke.setStyle(Paint.Style.STROKE);
            stroke.setStrokeCap(Paint.Cap.ROUND);
            stroke.setStrokeWidth(dp(2));
            stroke.setColor(color);
            setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        }
        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            float x = getWidth() * .43f, y = getHeight() * .43f;
            float radius = Math.min(getWidth(), getHeight()) * .25f;
            canvas.drawCircle(x, y, radius, stroke);
            canvas.drawLine(x + radius * .72f, y + radius * .72f,
                    x + radius * 1.52f, y + radius * 1.52f, stroke);
        }
    }

    private final class FileRowView extends LinearLayout {
        private final ImageView symbol;
        private final ImageView arrow;
        private final TextView title;
        private final TextView subtitle;
        private final View divider;
        FileRowView(Context context) {
            super(context);
            setOrientation(VERTICAL);
            LinearLayout main = horizontal(context);
            main.setGravity(Gravity.CENTER_VERTICAL);
            main.setMinimumHeight(dp(60));
            main.setPaddingRelative(dp(10), dp(7), dp(10), dp(7));
            main.setBackground(Theme.createSimpleSelectorRoundRectDrawable(
                    dp(12), 0x00000000, color(Theme.key_listSelector)));
            symbol = icon(context, R.drawable.flexy_studio_document,
                    Theme.key_windowBackgroundWhiteGrayIcon);
            LinearLayout.LayoutParams symbolParams =
                    new LinearLayout.LayoutParams(dp(23), dp(27));
            symbolParams.setMarginEnd(dp(14));
            main.addView(symbol, symbolParams);

            LinearLayout lines = vertical(context);
            title = text(context, "", 15, Theme.key_windowBackgroundWhiteBlackText);
            title.setMaxLines(1);
            title.setEllipsize(TextUtils.TruncateAt.MIDDLE);
            lines.addView(title);
            subtitle = text(context, "", 12, Theme.key_windowBackgroundWhiteGrayText2);
            subtitle.setSingleLine(true);
            add(lines, subtitle, 3, 0);
            main.addView(lines, new LinearLayout.LayoutParams(0, -2, 1f));
            arrow = icon(context, R.drawable.round_keyboard_arrow_right_24,
                    Theme.key_windowBackgroundWhiteGrayIcon);
            LinearLayout.LayoutParams arrowParams =
                    new LinearLayout.LayoutParams(dp(20), dp(20));
            arrowParams.setMarginStart(dp(7));
            main.addView(arrow, arrowParams);
            addView(main, new LinearLayout.LayoutParams(-1, -2));
            divider = new View(context);
            divider.setBackgroundColor(color(Theme.key_divider));
            LinearLayout.LayoutParams lineParams = new LinearLayout.LayoutParams(-1, dp(1));
            lineParams.setMarginStart(dp(46));
            addView(divider, lineParams);
        }
        void bind(Row row, boolean last) {
            symbol.setImageResource(row.folder ? R.drawable.msg_folders_archive :
                    R.drawable.flexy_studio_document);
            symbol.setColorFilter(color(row.folder ?
                    Theme.key_windowBackgroundWhiteBlueText :
                    Theme.key_windowBackgroundWhiteGrayIcon));
            title.setText(row.label);
            String detail = row.folder ? getString(R.string.FlexyFilesSignatureFolder) :
                    extension(row.label);
            if (!row.folder && row.size >= 0) {
                String size = AndroidUtilities.formatFileSize(row.size);
                detail = detail.isEmpty() ? size : detail + " · " + size;
            } else if (!row.folder && detail.isEmpty())
                detail = getString(R.string.FlexyFilesSignatureDocument);
            subtitle.setText(detail);
            arrow.setVisibility(row.folder ? View.VISIBLE : View.GONE);
            arrow.setScaleX(org.telegram.messenger.LocaleController.isRTL ? -1f : 1f);
            divider.setVisibility(last ? View.GONE : View.VISIBLE);
            setContentDescription(row.label + ", " + detail);
        }
    }

    private final class Adapter extends RecyclerListView.SelectionAdapter {
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) {
            return !closed;
        }
        @Override public int getItemCount() {
            return rows.size();
        }
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int type) {
            FileRowView view = new FileRowView(parent.getContext());
            view.setLayoutParams(new RecyclerView.LayoutParams(-1, -2));
            return new RecyclerListView.Holder(view);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position) {
            ((FileRowView) holder.itemView).bind(rows.get(position), position == rows.size() - 1);
        }
    }
}
