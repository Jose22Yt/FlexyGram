/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

/** Age of the last actual connectivity query, not of the last cache consumer. */
public final class NetworkSnapshotAge {
    private NetworkSnapshotAge() { }
    public static boolean expired(long now, long lastQuery) {
        return lastQuery < 0 || now < lastQuery || now - lastQuery > 5000;
    }
}
