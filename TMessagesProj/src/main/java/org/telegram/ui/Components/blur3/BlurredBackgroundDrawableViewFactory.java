package org.telegram.ui.Components.blur3;

import android.os.Build;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.Nullable;

import org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable;
import org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawableRenderNode;
import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundColorProvider;
import org.telegram.ui.Components.blur3.source.BlurredBackgroundSource;
import org.telegram.ui.Components.chat.ViewPositionWatcher;
import org.telegram.utils.glass.GlassEngine;

import java.lang.ref.WeakReference;
import java.util.ArrayList;

import me.vkryl.core.reference.ReferenceList;

public class BlurredBackgroundDrawableViewFactory {

    private final BlurredBackgroundSource source;
    private int outsetX, outsetY;

    public BlurredBackgroundDrawableViewFactory(BlurredBackgroundSource source) {
        this.source = source;
    }

    public BlurredBackgroundDrawableViewFactory(ViewPositionWatcher watcher, ViewGroup parent, BlurredBackgroundSource source) {
        this(source);
        setSourceRootView(watcher, parent);
    }

    public void setSourceRootView(ViewPositionWatcher watcher, ViewGroup parent) {
        this.viewPositionWatcher = watcher;
        this.parent = parent;
    }

    public void setGlassEngine(GlassEngine engine) {
        this.engine = engine;
    }

    public void setOutset(int outset) {
        setOutset(outset, outset);
    }

    public void setOutset(int dx, int dy) {
        outsetX = dx;
        outsetY = dy;
    }


    private @Nullable ReferenceList<BlurredBackgroundDrawable> linkedDrawables;
    private @Nullable ReferenceList<View> linkedViews;
    private @Nullable ViewPositionWatcher viewPositionWatcher;
    private @Nullable ViewGroup parent;
    private @Nullable GlassEngine engine;

    public void setLinkedViewsRef(@Nullable ReferenceList<View> linkedViews) {
        this.linkedViews = linkedViews;
    }

    public void unsubscribe(@Nullable View view) {
        if (viewPositionWatcher != null && view != null) {
            viewPositionWatcher.unsubscribe(view);
        }
    }

    public void setLinkedDrawablesRef(@Nullable ReferenceList<BlurredBackgroundDrawable> linkedDrawables) {
        this.linkedDrawables = linkedDrawables;
    }

    public void invalidateAllLinkedViews() {
        if (linkedViews != null) {
            for (View v : linkedViews) {
                v.invalidate();
            }
        }
    }


    private boolean isKyantEffectAllowed;
    // Factories outlive their views. Never retain a chat or a removed tab here.
    private final ArrayList<WeakReference<BlurredBackgroundDrawable>> createdDrawables = new ArrayList<>();
    private int creationsSincePrune;

    public void setKyantEffectAllowed(boolean allowed) {
        isKyantEffectAllowed = allowed;
        for (int i = createdDrawables.size() - 1; i >= 0; i--) {
            BlurredBackgroundDrawable drawable = createdDrawables.get(i).get();
            if (drawable == null) {
                createdDrawables.remove(i);
                continue;
            }
            if (Build.VERSION.SDK_INT >= 33 && drawable instanceof BlurredBackgroundDrawableRenderNode) {
                ((BlurredBackgroundDrawableRenderNode) drawable).setKyantEffectAllowed(allowed);
            }
            drawable.updateColors();
        }
    }

    public BlurredBackgroundDrawable create() {
        return create(null);
    }

    public BlurredBackgroundDrawable create(View view) {
        return create(view, null);
    }

    public BlurredBackgroundDrawable create(View view, boolean multiwindow) {
        return create(view, null, multiwindow);
    }

    public BlurredBackgroundDrawable create(View view, BlurredBackgroundColorProvider provider) {
        return create(view, provider, false);
    }

    public BlurredBackgroundDrawable create(View view, BlurredBackgroundColorProvider provider, boolean multiwindow) {
        return createInternal(view, provider, multiwindow, false);
    }

    /** Opt-in belongs to the requested surface, never to an entire screen or shared source. */
    public BlurredBackgroundDrawable createKyant(View view) { return createKyant(view, null); }

    public BlurredBackgroundDrawable createKyant(View view, BlurredBackgroundColorProvider provider) {
        return createInternal(view, provider, false, true);
    }

    private BlurredBackgroundDrawable createInternal(View view, BlurredBackgroundColorProvider provider,
                                                     boolean multiwindow, boolean kyantSurface) {
        final BlurredBackgroundDrawable drawable = source.createDrawable();
        if (++creationsSincePrune >= 32) {
            creationsSincePrune = 0;
            for (int i = createdDrawables.size() - 1; i >= 0; i--) {
                if (createdDrawables.get(i).get() == null) createdDrawables.remove(i);
            }
        }
        createdDrawables.add(new WeakReference<>(drawable));
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                && drawable instanceof BlurredBackgroundDrawableRenderNode) {
            BlurredBackgroundDrawableRenderNode node = (BlurredBackgroundDrawableRenderNode) drawable;
            node.setKyantSurface(kyantSurface);
            node.setKyantEffectAllowed(isKyantEffectAllowed);
        }

        drawable.setColorProvider(provider);
        drawable.setOutset(outsetX, outsetY);

        if (linkedViews != null && view != null) {
            linkedViews.add(view);
        }

        if (engine != null && view != null) {
            engine.registerDrawable(view, drawable);
        }

        if (viewPositionWatcher != null && parent != null && view != null) {
            final WeakReference<View> viewInstance = new WeakReference<>(view);
            viewPositionWatcher.subscribe(view, parent, (v, pos) -> {
                drawable.setSourceOffset(pos.left, pos.top);
                final View viewR = viewInstance.get();
                if (viewR != null) {
                    viewR.invalidate();
                }
            }, multiwindow);
        }

        if (linkedDrawables != null) {
            linkedDrawables.add(drawable);
        }

        return drawable;
    }
}
