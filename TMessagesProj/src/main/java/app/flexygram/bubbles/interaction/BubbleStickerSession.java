/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.graphics.Bitmap;
import java.io.File;
import java.lang.ref.WeakReference;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;
import java.util.function.Supplier;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.tgnet.TLRPC;

/** One menu lease; closes on native panel detach. No Activity retained by a pending upload. */
public final class BubbleStickerSession implements BubbleStickerWorkflow.Listener {
    private final WeakReference<BubbleActionPanelView> panel;
    private final BubbleStickerWorkflow workflow;
    private BooleanSupplier admitted;
    private Supplier<BubbleStickerEncoder.NativeBubblePainter> painter;
    private BubbleStickerWorkflow.NativeStickerSender sender;
    private Consumer<File> exporter;
    private boolean closed;
    public BubbleStickerSession(BubbleActionPanelView panel, File cache, BooleanSupplier admitted,
            Supplier<BubbleStickerEncoder.NativeBubblePainter> painter,
            BubbleStickerWorkflow.NativeStickerSender sender, Consumer<File> exporter) {
        this.panel=new WeakReference<>(panel);this.workflow=new BubbleStickerWorkflow(cache);
        this.admitted=admitted;this.painter=painter;this.sender=sender;this.exporter=exporter;
        panel.setOnDispose(this::close);
    }
    public void handle(BubbleActionPanelView.Action action) {
        BubbleActionPanelView view=panel.get();
        if (closed || view==null || admitted==null || !admitted.getAsBoolean()) return;
        if (action==BubbleActionPanelView.Action.BUILD_STICKER) {
            if(workflow.isPreparing() || workflow.exportFile()!=null)return;
            view.setStickerStatus(LocaleController.getString(R.string.FlexyContextStickerPreparing));
            view.setStickerActions(false,false);
            try { workflow.prepare(painter.get(),this); }
            catch(RuntimeException failure){onError("capture");}
        } else if(action==BubbleActionPanelView.Action.SEND_STICKER && workflow.canSend()) {
            view.setStickerStatus(LocaleController.getString(R.string.FlexyContextStickerSending));
            view.setStickerActions(false,true);
            workflow.confirmAndSend(sender,this);
        } else if(action==BubbleActionPanelView.Action.SAVE_STICKER && workflow.exportFile()!=null) exporter.accept(workflow.exportFile());
    }
    @Override public void onReady(File webp, Bitmap preview, TLRPC.Document metadata) {
        BubbleActionPanelView view=panel.get();
        if(closed || view==null || admitted==null || !admitted.getAsBoolean()){close();return;}
        view.setStickerPreview(preview);
        view.setStickerStatus(LocaleController.getString(R.string.FlexyContextStickerReady));
        view.setStickerActions(workflow.canSend(),true);
    }
    @Override public void onError(String reason) {
        BubbleActionPanelView view=panel.get();if(closed||view==null)return;
        view.setStickerStatus(LocaleController.getString("unconfirmed".equals(reason)?R.string.FlexyContextStickerUnconfirmed:R.string.FlexyContextStickerFailed));
        view.setStickerActions(false,workflow.exportFile()!=null && workflow.exportFile().isFile());
    }
    @Override public void onSent() {
        BubbleActionPanelView view=panel.get();if(closed||view==null)return;
        view.setStickerStatus(LocaleController.getString(R.string.FlexyContextStickerSent));
        view.setStickerActions(false,false);
    }
    public void close() {
        if(closed)return;closed=true;workflow.cancel();
        BubbleActionPanelView view=panel.get();if(view!=null)view.clearStickerPreview();
        panel.clear();admitted=null;painter=null;sender=null;exporter=null;
        // Published preview bitmaps may still be referenced by HWUI. Do not recycle them.
    }
}
