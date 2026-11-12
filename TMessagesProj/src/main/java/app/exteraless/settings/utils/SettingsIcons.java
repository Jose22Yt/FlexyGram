package app.exteraless.settings.utils;

import android.content.Context;
import android.content.res.Resources;
import android.util.SparseIntArray;
import org.telegram.messenger.R;

/** Reviewed duotone resources for settings navigation; unfamiliar plugin icons retain their meaning. */
public final class SettingsIcons {
    private SettingsIcons() {}
    // Row binding is UI-owned. Resource identity separates app/plugin resource tables.
    private static Resources cachedResources;
    private static final SparseIntArray resolvedIcons = new SparseIntArray();

    public static int resolve(Context context, int icon) {
        if (icon == 0) return 0;
        Resources resources = context.getResources();
        if (cachedResources != resources) {
            cachedResources = resources;
            resolvedIcons.clear();
        }
        int cached = resolvedIcons.get(icon, 0);
        if (cached != 0) return cached;
        int resolved = resolveUncached(context, icon);
        if (resolved == 0) return icon; // A resource loader can make a missing ID available later.
        if (resolvedIcons.size() >= 128) resolvedIcons.clear();
        resolvedIcons.put(icon, resolved);
        return resolved;
    }

    public static boolean appliesTo(Object fragment) {
        String name = fragment.getClass().getName();
        return name.startsWith("app.exteraless.settings.")
                || name.startsWith("app.exteraless.plugins.ui.")
                || name.startsWith("app.exteraless.icons.");
    }

    private static int resolveUncached(Context context, int icon) {
        if (icon == 0) return 0;
        final String name;
        try {
            name = context.getResources().getResourceEntryName(icon);
        } catch (Resources.NotFoundException ignored) {
            return 0;
        }
        switch (name) {
            case "fg_settings_chats": return R.drawable.fg_dm_conversaciones;
            case "fg_settings_chat": return R.drawable.fg_dm_conversaciones;
            case "fg_settings_home": return R.drawable.fg_dm_pantalla_principal;
            case "fg_settings_gesture": return R.drawable.fg_dm_gestos;
            case "fg_settings_canales": return R.drawable.fg_dm_ayumoments;
            case "fg_settings_plugin": return R.drawable.fg_dm_plugins;
            case "fg_settings_plugins": return R.drawable.fg_dm_plugins;
            case "fg_settings_folder": return R.drawable.fg_dm_carpetas;
            case "fg_settings_download": return R.drawable.fg_dm_descargas;
            case "fg_settings_general": return R.drawable.fg_dm_general;
            case "fg_settings_layers": return R.drawable.fg_dm_pillstack;
            case "fg_settings_comunidad": return R.drawable.fg_dm_acerca_de;
            case "fg_settings_settings": return R.drawable.fg_dm_sistema;
            case "fg_settings_file": return R.drawable.fg_dm_documento;
            case "fg_settings_info": return R.drawable.fg_dm_informacion;
            case "fg_settings_palette": return R.drawable.fg_dm_apariencia;
            case "fg_settings_camera": return R.drawable.fg_dm_fotos_video_voz;
            case "fg_settings_history": return R.drawable.fg_dm_guardado_historial;
            case "fg_settings_eye": return R.drawable.fg_dm_elementos_visibles;
            case "fg_settings_globe": return R.drawable.fg_dm_acerca_de;
            case "fg_settings_cloud": return R.drawable.fg_dm_nube;
            case "fg_settings_share": return R.drawable.fg_dm_compartir;
            case "fg_settings_reset": return R.drawable.fg_dm_restablecer;
            case "fg_settings_trash": return R.drawable.fg_dm_mantenimiento;
            case "fg_settings_users": return R.drawable.fg_dm_miembros;
            case "fg_settings_list": return R.drawable.fg_dm_lista_titulo;
            case "flexy_studio_export": return R.drawable.fg_dm_exportar;
            case "flexy_studio_import": return R.drawable.fg_dm_importar;
            case "flexy_studio_share": return R.drawable.fg_dm_compartir;
            case "flexy_studio_document": return R.drawable.fg_dm_documento;
            case "msg_folders_archive": return R.drawable.fg_dm_comprimir_zip;
            case "msg_close": return R.drawable.fg_dm_cerrar;
            case "msg_help": return R.drawable.fg_dm_ayuda;

            case "settings3_chat": return R.drawable.fg_dm_conversaciones;
            case "settings3_stack": return R.drawable.fg_dm_pillstack;
            case "settings3_sliders": return R.drawable.fg_dm_sistema;
            case "settings3_ghost": return R.drawable.fg_dm_guardado_historial;
            case "settings3_plugins": return R.drawable.fg_dm_plugins;
            case "settings3_document": return R.drawable.fg_dm_documento;
            case "settings3_folder": return R.drawable.fg_dm_carpetas;
            case "settings3_hand": return R.drawable.fg_dm_gestos;
            case "settings3_info": return R.drawable.fg_dm_informacion;

            case "msg_discussion":
            case "msg_discuss":
            case "msg_message":
            case "input_message":
            case "msg_channel":
                return R.drawable.fg_dm_conversaciones;
            case "msg_home":
            case "msg_newphone":
                return R.drawable.fg_dm_pantalla_principal;
            case "msg_gesture":
            case "msg_hand":
                return R.drawable.fg_dm_gestos;
            case "ayu_ghost":
            case "msg_recent":
            case "msg_log":
                return R.drawable.fg_dm_guardado_historial;
            case "msg_plugins":
                return R.drawable.fg_dm_plugins;
            case "msg_view_file":
            case "msg_document":
                return R.drawable.fg_dm_documento;
            case "msg_folder":
                return R.drawable.fg_dm_carpetas;
            case "msg_download":
                return R.drawable.fg_dm_descargas;
            case "msg_settings_old":
            case "msg_settings":
            case "msg_media":
                return R.drawable.fg_dm_sistema;
            case "msg_layers":
            case "msg_tabs":
                return R.drawable.fg_dm_pillstack;
            case "msg_info":
                return R.drawable.fg_dm_informacion;
            case "msg_theme":
            case "msg_sticker":
            case "msg_emoji_smiles":
                return R.drawable.fg_dm_apariencia;
            case "msg_camera":
                return R.drawable.fg_dm_fotos_video_voz;
            case "msg_archive_hide":
            case "msg_block":
                return R.drawable.fg_dm_elementos_visibles;
            case "msg_language":
                return R.drawable.fg_dm_acerca_de;
            case "cloud_sync":
                return R.drawable.fg_dm_nube;
            case "msg_share":
            case "msg_shareout":
                return R.drawable.fg_dm_compartir;
            case "msg_reset":
                return R.drawable.fg_dm_restablecer;
            case "msg_delete":
            case "msg_clearcache":
                return R.drawable.fg_dm_mantenimiento;
            case "msg_fave":
                return R.drawable.fg_settings_heart;
            case "msg_groups":
                return R.drawable.fg_dm_miembros;
            case "msg_list":
            case "outline_header_search":
                return R.drawable.fg_dm_lista_titulo;
            case "deproko_baseline_lamp_filled_24":
                return R.drawable.fg_settings_light;
            default:
                return icon;
        }
    }
}
