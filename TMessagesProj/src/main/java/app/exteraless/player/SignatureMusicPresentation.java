package app.exteraless.player;

import java.lang.ref.WeakReference;
import java.util.ArrayList;

/** UI-only session state; Telegram remains the only owner of playback and audio focus. */
public final class SignatureMusicPresentation {
    public interface Listener { void onPresentationChanged(); }
    private static boolean compact;
    private static final ArrayList<WeakReference<Listener>> listeners = new ArrayList<>();
    private SignatureMusicPresentation() {}
    public static boolean isCompact() { return compact; }
    public static void add(Listener listener) {
        remove(listener);
        listeners.add(new WeakReference<>(listener));
    }
    public static void remove(Listener listener) {
        for (int i = listeners.size() - 1; i >= 0; i--) {
            Listener value = listeners.get(i).get();
            if (value == null || value == listener) listeners.remove(i);
        }
    }
    public static void setCompact(boolean value) {
        if (compact == value) return;
        compact = value;
        // Snapshot only on a user action, never on a playback frame; callbacks may detach.
        ArrayList<WeakReference<Listener>> copy = new ArrayList<>(listeners);
        for (WeakReference<Listener> ref : copy) {
            Listener listener = ref.get();
            if (listener != null) listener.onPresentationChanged();
        }
    }
}
