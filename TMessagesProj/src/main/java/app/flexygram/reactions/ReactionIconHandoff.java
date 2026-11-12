/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.reactions;

/** Keep the inline icon until the overlay actually draws near its destination. */
public final class ReactionIconHandoff {
    private boolean frameVisible, landed, finished;
    public void update(boolean frameVisible, boolean landed) {
        this.frameVisible = frameVisible;
        this.landed = landed;
    }
    public void finish() { finished = true; }
    public boolean hidesIcon() { return !finished && frameVisible && landed; }
}
