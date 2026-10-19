package tw.nekomimi.nekogram.helpers;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.widget.LinearLayout;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;

import org.json.JSONException;
import org.json.JSONObject;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.PushListenerController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.CheckBoxCell;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.LaunchActivity;

import java.io.File;
import java.util.ArrayList;
import java.util.Date;
import java.util.Map;
import java.util.function.Function;

import kotlin.text.StringsKt;
import tw.nekomimi.nekogram.utils.AlertUtil;
import tw.nekomimi.nekogram.utils.FileUtil;
import tw.nekomimi.nekogram.utils.GsonUtil;
import tw.nekomimi.nekogram.utils.ShareUtil;
import xyz.nextalone.nagram.NaConfig;

public final class SettingsBackupHelper {
    public static String backupSettingsJson(boolean isCloud, int indentSpaces) throws JSONException {
        return backupSettingsJson(isCloud, indentSpaces, false);
    }

    public static String backupSettingsJson(boolean isCloud, int indentSpaces, boolean includeApiKeys) throws JSONException {

        JSONObject configJson = new JSONObject();

        ArrayList<String> mainconfig = new ArrayList<>();
        mainconfig.add("saveToGallery");
        mainconfig.add("autoplayGifs");
        mainconfig.add("autoplayVideo");
        mainconfig.add("mapPreviewType");
        mainconfig.add("raiseToSpeak");
        mainconfig.add("customTabs");
        mainconfig.add("directShare");
        mainconfig.add("shuffleMusic");
        mainconfig.add("playOrderReversed");
        mainconfig.add("inappCamera");
        mainconfig.add("repeatMode");
        mainconfig.add("fontSize");
        mainconfig.add("bubbleRadius");
        mainconfig.add("ivFontSize");
        mainconfig.add("allowBigEmoji");
        mainconfig.add("streamMedia");
        mainconfig.add("saveStreamMedia");
        mainconfig.add("smoothKeyboard");
        mainconfig.add("pauseMusicOnRecord");
        mainconfig.add("streamAllVideo");
        mainconfig.add("streamMkv");
        mainconfig.add("suggestStickers");
        mainconfig.add("sortContactsByName");
        mainconfig.add("sortFilesByName");
        mainconfig.add("noSoundHintShowed");
        mainconfig.add("directShareHash");
        mainconfig.add("useThreeLinesLayout");
        mainconfig.add("archiveHidden");
        mainconfig.add("distanceSystemType");
        mainconfig.add("loopStickers");
        mainconfig.add("keepMedia");
        mainconfig.add("noStatusBar");
        mainconfig.add("lastKeepMediaCheckTime");
        mainconfig.add("searchMessagesAsListHintShows");
        mainconfig.add("searchMessagesAsListUsed");
        mainconfig.add("stickersReorderingHintUsed");
        mainconfig.add("textSelectionHintShows");
        mainconfig.add("scheduledOrNoSoundHintShows");
        mainconfig.add("lockRecordAudioVideoHint");
        mainconfig.add("disableVoiceAudioEffects");
        mainconfig.add("chatSwipeAction");

        if (!isCloud) mainconfig.add("theme");
        mainconfig.add("selectedAutoNightType");
        mainconfig.add("autoNightScheduleByLocation");
        mainconfig.add("autoNightBrighnessThreshold");
        mainconfig.add("autoNightDayStartTime");
        mainconfig.add("autoNightDayEndTime");
        mainconfig.add("autoNightSunriseTime");
        mainconfig.add("autoNightCityName");
        mainconfig.add("autoNightSunsetTime");
        mainconfig.add("autoNightLocationLatitude3");
        mainconfig.add("autoNightLocationLongitude3");
        mainconfig.add("autoNightLastSunCheckDay");

        mainconfig.add("lang_code");

        mainconfig.add("web_restricted_domains2");

        spToJSON("mainconfig", configJson, mainconfig::contains);
        if (!isCloud) spToJSON("themeconfig", configJson, null);
        spToJSON("nkmrcfg", configJson, null, includeApiKeys);

        // Both local and cloud output pass the same settings-only boundary.
        // The legacy includeApiKeys argument cannot opt credentials back in.
        return new JSONObject(org.telegram.messenger.SettingsBackupPolicy.sanitize(
                GsonUtil.toJsonObject(configJson.toString())).toString()).toString(indentSpaces);
    }

    private static void spToJSON(String sp, JSONObject object, Function<String, Boolean> filter) throws JSONException {
        spToJSON(sp, object, filter, true);
    }

    private static void spToJSON(String sp, JSONObject object, Function<String, Boolean> filter, boolean includeApiKeys) throws JSONException {
        SharedPreferences preferences = ApplicationLoader.applicationContext.getSharedPreferences(sp, Activity.MODE_PRIVATE);
        JSONObject jsonConfig = new JSONObject();
        for (Map.Entry<String, ?> entry : preferences.getAll().entrySet()) {
            String key = entry.getKey();
            if ("nkmrcfg".equals(sp) && isDeviceSpecificPushKey(key)) {
                continue;
            }
            if (!includeApiKeys && (key.endsWith("Key") || key.contains("Token") || key.contains("AccountID"))) {
                continue;
            }
            if (filter != null && !filter.apply(key)) {
                continue;
            }
            if (entry.getValue() instanceof Long) {
                key = key + "_long";
            } else if (entry.getValue() instanceof Float) {
                key = key + "_float";
            }
            jsonConfig.put(key, entry.getValue());
        }
        object.put(sp, jsonConfig);
    }

    public static void importSettings(Context context, File settingsFile) {
        AlertUtil.showConfirm(context,
                getString(R.string.ImportSettingsAlert),
                R.drawable.msg_photo_settings_solar,
                getString(R.string.Import),
                true,
                () -> importSettingsConfirmed(context, settingsFile));
    }

    public static void importSettingsConfirmed(Context context, File settingsFile) {
        try {
            JsonObject configJson = GsonUtil.toJsonObject(FileUtil.readUtf8String(settingsFile));
            importSettings(configJson);

            AlertDialog restart = new AlertDialog(context, 0);
            restart.setTitle(getString(R.string.NagramX));
            restart.setMessage(getString(R.string.RestartAppToTakeEffect));
            restart.setPositiveButton(getString(R.string.OK), (__, ___) -> AppRestartHelper.triggerRebirth(context, new Intent(context, LaunchActivity.class)));
            restart.show();
        } catch (Exception e) {
            AlertUtil.showSimpleAlert(context, new IllegalArgumentException("Settings backup could not be processed"));
        }
    }

    @SuppressLint("ApplySharedPref")
    public static void importSettings(JsonObject configJson) throws JSONException {
        // Filter BEFORE looking up any SharedPreferences namespace from untrusted JSON.
        configJson = org.telegram.messenger.SettingsBackupPolicy.sanitize(configJson);
        for (Map.Entry<String, JsonElement> element : configJson.entrySet()) {
            String spName = element.getKey();
            SharedPreferences preferences = ApplicationLoader.applicationContext.getSharedPreferences(spName, Activity.MODE_PRIVATE);
            SharedPreferences.Editor editor = preferences.edit();
            for (Map.Entry<String, JsonElement> config : ((JsonObject) element.getValue()).entrySet()) {
                String key = config.getKey();
                JsonPrimitive value = config.getValue().getAsJsonPrimitive();
                if (value.isBoolean()) {
                    editor.putBoolean(key, value.getAsBoolean());
                } else if (value.isNumber()) {
                    boolean isLong = false;
                    boolean isFloat = false;
                    if (key.endsWith("_long")) {
                        key = StringsKt.substringBeforeLast(key, "_long", key);
                        isLong = true;
                    } else if (key.endsWith("_float")) {
                        key = StringsKt.substringBeforeLast(key, "_float", key);
                        isFloat = true;
                    }
                    if (isLong) {
                        editor.putLong(key, value.getAsLong());
                    } else if (isFloat) {
                        editor.putFloat(key, value.getAsFloat());
                    } else {
                        editor.putInt(key, value.getAsInt());
                    }
                } else {
                    editor.putString(key, value.getAsString());
                }
            }
            editor.commit();
        }
        PushListenerController.reconcilePushRegistration();
    }

    public static void backupSettings(Context context, Theme.ResourcesProvider resourceProvider) {
        if (context == null) return;

        AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle(getString(R.string.BackupSettings));

        LinearLayout linearLayout = new LinearLayout(context);
        linearLayout.setOrientation(LinearLayout.VERTICAL);

        CheckBoxCell checkBoxCell = new CheckBoxCell(context, CheckBoxCell.TYPE_CHECK_BOX_DEFAULT, resourceProvider);
        checkBoxCell.setBackground(Theme.getSelectorDrawable(false));
        checkBoxCell.setText(getString(R.string.ExportSettingsIncludeApiKeys), "", false, false);
        checkBoxCell.setPadding(LocaleController.isRTL ? dp(16) : dp(8), 0, LocaleController.isRTL ? dp(8) : dp(16), 0);
        checkBoxCell.setChecked(false, false);
        checkBoxCell.setEnabled(false);
        // Credential export is intentionally unavailable for every variant.
        linearLayout.addView(checkBoxCell, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 48));

        builder.setView(linearLayout);
        builder.setPositiveButton(getString(R.string.ExportTheme), (dialog, which) -> {
            boolean includeApiKeys = false;
            try {
                File cacheFile = new File(AndroidUtilities.getCacheDir(), new Date() + ".nekox-settings.json");
                FileUtil.writeUtf8String(SettingsBackupHelper.backupSettingsJson(false, 4, includeApiKeys), cacheFile);
                ShareUtil.shareFile(context, cacheFile);
            } catch (Exception e) {
                AlertUtil.showSimpleAlert(context, new IllegalArgumentException("Settings backup could not be processed"));
            }
        });
        builder.setNegativeButton(getString(R.string.Cancel), null);
        builder.show();
    }

    private static boolean isDeviceSpecificPushKey(String key) {
        return key.equals(NaConfig.INSTANCE.getPushServiceTypeUnifiedSimple().getKey())
                || key.equals(NaConfig.INSTANCE.getPushServiceTypeUnifiedWebPushPrivateKey().getKey())
                || key.equals(NaConfig.INSTANCE.getPushServiceTypeUnifiedWebPushPublicKey().getKey())
                || key.equals(NaConfig.INSTANCE.getPushServiceTypeUnifiedWebPushAuthSecret().getKey());
    }
}
