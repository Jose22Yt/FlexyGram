package app.flexygram.effects;

import androidx.core.graphics.ColorUtils;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundColorProviderThemed;
import org.telegram.ui.Components.blur3.drawable.color.impl.BlurredBackgroundProviderImpl;

/** Shared material policy for chat header, pinned panel and input islands.
 * Keeps the existing input opacity, native glass contours and power-saving fallback. */
public final class ChatGlassColorProvider extends BlurredBackgroundColorProviderThemed {
    private final int account;
    private final Theme.ResourcesProvider provider;
    private final int backgroundKey;

    public ChatGlassColorProvider(int account, Theme.ResourcesProvider provider, int backgroundKey) {
        super(provider, backgroundKey);
        this.account = account;
        this.provider = provider;
        this.backgroundKey = backgroundKey;
    }

    @Override public int getBackgroundColor() {
        if (!BlurredBackgroundProviderImpl.checkBlurEnabled(account, provider)) {
            return ColorUtils.setAlphaComponent(Theme.getColor(backgroundKey, provider), 255);
        }
        int color = super.getBackgroundColor();
        boolean dark = provider != null ? provider.isDark() : Theme.isCurrentThemeDark();
        return dark ? color : ColorUtils.setAlphaComponent(color, 140);
    }
}
