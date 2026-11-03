package app.exteraless.settings.utils;

import android.content.Context;
import android.content.res.Resources;
import org.telegram.messenger.R;

/** Outline resources for settings navigation; unfamiliar/plugin icons retain their meaning. */
public final class SettingsIcons {
    private SettingsIcons() {}

    public static boolean appliesTo(Object fragment) {
        String name = fragment.getClass().getName();
        return name.startsWith("app.exteraless.settings.")
                || name.startsWith("app.exteraless.plugins.ui.")
                || name.startsWith("app.exteraless.icons.");
    }

    public static int resolve(Context context, int icon) {
        if (icon == 0) return 0;
        final String name;
        try {
            name = context.getResources().getResourceEntryName(icon);
        } catch (Resources.NotFoundException ignored) {
            return icon;
        }
        switch (name) {
            case "settings3_chat": return R.drawable.fg_settings_chat;
            case "settings3_stack": return R.drawable.fg_settings_layers;
            case "settings3_sliders": return R.drawable.fg_settings_settings;
            case "settings3_ghost": return R.drawable.fg_settings_history;
            case "settings3_plugins": return R.drawable.fg_settings_plugins;
            case "settings3_document": return R.drawable.fg_settings_file;
            case "settings3_folder": return R.drawable.fg_settings_folder;
            case "settings3_hand": return R.drawable.fg_settings_gesture;
            case "settings3_info": return R.drawable.fg_settings_info;

            case "msg_discussion":
            case "msg_discuss":
            case "msg_message":
            case "input_message":
            case "msg_channel":
                return R.drawable.fg_settings_chat;
            case "msg_home":
            case "msg_newphone":
                return R.drawable.fg_settings_home;
            case "msg_gesture":
            case "msg_hand":
                return R.drawable.fg_settings_gesture;
            case "ayu_ghost":
            case "msg_recent":
            case "msg_log":
                return R.drawable.fg_settings_history;
            case "msg_plugins":
                return R.drawable.fg_settings_plugins;
            case "msg_view_file":
            case "msg_document":
                return R.drawable.fg_settings_file;
            case "msg_folder":
                return R.drawable.fg_settings_folder;
            case "msg_download":
                return R.drawable.fg_settings_download;
            case "msg_settings_old":
            case "msg_settings":
            case "msg_media":
                return R.drawable.fg_settings_settings;
            case "msg_layers":
            case "msg_tabs":
                return R.drawable.fg_settings_layers;
            case "msg_info":
            case "msg_help":
                return R.drawable.fg_settings_info;
            case "msg_theme":
            case "msg_sticker":
            case "msg_emoji_smiles":
                return R.drawable.fg_settings_palette;
            case "msg_camera":
                return R.drawable.fg_settings_camera;
            case "msg_archive_hide":
            case "msg_block":
                return R.drawable.fg_settings_eye;
            case "msg_language":
                return R.drawable.fg_settings_globe;
            case "cloud_sync":
                return R.drawable.fg_settings_cloud;
            case "msg_share":
            case "msg_shareout":
                return R.drawable.fg_settings_share;
            case "msg_reset":
                return R.drawable.fg_settings_reset;
            case "msg_delete":
            case "msg_clearcache":
                return R.drawable.fg_settings_trash;
            case "msg_fave":
                return R.drawable.fg_settings_heart;
            case "msg_groups":
                return R.drawable.fg_settings_users;
            case "msg_list":
            case "outline_header_search":
                return R.drawable.fg_settings_list;
            case "deproko_baseline_lamp_filled_24":
                return R.drawable.fg_settings_light;
            default:
                return icon;
        }
    }
}
