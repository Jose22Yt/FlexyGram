package org.telegram.ui;

import android.content.ComponentName;
import android.content.Context;
import android.content.pm.PackageManager;

import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.R;

public class LauncherIconController {
    public static void tryFixLauncherIconIfNeeded() {
        // Preserve existing PackageManager overrides, including all legacy aliases.
        LauncherIcon active = null;
        int count = 0;
        for (LauncherIcon icon : LauncherIcon.values()) if (isEnabled(icon)) { active = icon; count++; }
        Context context = ApplicationLoader.applicationContext;
        int legacyState = context.getPackageManager().getComponentEnabledSetting(legacyPrimary(context));
        boolean legacyEnabled = legacyState == PackageManager.COMPONENT_ENABLED_STATE_ENABLED;
        String saved = ApplicationLoader.applicationContext.getSharedPreferences("flexy_launcher", Context.MODE_PRIVATE).getString("selected", "");
        LauncherIcon remembered = null;
        try { remembered = LauncherIcon.valueOf(saved); }
        catch (IllegalArgumentException ignored) { }
        if (count == 1 && !legacyEnabled && (remembered == null || active == remembered)) return;
        if (remembered != null) active = remembered;
        try {
            applyIcon(active == null ? LauncherIcon.FLEX_NEON : active, false);
        } catch (IllegalArgumentException | SecurityException rejected) {
            // Atomic migration rejected: keep the existing launcher and retry next startup.
        }
    }

    public static boolean isEnabled(LauncherIcon icon) {
        Context ctx = ApplicationLoader.applicationContext;
        int i = ctx.getPackageManager().getComponentEnabledSetting(icon.getComponentName(ctx));
        // Manifest default is effective before the process starts. Explicit overrides survive updates.
        return i == PackageManager.COMPONENT_ENABLED_STATE_ENABLED
                || i == PackageManager.COMPONENT_ENABLED_STATE_DEFAULT && icon == LauncherIcon.FLEX_NEON;
    }

    private static ComponentName legacyPrimary(Context ctx) {
        return new ComponentName(ctx.getPackageName(), "org.telegram.messenger.ExteralessIcon");
    }
    public static void setIcon(LauncherIcon icon) { applyIcon(icon, true); }
    private static void applyIcon(LauncherIcon icon, boolean explicit) {
        Context ctx = ApplicationLoader.applicationContext;
        PackageManager pm = ctx.getPackageManager();
        if (android.os.Build.VERSION.SDK_INT >= 33) {
            java.util.ArrayList<PackageManager.ComponentEnabledSetting> changes = new java.util.ArrayList<>();
            for (LauncherIcon i : LauncherIcon.values()) {
                changes.add(new PackageManager.ComponentEnabledSetting(i.getComponentName(ctx), i == icon
                    ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED : PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                    PackageManager.DONT_KILL_APP));
            }
            changes.add(new PackageManager.ComponentEnabledSetting(legacyPrimary(ctx),
                    PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP));
            pm.setComponentEnabledSettings(changes);
        } else {
            // Enable the destination first: a failed switch must never remove the only launcher entry.
            pm.setComponentEnabledSetting(icon.getComponentName(ctx), PackageManager.COMPONENT_ENABLED_STATE_ENABLED, PackageManager.DONT_KILL_APP);
            for (LauncherIcon i : LauncherIcon.values()) if (i != icon) {
                pm.setComponentEnabledSetting(i.getComponentName(ctx), PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
            }
        }
        if (android.os.Build.VERSION.SDK_INT < 33) {
            pm.setComponentEnabledSetting(legacyPrimary(ctx), PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
        }
        android.content.SharedPreferences.Editor editor = ctx.getSharedPreferences("flexy_launcher", Context.MODE_PRIVATE).edit();
        editor.putInt("signature_launcher_migration", 2);
        if (explicit) editor.putString("selected", icon.name());
        editor.apply();
    }

    public enum LauncherIcon {
        FLEX_NEON("FlexyNeonIcon", R.drawable.flexy_neon_background, R.drawable.flexy_neon_foreground, R.string.FlexyIconNeon),
        FLEX_GLOSSY("FlexyGlossyIcon", R.drawable.flexy_glossy_background, R.drawable.flexy_glossy_foreground, R.string.FlexyIconGlossy),
        FLEX_COSMIC("FlexyCosmicIcon", R.drawable.flexy_cosmic_background, R.drawable.flexy_cosmic_foreground, R.string.FlexyIconCosmic),
        FLEX_CYBER("FlexyCyberIcon", R.drawable.flexy_cyber_background, R.drawable.flexy_cyber_foreground, R.string.FlexyIconCyber),
        EXTERALESS("FlexyBlueIcon", R.drawable.flexy_blue_background,
                R.drawable.flexy_blue_foreground, R.string.FlexyIconBlue),
        FLEX_GREEN("FlexyGreenIcon", R.drawable.flexy_green_background, R.drawable.flexy_green_foreground, R.string.FlexyIconGreen),
        FLEX_CORAL("FlexyCoralIcon", R.drawable.flexy_coral_background, R.drawable.flexy_coral_foreground, R.string.FlexyIconCoral),
        FLEX_MONO("FlexyMonoIcon", R.drawable.flexy_mono_background, R.drawable.flexy_mono_foreground, R.string.FlexyIconMono),
        FLEX_BLUEPRINT("FlexyBlueprintIcon", R.drawable.flexy_blueprint_background, R.drawable.flexy_blueprint_foreground, R.string.FlexyIconBlueprint),
        FLEX_NYA("FlexyNyaIcon", R.drawable.flexy_nya_background, R.drawable.flexy_nya_foreground, R.string.FlexyIconNya),
        FLEX_QUACK("FlexyQuackIcon", R.drawable.flexy_quack_background, R.drawable.flexy_quack_foreground, R.string.FlexyIconQuack),
        FLEX_GO("FlexyGoIcon", R.drawable.flexy_go_background, R.drawable.flexy_go_foreground, R.string.FlexyIconGo),
        LEGACY_EXTERALESS("FlexyLegacyExteralessIcon", R.drawable.exteraless_icon_background, R.drawable.exteraless_icon_foreground, R.string.FlexyIconLegacy),
        BLUEPRINT("BlueprintIcon", R.drawable.blueprint_icon_background,
                R.drawable.blueprint_icon_foreground, R.string.AppIconBlueprint),
        RED("RedIcon", R.drawable.red_icon_background,
                R.drawable.red_icon_foreground, R.string.AppIconRed),
        NYA("NyaIcon", R.drawable.nya_icon_background,
                R.drawable.nya_icon_foreground, R.string.AppIconNya),
        AYU("AyuIcon", R.drawable.ayu_icon_background,
                R.drawable.ayu_icon_foreground, R.string.AppIconAyu),
        QUACK("QuackIcon", R.drawable.quack_icon_background,
                R.drawable.quack_icon_foreground, R.string.AppIconQuack),
        GO("GoIcon", R.drawable.go_icon_background,
                R.drawable.app_icon_empty_foreground, R.string.AppIconGo),
        HAND("HandIcon", R.drawable.hand_icon_background,
                R.drawable.app_icon_empty_foreground, R.string.AppIconHand),
        MONO("MonoIcon", R.drawable.mono_icon_background,
                R.drawable.app_icon_empty_foreground, R.string.AppIconMono),
        NOTHING("NothingIcon", R.drawable.nothing_icon_background,
                R.drawable.app_icon_empty_foreground, R.string.AppIconNothing),
        PLUS("PlusIcon", R.drawable.plus_icon_background,
                R.drawable.app_icon_empty_foreground, R.string.AppIconPlus),
        TELEGRAM("TelegramIcon", R.drawable.icon_background_sa, R.mipmap.icon_foreground_sa, R.string.AppIconTelegramOriginal),
        VINTAGE("VintageIcon", R.drawable.icon_6_background_sa, R.mipmap.icon_6_foreground_sa, R.string.AppIconVintage),
        AQUA("AquaIcon", R.drawable.icon_4_background_sa, R.mipmap.icon_foreground_sa, R.string.AppIconAqua),
        PREMIUM("PremiumIcon", R.drawable.icon_3_background_sa, R.mipmap.icon_3_foreground_sa, R.string.AppIconPremium),
        TURBO("TurboIcon", R.drawable.icon_5_background_sa, R.mipmap.icon_5_foreground_sa, R.string.AppIconTurbo),
        NOX("NoxIcon", R.mipmap.icon_2_background_sa, R.mipmap.icon_foreground_sa, R.string.AppIconNox);

        public final String key;
        public final int background;
        public final int foreground;
        public final int title;
        public final boolean premium;

        private ComponentName componentName;

        public ComponentName getComponentName(Context ctx) {
            if (componentName == null) {
                componentName = new ComponentName(ctx.getPackageName(), "org.telegram.messenger." + key);
            }
            return componentName;
        }

        LauncherIcon(String key, int background, int foreground, int title) {
            this(key, background, foreground, title, false);
        }

        LauncherIcon(String key, int background, int foreground, int title, boolean premium) {
            this.key = key;
            this.background = background;
            this.foreground = foreground;
            this.title = title;
            this.premium = premium;
        }

    }
}
