/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

/** Account zero owns Telegram's global preferences; the selected account follows it.
 * All configurations retain their original relative order; empty controller slots stay lazy. */
public final class StartupAccounts {
    private StartupAccounts() { }
    public static boolean needsControllers(int account, int selected, boolean activated) {
        // Account zero owns native global services; selected may be the login account.
        return account == 0 || account == selected || activated;
    }
    public static int accountAt(int position, int selected, int count) {
        if (position < 0 || position >= count) throw new IndexOutOfBoundsException();
        if (selected <= 0 || selected >= count || position == 0) return position;
        if (position == 1) return selected;
        return position <= selected ? position - 1 : position;
    }
}
