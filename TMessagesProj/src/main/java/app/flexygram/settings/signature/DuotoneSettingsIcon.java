package app.flexygram.settings.signature;

import android.content.Context;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.util.LruCache;
import android.util.SparseIntArray;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;

/** Reviewed raster geometry, tinted once per palette and shared in a bounded cache.
 * Coverage is combined numerically so overlapping accent/body masks never darken edges.
 * UI-thread owned, like Android View drawables. No frame callbacks or touch interception.
 */
public final class DuotoneSettingsIcon extends Drawable implements app.flexygram.icons.IconPressFeedback.Target {
    private static final LruCache<String, Bitmap> CACHE = new LruCache<String, Bitmap>(2 * 1024 * 1024) {
        @Override protected int sizeOf(String key, Bitmap bitmap) { return bitmap.getAllocationByteCount(); }
    };
    private static Resources cacheResources;
    private static Configuration cacheConfiguration;
    private final Resources resources;
    private final int coverageResource;
    private final Theme.ResourcesProvider provider;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private final Rect target = new Rect();
    private Bitmap bitmap;
    private int lastBody, lastAccent;
    private boolean initialized;

    static Drawable create(Context context, int resource, Theme.ResourcesProvider provider) {
        int coverage = coverage(resource);
        return coverage == 0 ? null : new DuotoneSettingsIcon(context.getResources(), coverage, provider);
    }
    private DuotoneSettingsIcon(Resources resources, int coverage, Theme.ResourcesProvider provider) {
        this.resources = resources;
        coverageResource = coverage;
        this.provider = provider;
        refreshPalette();
    }
    private void refreshPalette() {
        boolean dark = provider == null ? Theme.isCurrentThemeDark() : provider.isDark();
        int body = dark ? 0xffffffff : 0xff000000;
        int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueHeader, provider) | 0xff000000;
        if (initialized && body == lastBody && accent == lastAccent) return;
        Configuration configuration = resources.getConfiguration();
        if (cacheResources != resources || !configuration.equals(cacheConfiguration)) {
            CACHE.evictAll();
            cacheResources = resources;
            cacheConfiguration = new Configuration(configuration);
        }
        String key = coverageResource + ":" + body + ":" + accent;
        Bitmap next = CACHE.get(key);
        if (next == null) {
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inScaled = false;
            Bitmap packed = BitmapFactory.decodeResource(resources, coverageResource, options);
            if (packed == null) return;
            int width = packed.getWidth(), height = packed.getHeight();
            int[] pixels = new int[width * height];
            packed.getPixels(pixels, 0, width, 0, 0, width, height);
            for (int i = 0; i < pixels.length; i++) {
                int value = pixels[i];
                pixels[i] = tintCoverage((value >>> 16) & 255, (value >>> 8) & 255, body, accent);
            }
            next = Bitmap.createBitmap(pixels, width, height, Bitmap.Config.ARGB_8888);
            packed.recycle();
            CACHE.put(key, next);
        }
        bitmap = next;
        lastBody = body;
        lastAccent = accent;
        initialized = true;
        updateTarget(getBounds());
    }
    /** Pure, straight-alpha composition. It retains coverage rather than drawing two SRC_OVER masks. */
    static int tintCoverage(int bodyAlpha, int accentAlpha, int body, int accent) {
        int alpha = bodyAlpha + accentAlpha;
        if (alpha == 0) return 0;
        int r = (((body >>> 16) & 255) * bodyAlpha + ((accent >>> 16) & 255) * accentAlpha + alpha / 2) / alpha;
        int g = (((body >>> 8) & 255) * bodyAlpha + ((accent >>> 8) & 255) * accentAlpha + alpha / 2) / alpha;
        int b = ((body & 255) * bodyAlpha + (accent & 255) * accentAlpha + alpha / 2) / alpha;
        return (alpha << 24) | (r << 16) | (g << 8) | b;
    }
    private void updateTarget(Rect bounds) {
        if (bitmap == null) return;
        float scale = Math.min(bounds.width() / (float)bitmap.getWidth(), bounds.height() / (float)bitmap.getHeight());
        int width = Math.round(bitmap.getWidth() * scale), height = Math.round(bitmap.getHeight() * scale);
        int left = bounds.left + (bounds.width() - width) / 2;
        int top = bounds.top + (bounds.height() - height) / 2;
        target.set(left, top, left + width, top + height);
    }
    @Override protected void onBoundsChange(Rect bounds) { updateTarget(bounds); }
    @Override public void draw(Canvas canvas) {
        refreshPalette();
        if (bitmap != null) canvas.drawBitmap(bitmap, null, target, paint);
    }
    @Override public void setAlpha(int alpha) { if (paint.getAlpha() != alpha) { paint.setAlpha(alpha); invalidateSelf(); } }
    // Parent cells/ThemeDescription may still send a monochrome filter. Retain both semantic colours.
    @Override public void setColorFilter(ColorFilter ignored) {}
    @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    @Override public int getIntrinsicWidth() { return AndroidUtilities.dp(SettingsCardStyle.ICON); }
    @Override public int getIntrinsicHeight() { return AndroidUtilities.dp(SettingsCardStyle.ICON); }
    @Override public void setIconPressScale(float scale) {}
    // Modern Android Gradle resource IDs are non-final: never use R.* in switch cases.
    private static final SparseIntArray COVERAGE = createCoverageMap();
    private static SparseIntArray createCoverageMap() {
        SparseIntArray map = new SparseIntArray(85);
        map.put(R.drawable.fg_dm_abrir_archivo, R.raw.fg_dm_abrir_archivo_coverage);
        map.put(R.drawable.fg_dm_acerca_de, R.raw.fg_dm_acerca_de_coverage);
        map.put(R.drawable.fg_dm_animaciones, R.raw.fg_dm_animaciones_coverage);
        map.put(R.drawable.fg_dm_apariencia, R.raw.fg_dm_apariencia_coverage);
        map.put(R.drawable.fg_dm_aplicar_estilo, R.raw.fg_dm_aplicar_estilo_coverage);
        map.put(R.drawable.fg_dm_archivo, R.raw.fg_dm_archivo_coverage);
        map.put(R.drawable.fg_dm_avatares, R.raw.fg_dm_avatares_coverage);
        map.put(R.drawable.fg_dm_ayuda, R.raw.fg_dm_ayuda_coverage);
        map.put(R.drawable.fg_dm_ayumoments, R.raw.fg_dm_ayumoments_coverage);
        map.put(R.drawable.fg_dm_barra_inferior, R.raw.fg_dm_barra_inferior_coverage);
        map.put(R.drawable.fg_dm_bordes_reflejos, R.raw.fg_dm_bordes_reflejos_coverage);
        map.put(R.drawable.fg_dm_borrador, R.raw.fg_dm_borrador_coverage);
        map.put(R.drawable.fg_dm_burbujas, R.raw.fg_dm_burbujas_coverage);
        map.put(R.drawable.fg_dm_buscar, R.raw.fg_dm_buscar_coverage);
        map.put(R.drawable.fg_dm_carpeta_superior, R.raw.fg_dm_carpeta_superior_coverage);
        map.put(R.drawable.fg_dm_carpetas, R.raw.fg_dm_carpetas_coverage);
        map.put(R.drawable.fg_dm_cerrar, R.raw.fg_dm_cerrar_coverage);
        map.put(R.drawable.fg_dm_codigo_acceso, R.raw.fg_dm_codigo_acceso_coverage);
        map.put(R.drawable.fg_dm_compartir, R.raw.fg_dm_compartir_coverage);
        map.put(R.drawable.fg_dm_comportamiento, R.raw.fg_dm_comportamiento_coverage);
        map.put(R.drawable.fg_dm_comprimir_zip, R.raw.fg_dm_comprimir_zip_coverage);
        map.put(R.drawable.fg_dm_configuracion_completa, R.raw.fg_dm_configuracion_completa_coverage);
        map.put(R.drawable.fg_dm_confirmar, R.raw.fg_dm_confirmar_coverage);
        map.put(R.drawable.fg_dm_contactos, R.raw.fg_dm_contactos_coverage);
        map.put(R.drawable.fg_dm_conversaciones, R.raw.fg_dm_conversaciones_coverage);
        map.put(R.drawable.fg_dm_conversiones, R.raw.fg_dm_conversiones_coverage);
        map.put(R.drawable.fg_dm_descargas, R.raw.fg_dm_descargas_coverage);
        map.put(R.drawable.fg_dm_deshacer, R.raw.fg_dm_deshacer_coverage);
        map.put(R.drawable.fg_dm_desplegar, R.raw.fg_dm_desplegar_coverage);
        map.put(R.drawable.fg_dm_documento, R.raw.fg_dm_documento_coverage);
        map.put(R.drawable.fg_dm_editor_navegacion, R.raw.fg_dm_editor_navegacion_coverage);
        map.put(R.drawable.fg_dm_elementos_visibles, R.raw.fg_dm_elementos_visibles_coverage);
        map.put(R.drawable.fg_dm_emoji, R.raw.fg_dm_emoji_coverage);
        map.put(R.drawable.fg_dm_enviar_copia_chat, R.raw.fg_dm_enviar_copia_chat_coverage);
        map.put(R.drawable.fg_dm_exportar, R.raw.fg_dm_exportar_coverage);
        map.put(R.drawable.fg_dm_filtros_transferencia, R.raw.fg_dm_filtros_transferencia_coverage);
        map.put(R.drawable.fg_dm_flexyfiles, R.raw.fg_dm_flexyfiles_coverage);
        map.put(R.drawable.fg_dm_flexystudio, R.raw.fg_dm_flexystudio_coverage);
        map.put(R.drawable.fg_dm_fotos_video_voz, R.raw.fg_dm_fotos_video_voz_coverage);
        map.put(R.drawable.fg_dm_fuentes, R.raw.fg_dm_fuentes_coverage);
        map.put(R.drawable.fg_dm_general, R.raw.fg_dm_general_coverage);
        map.put(R.drawable.fg_dm_gestos, R.raw.fg_dm_gestos_coverage);
        map.put(R.drawable.fg_dm_guardado_historial, R.raw.fg_dm_guardado_historial_coverage);
        map.put(R.drawable.fg_dm_guardar, R.raw.fg_dm_guardar_coverage);
        map.put(R.drawable.fg_dm_icono_app, R.raw.fg_dm_icono_app_coverage);
        map.put(R.drawable.fg_dm_importar, R.raw.fg_dm_importar_coverage);
        map.put(R.drawable.fg_dm_informacion, R.raw.fg_dm_informacion_coverage);
        map.put(R.drawable.fg_dm_inteligencia_artificial, R.raw.fg_dm_inteligencia_artificial_coverage);
        map.put(R.drawable.fg_dm_interfaz_inferior, R.raw.fg_dm_interfaz_inferior_coverage);
        map.put(R.drawable.fg_dm_interfaz_superior, R.raw.fg_dm_interfaz_superior_coverage);
        map.put(R.drawable.fg_dm_lista_titulo, R.raw.fg_dm_lista_titulo_coverage);
        map.put(R.drawable.fg_dm_mantenimiento, R.raw.fg_dm_mantenimiento_coverage);
        map.put(R.drawable.fg_dm_mapas, R.raw.fg_dm_mapas_coverage);
        map.put(R.drawable.fg_dm_mas_acciones, R.raw.fg_dm_mas_acciones_coverage);
        map.put(R.drawable.fg_dm_mas_opciones, R.raw.fg_dm_mas_opciones_coverage);
        map.put(R.drawable.fg_dm_mensajes, R.raw.fg_dm_mensajes_coverage);
        map.put(R.drawable.fg_dm_menu_mensajes, R.raw.fg_dm_menu_mensajes_coverage);
        map.put(R.drawable.fg_dm_menus_acciones, R.raw.fg_dm_menus_acciones_coverage);
        map.put(R.drawable.fg_dm_miembros, R.raw.fg_dm_miembros_coverage);
        map.put(R.drawable.fg_dm_mini_pildoras, R.raw.fg_dm_mini_pildoras_coverage);
        map.put(R.drawable.fg_dm_modo_fantasma, R.raw.fg_dm_modo_fantasma_coverage);
        map.put(R.drawable.fg_dm_navegacion, R.raw.fg_dm_navegacion_coverage);
        map.put(R.drawable.fg_dm_notificaciones, R.raw.fg_dm_notificaciones_coverage);
        map.put(R.drawable.fg_dm_nube, R.raw.fg_dm_nube_coverage);
        map.put(R.drawable.fg_dm_opciones_extra, R.raw.fg_dm_opciones_extra_coverage);
        map.put(R.drawable.fg_dm_packs_iconos, R.raw.fg_dm_packs_iconos_coverage);
        map.put(R.drawable.fg_dm_pantalla_principal, R.raw.fg_dm_pantalla_principal_coverage);
        map.put(R.drawable.fg_dm_pillstack, R.raw.fg_dm_pillstack_coverage);
        map.put(R.drawable.fg_dm_plugins, R.raw.fg_dm_plugins_coverage);
        map.put(R.drawable.fg_dm_plugins_herramientas, R.raw.fg_dm_plugins_herramientas_coverage);
        map.put(R.drawable.fg_dm_privacidad, R.raw.fg_dm_privacidad_coverage);
        map.put(R.drawable.fg_dm_privacidad_historias, R.raw.fg_dm_privacidad_historias_coverage);
        map.put(R.drawable.fg_dm_red_velocidad, R.raw.fg_dm_red_velocidad_coverage);
        map.put(R.drawable.fg_dm_reemplazar, R.raw.fg_dm_reemplazar_coverage);
        map.put(R.drawable.fg_dm_rehacer, R.raw.fg_dm_rehacer_coverage);
        map.put(R.drawable.fg_dm_restablecer, R.raw.fg_dm_restablecer_coverage);
        map.put(R.drawable.fg_dm_sangria, R.raw.fg_dm_sangria_coverage);
        map.put(R.drawable.fg_dm_sistema, R.raw.fg_dm_sistema_coverage);
        map.put(R.drawable.fg_dm_stickers_emoji, R.raw.fg_dm_stickers_emoji_coverage);
        map.put(R.drawable.fg_dm_superficies_efectos, R.raw.fg_dm_superficies_efectos_coverage);
        map.put(R.drawable.fg_dm_traduccion, R.raw.fg_dm_traduccion_coverage);
        map.put(R.drawable.fg_dm_traductor, R.raw.fg_dm_traductor_coverage);
        map.put(R.drawable.fg_dm_validar, R.raw.fg_dm_validar_coverage);
        map.put(R.drawable.fg_dm_vista_html, R.raw.fg_dm_vista_html_coverage);
        map.put(R.drawable.fg_dm_volver, R.raw.fg_dm_volver_coverage);
        return map;
    }
    static int coverage(int resource) { return COVERAGE.get(resource, 0); }
}
