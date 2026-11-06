/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;

import android.content.SharedPreferences;
import app.flexygram.studio.core.*;
import org.telegram.messenger.*;
import org.telegram.ui.LauncherIconController;
import java.io.IOException;
import java.util.*;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicReference;

/** Complete portable client settings. File names and keys always come from native metadata. */
final class StudioClientBackup {
    private StudioClientBackup() {}
    static String snapshot() { return snapshotLike(null); }
    static String snapshotLike(String encodedScope) {
        Map<String,Object> scope=encodedScope==null?null:object(StudioCodec.decodeValues(encodedScope));
        Map<String,Object> scopeFiles=scope==null?null:object(scope.get("files"));
        StudioClientCatalog catalog = new StudioClientCatalog();
        Map<String,Object> files = new TreeMap<>();
        for (Map.Entry<String,Map<String,StudioClientCatalog.Spec>> file : catalog.files().entrySet()) {
            if(scopeFiles!=null&&!scopeFiles.containsKey(file.getKey()))continue;
            Map<String,Object> scoped=scopeFiles==null?null:object(scopeFiles.get(file.getKey()));
            Map<String,?> values = catalog.preferences(file.getKey()).getAll();
            Map<String,Object> settings = new TreeMap<>();
            for (Map.Entry<String,StudioClientCatalog.Spec> item : file.getValue().entrySet()) {
                if(scoped!=null&&!scoped.containsKey(item.getKey()))continue;
                Map<String,Object> slot = new TreeMap<>();
                boolean present = values.containsKey(item.getKey());
                slot.put("present", present);
                if (present) slot.put("value", item.getValue().encode(values.get(item.getKey())));
                settings.put(item.getKey(), slot);
            }
            files.put(file.getKey(), settings);
        }
        Map<String,Object> result = new TreeMap<>();
        result.put("version", 1); result.put("files", files);
        if(scope==null||scope.containsKey("icon"))result.put("icon", activeIcon());
        if(scope==null||scope.containsKey("theme"))result.put("theme", StudioClientTheme.snapshot());
        return StudioCodec.encodeValues(result);
    }
    private static String activeIcon() {
        for (LauncherIconController.LauncherIcon icon : LauncherIconController.LauncherIcon.values())
            if (LauncherIconController.isEnabled(icon)) return icon.name();
        return "EXTERALESS";
    }
    static Map<String,Object> object(Object value) {
        if (!(value instanceof Map)) throw new IllegalArgumentException("client_object");
        return (Map<String,Object>) value;
    }
    static Map<String,Object> validate(String encoded) {
        Map<String,Object> root = object(StudioCodec.decodeValues(encoded));
        if (!root.keySet().containsAll(Arrays.asList("version","files"))
                || !new HashSet<>(Arrays.asList("version","files","icon","theme")).containsAll(root.keySet())
                || !Long.valueOf(1).equals(root.get("version"))) throw new IllegalArgumentException("client_version");
        StudioClientCatalog catalog = new StudioClientCatalog();
        Map<String,Object> files = object(root.get("files"));
        if (files.isEmpty()&&!root.containsKey("icon")&&!root.containsKey("theme")) throw new IllegalArgumentException("client_empty");
        for (Map.Entry<String,Object> file : files.entrySet()) {
            Map<String,StudioClientCatalog.Spec> specs = catalog.files().get(file.getKey());
            if (specs == null) throw new StudioSchema.Unsupported("client."+file.getKey());
            for (Map.Entry<String,Object> setting : object(file.getValue()).entrySet()) {
                StudioClientCatalog.Spec spec = specs.get(setting.getKey());
                if (spec == null) throw new StudioSchema.Unsupported("client."+setting.getKey());
                Map<String,Object> slot = object(setting.getValue());
                if (!(slot.get("present") instanceof Boolean)) throw new IllegalArgumentException("client_presence");
                boolean present = (Boolean)slot.get("present");
                if (!slot.keySet().equals(present ? new HashSet<>(Arrays.asList("present","value")) : Collections.singleton("present"))) throw new IllegalArgumentException("client_slot");
                if (present) spec.validate(slot.get("value"));
            }
        }
        if(root.containsKey("icon"))LauncherIconController.LauncherIcon.valueOf((String)root.get("icon"));
        Object main=files.get("mainconfig");
        if(main!=null && object(main).containsKey("language")) {
            Map<String,Object> language=object(object(main).get("language"));
            if(Boolean.TRUE.equals(language.get("present"))) {
                String code=(String)language.get("value");
                if(!onUi(() -> LocaleController.getInstance().getLanguageFromDict(code)!=null))throw new StudioSchema.Unsupported("client.language");
            }
        }
        if(root.containsKey("theme"))StudioClientTheme.validate(root.get("theme"));
        return root;
    }
    static void apply(String encoded) throws Exception {
        // Validate the whole document before the first edit. The outer transaction journals the current snapshot.
        Map<String,Object> root = validate(encoded);
        StudioClientCatalog catalog = new StudioClientCatalog();
        for (Map.Entry<String,Object> file : object(root.get("files")).entrySet()) {
            SharedPreferences.Editor editor = catalog.preferences(file.getKey()).edit();
            for (Map.Entry<String,Object> setting : object(file.getValue()).entrySet()) {
                Map<String,Object> slot = object(setting.getValue());
                if (!(Boolean)slot.get("present")) editor.remove(setting.getKey());
                else catalog.files().get(file.getKey()).get(setting.getKey()).write(editor, setting.getKey(), slot.get("value"));
            }
            if (!editor.commit()) throw new IOException("client_preferences");
        }
        onUi(() -> {
            if(root.containsKey("icon"))LauncherIconController.setIcon(LauncherIconController.LauncherIcon.valueOf((String)root.get("icon")));
            reload(); return null;
        });
        app.exteraless.icons.IconPackManager.getInstance().reloadInternal();
        if(root.containsKey("theme"))StudioClientTheme.apply(root.get("theme"));
    }
    static void reload() {
        app.flexygram.home.HomeStyleConfig.load();
        tw.nekomimi.nekogram.NekoConfig.loadConfig(true);
        xyz.nextalone.nagram.NaConfig.INSTANCE.loadConfig(true);
        app.exteraless.OpenExteraConfig.INSTANCE.loadConfig(true);
        app.exteraless.appearance.AppearanceConfig.INSTANCE.loadConfig(true);
        app.exteraless.chats.ChatsConfig.INSTANCE.loadConfig(true);
        app.exteraless.general.GeneralConfig.INSTANCE.loadConfig(true);
        app.exteraless.icons.IconPacksConfig.INSTANCE.loadConfig(true);
        app.exteraless.pillstack.PillStackConfig.INSTANCE.loadConfig(true);
        app.exteraless.utils.UtilsConfig.INSTANCE.loadConfig(true);
        app.exteraless.glyph.GlyphConfig.INSTANCE.loadConfig(true);
        SharedConfig.reloadStudioSettings();
        LocaleController.getInstance().reloadStudioLanguage();
        app.exteraless.appearance.AppearanceConfig.invalidateDividerStyle();
        LiteMode.loadPreference();
        app.flexygram.animation.FastMotionConfig.load();
        app.flexygram.bubbles.BubbleConfig.load();
        app.flexygram.header.HeaderConfig.load();
        app.flexygram.bubbles.interaction.BubbleInteractionSettings.reload();
        app.flexygram.inlineconverter.InlineConversionConfig.reload();
        app.flexygram.navigation.LiquidNavigationConfig.reload();
        app.flexygram.home.SignatureSmartPreviews.reload();
    }
    interface UiTask<T> { T run() throws Exception; }
    static <T> T onUi(UiTask<T> task) {
        if (android.os.Looper.myLooper() == android.os.Looper.getMainLooper()) {
            try { return task.run(); } catch(Exception failed) { throw new IllegalStateException(failed); }
        }
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<T> result = new AtomicReference<>();
        AtomicReference<Exception> error = new AtomicReference<>();
        AndroidUtilities.runOnUIThread(() -> { try { result.set(task.run()); } catch(Exception failed) { error.set(failed); } finally { done.countDown(); } });
        // A queued UI mutation must finish before rollback can start; never time out then mutate later.
        boolean interrupted = false;
        for (;;) { try { done.await(); break; } catch(InterruptedException signal) { interrupted = true; } }
        if (interrupted) Thread.currentThread().interrupt();
        if (error.get() != null) throw new IllegalStateException(error.get());
        return result.get();
    }
}
