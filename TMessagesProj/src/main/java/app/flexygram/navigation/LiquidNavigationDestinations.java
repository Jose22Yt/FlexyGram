/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

import java.util.ArrayList;

/** Stable destination IDs, deliberately independent from native pager positions. */
public final class LiquidNavigationDestinations {
    public static final int CHATS=0, CONTACTS=1, SETTINGS=2, CALLS=3, PROFILE=4,
            FEED=5, GROUPS=6, CHANNELS=7, SAVED=8, MORE=9;
    public static final int COUNT=9;
    private LiquidNavigationDestinations() {}
    public static int[] defaults() { return new int[]{CHATS,CONTACTS,SETTINGS,PROFILE}; }
    public static int[] sanitize(int[] input) {
        ArrayList<Integer> result=new ArrayList<>(COUNT);
        if (input != null) for (int id:input) {
            if (id>=0 && id<COUNT && !result.contains(id)) result.add(id);
        }
        if (!result.contains(CHATS)) {
            result.add(0,CHATS);
        }
        if (result.size()==1) result.add(SETTINGS);
        int[] ids=new int[result.size()];
        for (int i=0;i<ids.length;i++) ids[i]=result.get(i);
        return ids;
    }
    public static boolean contains(int[] ids,int id) {
        for (int value:ids) if (value==id) return true;
        return false;
    }
    /** Narrow windows use a real overflow destination, never sub-48dp overlapping tabs. */
    public static int[] fit(int[] order,int slots) {
        order=sanitize(order); slots=Math.max(2,Math.min(COUNT,slots));
        if (order.length<=slots) return order;
        int[] result=new int[slots];
        System.arraycopy(order,0,result,0,slots-1);
        result[slots-1]=MORE;
        if (!contains(result,CHATS)) result[slots-2]=CHATS;
        return result;
    }
}
