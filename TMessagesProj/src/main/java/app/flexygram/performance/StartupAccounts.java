/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

/** Account zero owns Telegram's global preferences; the selected account follows it.
 * Every remaining account keeps its original relative order and initialization. */
public final class StartupAccounts {
    private StartupAccounts() { }
    public static int accountAt(int position, int selected, int count) {
        if (position < 0 || position >= count) throw new IndexOutOfBoundsException();
        if (selected <= 0 || selected >= count || position == 0) return position;
        if (position == 1) return selected;
        return position <= selected ? position - 1 : position;
    }
}
