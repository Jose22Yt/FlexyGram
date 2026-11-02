/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.memberlens;

/** Existing client preferences; no separate store or observer. Opt-in by default. */
public final class MemberLensConfig {
    public static final String KEY="flexy_quick_member_lens";
    private MemberLensConfig() {}
    public static boolean enabled() { return tw.nekomimi.nekogram.NekoConfig.getPreferences().getBoolean(KEY,false); }
    public static void setEnabled(boolean value) { tw.nekomimi.nekogram.NekoConfig.getPreferences().edit().putBoolean(KEY,value).apply(); }
}
