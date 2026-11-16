package app.flexygram.chat;

import android.os.Build;
import org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable;
import org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawableRenderNode;

/** Exclude inactive chat materials from native blur regions, without changing their alpha. */
public final class ChatMaterialCapture {
    private ChatMaterialCapture() {}
    public static void setEnabled(BlurredBackgroundDrawable material, boolean enabled) {
        if(Build.VERSION.SDK_INT>=29 && material instanceof BlurredBackgroundDrawableRenderNode)
            ((BlurredBackgroundDrawableRenderNode)material).setSourceCaptureEnabled(enabled);
    }
}
