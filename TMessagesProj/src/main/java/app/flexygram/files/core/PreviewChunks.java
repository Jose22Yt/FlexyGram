/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files.core;

import java.util.ArrayList;
import java.util.List;

/**
 * Pure, bounded text chunker for RecyclerView-based file previews.
 * Runs on the selected-file worker, not the Android UI thread.
 * Does not normalize line endings or break UTF-16 surrogate pairs.
 */
public final class PreviewChunks {
    private PreviewChunks() {}

    public static List<String> split(String value, int budget) {
        if (value == null || budget < 32) throw new IllegalArgumentException("invalid preview chunk");
        ArrayList<String> chunks = new ArrayList<>(Math.max(1, value.length() / budget + 1));
        int start = 0;
        while (start < value.length()) {
            int end = Math.min(value.length(), start + budget);
            if (end < value.length()) {
                int newline = value.lastIndexOf('\n', end - 1);
                if (newline >= start + budget / 2) {
                    end = newline + 1;
                } else if (Character.isHighSurrogate(value.charAt(end - 1))
                        && Character.isLowSurrogate(value.charAt(end))) {
                    --end;
                }
            }
            chunks.add(value.substring(start, end));
            start = end;
        }
        if (chunks.isEmpty()) chunks.add("");
        return chunks;
    }
}
