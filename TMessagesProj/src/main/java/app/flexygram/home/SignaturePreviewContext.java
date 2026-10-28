/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

/** Row semantics, not numeric filter IDs. Forum summaries keep their native multi-topic text. */
public final class SignaturePreviewContext {
    private SignaturePreviewContext() {}
    public static boolean isMessageRow(boolean dialog, boolean topic, boolean shareStory,
                                       boolean dialogFolder, boolean forumSummary, boolean folderSummary) {
        return (dialog || topic) && !shareStory && !dialogFolder && !forumSummary && !folderSummary;
    }
}
