package org.telegram.messenger;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import java.math.BigDecimal;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/** Settings-only portable boundary. Unknown namespaces/keys/types fail closed.
 * Credentials, account state, push identities, paths and plugin switches are never portable.
 * This policy applies even to a future authenticated variant; it never enables authentication.
 */
public final class SettingsBackupPolicy {
    private SettingsBackupPolicy() {}
    private static Set<String> keys(String value) {
        return new HashSet<>(Arrays.asList(value.split(" ")));
    }
    private static final Set<String> MAIN_BOOL = keys(
        "autoplayGifs autoplayVideo raiseToSpeak customTabs directShare shuffleMusic " +
        "playOrderReversed inappCamera allowBigEmoji streamMedia saveStreamMedia " +
        "smoothKeyboard pauseMusicOnRecord streamAllVideo streamMkv sortContactsByName " +
        "sortFilesByName useThreeLinesLayout archiveHidden loopStickers noStatusBar " +
        "disableVoiceAudioEffects");
    private static final Set<String> MAIN_INT = keys(
        "saveToGallery mapPreviewType repeatMode fontSize bubbleRadius ivFontSize " +
        "suggestStickers distanceSystemType keepMedia chatSwipeAction selectedAutoNightType " +
        "autoNightDayStartTime autoNightDayEndTime");
    private static final Set<String> NEKO_BOOL = keys(
        "unreadBadgeOnBackButton useCustomEmoji repeatConfirm DisableInstantCamera showSeconds " +
        "HidePhone TypefaceUseDefault forceFontWeightFallback showAddToSavedMessages " +
        "showReport showViewHistory showAdminActions showChangePermissions " +
        "showDeleteDownloadedFile showMessageDetails showTranslate showRepeat " +
        "showShareMessages showMessageHide");
    private static final Set<String> NEKO_INT = keys(
        "TabletMode NameOrder ActionBarDecoration");

    /** Returns a new object; rejected fields never reach SharedPreferences or export output. */
    public static JsonObject sanitize(JsonObject input) {
        JsonObject result = new JsonObject();
        if (input == null) return result;
        for (String name : Arrays.asList("mainconfig", "nkmrcfg", "themeconfig")) {
            JsonElement section = input.get(name);
            if (section == null || !section.isJsonObject()) continue;
            JsonObject clean = new JsonObject();
            for (java.util.Map.Entry<String, JsonElement> entry : section.getAsJsonObject().entrySet()) {
                JsonElement value = entry.getValue();
                if (value != null && value.isJsonPrimitive()
                        && allows(name, entry.getKey(), value.getAsJsonPrimitive())) {
                    clean.add(entry.getKey(), value.deepCopy());
                }
            }
            if (clean.size() != 0) result.add(name, clean);
        }
        return result;
    }

    private static boolean allows(String section, String key, JsonPrimitive value) {
        if ("mainconfig".equals(section)) {
            if (MAIN_BOOL.contains(key)) return value.isBoolean();
            if (MAIN_INT.contains(key)) return integer(value);
            if ("lang_code".equals(key)) return value.isString()
                && value.getAsString().matches("[A-Za-z]{2,8}([_-][A-Za-z0-9]{2,8}){0,2}");
            if ("theme".equals(key)) return themeName(value);
            return false;
        }
        if ("nkmrcfg".equals(section)) {
            if (NEKO_BOOL.contains(key)) return value.isBoolean();
            if (NEKO_INT.contains(key)) return integer(value);
            if ("stickerSize_float".equals(key)) return value.isNumber()
                && value.getAsDouble() >= 4 && value.getAsDouble() <= 20;
            return false;
        }
        if ("themeconfig".equals(section)) {
            if ("lastDayTheme".equals(key) || "lastDarkTheme".equals(key)) return themeName(value);
            return key.matches("accent_current_[A-Za-z0-9_-]{1,64}") && integer(value);
        }
        return false;
    }

    private static boolean themeName(JsonPrimitive value) {
        return value.isString() && value.getAsString().matches("[A-Za-z0-9_-]{1,64}");
    }
    private static boolean integer(JsonPrimitive value) {
        if (!value.isNumber()) return false;
        try { new BigDecimal(value.getAsString()).intValueExact(); return true; }
        catch (NumberFormatException | ArithmeticException invalid) { return false; }
    }
}
