package app.flexygram.effects;

import androidx.core.graphics.ColorUtils;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundColorProviderThemed;
import org.telegram.ui.Components.blur3.drawable.color.impl.BlurredBackgroundProviderImpl;

/** Theme-aware tint for the native chat header and composer materials. */
public final class ChatGlassColorProvider extends BlurredBackgroundColorProviderThemed {
    private final int account;
    private final Theme.ResourcesProvider provider;
    private final java.util.function.IntSupplier opacity;

    public ChatGlassColorProvider(int account, Theme.ResourcesProvider provider, int backgroundKey) {
        this(account, provider, backgroundKey, null);
    }

    public ChatGlassColorProvider(int account, Theme.ResourcesProvider provider, int backgroundKey,
            java.util.function.IntSupplier opacity) {
        super(provider, backgroundKey);
        this.opacity = opacity;
        this.account = account;
        this.provider = provider;
    }

    public boolean isBlurEnabled() {
        return BlurredBackgroundProviderImpl.checkBlurEnabled(account, provider);
    }

    public boolean isChatThemeDark() {
        return provider != null ? provider.isDark() : Theme.isCurrentThemeDark();
    }

    @Override public int getStrokeColorFull() {
        if (isBlurEnabled()) return super.getStrokeColorFull();
        return ChatChromePalette.outline(isChatThemeDark());
    }

    @Override public int getBackgroundColor() {
        final boolean dark = isChatThemeDark();
        if (!isBlurEnabled()) return ChatChromePalette.surface(dark);
        final int color = super.getBackgroundColor();
        final int alpha = dark ? color >>> 24 : 140;
        final int channels = color & 0x00f0f0f0;
        final boolean nearBackgroundExtreme = dark ? channels == 0 : channels == 0x00f0f0f0;
        final int tint = nearBackgroundExtreme ? ChatChromePalette.surface(dark) : color;
        return ColorUtils.setAlphaComponent(tint, opacity == null ? alpha : Math.round(alpha * opacity.getAsInt() / 100f));
    }
}
