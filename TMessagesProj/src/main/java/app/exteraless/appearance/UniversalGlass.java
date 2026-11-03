package app.exteraless.appearance;

import android.graphics.Color;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundProvider;
import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundProviderBuilder;
import org.telegram.ui.Components.blur3.drawable.color.impl.BlurredBackgroundProviderImpl;

/** Shared frosted material. The native engine owns backdrop blur, clipping and performance gates. */
public final class UniversalGlass {
    public static final int INPUT = 1, HEADER = 2, NAVIGATION = 4, SEARCH = 8, MENUS = 16, FOLDERS = 32, PROFILE = 64;
    private UniversalGlass() {}

    public static boolean enabled(int surface) {
        return FlexyGlassConfig.enabled() && UniversalGlassConfig.enabled()
                && (surface & UniversalGlassConfig.surfaces()) != 0;
    }

    public static boolean canRender(int surface, Theme.ResourcesProvider provider) {
        return enabled(surface) && BlurredBackgroundProviderImpl.checkBlurEnabled(provider);
    }

    public static int backgroundColor(Theme.ResourcesProvider provider, int colorKey) {
        boolean dark = provider != null ? provider.isDark() : Theme.isCurrentThemeDark();
        float opacity = Math.max(20, Math.min(100, UniversalGlassConfig.opacity())) / 100f;
        int color = Theme.getColor(colorKey, provider);
        return dark ? Theme.multAlpha(color, opacity * 0.85f)
                : GlassContrastPolicy.lightSurface(color, Math.round(opacity * 255));
    }

    public static int edgeColor(boolean top) { return edgeColor(top, Theme.isCurrentThemeDark()); }
    public static int edgeColor(boolean top, boolean dark) { return borderColor(null, top); }
    private static int borderColor(Theme.ResourcesProvider provider, boolean top) {
        var settings = UniversalGlassConfig.snapshot();
        int color = settings.color == 0 ? Theme.getColor(Theme.key_telegram_color, provider) : settings.color;
        float strength = settings.edge / 100f;
        float style = settings.style == 0 ? .55f : settings.style == 2 ? 1f : .85f;
        return Theme.multAlpha(color | 0xff000000, strength * style * (top ? 1f : .6f));
    }
    public static int contourColor(boolean dark) { return borderColor(null, true); }

    public static BlurredBackgroundProvider material(Theme.ResourcesProvider provider, int colorKey) {
        return new CustomGlassProvider(new BlurredBackgroundProviderBuilder(provider)
                .setBackgroundColor((p, dark) -> backgroundColor(p, colorKey))
                .setStrokeColorTop((p, dark) -> borderColor(p, true))
                .setStrokeColorBottom((p, dark) -> borderColor(p, false))
                .setStrokeColorFull((p, dark) -> borderColor(p, true))
                .setStrokeWidth(AndroidUtilities.dpf2(UniversalGlassConfig.snapshot().width / 10f),
                        AndroidUtilities.dpf2(UniversalGlassConfig.snapshot().width / 10f))
                .setShadowColor(0x18000000, 0x18000000)
                .setShadowLayer(AndroidUtilities.dpf2(3), 0, AndroidUtilities.dpf2(1))
                .build(), UniversalGlassConfig.snapshot());
    }

    public static BlurredBackgroundProvider fill(Theme.ResourcesProvider provider, int colorKey) {
        return new BlurredBackgroundProviderBuilder(provider)
                .setBackgroundColor((p, dark) -> backgroundColor(p, colorKey))
                .setStrokeColorTop(0, 0).setStrokeColorBottom(0, 0).setStrokeColorFull(0, 0)
                .setStrokeWidth(0, 0).setShadowColor(0, 0).setShadowLayer(0, 0, 0).build();
    }

    public static BlurredBackgroundProvider surface(int scope, Theme.ResourcesProvider provider, BlurredBackgroundProvider fallback) {
        return canRender(scope, provider) ? material(provider, Theme.key_windowBackgroundWhite) : fallback;
    }
}
