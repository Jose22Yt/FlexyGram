package app.exteraless.player;

import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;

/** Lifecycle-bound adapter, driven by the host's existing Telegram observers. */
public final class SignatureMusicHost implements SignatureMusicPresentation.Listener {
    private final BaseFragment fragment;
    private final Theme.ResourcesProvider provider;
    private final Runnable refresh;
    private SignatureMusicBubble bubble;
    public SignatureMusicHost(BaseFragment fragment, Theme.ResourcesProvider provider, Runnable refresh) {
        this.fragment = fragment; this.provider = provider; this.refresh = refresh;
    }
    public void attach() {
        SignatureMusicPresentation.add(this);
        if (bubble == null) bubble = SignatureMusicBubble.attach(fragment);
    }
    public boolean canCompact() { return bubble != null; }
    public void update(boolean allowed) {
        if (bubble == null) bubble = SignatureMusicBubble.attach(fragment);
        if (bubble != null) bubble.update(allowed, PlayerColors.isDark(provider));
    }
    public void detachFromWindow() {
        SignatureMusicPresentation.remove(this);
        if (bubble != null) { bubble.releaseFromWindow(); bubble = null; }
    }
    public void detach() {
        SignatureMusicPresentation.remove(this);
        if (bubble != null) { bubble.release(); bubble = null; }
    }
    @Override public void onPresentationChanged() { refresh.run(); }
}
