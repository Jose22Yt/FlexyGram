/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.memberlens;

/** Immutable query identity; Telegram sender, never a forwarded author's identity. */
public final class MemberLensScope {
    public final int account;
    public final long dialogId, userId;
    public final int topicId;
    public MemberLensScope(int account, long dialogId, long userId, int topicId) {
        if (account < 0 || dialogId >= 0 || dialogId == Long.MIN_VALUE || userId <= 0 || topicId < 0)
            throw new IllegalArgumentException("Group, personal sender and topic scope required");
        this.account=account;this.dialogId=dialogId;this.userId=userId;this.topicId=topicId;
    }
    public boolean accepts(long dialog, long sender) { return dialog == dialogId && sender == userId; }
    public String key() { return account+":"+dialogId+":"+userId+":"+topicId; }
}
