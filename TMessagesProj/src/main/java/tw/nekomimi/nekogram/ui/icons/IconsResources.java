package tw.nekomimi.nekogram.ui.icons;

import android.annotation.SuppressLint;
import android.content.res.Resources;
import android.content.res.Configuration;
import android.util.DisplayMetrics;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import android.graphics.drawable.Drawable;
import android.util.LruCache;

import androidx.annotation.Nullable;

import app.exteraless.icons.IconPackManager;

import xyz.nextalone.nagram.NaConfig;

@SuppressLint("UseCompatLoadingForDrawables")
public class IconsResources extends Resources {

    public static final int ICON_REPLACE_SOLAR = 1;
    private int _iconsType = -1;
    private final LruCache<Long, Drawable.ConstantState> constantStates = new LruCache<>(300);
    private final Object cacheLock = new Object();
    private volatile long cacheGeneration;
    private Configuration warmedConfiguration;
    private int[] warmedSources;
    private final AtomicBoolean warming = new AtomicBoolean();
    private static final ThreadPoolExecutor PRELOADER = new ThreadPoolExecutor(0, 1, 1, TimeUnit.SECONDS,
            new ArrayBlockingQueue<>(1), task -> {
                Thread thread = new Thread(() -> {
                    android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_BACKGROUND);
                    task.run();
                }, "FlexyIconPreload");
                thread.setDaemon(true);
                return thread;
            }, new ThreadPoolExecutor.AbortPolicy());

    @Override
    public void updateConfiguration(Configuration config, DisplayMetrics metrics) {
        super.updateConfiguration(config, metrics);
        // Resources constructors can call this override before subclass fields exist.
        if (cacheLock == null) return;
        synchronized (cacheLock) {
            cacheGeneration++;
            warmedConfiguration = null;
            warmedSources = null;
            constantStates.evictAll();
        }
    }

    /** Only static source PNG IDs; no Theme, Views, icon-pack manager or shared tinted drawables. */
    public Runnable preloadOriginalIcons(int[] sources) {
        if (sources == null || sources.length == 0 || sources.length > 32) return null;
        final int[] ids;
        final Configuration configuration;
        final long generation;
        synchronized (cacheLock) {
            if (getConfiguration().equals(warmedConfiguration) && java.util.Arrays.equals(sources, warmedSources)) return null;
            if (warming.get()) return null;
            ids = sources.clone();
            configuration = new Configuration(getConfiguration());
            warming.set(true);
            generation = cacheGeneration;
        }
        final AtomicBoolean cancelled = new AtomicBoolean();
        try {
            PRELOADER.execute(() -> {
                boolean completed = false;
                try {
                    for (int id : ids) {
                        if (cancelled.get() || generation != cacheGeneration) return;
                        long key = ((long) id << 32);
                        if (constantStates.get(key) != null) continue;
                        // Bypass replacement/config code; framework decode is thread-safe.
                        Drawable source = super.getDrawableForDensity(id, 0, null);
                        Drawable.ConstantState state = source != null ? source.getConstantState() : null;
                        synchronized (cacheLock) {
                            if (cancelled.get() || generation != cacheGeneration) return;
                            if (state != null && !state.canApplyTheme()) constantStates.put(key, state);
                        }
                    }
                    completed = true;
                } catch (RuntimeException | OutOfMemoryError unavailable) {
                    // Opportunistic only: a miss still uses the normal synchronous resource path.
                } finally {
                    synchronized (cacheLock) {
                        if (completed && !cancelled.get() && generation == cacheGeneration
                                && configuration.equals(getConfiguration())) {
                            warmedConfiguration = configuration;
                            warmedSources = ids;
                        }
                        warming.set(false);
                    }
                }
            });
        } catch (RejectedExecutionException busy) {
            warming.set(false);
            return null;
        }
        return () -> cancelled.set(true);
    }


    public IconsResources(Resources resources) {
        super(resources.getAssets(), resources.getDisplayMetrics(), resources.getConfiguration());
    }

    @Override
    public Drawable getDrawable(int id) throws NotFoundException {
        return getDrawableForDensity(id, 0, null);
    }

    @Override
    public Drawable getDrawable(int id, @Nullable Theme theme) throws NotFoundException {
        return getDrawableForDensity(id, 0, theme);
    }

    @Nullable
    @Override
    public Drawable getDrawableForDensity(int id, int density, @Nullable Theme theme) {
        // openExtera: сначала спрашиваем установленные паки иконок
        Drawable fromPack = IconPackManager.getInstance().getDrawable(this, id, density, theme);
        if (fromPack != null) {
            return fromPack;
        }
        return getOriginalDrawableForDensity(id, density, theme);
    }

    @Nullable
    @Override
    public Drawable getDrawableForDensity(int id, int density) throws NotFoundException {
        return getDrawableForDensity(id, density, null);
    }

    /**
     * openExtera: оригинальный drawable (с учётом Solar-подмены, но без паков иконок).
     * Нужен менеджеру паков, чтобы узнать исходный размер иконки без рекурсии.
     */
    @Nullable
    public Drawable getOriginalDrawableForDensity(int id, int density, @Nullable Theme theme) {
        Drawable exact = app.flexygram.icons.ExactIcons.create(this, id, density, theme);
        if (exact != null) return exact;
        int converted = getConversion(id);
        long key = ((long) converted << 32) | (density & 0xffffffffL);
        Drawable.ConstantState state = constantStates.get(key);
        if (state != null) {
            return state.newDrawable(this).mutate();
        }
        // Только super.getDrawableForDensity: это терминальная реализация в Resources.
        // super.getDrawable(...) звать нельзя — он внутри вызывает виртуальный
        // getDrawableForDensity, попадает обратно в наш override и уходит в рекурсию.
        // density == 0 базовый Resources трактует как «без переопределения плотности».
        Drawable drawable = super.getDrawableForDensity(converted, density, theme);
        Drawable.ConstantState loaded = drawable != null ? drawable.getConstantState() : null;
        if (loaded == null || loaded.canApplyTheme()) {
            return drawable;
        }
        constantStates.put(key, loaded);
        return loaded.newDrawable(this).mutate();
    }

    private int getConversion(int icon) {
        return getConversion(icon, -1);
    }

    private int getConversion(int icon, int forcedIconsType) {
        if (_iconsType == -1) {
            _iconsType = NaConfig.INSTANCE.getIconReplacements().Int();
        }

        int consideredIconsType = forcedIconsType == -1 ? _iconsType : forcedIconsType;

        if (consideredIconsType == ICON_REPLACE_SOLAR) {
            return SolarIcons.Companion.getConversion(icon);
        }

        return icon;
    }
}
