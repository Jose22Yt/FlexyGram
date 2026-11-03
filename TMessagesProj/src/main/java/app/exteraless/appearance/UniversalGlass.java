package app.exteraless.appearance;

import android.graphics.Color;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundProvider;
import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundProviderBuilder;
import org.telegram.ui.Components.blur3.drawable.color.impl.BlurredBackgroundProviderImpl;

/** Shared frosted material. The native engine owns backdrop blur, clipping and performance gates. */
public final class UniversalGlass {
    public static final int INPUT = 1, HEADER = 2, NAVIGATION = 4, SEARCH = 8, MENUS = 16, FOLDERS = 32;
    private UniversalGlass() {}

    public static boolean enabled(int surface) {
        return FlexyGlassConfig.enabled() && UniversalGlassConfig.enabled()
                && (surface & (INPUT | HEADER | NAVIGATION | SEARCH | MENUS | FOLDERS)) != 0;
    }

    public static boolean canRender(int surface, Theme.ResourcesProvider provider) {
        return enabled(surface) && BlurredBackgroundProviderImpl.checkBlurEnabled(provider);
    }

    public static int backgroundColor(Theme.ResourcesProvider provider, int colorKey) {
        boolean dark = provider != null ? provider.isDark() : Theme.isCurrentThemeDark();
        float opacity = Math.max(20, Math.min(85, UniversalGlassConfig.opacity())) / 100f;
        int color = Theme.getColor(colorKey, provider);
        return dark ? Theme.multAlpha(color, opacity * 0.85f)
                : GlassContrastPolicy.lightSurface(color, Math.round(opacity * 255));
    }

    public static int edgeColor(boolean top) {
        float strength = Math.max(0, Math.min(200, UniversalGlassConfig.edge())) / 100f;
        return (Color.WHITE & 0xffffff) | (Math.min(255, Math.round(255 * strength * (top ? .85f : .60f))) << 24);
    }

    public static int edgeColor(boolean top, boolean dark) {
        if (dark || top) return edgeColor(top);
        float strength = Math.max(0, Math.min(200, UniversalGlassConfig.edge())) / 100f;
        return 0x253040 | (Math.min(255, Math.round(255 * strength * .40f)) << 24);
    }

    public static int contourColor(boolean dark) {
        return dark ? edgeColor(true) : edgeColor(false, false);
    }

    public static BlurredBackgroundProvider material(Theme.ResourcesProvider provider, int colorKey) {
        return new SimpleGlassProvider(new BlurredBackgroundProviderBuilder(provider)
                .setBackgroundColor((p, dark) -> backgroundColor(p, colorKey))
                .setStrokeColorTop((p, dark) -> edgeColor(true, dark))
                .setStrokeColorBottom((p, dark) -> edgeColor(false, dark))
                .setStrokeColorFull((p, dark) -> contourColor(dark))
                .setStrokeWidth(AndroidUtilities.dpf2(UniversalGlassConfig.snapshot().width / 10f),
                        AndroidUtilities.dpf2(UniversalGlassConfig.snapshot().width * .08125f))
                .setShadowColor(0x18000000, 0x18000000)
                .setShadowLayer(AndroidUtilities.dpf2(3), 0, AndroidUtilities.dpf2(1))
                .build(), provider, colorKey);
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
