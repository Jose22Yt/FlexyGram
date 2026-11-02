/* SPDX-License-Identifier: GPL-3.0-or-later */
import app.flexygram.navigation.LiquidNavigationDestinations;
import java.util.Arrays;

/** Pure JVM regression tests for editable FlexyGram bottom tabs. */
public final class BottomTabsDestinationsTest {
    private static void expect(boolean ok, String label) {
        if (!ok) throw new AssertionError(label);
    }
    private static void equals(int[] expected, int[] actual, String label) {
        expect(Arrays.equals(expected, actual),
                label + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
    }
    public static void main(String[] args) {
        final int CHATS = LiquidNavigationDestinations.CHATS;
        final int SEARCH = LiquidNavigationDestinations.SEARCH;
        final int MORE = LiquidNavigationDestinations.MORE;
        expect(LiquidNavigationDestinations.MAX_VISIBLE == 6, "six slot limit");
        expect(!LiquidNavigationDestinations.isSelectable(MORE), "overflow is never an editable destination");
        expect(LiquidNavigationDestinations.isSelectable(SEARCH), "search is editable");
        expect(!LiquidNavigationDestinations.isSelectable(-1), "reject negative ids");
        expect(!LiquidNavigationDestinations.isSelectable(12), "reject unknown ids");

        equals(new int[]{CHATS, SEARCH}, LiquidNavigationDestinations.sanitize(
                new int[]{MORE, SEARCH, SEARCH, -8}), "restore chats, remove duplicates and overflow");
        equals(new int[]{CHATS, LiquidNavigationDestinations.SETTINGS},
                LiquidNavigationDestinations.sanitize(new int[]{CHATS}), "minimum two");
        equals(new int[]{SEARCH, LiquidNavigationDestinations.PROFILE, CHATS},
                LiquidNavigationDestinations.sanitize(new int[]{SEARCH, LiquidNavigationDestinations.PROFILE, CHATS}),
                "preserve explicit order");
        equals(new int[]{CHATS, SEARCH, 8, 7, 6, 5},
                LiquidNavigationDestinations.sanitize(new int[]{SEARCH, 8, 7, 6, 5, 4, 3}),
                "six slots including mandatory chats");

        int[] six = new int[]{CHATS, 1, 2, 3, 4, SEARCH};
        equals(six, LiquidNavigationDestinations.fit(six, 6), "no overflow on six slots");
        equals(new int[]{CHATS, MORE},
                LiquidNavigationDestinations.fit(six, 2), "narrow bar retains chats and overflow");
        equals(new int[]{CHATS, 1, 2, MORE},
                LiquidNavigationDestinations.fit(six, 4), "overflow visible at four slots");
        equals(new int[]{CHATS, MORE},
                LiquidNavigationDestinations.fit(new int[]{SEARCH, CHATS, 1, 2}, 2),
                "mandatory chats visible even when reordered");
        System.out.println("OK: bottom-tabs destination cases passed");
    }
}
