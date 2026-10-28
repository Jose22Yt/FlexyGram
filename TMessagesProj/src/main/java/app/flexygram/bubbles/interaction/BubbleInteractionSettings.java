/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.content.SharedPreferences;

/** Cached chat-scoped presentation preferences. No synchronous disk access per message tap. */
public final class BubbleInteractionSettings {
    private static final String FILE = "flexy_bubble_interaction";
    private static final String TAP = "tap_motion", PANEL = "signature_panel", STICKER = "sticker_conversion";
    private static volatile State cached;
    private BubbleInteractionSettings() {}
    private static final class State {
        final boolean tap, panel, sticker;
        State(boolean tap, boolean panel, boolean sticker) {
            this.tap=tap; this.panel=panel; this.sticker=sticker;
        }
    }
    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }
    private static State state(Context context) {
        State s=cached;
        if (s!=null) return s;
        synchronized (BubbleInteractionSettings.class) {
            if (cached==null) {
                SharedPreferences p=prefs(context);
                cached=new State(p.getBoolean(TAP,true),p.getBoolean(PANEL,false),p.getBoolean(STICKER,false));
            }
            return cached;
        }
    }
    public static boolean tapMotion(Context context) { return state(context).tap; }
    public static boolean signaturePanel(Context context) { return state(context).panel; }
    public static boolean stickerConversion(Context context) { return state(context).sticker; }
    public static synchronized void setTapMotion(Context context, boolean enabled) {
        State s=state(context);cached=new State(enabled,s.panel,s.sticker);
        prefs(context).edit().putBoolean(TAP,enabled).apply();
    }
    public static synchronized void setSignaturePanel(Context context, boolean enabled) {
        State s=state(context);cached=new State(s.tap,enabled,s.sticker);
        prefs(context).edit().putBoolean(PANEL,enabled).apply();
    }
    public static synchronized void setStickerConversion(Context context, boolean enabled) {
        State s=state(context);cached=new State(s.tap,s.panel,enabled);
        prefs(context).edit().putBoolean(STICKER,enabled).apply();
    }
}
