/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.stickers;

import static org.telegram.messenger.AndroidUtilities.dp;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.FileLog;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.R;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ChatActivity;
import org.telegram.ui.ActionBar.BottomSheet;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.ChatMessageCell;
import org.telegram.ui.Components.BulletinFactory;
import org.telegram.ui.Components.LayoutHelper;
import java.io.File;
import java.io.InterruptedIOException;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.FutureTask;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Signature FlexyGram bottom sheet for previewing, sending directly, or saving
 * converted message bubbles as native Telegram static stickers.
 */
public final class FlexyStickerSheet extends BottomSheet {
    // One bounded encoder for all sheets. Idle threads expire instead of accumulating.
    private static final ThreadPoolExecutor ENCODER = new ThreadPoolExecutor(0, 1, 30,
            TimeUnit.SECONDS, new ArrayBlockingQueue<>(4), runnable -> new Thread(runnable, "FlexyStickerEncoder"));
    private FutureTask<Void> encodingTask;
    private boolean dismissed;


    private final ChatActivity fragment;

    private Bitmap capturedBitmap;
    private FlexyStickerEncoder.StickerBytes stickerBytes;
    private File stickerFile;
    private TLRPC.TL_document stickerDoc;

    private TextView sendButton;
    private TextView favoriteButton;
    private TextView exportButton;

    public static void show(ChatActivity fragment, ChatMessageCell cell, MessageObject message) {
        if (fragment == null || fragment.getParentActivity() == null || cell == null || message == null) {
            return;
        }
        try {
            FlexyStickerSheet sheet = new FlexyStickerSheet(fragment, cell, message);
            // Let fragment pause/navigation dismiss the preview and release its resources.
            if (fragment.showDialog(sheet) == null) sheet.dismiss();
        } catch (Throwable t) {
            FileLog.e(t);
        }
    }

    private FlexyStickerSheet(ChatActivity fragment, ChatMessageCell cell, MessageObject message) {
        super(fragment.getParentActivity(), false);
        this.fragment = fragment;

        final Context context = fragment.getParentActivity();
        setApplyTopPadding(false);
        setApplyBottomPadding(false);

        // Capture bubble synchronously on UI thread before views shift
        try {
            capturedBitmap = FlexyStickerEncoder.captureBubble(cell, message);
        } catch (Throwable t) {
            FileLog.e(t);
        }

        LinearLayout root = new LinearLayout(context);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(12), dp(20), dp(20));

        // Drag handle
        View handle = new View(context);
        GradientDrawable handleDrawable = new GradientDrawable();
        handleDrawable.setShape(GradientDrawable.RECTANGLE);
        handleDrawable.setColor(Theme.getColor(Theme.key_sheet_scrollUp, resourcesProvider));
        handleDrawable.setCornerRadius(dp(3));
        handle.setBackground(handleDrawable);
        root.addView(handle, LayoutHelper.createLinear(36, 4, Gravity.CENTER_HORIZONTAL, 0, 0, 0, 14));

        // Header Title
        TextView title = new TextView(context);
        title.setText(LocaleController.getString(R.string.FlexyContextConvertToSticker));
        title.setTextSize(18);
        title.setTypeface(AndroidUtilities.bold());
        title.setTextColor(Theme.getColor(Theme.key_dialogTextBlack, resourcesProvider));
        title.setGravity(Gravity.CENTER);
        root.addView(title, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 0, 0, 4));

        TextView subtitle = new TextView(context);
        subtitle.setText(LocaleController.getString(R.string.FlexyStickerSubtitle));
        subtitle.setTextSize(13);
        subtitle.setTextColor(Theme.getColor(Theme.key_dialogTextGray2, resourcesProvider));
        subtitle.setGravity(Gravity.CENTER);
        root.addView(subtitle, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 0, 0, 16));

        // Preview Container (frosted rounded frame)
        FrameLayout previewFrame = new FrameLayout(context);
        GradientDrawable frameBg = new GradientDrawable();
        frameBg.setColor(Theme.multAlpha(Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider), 0.5f));
        frameBg.setCornerRadius(dp(18));
        frameBg.setStroke(dp(1), Theme.multAlpha(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider), 0.2f));
        previewFrame.setBackground(frameBg);
        previewFrame.setPadding(dp(16), dp(16), dp(16), dp(16));

        ImageView previewImage = new ImageView(context);
        previewImage.setScaleType(ImageView.ScaleType.FIT_CENTER);
        if (capturedBitmap != null) {
            previewImage.setImageBitmap(capturedBitmap);
        }
        previewFrame.addView(previewImage, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, 180, Gravity.CENTER));
        root.addView(previewFrame, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 210, 0, 0, 0, 20));

        // Action 1: Enviar directamente en este chat
        sendButton = new TextView(context);
        sendButton.setText(LocaleController.getString(R.string.FlexyStickerSendDirect));
        sendButton.setTextSize(15);
        sendButton.setTypeface(AndroidUtilities.bold());
        sendButton.setTextColor(0xFFFFFFFF);
        sendButton.setGravity(Gravity.CENTER);

        GradientDrawable sendBg = new GradientDrawable();
        sendBg.setColor(Theme.getColor(Theme.key_featuredStickers_addButton, resourcesProvider));
        sendBg.setCornerRadius(dp(22));
        sendButton.setBackground(sendBg);
        sendButton.setPadding(dp(16), dp(12), dp(16), dp(12));
        sendButton.setEnabled(false);
        sendButton.setAlpha(0.5f);
        sendButton.setOnClickListener(v -> onSendClicked(false));
        root.addView(sendButton, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 46, 0, 0, 0, 10));

        // Action 2: Añadir a Favoritos
        favoriteButton = new TextView(context);
        favoriteButton.setText(LocaleController.getString(R.string.FlexyStickerSaveFavorite));
        favoriteButton.setTextSize(15);
        favoriteButton.setTypeface(AndroidUtilities.bold());
        favoriteButton.setTextColor(Theme.getColor(Theme.key_dialogTextBlack, resourcesProvider));
        favoriteButton.setGravity(Gravity.CENTER);

        GradientDrawable faveBg = new GradientDrawable();
        faveBg.setColor(Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider));
        faveBg.setCornerRadius(dp(22));
        faveBg.setStroke(dp(1), Theme.multAlpha(Theme.getColor(Theme.key_dialogTextBlack, resourcesProvider), 0.15f));
        favoriteButton.setBackground(faveBg);
        favoriteButton.setPadding(dp(16), dp(12), dp(16), dp(12));
        favoriteButton.setEnabled(false);
        favoriteButton.setAlpha(0.5f);
        favoriteButton.setOnClickListener(v -> onSendClicked(true));
        root.addView(favoriteButton, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 46, 0, 0, 0, 10));

        // Action 3: Exportar WebP local
        exportButton = new TextView(context);
        exportButton.setText(LocaleController.getString(R.string.FlexyStickerExportWebp));
        exportButton.setTextSize(13);
        exportButton.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText, resourcesProvider));
        exportButton.setGravity(Gravity.CENTER);
        exportButton.setPadding(dp(8), dp(6), dp(8), dp(6));
        exportButton.setEnabled(false);
        exportButton.setAlpha(0.5f);
        exportButton.setOnClickListener(v -> onExportClicked());
        root.addView(exportButton, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 0, 0, 4));

        setCustomView(root);

        // Encode in background thread
        startEncoding();
    }

    private void startEncoding() {
        if (capturedBitmap == null || dismissed || encodingTask != null) return;
        final AtomicReference<Bitmap> pendingBitmap = new AtomicReference<>(capturedBitmap.copy(Bitmap.Config.ARGB_8888, false));
        final File cacheDir = getContext().getCacheDir();
        encodingTask = new FutureTask<>(() -> {
            Bitmap bitmap = pendingBitmap.getAndSet(null);
            if (bitmap == null) return;
            File prepared = null;
            try {
                FlexyStickerEncoder.StickerBytes encoded = FlexyStickerEncoder.encodeAndRecycle(bitmap);
                if (Thread.currentThread().isInterrupted()) return;
                prepared = FlexyStickerEncoder.writeToCache(cacheDir, encoded);
                TLRPC.TL_document doc = FlexyStickerMetadata.create(encoded.width, encoded.height, encoded.bytes.length, "💬");
                if (Thread.currentThread().isInterrupted()) return;
                final File file = prepared;

                AndroidUtilities.runOnUIThread(() -> {
                    if (dismissed) { file.delete(); return; }
                    encodingTask = null;
                    stickerBytes = encoded;
                    stickerFile = file;
                    stickerDoc = doc;

                    if (sendButton != null) {
                        sendButton.setEnabled(true);
                        sendButton.setAlpha(1.0f);
                    }
                    if (favoriteButton != null) {
                        favoriteButton.setEnabled(true);
                        favoriteButton.setAlpha(1.0f);
                    }
                    if (exportButton != null) {
                        exportButton.setEnabled(true);
                        exportButton.setAlpha(1.0f);
                    }
                });
                prepared = null; // The queued UI callback now owns the file.
            } catch (Throwable t) {
                if (!(t instanceof InterruptedIOException)) FileLog.e(t);
            } finally {
                if (prepared != null) prepared.delete();
            }
        }, null) {
            @Override protected void done() {
                // A cancelled queued task never enters the encoder's finally block.
                Bitmap unused = pendingBitmap.getAndSet(null);
                if (unused != null && !unused.isRecycled()) unused.recycle();
            }
        };
        try {
            ENCODER.execute(encodingTask);
        } catch (RejectedExecutionException full) {
            encodingTask.cancel(false);
            encodingTask = null;
            FileLog.e(full);
        }
    }

    private void onSendClicked(boolean toFavorites) {
        if (stickerFile == null || stickerDoc == null) return;
        File source = stickerFile;
        stickerFile = null; // Transfer before dismiss() releases preview resources.
        AndroidUtilities.vibrateCursor(sendButton);
        dismiss();

        FlexyStickerSender.send(fragment, source, stickerDoc, toFavorites, new FlexyStickerSender.Callback() {
            @Override
            public void onSuccess(TLRPC.Document serverDoc) {
                int resId = toFavorites ? R.string.FlexyStickerSavedFavorite : R.string.FlexyStickerSent;
                int iconId = toFavorites ? R.drawable.stickers_favorites_remix : R.drawable.msg_send_remix;
                if (BulletinFactory.canShowBulletin(fragment)) {
                    BulletinFactory.of(fragment).createSimpleBulletin(iconId, LocaleController.getString(resId)).show();
                }
            }

            @Override
            public void onError(Throwable error) {
                if (error instanceof InterruptedIOException) return;
                FileLog.e(error);
                if (BulletinFactory.canShowBulletin(fragment)) {
                    BulletinFactory.of(fragment).createErrorBulletin(LocaleController.getString(R.string.ErrorOccurred)).show();
                }
            }
        });
    }

    private void onExportClicked() {
        if (stickerFile == null || !stickerFile.exists()) return;
        // The fragment retains the source while Android's document picker is open.
        if (!fragment.exportFlexySticker(stickerFile)) return;
        stickerFile = null;
        AndroidUtilities.vibrateCursor(exportButton);
        dismiss();
    }

    @Override
    public void dismiss() {
        dismissed = true;
        if (encodingTask != null) {
            encodingTask.cancel(true);
            ENCODER.remove(encodingTask);
            encodingTask = null;
        }
        if (stickerFile != null) {
            stickerFile.delete();
            stickerFile = null;
        }
        super.dismiss();
        if (capturedBitmap != null && !capturedBitmap.isRecycled()) {
            capturedBitmap.recycle();
            capturedBitmap = null;
        }
    }
}
