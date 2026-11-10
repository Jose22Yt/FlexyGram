package app.flexygram.composer;

import org.telegram.messenger.R;

/** Presentation only: the native state/gesture determines the action, never the theme. */
public final class ComposerIcons {
    private ComposerIcons() { }
    public static int resource(String state, int fallback, boolean reference) {
        switch (state) {
            case "VOICE": return R.drawable.flexy_composer_voice;
            case "VIDEO": return R.drawable.flexy_composer_video;
            case "SMILE": return R.drawable.flexy_composer_folded;
            case "KEYBOARD": return R.drawable.flexy_composer_keyboard;
            case "STICKER": return R.drawable.flexy_composer_folded;
            default: return fallback; // GIF/menu retain their native, labelled meaning.
        }
    }
}
